"""Recursive orchestrator using the same four-stage contract as its children."""

from datetime import datetime, timezone

from ..models import Engine, GoalStatus, RunStatus, Stage, StageResult


class DirectorEngine(Engine):
    id = "director"
    description = "Coordinates child goals while preserving their state and approvals."
    version = "2.1.0"
    goal_schema = {
        "metrics": ["all_children_achieved", "achieved_children", "reply_rate", "sales", "booked_calls"],
        "config": {"accepted_evidence_validity": {"type": "array"}},
    }

    def observe(self, ctx):
        children = list(ctx.cycle.get("children") or ())
        evaluations = [child.get("evaluation") for child in children if child.get("evaluation")]
        return StageResult("collect", {"children": children, "evaluations": evaluations},
                           evidence=[{"kind": "director_observation", "source": "director",
                                      "payload": {"child_count": len(children),
                                                  "evaluation_count": len(evaluations)}}],
                           message=f"Observed {len(children)} child goals and {len(evaluations)} evaluations")

    def decide(self, ctx, observation):
        children = observation.get("children") or []
        if not children:
            return StageResult("diagnose", {"reason": "no child goals"}, RunStatus.BLOCKED,
                               Stage.DECIDE, message="Director needs at least one child goal")
        attention = [c for c in children if c["cycle"]["run_status"] in
                     ("awaiting_approval", "blocked", "failed")]
        if attention:
            child = attention[0]
            payload = {"action": "surface", "child_id": child["id"],
                       "child_status": child["cycle"]["run_status"]}
            return StageResult("choose_intervention", payload,
                               decision={"type": "surface_attention",
                                         "rationale": "A child run requires approval or remediation",
                                         "payload": payload})
        invalid = [c for c in children if c.get("evaluation") and
                   c["evaluation"].get("validity") in ("contaminated", "invalid")]
        if invalid:
            child = invalid[0]
            proposal = (child["evaluation"].get("next_experiment") or {}).get("system_improvement")
            if proposal:
                payload = {"action": "create_system_improvement", "child_id": child["id"],
                           "originating_run_id": child["evaluation"]["run_id"], "proposal": proposal}
                return StageResult("choose_intervention", payload,
                                   decision={"type": "system_improvement",
                                             "rationale": child["evaluation"].get("contamination_reason") or
                                                          "Engine failure invalidated business evidence",
                                             "next_run_type": "system_improvement", "payload": payload})
        runnable = [c for c in children if c["goal_status"] == "active" and _runnable(c)]
        if runnable:
            payload = {"action": "dispatch", "child_id": runnable[0]["id"]}
            return StageResult("choose_intervention", payload,
                               decision={"type": "dispatch", "rationale": "Next active child can progress",
                                         "payload": payload})
        completed = [c for c in children if c["cycle"]["run_status"] == "completed"]
        if completed:
            payload = {"action": "evaluate_children",
                       "completed_run_ids": [c["cycle"]["id"] for c in completed]}
            return StageResult("choose_intervention", payload,
                               decision={"type": "evaluate",
                                         "rationale": "Child runs completed and produced evidence",
                                         "payload": payload})
        active = [c for c in children if c["goal_status"] == "active"]
        if active:
            resume_at = min((c["cycle"].get("resume_at") for c in active
                             if c["cycle"].get("resume_at")), default=None)
            payload = {"action": "wait_for_children", "resume_at": resume_at,
                       "child_ids": [c["id"] for c in active]}
            return StageResult("choose_intervention", payload,
                               decision={"type": "wait_for_children",
                                         "rationale": "Active children are suspended awaiting evidence",
                                         "payload": payload})
        payload = {"action": "evaluate_children"}
        return StageResult("choose_intervention", payload,
                           decision={"type": "evaluate", "rationale": "No child can currently execute",
                                     "payload": payload})

    def act(self, ctx, decision):
        if decision.get("action") == "surface":
            return StageResult("review", decision, RunStatus.WAITING, Stage.OBSERVE,
                               resume_at=None,
                               message=f"Child {decision.get('child_id')} requires user or executor attention")
        if decision.get("action") == "dispatch":
            if not ctx.dispatch_goal:
                return StageResult("execute", {"error": "dispatcher unavailable"}, RunStatus.FAILED, Stage.ACT)
            outcome = ctx.dispatch_goal(decision["child_id"])
            child_cycle = outcome["cycle"]
            if outcome["goal"]["goal_status"] == "active" and child_cycle["run_status"] in {
                "waiting", "awaiting_approval", "blocked", "failed"
            }:
                return StageResult("wait_for_child", {"child_id": decision["child_id"],
                                                       "outcome": outcome},
                                   RunStatus.WAITING, Stage.OBSERVE,
                                   resume_at=child_cycle.get("resume_at"),
                                   message="Director parked until the child run changes")
            return StageResult("execute", {"child_id": decision["child_id"], "outcome": outcome})
        if decision.get("action") == "create_system_improvement":
            if not ctx.create_child_goal:
                return StageResult("execute", {"error": "child creator unavailable"}, RunStatus.FAILED, Stage.ACT)
            proposal = decision["proposal"]
            child = ctx.create_child_goal({
                "name": f"Repair {proposal['engine_id']}: {proposal['problem']}",
                "engine_id": "system-improvement", "metric": "acceptance_tests_passed",
                "operator": "eq", "target": True, "run_type": "system_improvement",
                "evidence_validity": "technical_only", "resume_run_id": decision["originating_run_id"],
                "config": {**proposal, "originating_run_id": decision["originating_run_id"]},
                "hypothesis": {"statement": proposal["problem"], "variable": "engine_version",
                               "prediction": "The bounded repair restores valid execution"},
            })
            return StageResult("execute", {"created_goal": child["id"], "action": "system_improvement"})
        if decision.get("action") == "wait_for_children":
            return StageResult("wait_for_children", decision, RunStatus.WAITING,
                               Stage.OBSERVE, resume_at=decision.get("resume_at"),
                               message="Director is waiting for child evidence or a child transition")
        return StageResult("execute", {"action": decision.get("action")})

    def evaluate(self, ctx, action_result):
        children = list(ctx.cycle.get("children") or ())
        achieved = sum(child["goal_status"] == "achieved" for child in children)
        accepted = set(ctx.goal.config.get("accepted_evidence_validity") or ["business"])
        evaluations = [child.get("evaluation") for child in children if child.get("evaluation") and
                       child["evaluation"].get("validity") in accepted]
        metric_values = [item.get("metrics", {}).get(ctx.goal.metric) for item in evaluations
                         if item.get("metrics", {}).get(ctx.goal.metric) is not None]
        if ctx.goal.metric == "all_children_achieved":
            met = bool(children) and achieved == len(children)
            measured = achieved
        elif ctx.goal.metric == "achieved_children":
            measured = achieved
            met = _compare(measured, ctx.goal.operator, ctx.goal.target)
        else:
            measured = max(metric_values) if metric_values else None
            met = measured is not None and _compare(measured, ctx.goal.operator, ctx.goal.target)
        payload = {"achieved_children": achieved, "total_children": len(children),
                   "metric": ctx.goal.metric, "metric_value": measured, "goal_met": met,
                   "accepted_evidence_validity": sorted(accepted)}
        evaluation = {"verdict": "goal_met" if met else "continue", "goal_met": met,
                      "metrics": {ctx.goal.metric: measured, "achieved_children": achieved},
                      "validity": next(iter(accepted)) if len(accepted) == 1 else "business",
                      "next_experiment": {} if met else {"action": "continue_child_runs"}}
        if met:
            return StageResult("goal_check", payload, RunStatus.COMPLETED, goal_status=GoalStatus.ACHIEVED,
                               evaluation=evaluation, message="Director goal achieved")
        if not any(child["goal_status"] == "active" for child in children):
            evaluation["verdict"] = "blocked"
            evaluation["next_experiment"] = {"action": "set_or_reopen_child_goal"}
            return StageResult("goal_check", payload, RunStatus.BLOCKED, Stage.EVALUATE,
                               evaluation=evaluation,
                               message="Director goal is unmet and no active child can continue")
        return StageResult("goal_check", payload, RunStatus.COMPLETED, evaluation=evaluation,
                           next_run={"run_type": "evaluation",
                                     "evidence_validity": next(iter(accepted)) if len(accepted) == 1 else "business"},
                           message="Director evaluated the run; the proposed next run needs user approval")


def _compare(value, operator, target):
    return {"ge": value >= target, "gt": value > target, "eq": value == target,
            "le": value <= target, "lt": value < target}.get(operator, False)


def _runnable(child):
    cycle = child["cycle"]
    if cycle["run_status"] == "idle":
        return True
    if cycle["run_status"] != "waiting" or not cycle.get("resume_at"):
        return False
    return datetime.fromisoformat(cycle["resume_at"]) <= datetime.now(timezone.utc)
