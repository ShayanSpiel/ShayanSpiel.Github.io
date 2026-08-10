"""One portable command surface for Codex, OpenCode, and humans."""

import argparse
import json
import sys
from pathlib import Path

from .runtime.models import GoalStatus
from .runtime.registry import departments
from .runtime.runner import Runner
from .runtime.loop import Runtime
from .runtime.service import RunnerService

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / ".spielos" / "state" / "company.sqlite"


def build_parser():
    parser = argparse.ArgumentParser(prog="python3 -m company")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("departments")
    commands.add_parser("catalog")
    goal = commands.add_parser("goal")
    goals = goal.add_subparsers(dest="goal_command", required=True)
    create = goals.add_parser("create")
    create.add_argument("--name", required=True)
    create.add_argument("--owner", required=True)
    create.add_argument("--metric", required=True)
    create.add_argument("--operator", choices=("ge", "gt", "eq", "le", "lt"), default="ge")
    create.add_argument("--target", required=True)
    create.add_argument("--deadline")
    create.add_argument("--parent")
    create.add_argument("--config", default="{}")
    create.add_argument("--id")
    create.add_argument("--run-type", default="execution",
                        choices=("business_experiment", "execution", "diagnostic", "system_improvement", "evaluation", "system_test"))
    create.add_argument("--hypothesis", default="{}", help="JSON: statement, variable, prediction")
    create.add_argument("--controlled", default="{}", help="JSON object of fixed variables")
    create.add_argument("--changed", default="{}", help="JSON object of changed variables")
    create.add_argument("--validity", default="business",
                        choices=("business", "technical_only", "contaminated", "invalid"))
    create.add_argument("--parent-run")
    create.add_argument("--triggered-by")
    create.add_argument("--resume-run")
    goals.add_parser("list")
    show = goals.add_parser("show"); show.add_argument("goal_id")
    once = commands.add_parser("once"); once.add_argument("goal_id")
    next_run = commands.add_parser("next"); next_run.add_argument("goal_id")
    status = commands.add_parser("status"); status.add_argument("goal_id", nargs="?")
    approve = commands.add_parser("approve"); approve.add_argument("goal_id"); approve.add_argument("--note", default="")
    for name in ("pause", "resume", "abandon"):
        item = commands.add_parser(name); item.add_argument("goal_id")
    retry = commands.add_parser("retry"); retry.add_argument("goal_id")
    report = commands.add_parser("report"); report.add_argument("goal_id"); report.add_argument("--events", type=int, default=10); report.add_argument("--json", action="store_true")
    evidence = commands.add_parser("evidence")
    evidence_commands = evidence.add_subparsers(dest="evidence_command", required=True)
    reply = evidence_commands.add_parser("reply"); reply.add_argument("goal_id"); reply.add_argument("--recipient", required=True); reply.add_argument("--note", default="")
    add = evidence_commands.add_parser("add"); add.add_argument("goal_id"); add.add_argument("--kind", required=True); add.add_argument("--source", required=True); add.add_argument("--payload", default="{}"); add.add_argument("--validity")
    change = commands.add_parser("change")
    change_commands = change.add_subparsers(dest="change_command", required=True)
    complete = change_commands.add_parser("complete"); complete.add_argument("task_id"); complete.add_argument("--passed", action="store_true"); complete.add_argument("--deployed", action="store_true"); complete.add_argument("--result", default="{}")
    runner = commands.add_parser("runner")
    runner_commands = runner.add_subparsers(dest="runner_command", required=True)
    tick = runner_commands.add_parser("tick"); tick.add_argument("goal_id", nargs="?"); tick.add_argument("--max-advances", type=int, default=100)
    watch = runner_commands.add_parser("watch"); watch.add_argument("goal_id", nargs="?"); watch.add_argument("--interval", type=float, default=2.0); watch.add_argument("--max-ticks", type=int)
    start = runner_commands.add_parser("start"); start.add_argument("--interval", type=float, default=2.0)
    runner_commands.add_parser("enable")
    runner_commands.add_parser("stop")
    runner_commands.add_parser("status")
    notifications = commands.add_parser("notifications")
    notification_commands = notifications.add_subparsers(dest="notification_command", required=True)
    listed = notification_commands.add_parser("list"); listed.add_argument("--status", choices=("pending", "delivered")); listed.add_argument("--limit", type=int, default=100)
    acknowledge = notification_commands.add_parser("ack"); acknowledge.add_argument("notification_id")
    return parser


def scalar(value):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def main(argv=None):
    args = build_parser().parse_args(argv)
    runtime = Runtime(args.db)
    try:
        if args.command == "departments":
            output = [{"id": key, "version": value.version, "description": value.description,
                       "goal_schema": value.goal_schema}
                      for key, value in departments().items()]
        elif args.command == "catalog":
            from .runtime.catalog import catalog
            output = catalog()
        elif args.command == "goal" and args.goal_command == "create":
            config = json.loads(args.config)
            hypothesis = json.loads(args.hypothesis)
            controlled = json.loads(args.controlled)
            changed = json.loads(args.changed)
            if not isinstance(config, dict):
                raise ValueError("--config must be a JSON object")
            output = runtime.create_goal(name=args.name, owner_id=args.owner, metric=args.metric,
                operator=args.operator, target=scalar(args.target), deadline=args.deadline,
                parent_id=args.parent, config=config, goal_id=args.id, run_type=args.run_type,
                hypothesis=hypothesis or None, controlled_variables=controlled, changed_variables=changed,
                evidence_validity=args.validity, parent_run_id=args.parent_run,
                triggered_by_run_id=args.triggered_by, resume_run_id=args.resume_run)
        elif args.command == "goal" and args.goal_command == "list":
            output = runtime.list_goals()
        elif args.command == "goal":
            output = runtime.status(args.goal_id)
        elif args.command == "once":
            output = runtime.once(args.goal_id)
        elif args.command == "next":
            runtime.next(args.goal_id)
            Runner(runtime).tick(args.goal_id)
            output = runtime.status(args.goal_id)
        elif args.command == "status":
            output = runtime.status(args.goal_id) if args.goal_id else runtime.list_goals()
        elif args.command == "approve":
            runtime.approve(args.goal_id, args.note)
            Runner(runtime).tick(args.goal_id)
            output = runtime.status(args.goal_id)
        elif args.command in ("pause", "resume", "abandon"):
            statuses = {"pause": GoalStatus.PAUSED, "resume": GoalStatus.ACTIVE, "abandon": GoalStatus.ABANDONED}
            output = runtime.set_goal_status(args.goal_id, statuses[args.command])
        elif args.command == "retry":
            output = runtime.retry(args.goal_id)
        elif args.command == "evidence":
            if args.evidence_command == "reply":
                runtime.add_evidence(args.goal_id, kind="reply", source="manual_inbox_confirmation",
                                     payload={"recipient": args.recipient, "note": args.note},
                                     validity="technical_only")
            else:
                runtime.add_evidence(args.goal_id, kind=args.kind, source=args.source,
                                     payload=json.loads(args.payload), validity=args.validity)
            Runner(runtime).tick(args.goal_id)
            output = runtime.status(args.goal_id)
        elif args.command == "change":
            output = runtime.complete_change(args.task_id, passed=args.passed,
                                             deployed=args.deployed, result=json.loads(args.result))
            Runner(runtime).tick(output["goal"]["id"])
            output = runtime.status(output["goal"]["id"])
        elif args.command == "runner":
            runner = Runner(runtime)
            if args.runner_command == "tick":
                output = runner.tick(args.goal_id, args.max_advances)
            elif args.runner_command == "watch":
                for result in runner.watch(args.interval, args.goal_id, args.max_ticks):
                    print(json.dumps(result, ensure_ascii=False, default=str), flush=True)
                return 0
            else:
                service = RunnerService(PROJECT_ROOT, Path(args.db))
                if args.runner_command == "start":
                    output = service.start(args.interval)
                elif args.runner_command == "stop":
                    output = service.stop()
                elif args.runner_command == "enable":
                    output = service.enable()
                else:
                    output = service.status()
        elif args.command == "notifications":
            if args.notification_command == "list":
                output = runtime.store.notifications(args.status, args.limit)
            else:
                output = runtime.store.acknowledge_notification(args.notification_id)
        else:
            state = runtime.status(args.goal_id)
            output = {**state, "events": runtime.store.events(args.goal_id, args.events),
                      "memory": runtime.store.memories(state["goal"]["owner_id"], args.goal_id)}
            if not args.json:
                print(render_report(output))
                return 0
        print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
        return 0
    except (KeyError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 1


def render_report(state):
    goal, cycle, run = state["goal"], state["cycle"], state["run"]
    latest = state.get("latest_result") or {}
    evaluation = state.get("evaluation") or latest.get("evaluation") or {}
    evidence = state.get("evidence") or latest.get("evidence") or []
    decisions = state.get("decisions") or latest.get("decisions") or []
    evaluated_run = latest.get("run") or run
    metrics = evaluation.get("metrics") or {}
    lines = [f"# Goal report: {goal['name']}", "",
             f"- Goal: `{goal['metric']} {goal['operator']} {goal['target']}`",
             f"- Goal status: `{goal['goal_status']}`",
             f"- Run: `{evaluated_run['id']}` · `{evaluated_run['run_type']}` · owner `{evaluated_run['owner_id']}@{evaluated_run['owner_version']}`",
             f"- Runtime: `{cycle['stage']}.{cycle['step']}` · `{cycle['run_status']}`",
             f"- Evidence validity: `{evaluated_run['evidence_validity']}`"]
    if evaluated_run.get("contamination_reason"):
        lines.append(f"- Contamination: {evaluated_run['contamination_reason']}")
    if metrics:
        lines += ["", "## Metrics"] + [f"- {key}: {value}" for key, value in metrics.items()]
    if evidence:
        lines += ["", "## Evidence"] + [f"- `{item['kind']}` via {item['source']} ({item['validity']})"
                                          for item in evidence]
    if decisions:
        lines += ["", "## Decisions"] + [f"- `{item['decision_type']}`: {item['rationale']}"
                                           for item in decisions]
    if evaluation:
        lines += ["", "## Evaluation", f"- Verdict: `{evaluation['verdict']}`",
                  f"- Goal met: `{bool(evaluation['goal_met'])}`"]
        if evaluation.get("next_experiment"):
            lines += ["", "## Proposed next run"] + [
                f"- {key}: {value}" for key, value in evaluation["next_experiment"].items()]
            lines += ["", "## Required action",
                      f"Ask the Director to start the next run for `{goal['id']}`."]
    if cycle["run_status"] == "awaiting_approval":
        preview = cycle.get("data", {}).get("action_result", {}).get("preview_path")
        lines += ["", "## Required action", "Review and approve the prepared action."]
        if preview:
            lines.append(f"Preview: `{preview}`")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
