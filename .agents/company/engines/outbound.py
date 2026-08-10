"""Production Outbound Department over the single company runtime."""

from .email import EmailEngine, _compare
from ..departments.outbound.workflows import social
from ..models import Department, GoalStatus, RunStatus, Stage, StageResult, WorkflowSpec


class OutboundDepartment(EmailEngine, Department):
    id = "outbound"
    department_id = "outbound"
    version = "3.0.0"
    description = "Finds and researches qualified prospects, prepares email or social outreach, and measures buyer outcomes."
    deprecated = False
    agent_ids = ("lead-researcher", "social-researcher", "outreach-writer")
    workflows = (
        WorkflowSpec("lead-research", "Discover, qualify, research, and verify ICP-matched prospects.",
                     ("discover", "qualify", "research", "verify", "record"),
                     ("lead-researcher",), ("outbound-email",), (),
                     ("lead_dossier", "verification_result"), ("public_research",)),
        WorkflowSpec("email-outreach", "Compose, validate, approve, send, and measure personalized email.",
                     ("select", "compose", "validate", "approve", "send", "measure"),
                     ("lead-researcher", "outreach-writer"), ("outbound-email", "copywriting-en"),
                     ("send",), ("provider_events", "reply", "booked_call"), ("send_email",)),
        WorkflowSpec("social-lead-research", "Research qualified LinkedIn and X prospects from authorized public sources.",
                     ("discover", "qualify", "research", "validate", "record"),
                     ("social-researcher",), ("outbound-email", "outreach-engine"), (),
                     ("social_prospect", "social_signal"), ("public_research",)),
        WorkflowSpec("social-dm", "Create and validate personalized LinkedIn and X DM drafts.",
                     ("select", "draft", "validate", "approve", "export", "measure"),
                     ("social-researcher", "outreach-writer"),
                     ("outbound-email", "copywriting-en", "copywriting-fa"),
                     ("external_send",), ("dm_draft", "reply", "booked_call"), ("export_dm",)),
    )
    goal_schema = {
        "metrics": ["reply_rate", "positive_reply_rate", "booked_calls", "sales",
                    "qualified_social_leads", "approved_dm_drafts"],
        "config": {**EmailEngine.goal_schema["config"],
                   "execution_mode": {"enum": ["dry_run", "live"],
                                      "required_when": {"workflow": "email-outreach"}},
                   "workflow": {"enum": ["email-outreach", "social-lead-research", "social-dm"]},
                   "required_count": {"type": "integer"}},
    }

    def observe(self, ctx):
        workflow = ctx.goal.config.get("workflow", "email-outreach")
        if workflow == "email-outreach":
            return super().observe(ctx)
        evidence = list(ctx.cycle.get("evidence") or ())
        prospects = social.prospects_from_evidence(evidence)
        drafts = social.drafts_from_evidence(evidence, prospects)
        payload = {"workflow": workflow, "prospects": prospects, "drafts": drafts,
                   "qualified_social_leads": len(prospects), "approved_dm_drafts": len(drafts)}
        return StageResult("collect", payload, message=f"Observed {len(prospects)} social prospects and {len(drafts)} DM drafts")

    def decide(self, ctx, observation):
        workflow = observation.get("workflow", "email-outreach")
        if workflow == "email-outreach":
            return super().decide(ctx, observation)
        metric = "qualified_social_leads" if workflow == "social-lead-research" else "approved_dm_drafts"
        target = int(ctx.goal.target if ctx.goal.metric == metric else ctx.goal.config.get("required_count") or 1)
        current = int(observation.get(metric) or 0)
        if current >= target:
            payload = {"action": "evaluate", "workflow_id": workflow, "metric": metric,
                       "value": current, "target": target}
            return StageResult("choose_intervention", payload,
                               decision={"type": "evaluate_workflow", "rationale": "Required artifacts are present",
                                         "payload": payload})
        request = social.agent_request(ctx.goal.id, workflow, target - current)
        payload = {"action": "request_agent", **request}
        return StageResult("choose_intervention", payload,
                           decision={"type": "request_agent", "rationale": "A bounded agent must produce validated evidence",
                                     "payload": payload})

    def act(self, ctx, decision):
        if ctx.goal.config.get("workflow", "email-outreach") == "email-outreach":
            return super().act(ctx, decision)
        if decision.get("action") == "request_agent":
            return StageResult("request_agent", decision, RunStatus.BLOCKED, Stage.ACT,
                               message=f"{decision.get('agent_id')} must produce {decision.get('needed')} validated artifact(s)",
                               attention=decision)
        return StageResult("collect_artifacts", decision, next_stage=Stage.EVALUATE)

    def evaluate(self, ctx, action_result):
        if ctx.goal.config.get("workflow", "email-outreach") == "email-outreach":
            return super().evaluate(ctx, action_result)
        metric = action_result.get("metric") or ctx.goal.metric
        value = int(action_result.get("value") or 0)
        met = _compare(value, ctx.goal.operator, ctx.goal.target)
        metrics = {metric: value}
        evaluation = {"verdict": "goal_met" if met else "continue", "goal_met": met,
                      "metrics": metrics, "validity": "technical_only",
                      "contamination_reason": None,
                      "next_experiment": {} if met else {"action": "request_more_validated_artifacts"}}
        return StageResult("goal_check", metrics, RunStatus.COMPLETED,
                           goal_status=GoalStatus.ACHIEVED if met else None,
                           evaluation=evaluation,
                           message="Outbound workflow artifact goal achieved" if met else "More workflow artifacts are required")
