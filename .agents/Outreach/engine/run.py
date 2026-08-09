#!/usr/bin/env python3
"""The engine CLI.

Manual cadence: nothing runs unless you call `once`. One `once` invocation
advances the loop as far as it can without a human, then parks.

Commands:
  once [--dry]            advance the loop (observe → decide → prepare →
                          validate → gate, then park at review/evidence/hold)
  status                  current phase, batch, hold reason, evidence due
  approve [--next]        review: approve the current batch for execute ·
                          hold: owner GO for the next batch cycle
  stop / clear-stop       raise / clear the STOP kill-switch
  goal                    show goal spec + knobs from data/control.json
  reset                   start a fresh batch cycle (from goal_met or hold)
  record-reply <id> [--note …]   log a reply against a sent email
  replies                 list recorded replies
  stats                   campaign database stats
  verify <cmd> [args]     email verification (probe|probe-queue|audit|sync-bounces)
  leads <cmd> [args]      lead engine (ingest|merge|score|reclassify|lookalikes)
"""

import argparse
import sys
from pathlib import Path

from .. import workflows
from ..store import OutreachStore
from .artifacts import Artifacts
from .control import Control
from .context import Context
from .loop import Loop
from .policy import Policy

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
LOGS_DIR = ROOT / "logs"
STOP_FILE = ROOT / "STOP"


def build_context(dry: bool = False) -> Context:
    workflows.import_all()
    store = OutreachStore(DATA_DIR / "engine.sqlite")
    control = Control(DATA_DIR / "control.json")
    workflow = workflows.get(control.workflow())
    artifacts = Artifacts(DATA_DIR, REPORTS_DIR, LOGS_DIR)
    policy = Policy(workflow)
    return Context(store=store, control=control, workflow=workflow,
                   artifacts=artifacts, policy=policy, stop_file=STOP_FILE,
                   data_dir=DATA_DIR, reports_dir=REPORTS_DIR, dry=dry)


def _phase_line(ctx: Context, status: dict) -> str:
    batch = ctx.store.current_batch_id() or "—"
    hold = ctx.store.hold_reason() or ""
    due = ctx.store.evidence_due() or ""
    return (f"phase={status['phase']} batch={batch}"
            + (f" hold=\"{hold}\"" if hold else "")
            + (f" evidence_due={due}" if due else ""))


def cmd_once(ctx: Context, dry: bool) -> int:
    say = lambda line: print(f"· {line}", flush=True)
    result = Loop(ctx).advance(dry=dry, say=say)
    print(f"\nPARKED AT {result['phase'].upper()}:")
    print("\n".join(result["msgs"]))
    if result.get("report_path"):
        print()
        print(Path(result["report_path"]).read_text().strip())
    print(f"\n`python3 -m Outreach status` for the full state.")
    return 0


def cmd_status(ctx: Context) -> int:
    from . import report as report_step
    status = _write_status(ctx)
    print(_phase_line(ctx, status))
    print()
    print(report_step.print_current(ctx).strip())
    return 0


def cmd_approve(ctx: Context, next_cycle: bool) -> int:
    phase = ctx.store.phase()
    if next_cycle:
        if phase != "hold":
            print(f"approve --next only works from a HOLD (current phase: {phase}).")
            return 1
        ctx.control.approve_next()
        print("Owner GO recorded — next `once` starts the next batch cycle.")
        return 0
    if phase != "review":
        print(f"approve only works at the REVIEW gate (current phase: {phase}).")
        return 1
    batch_id = ctx.store.current_batch_id()
    if not batch_id:
        print("no current batch to approve.")
        return 1
    ctx.control.approve_batch(batch_id)
    print(f"Batch {batch_id} approved — next `once` executes it.")
    return 0


def cmd_stop(ctx: Context) -> int:
    ctx.stop_file.touch()
    print(f"STOP raised ({ctx.stop_file}). The loop will not run while it exists.")
    return 0


def cmd_clear_stop(ctx: Context) -> int:
    if ctx.stop_file.exists():
        ctx.stop_file.unlink()
        print("STOP cleared — `once` is enabled again.")
    else:
        print("no STOP file present.")
    return 0


def cmd_goal(ctx: Context) -> int:
    goal = ctx.control.goal()
    knobs = ctx.control.knobs()
    print("GOAL (data/control.json):")
    for k, v in goal.items():
        print(f"  {k}: {v}")
    print("KNOBS:")
    for k, v in knobs.items():
        print(f"  {k}: {v}")
    print(f"approvals: {ctx.control._data.get('approvals')}")
    return 0


def cmd_reset(ctx: Context) -> int:
    phase = ctx.store.phase()
    if phase not in ("goal_met", "hold", "stopped"):
        print(f"reset only makes sense from goal_met/hold/stopped (current: {phase}).")
        return 1
    ctx.store.set_phase("observe")
    ctx.store.set_current_batch(None)
    ctx.store.set_evidence_due(None)
    ctx.store.set_hold_reason(None)
    print("Reset to OBSERVE — next `once` starts a fresh batch cycle.")
    return 0


def cmd_record_reply(ctx: Context, identifier: str, note: str) -> int:
    from ..workflows.email import cli as email_cli
    email_cli.record_reply(identifier, note)
    return 0


def cmd_replies(ctx: Context) -> int:
    from ..workflows.email import cli as email_cli
    email_cli.replies()
    return 0


def cmd_stats(ctx: Context) -> int:
    from ..workflows.email import cli as email_cli
    email_cli.stats()
    return 0


def cmd_verify(ctx: Context, args: list) -> int:
    from ..workflows.email import verify
    if not args:
        print(verify.__doc__)
        return 1
    cmd = args[0]
    if cmd == "probe" and len(args) > 1:
        e = args[1]
        l1 = verify.l1_check(e)
        if l1["tier"] == "Invalid":
            print(f"{e}: {l1['tier']} (L1: {l1['reason']})")
        else:
            r = verify.probe_one(e)
            print(f"{e}: {r['tier']} (L2: {r.get('detail', r.get('reason', ''))})")
        return 0
    if cmd == "probe-queue":
        limit = 40
        if "--limit" in args:
            limit = int(args[args.index("--limit") + 1])
        print(f"probe-queue: {verify.probe_queue(limit)}")
        return 0
    if cmd == "audit":
        print(f"audit: {verify.audit()}")
        return 0
    if cmd == "sync-bounces":
        n = verify.sync_bounces()
        print(f"sync-bounces: {n} rows marked 'Bounced; suppressed'")
        return 0
    print(verify.__doc__)
    return 1


def cmd_leads(ctx: Context, args: list) -> int:
    from ..workflows.email import leads
    if not args:
        print(leads.__doc__)
        return 1
    cmd, rest = args[0], args[1:]
    if cmd == "ingest" and rest:
        leads.ingest(rest[0])
        return 0
    if cmd == "merge" and rest:
        leads.merge(rest[0])
        return 0
    if cmd == "score" and rest:
        leads.score(rest[0])
        return 0
    if cmd == "reclassify":
        leads.reclassify(rest[0] if rest else None)
        return 0
    if cmd == "lookalikes":
        leads.lookalikes(rest[0] if rest else "")
        return 0
    print(leads.__doc__)
    return 1


def _write_status(ctx: Context) -> dict:
    from . import status as status_step
    return status_step.write(ctx)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m Outreach", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    once = sub.add_parser("once", help="advance the loop as far as it can without a human")
    once.add_argument("--dry", action="store_true", help="stop at the REVIEW gate; never execute")

    sub.add_parser("status", help="current phase, batch, hold, evidence window")
    app = sub.add_parser("approve", help="human gates")
    app.add_argument("--next", action="store_true",
                     help="owner GO: release a HOLD and start the next batch cycle")
    sub.add_parser("stop", help="raise the STOP kill-switch")
    sub.add_parser("clear-stop", help="clear the STOP kill-switch")
    sub.add_parser("goal", help="show goal spec + knobs (data/control.json)")
    sub.add_parser("reset", help="start a fresh batch cycle from goal_met/hold/stopped")

    rr = sub.add_parser("record-reply", help="log a reply against a sent email")
    rr.add_argument("identifier", help="lead_id or email address")
    rr.add_argument("--note", default="")
    sub.add_parser("replies", help="list recorded replies")
    sub.add_parser("stats", help="campaign database stats")

    verify = sub.add_parser("verify", help="email verification commands")
    verify.add_argument("args", nargs="*")
    leads = sub.add_parser("leads", help="lead engine commands")
    leads.add_argument("args", nargs="*")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    ctx = build_context(dry=getattr(args, "dry", False))
    try:
        if args.command == "once":
            return cmd_once(ctx, args.dry)
        if args.command == "status":
            return cmd_status(ctx)
        if args.command == "approve":
            return cmd_approve(ctx, args.next)
        if args.command == "stop":
            return cmd_stop(ctx)
        if args.command == "clear-stop":
            return cmd_clear_stop(ctx)
        if args.command == "goal":
            return cmd_goal(ctx)
        if args.command == "reset":
            return cmd_reset(ctx)
        if args.command == "record-reply":
            return cmd_record_reply(ctx, args.identifier, args.note)
        if args.command == "replies":
            return cmd_replies(ctx)
        if args.command == "stats":
            return cmd_stats(ctx)
        if args.command == "verify":
            return cmd_verify(ctx, args.args)
        if args.command == "leads":
            return cmd_leads(ctx, args.args)
    except Exception as e:  # surface step failures without a traceback dump
        ctx.artifacts.log(f"error: {type(e).__name__}: {e}")
        print(f"ERROR: {type(e).__name__}: {e}")
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
