"""Production Outbound Department over the single company runtime."""

from .email_workflow import EmailWorkflow, _compare
from .workflows import social
from ...runtime.contracts import agent_shortfall
from ...runtime.models import Department, GoalStatus, RunStatus, Stage, StageResult, WorkflowSpec, WorkflowStep


class OutboundDepartment(EmailWorkflow, Department):
    id = "outbound"
    department_id = "outbound"
    version = "3.2.0"
    description = "Finds and researches qualified prospects, prepares email or social outreach, and measures buyer outcomes."
    deprecated = False
    agent_ids = ("lead-researcher", "social-researcher", "outreach-writer")
    workflows = (
        WorkflowSpec("lead-research", "Discover, qualify, research, and verify ICP-matched prospects.",
                     ("discover", "qualify", "research", "verify", "record"),
                     ("lead-researcher",), ("outbound-email",), (),
                     ("lead_dossier", "verification_result"), ("web-research",),
                     graph=(WorkflowStep("record", "employee", "lead-researcher",
                                         produces=("lead_dossier",),
                                         skill_ids=("outbound-email",),
                                         connection_ids=("web-research",)),)),
        WorkflowSpec("email-outreach", "Compose, validate, approve, send, and measure personalized email.",
                     ("select", "compose", "validate", "approve", "send", "measure"),
                     ("lead-researcher", "outreach-writer"), ("outbound-email", "copywriting-en"),
                     ("send",), ("provider_events", "reply", "booked_call"), ("email-delivery",)),
        WorkflowSpec("social-lead-research", "Research qualified LinkedIn and X prospects from authorized public sources.",
                     ("discover", "qualify", "research", "validate", "record"),
                     ("social-researcher",), ("outbound-email", "outbound"), (),
                     ("social_prospect", "social_signal"), ("web-research",),
                     graph=(WorkflowStep("record", "employee", "social-researcher",
                                         produces=("social_prospect",),
                                         skill_ids=("outbound-email", "outbound"),
                                         connection_ids=("web-research",)),)),
        WorkflowSpec("social-dm", "Create and validate personalized LinkedIn and X DM drafts.",
                     ("select", "draft", "validate", "approve", "export", "measure"),
                     ("social-researcher", "outreach-writer"),
                     ("outbound-email", "copywriting-en", "copywriting-fa"),
                     ("external_send",), ("dm_draft", "reply", "booked_call"), (),
                     graph=(WorkflowStep("draft", "employee", "outreach-writer",
                                         produces=("dm_draft",),
                                         skill_ids=("outbound-email", "copywriting-en",
                                                    "copywriting-fa")),)),
    )
    workflow_agents = {
        "lead-research": "lead-researcher",
        "email-outreach": "outreach-writer",
        "social-lead-research": "social-researcher",
        "social-dm": "outreach-writer",
    }
    evidence_metrics = {
        "qualified_social_leads": ("social_prospect",),
        "approved_dm_drafts": ("dm_draft",),
    }
    goal_schema = {
        "metrics": ["reply_rate", "positive_reply_rate", "booked_calls", "sales",
                    "qualified_social_leads", "approved_dm_drafts"],
        "config": {
            **{key: value for key, value in EmailWorkflow.goal_schema["config"].items()
               if key != "execution_mode"},
            "execution_mode": {"enum": ["dry_run", "live"],
                               "required_when": {"workflow": "email-outreach"}},
            "workflow": {"enum": ["email-outreach", "social-lead-research", "social-dm",
                                  "lead-research"]},
            "required_count": {"type": "integer"},
        },
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
        workflow = observation.get("workflow") or ctx.goal.config.get("workflow", "email-outreach")
        if workflow == "email-outreach":
            return super().decide(ctx, observation)
        metric = ("qualified_social_leads" if workflow == "social-lead-research"
                  else "approved_dm_drafts" if workflow == "social-dm"
                  else ctx.goal.metric)
        target = int(ctx.goal.target if ctx.goal.metric == metric else ctx.goal.config.get("required_count") or 1)
        current = int(observation.get(metric) or 0)
        if current >= target:
            payload = {"action": "evaluate", "workflow_id": workflow, "metric": metric,
                       "value": current, "target": target}
            return StageResult("choose_intervention", payload,
                               decision={"type": "evaluate_workflow", "rationale": "Required artifacts are present",
                                         "payload": payload})
        payload = agent_shortfall(
            self, goal_id=ctx.goal.id, metric=metric, needed=target - current,
            workflow_id=workflow, config=ctx.goal.config)
        return StageResult("choose_intervention", payload,
                           decision={"type": "request_agent", "rationale": "A bounded employee must produce validated evidence",
                                     "payload": payload})

    def act(self, ctx, decision):
        if ctx.goal.config.get("workflow", "email-outreach") == "email-outreach":
            return super().act(ctx, decision)
        if decision.get("action") == "request_agent":
            employee = decision.get("agent_id") or decision.get("employee_id") or "employee"
            return StageResult("request_agent", decision, RunStatus.BLOCKED, Stage.ACT,
                               message=decision.get("required_user_action") or (
                                   f"{employee} must produce {decision.get('needed')} validated artifact(s)"),
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
