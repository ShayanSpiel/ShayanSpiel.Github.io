#!/usr/bin/env python3
"""Shared outreach engine CLI.

This manages discovery, qualification, state, and decisions. It does not
scrape platforms or send prohibited automated social actions.
"""

import argparse
import json
from pathlib import Path

from .models import Action, Lead, LeadState, WorkflowGoal
from .store import OutreachStore
from .workflow import OutreachLoop


ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "state" / "outreach.sqlite"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    add = sub.add_parser("add")
    add.add_argument("file", help="JSON array of lead records")
    queue = sub.add_parser("queue")
    queue.add_argument("channel")
    queue.add_argument("--limit", type=int, default=20)
    queue.add_argument("--min-score", type=int, default=75)
    nxt = sub.add_parser("next")
    nxt.add_argument("channel")
    nxt.add_argument("--action", default="send_dm")
    record = sub.add_parser("record")
    record.add_argument("lead_id")
    record.add_argument("channel")
    record.add_argument("action")
    record.add_argument("result")
    record.add_argument("--note", default="")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    store = OutreachStore(args.db)
    if args.command == "status":
        print(json.dumps(store.counts(), indent=2))
    elif args.command == "add":
        records = json.loads(Path(args.file).read_text())
        leads = []
        for item in records:
            item = dict(item)
            item["state"] = LeadState(item.get("state", "discovered"))
            leads.append(Lead(**item))
        print(f"upserted {store.upsert_leads(leads)} leads")
    elif args.command == "queue":
        leads = store.ready_queue(args.channel, args.limit, args.min_score)
        print(json.dumps([lead.__dict__ | {"state": lead.state.value} for lead in leads], indent=2, default=str))
    elif args.command == "next":
        goal = WorkflowGoal(f"{args.channel}-{args.action}", args.channel, args.action, 30)
        print(json.dumps(OutreachLoop(store, goal).next_work().__dict__, indent=2, default=str))
    elif args.command == "record":
        store.record_action(args.lead_id, args.channel, args.action, args.result, args.note)
        print(f"recorded {args.result} for {args.lead_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
