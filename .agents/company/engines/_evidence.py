"""Shared evidence-driven behavior for artifact-producing Departments."""

from ..models import GoalStatus, RunStatus, Stage, StageResult


def compare(value, operator, target):
    return {"ge": value >= target, "gt": value > target, "eq": value == target,
            "le": value <= target, "lt": value < target}[operator]


class EvidenceDepartment:
    evidence_metrics = {}
    workflow_agents = {}

    def observe(self, ctx):
        evidence = list(ctx.cycle.get("evidence") or ())
        counts = {metric: sum(1 for item in evidence if item.get("kind") in kinds)
                  for metric, kinds in self.evidence_metrics.items()}
        return StageResult("collect", {"workflow": ctx.goal.config.get("workflow"),
                                       "evidence": evidence, **counts},
                           message=f"Observed {len(evidence)} typed evidence records")

    def decide(self, ctx, observation):
        metric = ctx.goal.metric
        current = observation.get(metric, 0)
        if compare(current, ctx.goal.operator, ctx.goal.target):
            payload = {"action": "evaluate", "metric": metric, "value": current}
        else:
            workflow = ctx.goal.config.get("workflow") or self.workflows[0].id
            payload = {"action": "request_agent", "workflow_id": workflow,
                       "agent_id": self.workflow_agents.get(workflow, self.agent_ids[0]),
                       "needed": max(1, int(ctx.goal.target) - int(current)),
                       "accepted_evidence_kinds": list(self.evidence_metrics.get(metric, ())) }
        return StageResult("choose_intervention", payload,
                           decision={"type": payload["action"],
                                     "rationale": "Evaluate typed evidence or request the bounded producer",
                                     "payload": payload})

    def act(self, ctx, decision):
        if decision.get("action") == "request_agent":
            return StageResult("request_agent", decision, RunStatus.BLOCKED, Stage.ACT,
                               message=f"{decision['agent_id']} must produce {decision['needed']} validated artifact(s)",
                               attention=decision)
        return StageResult("collect_artifacts", decision, next_stage=Stage.EVALUATE)

    def evaluate(self, ctx, action_result):
        metric = action_result.get("metric", ctx.goal.metric)
        value = action_result.get("value", 0)
        met = compare(value, ctx.goal.operator, ctx.goal.target)
        validity = "business" if ctx.goal.config.get("business_learning_allowed") else "technical_only"
        evaluation = {"verdict": "goal_met" if met else "continue", "goal_met": met,
                      "metrics": {metric: value}, "validity": validity,
                      "contamination_reason": None,
                      "next_experiment": {} if met else {"action": "produce_more_validated_artifacts"}}
        return StageResult("goal_check", {metric: value}, RunStatus.COMPLETED,
                           goal_status=GoalStatus.ACHIEVED if met else None,
                           evaluation=evaluation)
