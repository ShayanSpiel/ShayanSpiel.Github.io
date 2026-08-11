"""The single GOAL -> OBSERVE -> DECIDE -> ACT -> EVALUATE loop."""

from __future__ import annotations

import importlib.util
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .models import GoalContext, Goal, GoalStatus, RunStatus, Stage
from .registry import handlers as installed_handlers
from .store import Store

TERMINAL = {"achieved", "abandoned", "expired"}
SUSPENDED = {RunStatus.WAITING, RunStatus.AWAITING_APPROVAL, RunStatus.BLOCKED,
             RunStatus.FAILED, RunStatus.COMPLETED}

logger = logging.getLogger("company.runtime.loop")

# Best-effort /live snapshot sync after every persisted transition. The
# runner's cwd is the repo root, so these are repo-root-relative paths.
LIVE_SYNC_SCRIPT = "scripts/sync-live-timeline.py"
LIVE_SYNC_DB = ".spielos/state/company.sqlite"
LIVE_SYNC_OUT = "src/data/live-goals.json"


def _load_live_sync():
    """Import scripts/sync-live-timeline.py; None (with a warning) when unavailable."""
    script = Path(LIVE_SYNC_SCRIPT)
    if not script.is_file():
        logger.warning("live timeline sync skipped: %s not found", LIVE_SYNC_SCRIPT)
        return None
    try:
        spec = importlib.util.spec_from_file_location("company_runtime_live_sync", script)
        if spec is None or spec.loader is None:
            logger.warning("live timeline sync skipped: could not resolve %s", LIVE_SYNC_SCRIPT)
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as exc:  # pragma: no cover - defensive; never breaks the loop
        logger.warning("live timeline sync skipped: could not load %s: %s", LIVE_SYNC_SCRIPT, exc)
        return None


class Runtime:
    def __init__(self, db_path: str | Path, registry: dict | None = None):
        self.store = Store(db_path)
        self.registry = registry or installed_handlers()
        for handler in self.registry.values():
            self.store.register_owner_version(handler.id, handler.version, status="deployed")

    def create_goal(self, **values) -> dict:
        if values["owner_id"] not in self.registry:
            raise KeyError(f"goal owner '{values['owner_id']}' is not installed")
        if values.get("deadline"):
            _timestamp(values["deadline"])
        values.setdefault("owner_version", self.registry[values["owner_id"]].version)
        return self.store.create_goal(**values)

    def once(self, goal_id: str, holder: str | None = None) -> dict:
        holder = holder or f"runtime-{uuid.uuid4().hex[:8]}"
        goal = self.store.goal(goal_id)
        if goal.get("deadline") and datetime.now(timezone.utc) >= _timestamp(goal["deadline"]):
            self.store.set_goal_status(goal_id, GoalStatus.EXPIRED.value)
            self.store.event(goal_id, self.store.cycle(goal_id)["id"], "goal.expired", {"deadline": goal["deadline"]})
            return self.status(goal_id)
        if goal["goal_status"] in TERMINAL:
            return self.status(goal_id)
        if goal["goal_status"] != "active":
            raise RuntimeError(f"goal {goal_id} is {goal['goal_status']}; resume it before running")
        if not self.store.acquire(goal_id, holder):
            raise RuntimeError(f"goal {goal_id} is already running in another client")
        try:
            before = self._state_signature(goal_id)
            result = self._advance(goal_id, holder)
            after = self._state_signature(goal_id)
            if before != after and goal.get("parent_id"):
                self.store.wake_goal(goal["parent_id"], f"child_changed:{goal_id}")
            return result
        finally:
            self.store.release(goal_id, holder)

    def _advance(self, goal_id: str, holder: str) -> dict:
        start_sequence = self.store.cycle(goal_id)["sequence"]
        for _ in range(8):
            row = self.store.goal(goal_id)
            cycle = self.store.cycle(goal_id)
            if cycle["run_status"] == "waiting":
                due = cycle.get("resume_at")
                if not due or datetime.now(timezone.utc) < datetime.fromisoformat(due):
                    return self.status(goal_id)
            if cycle["run_status"] in {"blocked", "failed"}:
                return self.status(goal_id)
            if cycle["run_status"] == "completed":
                return self.status(goal_id)
            if cycle["run_status"] == "awaiting_approval" and not self.store.approval(goal_id, cycle["id"], "execute"):
                return self.status(goal_id)

            handler = self.registry[row["owner_id"]]
            goal = Goal(id=row["id"], name=row["name"], owner_id=row["owner_id"],
                        metric=row["metric"], operator=row["operator"], target=row["target"],
                        deadline=row["deadline"], parent_id=row["parent_id"],
                        goal_status=row["goal_status"], config=row["config"])
            children = []
            for child in self.store.goals(parent_id=goal_id):
                child_cycle = self.store.cycle(child["id"])
                children.append({**child, "cycle": child_cycle,
                                 "run": self.store.run(child_cycle["id"]),
                                 "evaluation": self.store.latest_evaluation_for_goal(child["id"])})
            run = self.store.run(cycle["id"])
            context = GoalContext(
                goal=goal, cycle={**cycle, "run": run, "children": tuple(children),
                                  "evidence": tuple(self.store.evidence(cycle["id"])),
                                  "evaluation": self.store.evaluation(cycle["id"]),
                                  "change_tasks": tuple(self.store.change_tasks_for_run(cycle["id"]))},
                memory=self.store.memories(goal.owner_id, goal.id),
                approval_status=lambda key, g=goal_id, c=cycle["id"]: self.store.approval(g, c, key),
                dispatch_goal=lambda child_id: self.once(child_id, holder=f"{holder}:{goal_id}"),
                create_child_goal=lambda spec, p=goal_id, r=cycle["id"]: self._create_child(p, r, spec),
                create_change_task=lambda spec, g=goal_id, r=cycle["id"]: self.store.create_change_task(
                    goal_id=g, run_id=r, **spec),
                update_change_task=lambda task_id, status, result: self.store.complete_change_task(
                    task_id, status, result))
            result = self._call(handler, Stage(cycle["stage"]), context)
            if Stage(cycle["stage"]) is Stage.EVALUATE and result.run_status is RunStatus.IDLE:
                result.run_status = RunStatus.COMPLETED
            self._persist(goal, cycle, result)
            self._sync_live_snapshot()
            current = self.store.cycle(goal_id)
            if result.run_status in SUSPENDED or self.store.goal(goal_id)["goal_status"] in TERMINAL:
                return self.status(goal_id)
            if current["sequence"] != start_sequence:
                return self.status(goal_id)
        raise RuntimeError("goal owner exceeded the eight-transition safety limit")

    @staticmethod
    def _call(handler, stage, ctx):
        data = ctx.cycle.get("data") or {}
        if stage is Stage.OBSERVE:
            return handler.observe(ctx)
        if stage is Stage.DECIDE:
            return handler.decide(ctx, data.get("observation") or {})
        if stage is Stage.ACT:
            return handler.act(ctx, data.get("decision") or {})
        return handler.evaluate(ctx, data.get("action_result") or {})

    def _persist(self, goal, cycle, result):
        stage = Stage(cycle["stage"])
        next_stage = result.next_stage or {
            Stage.OBSERVE: Stage.DECIDE, Stage.DECIDE: Stage.ACT,
            Stage.ACT: Stage.EVALUATE, Stage.EVALUATE: Stage.OBSERVE}[stage]
        data = dict(cycle.get("data") or {})
        data[{Stage.OBSERVE: "observation", Stage.DECIDE: "decision",
              Stage.ACT: "action_result", Stage.EVALUATE: "evaluation"}[stage]] = result.payload
        if stage is Stage.EVALUATE:
            data["next_run"] = dict(result.next_run or {})
        goal_status = result.goal_status.value if result.goal_status else goal.goal_status
        self.store.set_goal_status(goal.id, goal_status)
        self.store.update_cycle(cycle["id"], stage=next_stage.value, step=result.step,
                                run_status=result.run_status.value, resume_at=result.resume_at, data=data)
        validity = result.evaluation.get("validity") if result.evaluation else None
        contamination = result.evaluation.get("contamination_reason") if result.evaluation else None
        self.store.update_run(cycle["id"], status=result.run_status.value,
                              validity=validity, contamination_reason=contamination)
        self.store.resolve_actionable_notifications(goal.id, cycle["id"])
        self.store.event(goal.id, cycle["id"], f"{stage.value.lower()}.{result.step}", {
            "status": result.run_status.value, "next_stage": next_stage.value,
            "message": result.message, "payload": result.payload})
        for learning in result.learnings:
            self.store.learn(goal.owner_id, goal.id, learning["claim"],
                             learning.get("evidence") or {}, float(learning.get("confidence", 0.5)))
        for evidence in result.evidence:
            self.store.add_evidence(goal.id, cycle["id"], evidence["kind"],
                                    evidence.get("source", goal.owner_id), evidence.get("payload", {}),
                                    evidence.get("validity", self.store.run(cycle["id"])["evidence_validity"]))
        if result.decision:
            self.store.add_decision(goal.id, cycle["id"], result.decision)
        if result.evaluation:
            self.store.add_evaluation(goal.id, cycle["id"], result.evaluation)
        if result.run_status is RunStatus.AWAITING_APPROVAL:
            self.store.notify(goal.id, cycle["id"], "approval_required",
                              self._notification_payload(goal, cycle, result, next_stage))
        elif result.attention:
            self.store.notify(goal.id, cycle["id"], "action_required",
                              self._notification_payload(goal, cycle, result, next_stage))
        elif result.run_status in (RunStatus.BLOCKED, RunStatus.FAILED):
            self.store.notify(goal.id, cycle["id"], result.run_status.value,
                              self._notification_payload(goal, cycle, result, next_stage))
        if goal_status in TERMINAL:
            self.store.notify(goal.id, cycle["id"], f"goal_{goal_status}",
                              self._notification_payload(goal, cycle, result, next_stage))
        elif stage is Stage.EVALUATE and result.run_status is RunStatus.COMPLETED:
            self.store.notify(goal.id, cycle["id"], "run_completed",
                              self._notification_payload(goal, cycle, result, next_stage))

    def _sync_live_snapshot(self):
        """Regenerate the committed /live snapshot after a persisted transition.

        Best-effort: a missing script or database, or a locked database, only
        logs a warning. Never raises and never touches the sqlite write path —
        the sync script opens the database read-only (mode=ro, busy_timeout).
        """
        module = _load_live_sync()
        if module is None:
            return
        try:
            module.sync_live(LIVE_SYNC_DB, LIVE_SYNC_OUT, quiet=True)
        except Exception as exc:  # pragma: no cover - defensive; never breaks the loop
            logger.warning("live timeline sync skipped (non-fatal): %s", exc)

    def _notification_payload(self, goal, cycle, result, next_stage):
        evaluation = result.evaluation or {}
        attention = result.attention or {}
        goal_met = bool(evaluation.get("goal_met")) or result.goal_status is GoalStatus.ACHIEVED
        return {
            "goal": {"id": goal.id, "name": goal.name, "metric": goal.metric,
                     "operator": goal.operator, "target": goal.target},
            "run": {"id": cycle["id"], "sequence": cycle["sequence"],
                    "owner_id": goal.owner_id, "owner_version": self.registry[goal.owner_id].version},
            "runtime": {"stage": next_stage.value, "step": result.step,
                        "status": result.run_status.value},
            "result": {"message": result.message, "verdict": evaluation.get("verdict"),
                       "goal_met": goal_met,
                       "metrics": evaluation.get("metrics", result.payload)},
            "next_experiment": evaluation.get("next_experiment", {}),
            "next_trigger": attention.get("next_trigger") or (
                f"company next {goal.id}" if result.run_status is RunStatus.COMPLETED and not goal_met else None),
            "required_user_action": attention.get("required_user_action") or (
                "Approve the prepared action" if result.run_status is RunStatus.AWAITING_APPROVAL else
                "Ask the Director to start the proposed next run"
                if result.run_status is RunStatus.COMPLETED and not goal_met else None),
            "attention": attention,
            "artifact": result.payload.get("preview_path") if isinstance(result.payload, dict) else None,
        }

    def _create_child(self, parent_goal_id: str, parent_run_id: str, spec: dict) -> dict:
        required = ("name", "owner_id", "metric", "operator", "target")
        missing = [key for key in required if key not in spec]
        if missing:
            raise ValueError(f"child goal spec missing: {', '.join(missing)}")
        return self.create_goal(
            name=spec["name"], owner_id=spec["owner_id"], metric=spec["metric"],
            operator=spec["operator"], target=spec["target"], deadline=spec.get("deadline"),
            parent_id=parent_goal_id, config=spec.get("config", {}),
            run_type=spec.get("run_type", "execution"), parent_run_id=parent_run_id,
            triggered_by_run_id=parent_run_id, hypothesis=spec.get("hypothesis"),
            controlled_variables=spec.get("controlled_variables", {}),
            changed_variables=spec.get("changed_variables", {}),
            evidence_validity=spec.get("evidence_validity", "business"),
            resume_run_id=spec.get("resume_run_id"))

    def approve(self, goal_id: str, note: str = "") -> dict:
        cycle = self.store.cycle(goal_id)
        if cycle["run_status"] != "awaiting_approval":
            raise RuntimeError(f"goal is not awaiting approval (status: {cycle['run_status']})")
        self.store.approve(goal_id, cycle["id"], "execute", note)
        return self.status(goal_id)

    def set_goal_status(self, goal_id: str, status: GoalStatus) -> dict:
        previous = self.store.goal(goal_id)["goal_status"]
        self.store.set_goal_status(goal_id, status.value)
        if status is GoalStatus.ACTIVE and previous in TERMINAL:
            self.store.new_cycle(goal_id)
        self.store.event(goal_id, self.store.cycle(goal_id)["id"], f"goal.{status.value}", {})
        return self.status(goal_id)

    def retry(self, goal_id: str) -> dict:
        cycle = self.store.cycle(goal_id)
        if cycle["run_status"] not in {"blocked", "failed"}:
            raise RuntimeError(f"retry requires blocked or failed status (current: {cycle['run_status']})")
        self.store.update_cycle(cycle["id"], stage="OBSERVE", step="collect",
                                run_status="idle", resume_at=None, data={})
        self.store.resolve_actionable_notifications(goal_id, cycle["id"])
        self.store.event(goal_id, cycle["id"], "run.retried", {})
        return self.status(goal_id)

    def next(self, goal_id: str) -> dict:
        goal = self.store.goal(goal_id)
        if goal["goal_status"] != "active":
            raise RuntimeError(f"next run requires an active goal (current: {goal['goal_status']})")
        cycle = self.store.cycle(goal_id)
        if cycle["run_status"] != "completed":
            raise RuntimeError(f"next run requires a completed run (current: {cycle['run_status']})")
        evaluation = self.store.evaluation(cycle["id"])
        if not evaluation:
            raise RuntimeError("completed run has no evaluation")
        if evaluation["goal_met"]:
            raise RuntimeError("goal is already met; do not start another run")
        if goal["owner_id"] == "director":
            for child in self.store.goals(parent_id=goal_id):
                child_cycle = self.store.cycle(child["id"])
                if child["goal_status"] == "active" and child_cycle["run_status"] == "completed":
                    self.next(child["id"])
        metadata = dict((cycle.get("data") or {}).get("next_run") or {})
        metadata.setdefault("owner_version", self.registry[goal["owner_id"]].version)
        created = self.store.new_cycle(goal_id, metadata)
        self.store.event(goal_id, created["id"], "run.started", {
            "previous_run_id": cycle["id"], "approved_experiment": evaluation["next_experiment"]})
        return self.status(goal_id)

    def add_evidence(self, goal_id: str, *, kind: str, source: str, payload: dict,
                     validity: str | None = None) -> dict:
        cycle = self.store.cycle(goal_id)
        run = self.store.run(cycle["id"])
        evidence = self.store.add_evidence(goal_id, cycle["id"], kind, source, payload,
                                           validity or run["evidence_validity"])
        self.store.event(goal_id, cycle["id"], "evidence.recorded", {"evidence_id": evidence["id"], "kind": kind})
        if cycle["run_status"] == "waiting" and self._goal_met_from_evidence(goal_id, cycle["id"]):
            self.store.update_cycle(cycle["id"], stage="EVALUATE", step="measure", run_status="waiting",
                                    resume_at=now_iso(), data=cycle["data"])
        return self.status(goal_id)

    def complete_change(self, task_id: str, *, passed: bool, result: dict,
                        deployed: bool = False) -> dict:
        task = self.store.change_task(task_id)
        status = "completed" if passed else "failed"
        task = self.store.complete_change_task(task_id, status, result)
        validity = "technical_only" if passed else "invalid"
        self.store.add_evidence(task["goal_id"], task["run_id"], "change_validation", "coding_executor",
                                {"task_id": task_id, "passed": passed, **result}, validity)
        if passed:
            self.store.register_owner_version(task["owner_id"], task["target_version"],
                                              status="deployed" if deployed else "tested",
                                              test_summary=result)
        cycle = self.store.cycle(task["goal_id"])
        self.store.update_cycle(cycle["id"], stage="EVALUATE", step="validate_change",
                                run_status="idle", resume_at=None, data=cycle["data"])
        self.store.update_run(cycle["id"], status="idle",
                              validity="technical_only" if passed else "invalid",
                              contamination_reason=None if passed else "Acceptance tests failed")
        return self.status(task["goal_id"])

    def _goal_met_from_evidence(self, goal_id: str, run_id: str) -> bool:
        goal = self.store.goal(goal_id)
        evidence = self.store.evidence(run_id)
        sent = len({item["payload"].get("recipient") for item in evidence
                    if item["kind"] == "email_sent" and item["payload"].get("recipient")})
        replies = len({item["payload"].get("recipient") for item in evidence
                       if item["kind"] == "reply" and item["payload"].get("recipient")})
        if goal["metric"] != "reply_rate" or not sent:
            return False
        return _compare(replies / sent, goal["operator"], goal["target"])

    def status(self, goal_id: str) -> dict:
        children = [{"goal": child, "cycle": self.store.cycle(child["id"])}
                    for child in self.store.goals(parent_id=goal_id)]
        cycle = self.store.cycle(goal_id)
        latest_evaluation = self.store.latest_evaluation_for_goal(goal_id)
        latest_result = None
        if latest_evaluation:
            result_run_id = latest_evaluation["run_id"]
            latest_result = {"run": self.store.run(result_run_id),
                             "evaluation": latest_evaluation,
                             "evidence": self.store.evidence(result_run_id),
                             "decisions": self.store.decisions(result_run_id)}
        return {"goal": self.store.goal(goal_id), "cycle": cycle, "run": self.store.run(cycle["id"]),
                "evidence": self.store.evidence(cycle["id"]),
                "decisions": self.store.decisions(cycle["id"]),
                "evaluation": self.store.evaluation(cycle["id"]),
                "latest_result": latest_result,
                "change_tasks": self.store.change_tasks_for_run(cycle["id"]),
                "children": children,
                "pending_notifications": [item for item in self.store.notifications("pending")
                                          if item["goal_id"] == goal_id]}

    def list_goals(self) -> list[dict]:
        return [{"goal": goal, "cycle": self.store.cycle(goal["id"])} for goal in self.store.goals()]

    def goal_summary(self, goal_id: str) -> dict:
        rows = self.store.goal_summaries(goal_id=goal_id, limit=1)
        if not rows:
            raise KeyError(f"unknown goal: {goal_id}")
        return {
            "goal": rows[0],
            "attention": [item for item in self.store.attention(100)
                          if item["goal_id"] == goal_id],
            "unread_results": [item for item in self.store.unread_results(100)
                               if item["goal_id"] == goal_id],
        }

    def company_snapshot(self, recent_limit: int = 5) -> dict:
        """Small current-state projection; immutable history remains in SQLite."""

        return {
            "counts": self.store.goal_counts(),
            "attention": self.store.attention(10),
            "active_goals": self.store.goal_summaries(statuses=("active",), limit=20),
            "paused_goals": self.store.goal_summaries(statuses=("paused",), limit=10),
            "unread_results": self.store.unread_results(5),
            "recent_results": self.store.goal_summaries(
                statuses=TERMINAL, limit=recent_limit),
        }

    def goal_history(self, limit: int = 10) -> list[dict]:
        return self.store.goal_summaries(statuses=TERMINAL, limit=limit)

    def _state_signature(self, goal_id: str):
        goal = self.store.goal(goal_id)
        cycle = self.store.cycle(goal_id)
        return (goal["goal_status"], cycle["id"], cycle["stage"], cycle["step"],
                cycle["run_status"], cycle.get("resume_at"),
                len(self.store.evidence(cycle["id"])), bool(self.store.evaluation(cycle["id"])))


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compare(value, operator, target):
    return {"ge": value >= target, "gt": value > target, "eq": value == target,
            "le": value <= target, "lt": value < target}.get(operator, False)
