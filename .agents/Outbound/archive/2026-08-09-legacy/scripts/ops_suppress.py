#!/usr/bin/env python3
"""Ops: suppress bounced + complained senders in the master database so the
gate's bounce-downgrade path can open (owner rule 2026-08-08: every bounced
email in metrics must be suppressed in master; the complained sender must
never be re-sent). Usage: python3 ops_suppress.py — takes the lead_ids from
metrics.json statuses bounced|complained, resolves their emails from
sent_log.json, marks the master rows.

Idempotent: re-running only (re)writes the suppression status."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))

import json
import openpyxl  # noqa: E402

import config  # noqa: E402
from outbound import COL_MAP, SHEET_NAME  # noqa: E402

STATUSES = {
    "bounced": "Bounced; suppressed",
    "complained": "Complained; suppressed",
}


def main() -> None:
    metrics = json.load(open(os.path.join(HERE, "metrics.json")))
    log = json.load(open(os.path.join(HERE, "sent_log.json")))
    sent = {s["lead_id"]: s for s in log.get("sent", []) if isinstance(s, dict)}

    targets = {}  # email -> new status
    for lead_id, rec in metrics.get("emails", {}).items():
        status = rec.get("status")
        if status in STATUSES and lead_id in sent:
            email = str(sent[lead_id].get("email") or "").strip().lower()
            if email:
                targets.setdefault(email, STATUSES[status])

    wb = openpyxl.load_workbook(config.DATABASE_PATH)
    ws = wb[SHEET_NAME]
    updated = 0
    for i, row in enumerate(ws.iter_rows(min_row=2), start=2):
        email_cell = row[COL_MAP["email"]]
        status_cell = row[COL_MAP["email_status"]]
        email = str(email_cell.value or "").strip().lower()
        if email in targets:
            new = targets[email]
            if str(status_cell.value or "") != new:
                status_cell.value = new
                updated += 1
            del targets[email]
    wb.save(config.DATABASE_PATH)
    print(f"suppressed {updated} master row(s); unmatched: {list(targets)[:5]}")


if __name__ == "__main__":
    main()
