"""Production Content Department."""

from .._evidence import EvidenceDepartment
from ...connections import connection
from ...runtime.models import Department, GoalStatus, RunStatus, Stage, StageResult, WorkflowSpec


class ContentDepartment(EvidenceDepartment, Department):
    id = department_id = "content"
    version = "1.1.0"
    description = "Turns company evidence into focused content that connects one topic-specific idea to the company promise."
    agent_ids = ("content-strategist", "content-writer", "publisher")
    production_ready = True
    workflows = (
        WorkflowSpec("content-package", "Coordinate one evidence-backed topic idea across formats.",
                     ("evidence", "idea_lock", "brief", "produce", "review", "package"),
                     ("content-strategist", "content-writer"), ("copywriting-en", "copywriting-fa"),
                     (), ("company_evidence", "content_package"), ()),
        WorkflowSpec("social-post", "Create a one-idea platform-native post from approved evidence.",
                     ("idea_lock", "brief", "draft", "edit", "approve"), ("content-writer",),
                     ("copywriting-en", "copywriting-fa"), (), ("content_draft",), ()),
        WorkflowSpec("article", "Create one evidence-backed, search-aware argument.",
                     ("idea_lock", "brief", "draft", "edit", "seo_review", "approve"), ("content-writer", "seo-operator"),
                     ("copywriting-en", "seo"), (), ("article_draft", "seo_brief"), ()),
        WorkflowSpec("publish", "Publish or schedule an approved package through a Connection.",
                     ("select", "validate", "approve", "dispatch", "verify"), ("publisher",), (),
                     ("publish",), ("content_package", "publication_receipt"),
                     ("buffer", "website")),
    )
    goal_schema = {"metrics": ["content_packages", "approved_drafts", "published_items"],
                   "config": {"workflow": {"enum": [w.id for w in workflows]},
                              "required_count": {"type": "integer"},
                              "connection": {"enum": ["buffer", "website"]},
                              "execution_mode": {"enum": ["dry_run", "live"]}}}
    evidence_metrics = {"content_packages": ("content_package",),
                        "approved_drafts": ("content_draft", "article_draft"),
                        "published_items": ("publication_receipt",)}
    workflow_agents = {"content-package": "content-strategist", "social-post": "content-writer",
                       "article": "content-writer", "publish": "publisher"}

    def decide(self, ctx, observation):
        if ctx.goal.config.get("workflow") != "publish" or observation.get("published_items"):
            return super().decide(ctx, observation)
        packages = [item for item in observation.get("evidence", ()) if item.get("kind") == "content_package"]
        if not packages:
            return super().decide(ctx, observation)
        payload = {"action": "publish", "connection": ctx.goal.config.get("connection", "buffer"),
                   "package": packages[-1].get("payload", {}),
                   "execution_mode": ctx.goal.config.get("execution_mode", "dry_run")}
        return StageResult("choose_intervention", payload,
                           decision={"type": "publish", "rationale": "A validated ContentPackage is ready for guarded dispatch",
                                     "payload": payload})

    def act(self, ctx, decision):
        if decision.get("action") != "publish":
            return super().act(ctx, decision)
        if ctx.approval_status("execute") != "approved":
            return StageResult("review", decision, RunStatus.AWAITING_APPROVAL, Stage.ACT,
                               message="Approve the exact package, channel, timing, and destination before publishing")
        try:
            selected = connection(decision["connection"])
        except KeyError as error:
            return StageResult("dispatch", {"error": str(error)}, RunStatus.FAILED, Stage.ACT)
        request = {
            "capability": "connection_execution",
            "connection_id": selected.id,
            "hosts": list(selected.hosts),
            "operation": "publish",
            "execution_mode": decision.get("execution_mode", "dry_run"),
            "package": decision["package"],
            "required_evidence": "publication_receipt",
            "required_user_action": (
                f"Use the available {selected.id} Connection and record its receipt"),
            "next_trigger": f"company retry {ctx.goal.id}",
        }
        return StageResult("dispatch", {"connection_request": request},
                           RunStatus.BLOCKED, Stage.ACT, attention=request,
                           message="Publishing is delegated to the active host Connection")

    def evaluate(self, ctx, action_result):
        if action_result.get("publication_receipt", {}).get("ok"):
            evaluation = {"verdict": "goal_met", "goal_met": True,
                          "metrics": {"published_items": 1}, "validity": "technical_only",
                          "contamination_reason": None, "next_experiment": {}}
            return StageResult("goal_check", {"published_items": 1}, RunStatus.COMPLETED,
                               goal_status=GoalStatus.ACHIEVED, evaluation=evaluation,
                               message="Approved content dispatch verified")
        return super().evaluate(ctx, action_result)
