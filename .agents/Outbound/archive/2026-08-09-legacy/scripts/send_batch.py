#!/usr/bin/env python3
"""
SpielOS Outbound — send a curated batch of researched-personal emails.

Usage:
    python3 send_batch.py <batch.json>

Batch JSON schema:
    {
      "batch": "BATCH-YYYY-MM-DD-01",          # unique batch id
      "hypothesis": "one-line hypothesis being tested",
      "emails": [
        {"lead_id": "EN-002", "subject": "...", "body_html": "...", "body_text": "..."}
      ]
    }

Rules enforced (deterministic, see SKILL.md Part 4 "Deterministic sending rules"):
  * daily send cap (warmup ramp + provider hard cap) — refuses to exceed it
  * every lead must exist and be unsent — refuses on mismatch
  * 1 email every THROTTLE_SECONDS (10 min default) = ~60 min per 6-batch
  * provider 429 quota error stops the batch immediately
  * logs each send to sent_log.json with variant "researched-personal"
"""

import json
import sys
import threading
import time
from datetime import datetime, timezone

import config
import outbound
import providers
from templates import SIGNATURE_HTML, SIGNATURE_TEXT


def _send_with_cap(provider, to_email, subject, body_html, body_text, reply_to, cap_s=180):
    """Send with a hard wall-clock cap. A hung transport (dead DNS, dead IP)
    must never stall a batch: past the cap the batch logs the failure and
    moves on; the lead stays queued for the next day's retry."""
    box = {}

    def _run():
        box["r"] = providers.send_email_via(provider, to_email, subject, body_html,
                                             body_text, reply_to=reply_to)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(cap_s)
    if t.is_alive():
        return {"error": True, "status": 0,
                "message": f"send exceeded {cap_s}s cap (hung transport); not sent"}
    return box.get("r", {"error": True, "status": 0, "message": "no result"})


def _provider_sent_id(email, hours=24):
    """Ask the provider whether this address already received a send in the
    last `hours`. Returns the provider id if found, None if clean, or the
    string "unknown" when the check itself failed (network/auth). This is the
    idempotency guard against double sends when a previous send's response was
    lost (a previous killed/hung batch can have created emails the log never
    recorded)."""
    try:
        r = providers._open(
            "https://api.resend.com/emails?limit=100",
            headers={"Authorization": f"Bearer {providers.RESEND_API_KEY}"},
        )
        if r.get("error"):
            return "unknown"
        cutoff = time.time() - hours * 3600
        for e in r.get("data", []):
            raw = ((e.get("created_at") or "")[:19]).replace("T", " ", 1)
            try:
                ts = time.mktime(time.strptime(raw, "%Y-%m-%d %H:%M:%S"))
            except ValueError:
                continue
            if ts < cutoff:
                continue
            tos = e.get("to") or []
            tos = tos if isinstance(tos, list) else [tos]
            if email in tos:
                return e.get("id") or "?"
        return None
    except Exception:
        return "unknown"


def main() -> None:
    argv = sys.argv[1:]
    dry = "--dry" in argv
    argv = [a for a in argv if a != "--dry"]
    forced_provider = None
    if "--provider" in argv:
        i = argv.index("--provider")
        if i + 1 < len(argv):
            forced_provider = argv[i + 1]
            argv = argv[:i] + argv[i + 2:]
    if len(argv) != 1:
        print(__doc__)
        sys.exit(1)

    path = argv[0]
    with open(path) as f:
        batch = json.load(f)

    batch_id = batch.get("batch", "UNNAMED")
    emails = batch.get("emails", [])
    if not emails:
        print(f"❌ {path}: no emails in batch")
        sys.exit(1)

    log = outbound.load_sent_log()
    contacts = outbound.read_contacts(lang_filter=None, tier_filter=None)
    by_id = {c["lead_id"]: c for c in contacts}

    cap, phase = outbound.daily_cap()
    used_today = outbound.sent_today(log)
    if used_today + len(emails) > cap:
        print(f"❌ Batch would exceed daily cap: {used_today} sent today + {len(emails)} "
              f"= {used_today + len(emails)} > {cap} ({phase}).")
        print("   Split the batch or wait for the next UTC day.")
        sys.exit(1)

    for e in emails:
        c = by_id.get(e["lead_id"])
        if c is None:
            print(f"❌ lead_id {e['lead_id']} not found in the contact list")
            sys.exit(1)
        if outbound.already_sent(e["lead_id"], log):
            print(f"❌ lead_id {e['lead_id']} is already in sent_log.json — refusing duplicate")
            sys.exit(1)
        if not e.get("subject") or not e.get("body_html") or not e.get("body_text"):
            print(f"❌ lead_id {e['lead_id']}: subject/body_html/body_text all required")
            sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  BATCH {batch_id} — {len(emails)} researched-personal emails")
    print(f"  Hypothesis: {batch.get('hypothesis', '(none)')}")
    print(f"  Rate: 1 email every {config.THROTTLE_SECONDS}s "
          f"(~{len(emails) * config.THROTTLE_SECONDS / 60:.0f} min total)")
    print(f"  Daily cap: {used_today + len(emails)}/{cap} after this batch ({phase})")
    print(f"  Reply-To: {config.REPLY_TO}")
    print(f"{'='*60}\n")

    if dry:
        print("  DRY RUN — no emails will be sent. Batch validated:")
        for e in emails:
            c = by_id[e["lead_id"]]
            wc = len(e["body_text"].replace("{SIGNATURE_TEXT}", "").replace("{SIGNATURE_HTML}", "").split())
            print(f"    ✓ {c['lead_id']:>7} {e['subject']:<30} <{c['email']}> ({wc} words)")
        print()
        return

    sent_count = 0
    fail_count = 0
    excluded = set()  # providers that hit quota today — rest of the batch moves on

    for i, e in enumerate(emails):
        c = by_id[e["lead_id"]]
        feat = e.get("features", {})
        provider = forced_provider or providers.pick_provider(log, exclude=excluded)
        # Reload the log from disk every iteration. If a sibling batch child
        # (e.g. orphaned by a daemon kill) appended while we slept, its sends
        # must be honored — never send a lead that another run already sent.
        log = outbound.load_sent_log()
        if outbound.already_sent(c["lead_id"], log):
            print(f"  [{i+1}/{len(emails)}] {c['lead_id']} {c['company']} "
                  f"<{c['email']}> | SKIP (already in sent_log from another run)")
            sent_count += 1
            continue
        pri = _provider_sent_id(c["email"])
        if pri not in (None, "unknown"):
            print(f"  [{i+1}/{len(emails)}] {c['lead_id']} {c['company']} "
                  f"<{c['email']}> | ALREADY SENT (provider id {str(pri)[:18]}, dedupe skip)")
            log.setdefault("sent", []).append({
                "lead_id": c["lead_id"],
                "email": c["email"],
                "company": c["company"],
                "contact_name": c["contact_name"],
                "variant": "researched-personal",
                "batch": batch_id,
                "subject": e["subject"],
                "provider": config.EMAIL_PROVIDER,
                "provider_id": str(pri),
                "resend_id": str(pri),
                "deduped": True,
                "timestamp": datetime.utcnow().isoformat(),
                **{f"feat_{k}": v for k, v in feat.items()},
            })
            outbound.save_sent_log(log)
            sent_count += 1
            continue
        if pri == "unknown":
            print(f"      ⚠ provider dedupe check failed; sending anyway (risk of duplicate)")

        body_html = e["body_html"].replace("{SIGNATURE_HTML}", SIGNATURE_HTML).replace("{SIGNATURE_TEXT}", SIGNATURE_TEXT)
        body_text = e["body_text"].replace("{SIGNATURE_HTML}", SIGNATURE_HTML).replace("{SIGNATURE_TEXT}", SIGNATURE_TEXT)
        print(f"  [{i+1}/{len(emails)}] {c['lead_id']} {c['company']} "
              f"<{c['email']}> | {e['subject']}", flush=True)

        # Transient failures (hung transport, timeouts, 5xx, unknown) retry
        # with backoff before landing in failed[]; quota errors never retry —
        # they switch providers for the rest of the batch instead.
        _TRANSIENT_MARKERS = ("transport", "timeout", "timed out", "hung",
                              "temporarily", "5", "no result")
        result = None
        attempts = 0
        while True:
            result = _send_with_cap(
                provider, c["email"], e["subject"], body_html, body_text,
                reply_to=config.REPLY_TO,
            )
            if not (result.get("error") or not str(result.get("id") or "").strip()):
                break
            err_msg = str(result.get("message", ""))
            is_quota = ("daily_quota_exceeded" in err_msg or "monthly_quota_exceeded" in err_msg
                        or result.get("status") == 429)
            is_transient = result.get("status") == 0 or any(
                m in err_msg.lower() for m in _TRANSIENT_MARKERS)
            attempts += 1
            if is_quota or not is_transient or attempts >= 3:
                break
            print(f"      ⚠ transient failure ({err_msg[:60]}) — retry {attempts}/2 in {10*attempts}s", flush=True)
            time.sleep(10 * attempts)

        if result.get("error") or not str(result.get("id") or "").strip():
            print(f"      ❌ FAILED — {result.get('message', 'no id returned (treating as failure)')}")
            err_msg = str(result.get("message", ""))
            if ("daily_quota_exceeded" in err_msg or "monthly_quota_exceeded" in err_msg
                    or result.get("status") == 429):
                print(f"      ⛔ Provider {provider} quota exceeded (429) — switching "
                      f"providers for the rest of the batch", flush=True)
                excluded.add(provider)
            log.setdefault("failed", []).append({
                "lead_id": c["lead_id"],
                "email": c["email"],
                "company": c["company"],
                "provider": provider,
                "error": result.get("message", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
            })
            fail_count += 1
        else:
            print(f"      ✅ id={result.get('id', '?')[:16]}...")
            for f in log.get("failed", []):
                if isinstance(f, dict) and f.get("lead_id") == c["lead_id"] and not f.get("resolved_at"):
                    f["resolved_at"] = datetime.utcnow().isoformat()
            log.setdefault("sent", []).append({
                "lead_id": c["lead_id"],
                "email": c["email"],
                "company": c["company"],
                "contact_name": c["contact_name"],
                "variant": "researched-personal",
                "batch": batch_id,
                "subject": e["subject"],
                "provider": provider,
                "provider_id": result.get("id"),
                "resend_id": result.get("id"),
                "timestamp": datetime.utcnow().isoformat(),
                **{f"feat_{k}": v for k, v in feat.items()},
            })
            outbound.save_sent_log(log)
            sent_count += 1

        if i < len(emails) - 1:
            time.sleep(config.THROTTLE_SECONDS)

    outbound.save_sent_log(log)

    print(f"\n{'='*60}")
    print(f"  BATCH COMPLETE — Sent: {sent_count}, Failed: {fail_count}")
    print(f"  Next: wait ≥60 min, then `python3 outbound.py metrics --force`,")
    print(f"        then `python3 outbound.py experiment --text \"...\"`")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
