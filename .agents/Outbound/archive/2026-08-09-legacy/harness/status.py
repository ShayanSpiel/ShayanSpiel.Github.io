#!/usr/bin/env python3
"""Harness — status: the engine talks to the owner.

On every meaningful state change the engine:
  1. refreshes experiments/status.json (machine-readable, one glance)
  2. appends ONE conversational line to experiments/report.md
  3. emails the owner a short status (throttled to state changes only)

Callers: the daemon after every run_block return, and after each cycle.
"""

import json
import os
from datetime import datetime, timezone

from harness import notify, report, state

HERE = os.path.dirname(os.path.abspath(__file__))
OUTBOUND_DIR = os.path.dirname(HERE)
STATUS_PATH = os.path.join(OUTBOUND_DIR, "experiments", "status.json")

LAST_EVENT = {"key": None}

EMAIL_MIN_INTERVAL = 2 * 3600  # owner rule 2026-08-09: at most one status
                               # email per 2h while the engine is running


def _pct(x):
    return f"{x*100:.1f}%" if isinstance(x, (int, float)) else "—"


def providers_health() -> dict:
    """Cheap live check of every configured provider (GETs only, no sends)."""
    import sys
    sys.path.insert(0, os.path.join(OUTBOUND_DIR, "scripts"))
    import base64
    import config
    import providers
    out = {}
    if config.RESEND_API_KEY:
        r = providers._open("https://api.resend.com/emails?limit=1",
                            headers={"Authorization": f"Bearer {config.RESEND_API_KEY}"},
                            retries=1)
        out["resend"] = "ok" if r.get("data") is not None else f"fail: {r.get('error')}"
    if config.MAILGUN_API_KEY:
        tok = base64.b64encode(f"api:{config.MAILGUN_API_KEY}".encode()).decode()
        r = providers._open("https://api.mailgun.net/v3/domains",
                            headers={"Authorization": f"Basic {tok}"}, retries=1)
        out["mailgun"] = "ok" if isinstance(r.get("items"), list) else f"fail: {str(r)[:60]}"
    if config.POSTMARK_API_TOKEN:
        r = providers._open("https://api.postmarkapp.com/server",
                            headers={"X-Postmark-Server-Token": config.POSTMARK_API_TOKEN},
                            retries=1)
        if isinstance(r, dict) and "ID" in r and "Name" in r:
            out["postmark"] = "ok (pending account approval)"
        elif isinstance(r, dict) and r.get("error"):
            out["postmark"] = f"token/network: {str(r.get('message'))[:50]}"
        else:
            out["postmark"] = f"unreachable: {str(r)[:50]}"
    if config.BREVO_API_KEY:
        r = providers._open("https://api.brevo.com/v3/account",
                            headers={"api-key": config.BREVO_API_KEY}, retries=1)
        out["brevo"] = "ok" if isinstance(r, dict) and "email" in r else f"fail: {str(r)[:60]}"
    if config.EMAILOCTOPUS_API_KEY:
        r = providers._open(f"https://emailoctopus.com/api/1.6/lists?limit=1"
                            f"&api_key={config.EMAILOCTOPUS_API_KEY}", retries=1)
        if isinstance(r, dict) and "data" in r:
            out["emailoctopus"] = "key valid — marketing ESP, NO transactional send (campaigns only)"
        else:
            out["emailoctopus"] = f"fail: {str(r)[:60]}"
    return out


def snapshot() -> dict:
    """Fresh totals + queue state for the status line."""
    import sys
    sys.path.insert(0, os.path.join(OUTBOUND_DIR, "scripts"))
    import analytics
    import outbound
    log = outbound.load_sent_log()
    metrics = analytics.load_metrics()
    totals = analytics.aggregate(log, metrics)
    return {
        "sent_total": totals.get("sent", 0),
        "sent_today": outbound.sent_today(log),
        "failed": len(log.get("failed", [])),
        "delivered_rate": totals.get("delivered_rate"),
        "open_rate": totals.get("open_rate"),
        "click_rate": totals.get("click_rate"),
        "reply_rate": totals.get("reply_rate"),
        "bounce_rate": totals.get("bounce_rate"),
        "spam_rate": totals.get("spam_rate"),
        "unresolved": totals.get("unresolved", 0),
        "providers": providers_health(),
    }


def _state_line(totals: dict) -> str:
    return (f"sent {totals['sent_total']} total · {totals['sent_today']} today · "
            f"reply {_pct(totals['reply_rate'])} · open {_pct(totals['open_rate'])} · "
            f"click {_pct(totals['click_rate'])} · "
            f"delivered {_pct(totals['delivered_rate'])} · bounce {_pct(totals['bounce_rate'])}")


def bump(event_key: str, headline: str, detail: str = "",
         email: bool = True, quiet_seconds: int = 900) -> None:
    """One status update. Same event within quiet_seconds → only refresh
    status.json (no new report line, no email). New event → full surface.
    Email is additionally throttled to EMAIL_MIN_INTERVAL (owner rule
    2026-08-09: the 30-min gate re-checks were emailing 48x/day). The
    throttle is persisted in status.json so a restart can't re-arm it."""
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%d %H:%M UTC")
    totals = snapshot()

    changed = LAST_EVENT["key"] != event_key
    LAST_EVENT["key"] = event_key

    last_email_at = None
    try:
        last_email_at = json.load(open(STATUS_PATH)).get("last_email_at") or None
    except Exception:
        pass
    email_due = bool(email and not last_email_at)
    if last_email_at:
        try:
            email_due = bool(email and
                             (now - datetime.fromisoformat(last_email_at)).total_seconds()
                             >= EMAIL_MIN_INTERVAL)
        except ValueError:
            email_due = bool(email)

    if not changed and LAST_EVENT.get("at"):
        elapsed = (now - LAST_EVENT["at"]).total_seconds()
        if elapsed < quiet_seconds:
            _write_json(event_key, headline, totals, ts, detail,
                        last_email_at or "")
            return
    LAST_EVENT["at"] = now

    _write_json(event_key, headline, totals, ts, detail,
                now.isoformat() if email_due else (last_email_at or ""))
    os.makedirs(os.path.dirname(report.REPORT_PATH), exist_ok=True)
    with open(report.REPORT_PATH, "a") as f:
        f.write(f"- {ts} — {headline}\n")
        if detail:
            f.write(f"  {detail}\n")

    if email_due:
        live = [k for k, v in (totals.get("providers") or {}).items()
                if str(v).startswith("ok")]
        notify.send_status(f"[SpielOS] {headline}", [
            headline,
            detail if detail else "",
            _state_line(totals),
            f"providers live: {', '.join(live) if live else 'NONE'}",
            f"Full report: .agents/Outbound/experiments/report.md",
        ])


def _write_json(event_key: str, headline: str, totals: dict, ts: str, detail: str,
                last_email_at: str = None) -> None:
    payload = {
        "updated_at": ts,
        "event": event_key,
        "headline": headline,
        "detail": detail,
        "last_email_at": last_email_at or "",
        "metrics": {k: round(v, 4) if isinstance(v, float) else v
                    for k, v in totals.items()},
    }
    os.makedirs(os.path.dirname(STATUS_PATH), exist_ok=True)
    with open(STATUS_PATH, "w") as f:
        json.dump(payload, f, indent=2, default=str)
