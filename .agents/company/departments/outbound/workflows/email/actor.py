#!/usr/bin/env python3
"""Outbound email ACT helper: PREPARE builds the batch, EXECUTE sends it.

PREPARE applies the intervention's levers (cohort filters, subject rotation),
composes per-lead emails in STRICT mode (unprepared leads are skipped), and
dedupes domains within the batch. EXECUTE is the deterministic paced send:
daily cap honored, sent-log + provider dedupe, transient retries with
backoff, quota errors switch providers, every send is recorded in the
sent log and the action ledger.
"""

import threading
import time
from datetime import datetime, timezone

from . import compose, config, content as content_bank, outbound, providers
from .templates import SIGNATURE_HTML, SIGNATURE_TEXT


def prepare(ctx, intervention: dict) -> dict:
    knobs = ctx.control.knobs()
    filters = dict(knobs.get("cohort_filters") or {})
    levers = intervention.get("levers") or {}
    if "cohort_filters" in levers:
        filters.update(levers["cohort_filters"])

    if levers.get("rotate_subjects"):
        for seg in (levers.get("subject_rotation") or {}):
            content_bank.rotate_bank(seg, note="act: subject lever applied")

    queue = compose.pick_queue(filters)
    cap, phase = outbound.daily_cap()
    knob_cap = knobs.get("daily_cap")
    if knob_cap:
        cap = min(cap, int(knob_cap))
    used_today = outbound.sent_today(outbound.load_sent_log())
    slice_size = min(knobs.get("block_size") or config.BLOCK_SIZE,
                     max(0, cap - used_today))
    if slice_size <= 0:
        return {"id": intervention.get("batch_id", "unset"), "emails": [],
                "skipped": [], "reason": "daily cap reached"}

    batch_id = intervention.get("batch_id", "unset")
    hypothesis = intervention.get("prediction") or "research-first: per-lead hook + pain hypothesis"
    built = compose.build_batch_emails(batch_id, queue[:slice_size], hypothesis)
    return {"id": batch_id, "hypothesis": hypothesis,
            "emails": built["emails"], "skipped": built["skipped"],
            "filters": filters, "cap": {"cap": cap, "phase": phase,
                                        "used_today": used_today},
            "intervention": intervention}


def _send_with_cap(provider, to_email, subject, body_html, body_text, reply_to, cap_s=180):
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
    """Provider-side dedupe guard: has this address received a send in the
    last `hours`? Returns provider id, None (clean), or "unknown" (check
    failed)."""
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


def execute(ctx, batch: dict, dry: bool = False) -> dict:
    batch_id = batch.get("id", "UNNAMED")
    emails = batch.get("emails", [])
    if not emails:
        return {"sent": 0, "failed": 0, "deduped": 0, "note": "empty batch"}

    log = outbound.load_sent_log()
    contacts = outbound.read_contacts(lang_filter=None, tier_filter=None)
    by_id = {c["lead_id"]: c for c in contacts}

    cap, phase = outbound.daily_cap()
    used_today = outbound.sent_today(log)
    if used_today + len(emails) > cap:
        return {"sent": 0, "failed": 0, "deduped": 0,
                "note": f"batch would exceed daily cap ({used_today} + {len(emails)} > {cap})"}

    for e in emails:
        c = by_id.get(e["lead_id"])
        if c is None:
            return {"sent": 0, "failed": 0, "deduped": 0,
                    "note": f"lead_id {e['lead_id']} not found in the contact list"}
        if outbound.already_sent(e["lead_id"], log):
            return {"sent": 0, "failed": 0, "deduped": 0,
                    "note": f"lead_id {e['lead_id']} is already in the sent log — refusing duplicate"}
        if not e.get("subject") or not e.get("body_html") or not e.get("body_text"):
            return {"sent": 0, "failed": 0, "deduped": 0,
                    "note": f"lead_id {e['lead_id']}: subject/body_html/body_text all required"}

    if dry:
        return {"sent": 0, "failed": 0, "deduped": 0,
                "note": f"DRY RUN — {len(emails)} emails validated, nothing sent"}

    sent_count = 0
    fail_count = 0
    deduped_count = 0
    excluded = set()

    for i, e in enumerate(emails):
        c = by_id[e["lead_id"]]
        feat = e.get("features", {})
        provider = providers.pick_provider(log, exclude=excluded)
        log = outbound.load_sent_log()
        if outbound.already_sent(c["lead_id"], log):
            deduped_count += 1
            continue
        pri = _provider_sent_id(c["email"])
        if pri not in (None, "unknown"):
            log.setdefault("sent", []).append({
                "lead_id": c["lead_id"], "email": c["email"], "company": c["company"],
                "contact_name": c["contact_name"], "variant": "researched-personal",
                "batch": batch_id, "subject": e["subject"],
                "provider": config.EMAIL_PROVIDER, "provider_id": str(pri),
                "resend_id": str(pri), "deduped": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **{f"feat_{k}": v for k, v in feat.items()},
            })
            outbound.save_sent_log(log)
            deduped_count += 1
            continue

        body_html = e["body_html"].replace("{SIGNATURE_HTML}", SIGNATURE_HTML).replace("{SIGNATURE_TEXT}", SIGNATURE_TEXT)
        body_text = e["body_text"].replace("{SIGNATURE_HTML}", SIGNATURE_HTML).replace("{SIGNATURE_TEXT}", SIGNATURE_TEXT)

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
            time.sleep(10 * attempts)

        if result.get("error") or not str(result.get("id") or "").strip():
            err_msg = str(result.get("message", ""))
            if ("daily_quota_exceeded" in err_msg or "monthly_quota_exceeded" in err_msg
                    or result.get("status") == 429):
                excluded.add(provider)
            log.setdefault("failed", []).append({
                "lead_id": c["lead_id"], "email": c["email"], "company": c["company"],
                "provider": provider, "error": result.get("message", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            fail_count += 1
            ctx.store.record_action(c["lead_id"], "email", "send_email", "failed",
                                    str(result.get("message", "unknown"))[:200])
        else:
            for f in log.get("failed", []):
                if isinstance(f, dict) and f.get("lead_id") == c["lead_id"] and not f.get("resolved_at"):
                    f["resolved_at"] = datetime.now(timezone.utc).isoformat()
            log.setdefault("sent", []).append({
                "lead_id": c["lead_id"], "email": c["email"], "company": c["company"],
                "contact_name": c["contact_name"], "variant": "researched-personal",
                "batch": batch_id, "subject": e["subject"],
                "provider": provider, "provider_id": result.get("id"),
                "resend_id": result.get("id"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **{f"feat_{k}": v for k, v in feat.items()},
            })
            outbound.save_sent_log(log)
            sent_count += 1
            ctx.store.record_action(c["lead_id"], "email", "send_email", "sent",
                                    f"batch {batch_id}")

        if i < len(emails) - 1:
            time.sleep(config.THROTTLE_SECONDS)

    outbound.save_sent_log(log)
    return {"sent": sent_count, "failed": fail_count, "deduped": deduped_count,
            "note": f"cap {used_today + sent_count}/{cap} after this batch ({phase})"}
