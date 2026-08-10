"""Production Content Department."""

from ._evidence import EvidenceDepartment
from ..connections.astro_blog import AstroBlogConnection
from ..connections.buffer import BufferConnection
from ..models import Department, GoalStatus, RunStatus, Stage, StageResult, WorkflowSpec


class ContentDepartment(EvidenceDepartment, Department):
    id = department_id = "content"
    version = "1.0.0"
    description = "Turns company evidence into coordinated content packages and publishes approved deliverables."
    agent_ids = ("content-strategist", "content-writer", "publisher")
    production_ready = True
    workflows = (
        WorkflowSpec("content-package", "Coordinate one evidence-backed idea across formats.",
                     ("evidence", "brief", "produce", "review", "package"),
                     ("content-strategist", "content-writer"), ("copywriting-en", "copywriting-fa"),
                     (), ("company_evidence", "content_package"), ()),
        WorkflowSpec("social-post", "Create a platform-native post from approved evidence.",
                     ("brief", "draft", "edit", "approve"), ("content-writer",),
                     ("copywriting-en", "copywriting-fa"), (), ("content_draft",), ()),
        WorkflowSpec("article", "Create an evidence-backed search-aware article.",
                     ("brief", "draft", "edit", "seo_review", "approve"), ("content-writer", "seo-operator"),
                     ("copywriting-en", "seo"), (), ("article_draft", "seo_brief"), ()),
        WorkflowSpec("publish", "Publish or schedule an approved package through a Connection.",
                     ("select", "validate", "approve", "dispatch", "verify"), ("publisher",), (),
                     ("publish",), ("content_package", "publication_receipt"),
                     ("publish_social", "publish_blog")),
    )
    goal_schema = {"metrics": ["content_packages", "approved_drafts", "published_items"],
                   "config": {"workflow": {"enum": [w.id for w in workflows]},
                              "required_count": {"type": "integer"},
                              "connection": {"enum": ["buffer", "astro-blog"]},
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
        package = decision["package"]
        dry_run = decision.get("execution_mode") != "live"
        if decision["connection"] == "buffer":
            result = BufferConnection().create_post(channel_id=package.get("channel_id", ""),
                text=package.get("text", ""), due_at=package.get("due_at"),
                assets=package.get("assets", ()), dry_run=dry_run)
        elif decision["connection"] == "astro-blog":
            result = AstroBlogConnection().publish(slug=package.get("slug", ""),
                source=package.get("source", ""), dry_run=dry_run)
        else:
            return StageResult("dispatch", {"error": "Unknown publishing Connection"}, RunStatus.FAILED, Stage.ACT)
        payload = {"publication_receipt": {"ok": result.ok, "connection": result.connection_id,
                                           "operation": result.operation, "data": result.data,
                                           "error": result.error}}
        if not result.ok:
            return StageResult("dispatch", payload, RunStatus.BLOCKED, Stage.ACT,
                               message=result.error or "Publishing Connection failed", attention=payload)
        return StageResult("verify_publication", payload, next_stage=Stage.EVALUATE,
                           evidence=[{"kind": "publication_receipt", "source": result.connection_id,
                                      "validity": "technical_only", "payload": payload["publication_receipt"]}])

    def evaluate(self, ctx, action_result):
        if action_result.get("publication_receipt", {}).get("ok"):
            evaluation = {"verdict": "goal_met", "goal_met": True,
                          "metrics": {"published_items": 1}, "validity": "technical_only",
                          "contamination_reason": None, "next_experiment": {}}
            return StageResult("goal_check", {"published_items": 1}, RunStatus.COMPLETED,
                               goal_status=GoalStatus.ACHIEVED, evaluation=evaluation,
                               message="Approved content dispatch verified")
        return super().evaluate(ctx, action_result)
