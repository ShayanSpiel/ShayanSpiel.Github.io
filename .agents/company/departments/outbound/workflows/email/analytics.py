#!/usr/bin/env python3
"""
Outbound Department — email analytics.

Pulls delivery/engagement status for every sent email from the provider and
stores per-email snapshots in metrics.json, then computes aggregates:
send rate, deliverability (delivered / bounced / complained=spam),
open rate, click rate, reply rate.

Reply detection is two-channel:
  1. Automatic — replies routed to a Resend receiving domain (set REPLY_TO
     to e.g. replies@in.spielos.xyz) are pulled via the received-emails API
     on every scheduled `metrics` run and matched to the sent lead.
     Auto-replies (out-of-office, ...) are recorded as kind="auto" and
     excluded from the reply-rate goal.
  2. Manual — anything that lands in the normal inbox:
     `python3 outbound.py record-reply <email|lead_id>`.

Provider honesty:
  - last_event covers: sent, delivered, delivery_delayed, opened, clicked,
    complained (recipient marked it as spam), bounced, failed, suppressed.
  - Inbox folder placement (Gmail Primary/Promotions/Spam) is NOT exposed by
    any sending API. `complained` + `bounced` are the closest signals; true
    placement checks need Google Postmaster or a seed list.

Usage (via outbound.py):
  python3 outbound.py metrics [--force] [--quiet]
"""

import json
from datetime import datetime, timedelta, timezone

from . import config, providers


def cap_status_supported() -> bool:
    return providers.cap_status()

# last_event values that mean the email reached the recipient's mail server
_DELIVERED = {"delivered", "opened", "clicked", "complained"}
# last_event values that mean the recipient engaged
_OPENED = {"opened", "clicked"}

_AUTO_REPLY_KEYWORDS = tuple(
    k.strip().casefold()
    for k in config.AUTO_REPLY_KEYWORDS.split(",")
    if k.strip()
)


# ── Persistence ───────────────────────────────────────────────────────────────

def load_metrics() -> dict:
    if config.METRICS_PATH.exists():
        with open(config.METRICS_PATH) as f:
            return json.load(f)
    return {"last_check": None, "emails": {}, "replies": []}


def save_metrics(metrics: dict) -> None:
    with open(config.METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2, default=str)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _valid_id(email_id) -> bool:
    return bool(email_id) and len(str(email_id)) >= 32


def _date_dist(a, b) -> float:
    pa, pb = _parse_dt(a), _parse_dt(b)
    if pa is None or pb is None:
        return float("inf")
    return abs((pa - pb).total_seconds())


def is_due(metrics: dict, force: bool = False) -> bool:
    """Scheduled check: only pull when the last check is older than
    METRICS_INTERVAL_HOURS (or never ran, or --force)."""
    if force or not metrics.get("last_check"):
        return True
    last = _parse_dt(metrics["last_check"])
    if last is None:
        return True
    return datetime.now(timezone.utc) - last >= timedelta(hours=config.METRICS_INTERVAL_HOURS)


# ── Collection ────────────────────────────────────────────────────────────────

def resolve_missing_ids(log: dict) -> dict:
    """Backfill missing/truncated provider ids by matching the provider's
    sent-email list on recipient + subject (resend only — see capabilities)."""
    if not providers.cap_list_sent():
        return {}
    missing = [s for s in log.get("sent", []) if not _valid_id(s.get("provider_id") or s.get("resend_id"))]
    if not missing:
        return {}
    listing = providers.list_sent_emails()
    if listing.get("error"):
        return {}
    resolved = {}
    for s in missing:
        candidates = [
            e for e in listing.get("data", [])
            if s.get("email") in (e.get("to") or [])
            and (s.get("subject") or "").casefold() == (e.get("subject") or "").casefold()
        ]
        if len(candidates) == 1:
            resolved[s["lead_id"]] = candidates[0]["id"]
        elif len(candidates) > 1:
            best = min(candidates, key=lambda e: _date_dist(e.get("created_at"), s.get("timestamp")))
            resolved[s["lead_id"]] = best["id"]
    return resolved


def collect(log: dict, force: bool = False):
    """Fetch the latest provider status for every sent email (and detect
    replies via the receiving API). Returns (metrics, ran) — ran is False
    when the scheduled check is not due yet."""
    metrics = load_metrics()
    if not is_due(metrics, force):
        return metrics, False

    resolved = resolve_missing_ids(log)
    emails = metrics.setdefault("emails", {})
    checked_at = datetime.now(timezone.utc).isoformat()

    if not providers.cap_status():
        return metrics, True  # provider has no tracking; nothing to collect

    # Resend fast path: one list call carries last_event for every recent
    # send (~8s each individually was making a full collect take an hour).
    resend_map = {}
    try:
        listing = providers.list_sent_emails()
        if not listing.get("error"):
            resend_map = {
                e.get("id"): e.get("last_event")
                for e in (listing.get("data") or []) if e.get("id")
            }
    except Exception:
        pass

    # WINDOW BOUND (owner rule 2026-08-09): the gate judges the last 48h.
    # Sends older than the window with a settled status never re-fetch —
    # the per-email provider path (mailgun: up to 9 calls, brevo: 1, plus
    # 5s error sleeps) is what made a full collect take 15+ minutes. The
    # reply sync below is provider-side and covers ALL ages, so the reply
    # rate stays complete; open/click history is already on disk.
    window_start = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()

    for s in log.get("sent", []):
        lead_id = s["lead_id"]
        email_id = s.get("provider_id") or s.get("resend_id")
        if not _valid_id(email_id):
            email_id = resolved.get(lead_id)
        if not _valid_id(email_id):
            rec = emails.setdefault(lead_id, {})
            rec["provider_id"] = None
            rec["status"] = "unresolved"
            rec["checked_at"] = checked_at
            continue

        provider = s.get("provider") or ""
        import time as _time
        rec_prev = emails.get(lead_id, {})
        prev_status = str(rec_prev.get("status") or "")
        prev_check = rec_prev.get("checked_at") or ""
        settled_old = bool(
            str(s.get("timestamp") or "") < window_start
            and prev_status and not prev_status.startswith(
                ("unknown", "unresolved", "denied", "error"))
        )
        fresh = False
        try:
            prev_dt = datetime.fromisoformat(str(prev_check))
            fresh = (datetime.now(timezone.utc) - prev_dt).total_seconds() < 3600
        except Exception:
            fresh = False
        if provider == "resend" and email_id in resend_map:
            status = {"last_event": resend_map[email_id]}
        elif settled_old or (
                fresh and prev_status and not prev_status.startswith(
                    ("unknown", "unresolved", "denied", "error"))):
            # settled beyond the gate's window, or already resolved within
            # the hour — skip the slow per-email provider fetch. The cheap
            # resend fast path above still runs every collect.
            continue
        else:
            for _attempt in range(2):  # flaky outbound network — one cheap retry
                status = providers.fetch_email_status(email_id, provider=provider or "")
                if not status.get("error"):
                    break
                _time.sleep(5)
        if status.get("error"):
            event = None
            code = status.get("status")
            err = f"{code}:{status.get('message') or ''}"[:200]
            denied = code in (401, 403, 404)
        else:
            event = status.get("last_event") or "unknown"
            err = None
            denied = False

        rec = emails.setdefault(lead_id, {})
        rec["provider_id"] = email_id
        rec["checked_at"] = checked_at
        if event is None:
            if rec.get("status") and not str(rec.get("status")).startswith(("error", "unknown", "unresolved", "denied")):
                pass  # keep the last verified status
            else:
                rec["status"] = "denied" if denied else "unknown"
            rec["last_error"] = err
        else:
            rec["status"] = event
            rec.pop("last_error", None)
        rec.setdefault("history", []).append({"at": checked_at, "status": event or rec["status"]})
        # PROGRESS SAVE (owner rule 2026-08-09): a killed collect used to lose
        # the whole pass. Persist every 50 emails so a timeout only loses the
        # last slice, never the whole window.
        if len(emails) % 50 == 0:
            metrics["last_check"] = checked_at
            save_metrics(metrics)

    # Retry ledger reconciliation: a failed entry whose lead is now in sent[]
    # was retried successfully on a later block — mark it resolved so it stops
    # counting against the day and pick_provider stops banning the provider
    # for it (owner rule 2026-08-08: failed[] was write-only; 17 dead emails
    # counted against the goal forever).
    sent_ids = {s["lead_id"] for s in log.get("sent", [])}
    changed = False
    for f in log.get("failed", []):
        if isinstance(f, dict) and not f.get("resolved_at") and f.get("lead_id") in sent_ids:
            f["resolved_at"] = checked_at
            changed = True
    if changed:
        try:
            from outbound import save_sent_log
            save_sent_log(log)
        except Exception:
            pass

    metrics["last_check"] = checked_at
    sync_replies(log, metrics)
    save_metrics(metrics)
    return metrics, True


def _is_auto_reply(subject: str) -> bool:
    subj = (subject or "").casefold()
    return any(kw in subj for kw in _AUTO_REPLY_KEYWORDS)


def sync_replies(log: dict, metrics: dict) -> int:
    """Pull received emails from the provider and record those that match a
    sent lead as replies (deduped by received email id). Auto-replies are
    recorded with kind="auto". Returns the number of newly recorded."""
    if not providers.cap_received():
        return 0
    listing = providers.list_received_emails()
    if listing.get("error"):
        return 0

    sent_by_email = {s["email"]: s for s in log.get("sent", [])}
    replies = metrics.setdefault("replies", [])
    known = {r.get("received_id") for r in replies}
    added = 0

    for e in listing.get("data", []):
        eid = e.get("id")
        if not eid or eid in known:
            continue
        sender = str(e.get("from") or "").strip().lower()
        if not sender or sender == config.FROM_EMAIL.lower():
            continue
        s = sent_by_email.get(sender)
        if not s:
            continue
        subject = str(e.get("subject") or "")
        replies.append({
            "received_id": eid,
            "lead_id": s["lead_id"],
            "email": sender,
            "company": s.get("company"),
            "variant": s.get("variant"),
            "subject": subject,
            "message_id": e.get("message_id"),
            "received_at": e.get("created_at"),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "kind": "auto" if _is_auto_reply(subject) else "reply",
            "note": "",
        })
        known.add(eid)
        added += 1

    if added:
        save_metrics(metrics)
    return added


# ── Aggregation ───────────────────────────────────────────────────────────────

def _rec(metrics: dict, lead_id: str) -> dict:
    return metrics.get("emails", {}).get(lead_id) or {}


def _reply_ids(metrics: dict) -> set:
    """Real replies only: kind 'reply' counts toward the goal; kind 'auto'
    (out-of-office) never counts; our own tests never count (variant starts
    with 'TEST', e.g. loop tests recorded via record-reply)."""
    return {r["lead_id"] for r in metrics.get("replies", [])
            if r.get("kind") == "reply"
            and not str(r.get("variant", "")).upper().startswith("TEST")}


def aggregate(log: dict, metrics: dict) -> dict:
    sent = log.get("sent", [])
    replied_ids = _reply_ids(metrics)
    auto_count = sum(1 for r in metrics.get("replies", []) if r.get("kind") == "auto")

    counts = {
        "sent": len(sent),
        "delivered": 0, "bounced": 0, "complained": 0,
        "opened": 0, "clicked": 0, "unresolved": 0, "unknown": 0, "denied": 0,
        "pending": 0, "replied": 0, "auto": auto_count,
    }
    _PENDING = {"sent", "delivery_delayed"}
    for s in sent:
        status = str(_rec(metrics, s["lead_id"]).get("status") or "")
        if status in _DELIVERED:
            counts["delivered"] += 1
        if status in _PENDING:
            counts["pending"] += 1
        if status == "bounced":
            counts["bounced"] += 1
        if status == "complained":
            counts["complained"] += 1
        if status in _OPENED:
            counts["opened"] += 1
        if status == "clicked":
            counts["clicked"] += 1
        if status == "unresolved":
            counts["unresolved"] += 1
        if status == "denied":
            counts["denied"] += 1
        if status == "unknown" or status.startswith("error"):
            counts["unknown"] += 1
        if s["lead_id"] in replied_ids:
            counts["replied"] += 1

    def rate(part, whole):
        return (part / whole) if whole else 0.0

    d = counts["delivered"]
    return {
        **counts,
        "delivered_rate": rate(counts["delivered"], counts["sent"]),
        "bounce_rate": rate(counts["bounced"], counts["sent"]),
        "spam_rate": rate(counts["complained"], counts["sent"]),
        "open_rate": rate(counts["opened"], d),
        "click_rate": rate(counts["clicked"], d),
        "reply_rate": rate(counts["replied"], counts["sent"]),
    }


def by_variant(log: dict, metrics: dict) -> dict:
    groups = {}
    for s in log.get("sent", []):
        groups.setdefault(s.get("variant") or "?", []).append(s)

    replied_ids = _reply_ids(metrics)
    out = {}
    for variant, items in groups.items():
        sub = {"sent": len(items), "delivered": 0, "opened": 0, "clicked": 0, "replied": 0, "unresolved": 0}
        for s in items:
            status = str(_rec(metrics, s["lead_id"]).get("status") or "")
            if status in _DELIVERED:
                sub["delivered"] += 1
            if status in _OPENED:
                sub["opened"] += 1
            if status == "clicked":
                sub["clicked"] += 1
            if status == "unresolved":
                sub["unresolved"] += 1
            if s["lead_id"] in replied_ids:
                sub["replied"] += 1
        d = sub["delivered"]
        sub["open_rate"] = sub["opened"] / d if d else 0.0
        sub["click_rate"] = sub["clicked"] / d if d else 0.0
        sub["reply_rate"] = sub["replied"] / sub["sent"] if sub["sent"] else 0.0
        out[variant] = sub
    return out


# ── Report ────────────────────────────────────────────────────────────────────

def print_report(log: dict, metrics: dict) -> None:
    t = aggregate(log, metrics)
    checked = metrics.get("last_check") or "never"

    def pct(x):
        return f"{x * 100:.1f}%"

    print(f"\n{'='*60}")
    print(f"  EMAIL DATA — provider: {config.EMAIL_PROVIDER} · checked: {checked}")
    print(f"{'='*60}")
    print(f"  Send rate:     {t['sent']:>3}/{t['sent']:>3}  accepted by provider")
    print(f"  Delivered:     {t['delivered']:>3}/{t['sent']:>3}  ({pct(t['delivered_rate'])})")
    print(f"  Bounced:       {t['bounced']:>3}/{t['sent']:>3}  ({pct(t['bounce_rate'])})  limit {config.MAX_BOUNCE_RATE*100:.0f}%")
    print(f"  Marked spam:   {t['complained']:>3}/{t['sent']:>3}  ({pct(t['spam_rate'])})  limit {config.MAX_SPAM_RATE*100:.2f}%")
    print(f"  Opened:        {t['opened']:>3}/{t['delivered']:>3}  ({pct(t['open_rate'])} of delivered)  goal {config.GOAL_OPEN_RATE*100:.0f}%")
    print(f"  Clicked:       {t['clicked']:>3}/{t['delivered']:>3}  ({pct(t['click_rate'])} of delivered)  goal {config.GOAL_CLICK_RATE*100:.0f}%")
    print(f"  Replied:       {t['replied']:>3}/{t['sent']:>3}  ({pct(t['reply_rate'])} of sent)  GOAL >{config.GOAL_REPLY_RATE*100:.0f}%")
    if t["auto"]:
        print(f"  Auto-replies:  {t['auto']:>3} (excluded from reply rate)")
    if t["unknown"]:
        print(f"  Unverified:    {t['unknown']:>3} (provider fetch failed — re-run `metrics --force` when the network recovers)")
    if t["denied"]:
        print(f"  Read denied:   {t['denied']:>3} (API key cannot read email status — see `review`)")
    if t["unresolved"]:
        print(f"  Unresolved:    {t['unresolved']:>3} (no queryable provider id — see `review`)")
    print(f"{'='*60}")
    print(f"  Goal + next action: python3 outbound.py review")
    print(f"{'='*60}\n")
