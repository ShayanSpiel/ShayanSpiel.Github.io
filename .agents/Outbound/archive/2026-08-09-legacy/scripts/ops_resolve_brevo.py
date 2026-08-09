#!/usr/bin/env python3
"""Ops: backfill provider ids for brevo sends that recorded no response id
(the n-bug era). Brevo has no list endpoint, so ids are recovered by querying
GET /v3/smtp/statistics/events?email=... and taking the messageId of the
first event. Writes provider_id into sent_log.json; the next metrics --force
then resolves those sends (they currently count as unresolved and block the
gate's data-problem check).

Usage: python3 ops_resolve_brevo.py   (idempotent; skips already-resolved)"""
import json
import os
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import providers  # noqa: E402

LOG_PATH = os.path.join(HERE, "sent_log.json")


def resolve_email(email: str) -> str | None:
    qs = urllib.parse.urlencode({"email": email, "limit": 1})
    r = providers._open(
        f"https://api.brevo.com/v3/smtp/statistics/events?{qs}",
        headers={"api-key": providers.BREVO_API_KEY}, retries=1)
    evs = (r.get("events") or []) if isinstance(r, dict) else []
    if not evs:
        return None
    return str(evs[0].get("messageId") or "").strip() or None


def main() -> None:
    log = json.load(open(LOG_PATH))
    metrics = json.load(open(os.path.join(HERE, "metrics.json")))
    unresolved = {lid for lid, v in metrics.get("emails", {}).items()
                  if v.get("status") == "unresolved"}
    fixed = 0
    for s in log.get("sent", []):
        if not isinstance(s, dict):
            continue
        if s.get("lead_id") not in unresolved:
            continue
        if s.get("provider") != "brevo":
            continue
        if s.get("provider_id"):
            continue
        email = str(s.get("email") or "").strip().lower()
        if not email:
            continue
        mid = resolve_email(email)
        if mid:
            s["provider_id"] = mid
            fixed += 1
            print(f"{s['lead_id']} {email} -> {mid[:45]}")
        else:
            print(f"{s['lead_id']} {email} -> NO EVENTS (still unresolved)")
        time.sleep(0.5)
    json.dump(log, open(LOG_PATH, "w"), indent=2)
    print(f"fixed {fixed} brevo ids — run metrics --force next")


if __name__ == "__main__":
    main()
