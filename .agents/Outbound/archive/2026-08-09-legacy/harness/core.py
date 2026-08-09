#!/usr/bin/env python3
"""
Harness — core: THE loop. One entry point, called by the pipeline after every
batch. It runs the full cycle: OBSERVE -> DIAGNOSE -> SELECT -> HYPOTHESIS ->
MEASURE -> LEARN -> UPDATE STATE -> REPORT.

    python3 harness/core.py <batch_id> [--apply]

--apply actually writes the chosen lever into content_variables.json /
state.json (the renderer reads them on the next batch). Without it the
engine reports the decision but does not act — safe for dry cycles.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
# Outbound dir as well — this module runs BOTH as an imported package (from
# the daemon, which already set the path) and as a standalone subprocess
# (run_block spawns `python3 ../harness/core.py` with cwd=scripts). Without
# the parent dir on the path, `from harness import ...` dies with
# ModuleNotFoundError and the whole cycle is silently skipped — the engine
# ran without DIAGNOSE/LEARN for days before this fix.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import analytics  # noqa: E402
import config  # noqa: E402
import outbound  # noqa: E402

from harness import measure, reflect, report, state, variables  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
AUTO_DIR = os.path.join(HERE, "..", "scripts", "experiments", "auto")


def _enrich_batch_emails(batch_id: str, log: dict, metrics: dict) -> list:
    """Rebuild per-email records for one batch from sent_log + metrics,
    adding opened/replied flags so cohort slices can be computed."""
    sent = [s for s in log.get("sent", []) if s.get("batch") == batch_id]
    replied = analytics._reply_ids(metrics)
    out = []
    for s in sent:
        rec = metrics.get("emails", {}).get(s["lead_id"], {})
        status = rec.get("status") or ""
        out.append({
            **s,
            "opened": status in ("opened", "clicked"),
            "replied": s["lead_id"] in replied,
        })
    return out


def gate() -> dict:
    """Deterministic pre-block gate (GUARDRAILS). Called BEFORE a batch is
    built/sent. Returns {ok, breaches: [...]}. Any breach refuses the block
    UNLESS the engine's cohort filter already removed the offending cohort
    (bounce evidence: 9/10 bounces were unverified role addresses — with
    skip_unverified=true the remaining queue's expected bounce is ~0).
    Spam and delivery breaches are never downgraded: hard halt."""
    log = outbound.load_sent_log()
    metrics = analytics.load_metrics()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    window_log = {
        "sent": [s for s in log.get("sent", []) if str(s.get("timestamp", "")) >= cutoff],
        "failed": log.get("failed", []),
    }
    totals = analytics.aggregate(window_log, metrics)
    breaches = reflect.guardrail_breaches(totals, state.load()["meta"])
    # OWNER-LEVEL SPAM OVERRIDE (time-boxed, journaled, sender-suppressed):
    # a single complaint hard-halts for the 48h window with no legitimate
    # way to clear earlier. The owner can time-box an override in engine.json
    # (gate_spam_override_until, ISO UTC) — only demotes the spam breach, and
    # only until the timestamp. After expiry any in-window complaint
    # re-hard-halts. Never overrides bounce/delivery/data breaches.
    warnings = []
    try:
        eng = json.load(open(os.path.join(AUTO_DIR, "engine.json")))
        until = str(eng.get("gate_spam_override_until") or "")
        if until and breaches:
            until_dt = datetime.fromisoformat(until)
            if datetime.now(timezone.utc) < until_dt:
                kept = [b for b in breaches if b["name"] != "spam rate"]
                if len(kept) != len(breaches):
                    breaches = kept
                    warnings.append(
                        f"spam rate breach overridden by owner until {until} "
                        f"(complained sender suppressed in master)")
    except Exception:
        pass  # no override file/format -> gate behaves as designed
    problems = reflect.data_problems(totals)
    unverified = (totals.get("unknown", 0) + totals.get("denied", 0)
                  + totals.get("unresolved", 0))
    noisy_data = unverified >= max(5, totals.get("sent", 0) * 0.1)
    if not breaches and not noisy_data:
        return {"ok": True, "breaches": [], "problems": []}
    if not breaches and noisy_data:
        return {"ok": False, "breaches": [], "problems": problems,
                "warnings": ["data unverified — metrics not trustworthy"]}

    filters = state.get_variable(state.load(), "cohort_filters", {}) or {}
    hard = [b for b in breaches if b["name"] != "bounce rate"]
    if not hard:
        # Bounce-breach downgrade ONLY when the fix actually covers the
        # evidence: every bounced email in metrics must already be suppressed
        # in the master. Any unsuppressed bounce = the fix lags = hard halt.
        log = outbound.load_sent_log()
        id2email = {s.get("lead_id"): str(s.get("email") or "").lower()
                    for s in log.get("sent", [])}
        bounced_emails = {id2email.get(k) for k, v in metrics.get("emails", {}).items()
                          if v.get("status") == "bounced"}
        bounced_emails.discard(None)
        if bounced_emails:
            master_status = {}
            for c in outbound.read_contacts():
                master_status[str(c.get("email") or "").lower()] = \
                    (c.get("email_status") or "").strip()
            unsuppressed = [e for e in bounced_emails
                            if "suppressed" not in master_status.get(e, "").lower()]
            if not unsuppressed:
                return {"ok": True, "breaches": [], "problems": problems,
                        "warnings": [f"bounce breach downgraded: all "
                                     f"{len(bounced_emails)} window bounces are "
                                     "suppressed in the master"]}
            return {"ok": False, "breaches": breaches, "problems": problems,
                    "warnings": [f"unsuppressed bounces in window: "
                                 f"{unsuppressed[:5]} — run verify.py sync-bounces"]}
    return {"ok": False, "breaches": breaches, "problems": problems}


def cycle(batch_id: str, apply: bool = False) -> dict:
    st = state.load()
    log = outbound.load_sent_log()
    metrics = analytics.load_metrics()
    totals = analytics.aggregate(log, metrics)
    sent_total = totals["sent"]
    sent_today = outbound.sent_today(log)
    cap, phase = outbound.daily_cap()

    # WINDOW TOTALS (owner rule 2026-08-09): the gate judges the 48h window
    # with bounce suppression; the cycle's diagnosis must speak the same
    # language. All-time totals stay in the report; the weakest-link and the
    # guardrail levers run on the window.
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    window_log = {"sent": [s for s in log.get("sent", [])
                           if str(s.get("timestamp", "")) >= cutoff],
                  "failed": log.get("failed", [])}
    window_totals = analytics.aggregate(window_log, metrics)

    # 1. OBSERVE — goals status + data problems. Guardrail verdict comes from
    # the gate (the single authority — same 48h window, suppression and
    # owner overrides), never re-judged from raw totals.
    goals = reflect.goals_status(totals, st["meta"])
    problems = reflect.data_problems(totals)
    gate_breaches = gate().get("breaches") or []

    # 1b. BOUNCE LEVER — evidence-driven queue depth, tracked on the GATE's
    # verdict. A window breach means the risky tier is bouncing again: only
    # verified leads send until the 48h window decays; when it clears, the
    # queue deepens automatically.
    bounce_breach = any(b["name"] == "bounce rate" for b in gate_breaches)
    filters = state.get_variable(st, "cohort_filters", {}) or {}
    current_min = str(filters.get("min_tier") or "plausible").lower()
    if apply:
        if bounce_breach and current_min != "verified":
            st["variables"]["cohort_filters"] = {**filters, "min_tier": "verified"}
            st["variables"].setdefault("notes", {})["cohort_filters"] = (
                f"{datetime.now(timezone.utc).isoformat()} — bounce window breach: "
                "min_tier=verified (only L2/Apollo-verified leads send) until the "
                "48h window decays; idle-time probing grows the verified pool")
            state.save(st)
            print(f"lever: bounce breach -> min_tier=verified (queue deepens when window clears)")
        elif not bounce_breach and current_min == "verified":
            st["variables"]["cohort_filters"] = {**filters, "min_tier": "plausible"}
            st["variables"].setdefault("notes", {})["cohort_filters"] = (
                f"{datetime.now(timezone.utc).isoformat()} — bounce window clear: "
                "min_tier released back to plausible")
            state.save(st)
            print(f"lever: bounce window clear -> min_tier=plausible")

    # 2. DIAGNOSE — weakest link (window totals + gate verdict)
    filters = state.get_variable(st, "cohort_filters", {}) or {}
    skip_unverified = bool(filters.get("skip_unverified"))
    weak = reflect.weakest_link(window_totals, st["meta"], sent_total,
                                skip_unverified, breaches=gate_breaches)
    weakest_text = weak["detail"] if weak else "—"

    # 3. MEASURE — verdict on the previous batch's experiment
    prev = state.last_batch(st)
    prev_verdict = None
    if prev and prev.get("lever"):
        target = prev.get("target_metric", "reply_rate")
        cur = {"metrics": {"sent": totals["sent"],
                           **{k: totals.get(k) for k in
                              ("delivered_rate", "open_rate", "click_rate",
                               "reply_rate", "bounce_rate", "spam_rate")}}}
        prev_verdict = measure.verdict(prev, cur, target)
        # LEARN — persist the verdict into the variable's history
        if apply and prev.get("variable"):
            state.record_knowledge(st, prev["variable"], {
                "at": datetime.now(timezone.utc).isoformat(),
                "from": prev.get("from"),
                "to": prev.get("to"),
                "target_metric": target,
                "before": prev.get("metrics", {}).get(target),
                "after": totals.get(target),
                "verdict": prev_verdict["verdict"],
            })

    # 4. SELECT LEVER — the weakest link maps to a variable; history-aware
    next_lever = None
    if apply and weak and weak.get("actionable"):
        variable = weak["variable"]
        knowledge = state.knowledge_for(st, variable)
        last_verdict = knowledge.get("verdict")
        if last_verdict == "reject":
            # tried and failed before — do not repeat the same change
            next_lever = (f"{variable}: already tried & rejected "
                          f"({len(knowledge.get('tried', []))} trial(s)) — needs a NEW angle")
        else:
            next_lever = variable

    # 5. HYPOTHESIS + APPLY (subject lever: rotate the active bank)
    hypothesis = None
    if next_lever == "subject":
        from_bank = variables.load_content()
        rotated_note = []
        for seg, bank in from_bank.get("subject_patterns", {}).items():
            if len(bank) > 1:
                rotated = bank[1:] + bank[:1]
                variables.set_subject_bank(seg, rotated, note="cycle rotation")
                rotated_note.append(f"{seg}: {bank[0]} -> {rotated[0]}")
        hypothesis = (f"subject: rotate active bank per segment "
                      f"({' ; '.join(rotated_note[:3])}) "
                      f"so open rate improves; reason: repetitive subjects "
                      f"suppress opens")
    elif next_lever == "cta":
        hypothesis = ("cta: shorten question so reply costs ~10s; reason: "
                      "opens fine but reply rate is the gap")
    elif next_lever == "cohort_unverified":
        hypothesis = ("cohort: skip 'Publicly listed; not deliverability-verified' "
                      "emails; reason: 9/10 bounces are unverified role addresses, "
                      "bounces suppress opens and replies")
        if apply:
            state.set_variable(st, "cohort_filters",
                               {"skip_unverified": True},
                               note="bounce evidence: unverified role addresses")
            next_lever = "cohort_unverified (skip_unverified=true)"

    # 6. REPORT — write the cycle report + persist the batch record
    batch_record = {
        "id": f"CYC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
        "batch": batch_id,
        "at": datetime.now(timezone.utc).isoformat(),
        "metrics": {k: totals.get(k) for k in
                    ("sent", "delivered", "opened", "clicked", "replied",
                     "delivered_rate", "open_rate", "click_rate", "reply_rate",
                     "bounce_rate", "spam_rate", "unknown", "denied", "unresolved")},
        "sent_today": sent_today,
        "cap": cap,
        "weakest": weak,
        "lever": weak.get("variable") if weak and weak.get("actionable") else None,
        "variable": weak.get("variable") if weak and weak.get("actionable") else None,
        "from": None,
        "to": next_lever,
        "target_metric": "reply_rate",
        "hypothesis": hypothesis,
        "problems": problems,
    }
    state.append_batch(st, batch_record)

    record = {
        "id": batch_record["id"],
        "batch": batch_id,
        "sent_total": sent_total,
        "sent_today": sent_today,
        "cap": cap,
        "totals": totals,
        "meta": st["meta"],
        "guardrail_breaches": gate_breaches,
        "weakest_text": weakest_text,
        "previous_verdict": prev_verdict,
        "next_lever": next_lever,
        "hypothesis": hypothesis,
        "problems": problems,
    }
    report.write_report(record)
    return record


def main():
    argv = sys.argv[1:]
    apply_flag = "--apply" in argv
    argv = [a for a in argv if a != "--apply"]
    batch_id = argv[0] if argv else "manual"
    record = cycle(batch_id, apply=apply_flag)
    print(report.status_line(record))
    if record.get("problems"):
        for p in record["problems"]:
            print(f"  ⚠ {p}")
    if record.get("guardrail_breaches"):
        for b in record["guardrail_breaches"]:
            print(f"  ⛔ GUARDRAIL {b['name']} {b['current']*100:.2f}% > {b['max']*100:.2f}%")
    if record.get("next_lever"):
        print(f"  LEVER -> {record['next_lever']}")
    if record.get("hypothesis"):
        print(f"  HYPOTHESIS: {record['hypothesis']}")


if __name__ == "__main__":
    main()
