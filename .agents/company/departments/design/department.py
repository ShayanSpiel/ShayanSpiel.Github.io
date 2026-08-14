"""Production Design Department — declarative Lego package."""

from __future__ import annotations

from typing import Any

from .._evidence import EvidenceDepartment
from ..campaign_contract import PLATFORMS, advance_campaign, creative_signature, validate_campaign
from ...runtime.models import Department, WorkflowSpec, WorkflowStep


def validate_design_order(manifest: dict[str, Any]) -> list[str]:
    """Accept only a strategy-complete shared campaign Artifact."""
    errors = validate_campaign(manifest, "strategy")
    if manifest.get("phase") != "strategy":
        errors.append("Design accepts campaign Artifacts only at the strategy phase")
    return errors


def accept_design_order(manifest: dict[str, Any]) -> dict[str, Any]:
    """Record Design ownership before any renderer can run."""
    errors = validate_design_order(manifest)
    if errors:
        raise ValueError("invalid Design order: " + "; ".join(errors))
    return advance_campaign(manifest, "designed", {"department": "design", "accepted": True})


def render_report(manifest: dict[str, Any], assets: list[dict[str, Any]]) -> dict[str, Any]:
    """Create Design's typed handoff without copying campaign copy or strategy."""
    errors = validate_campaign(manifest, "designed")
    if errors:
        raise ValueError("invalid Design order: " + "; ".join(errors))
    expected = {(item["item_id"], platform) for item in manifest["items"] for platform in PLATFORMS}
    indexed = {(str(asset.get("item_id")), str(asset.get("platform"))): asset for asset in assets}
    if set(indexed) != expected:
        raise ValueError("Design render evidence must contain exactly one asset for every item/platform pair")
    renditions = []
    for item in manifest["items"]:
        for platform in PLATFORMS:
            asset = indexed[(item["item_id"], platform)]
            for field in ("local_path", "sha256", "render_report_id"):
                if not asset.get(field):
                    raise ValueError(f"Design asset {item['item_id']}/{platform} needs {field}")
            rendition = item["renditions"][platform]
            renditions.append({
                "item_id": item["item_id"], "platform": platform,
                "content_id": rendition["content_id"],
                "creative_signature": creative_signature(
                    manifest["campaign_id"], item["item_id"], platform, rendition["design"]),
                "template_id": rendition["design"]["template_id"],
                "size_preset": rendition["design"]["size_preset"],
                "asset": dict(asset),
            })
    return {"schema_version": manifest["schema_version"],
            "campaign_id": manifest["campaign_id"], "batch_id": manifest["batch_id"],
            "source_phase": "designed", "target_phase": "rendered",
            "department": "design", "renditions": renditions}


class DesignDepartment(EvidenceDepartment, Department):
    id = department_id = "design"
    version = "3.2.1"
    description = "Consumes a shared campaign Artifact and returns verified renditions whose spoken text, displayed copy, components, icons, labels, timing, and evidence remain controlled by that one campaign identity."
    agent_ids = ("designer", "video-producer")
    production_ready = True
    workflows = (
        WorkflowSpec(
            "social-visual",
            "Render a focused platform-ready social graphic.",
            ("idea_lock", "brief", "compose", "render", "qa"), ("designer",), ("spielos-ui",), (),
            ("design_brief", "render_report"), (),
            graph=(WorkflowStep("render", "employee", "designer",
                                produces=("approved_design",), skill_ids=("spielos-ui",)),),
        ),
        WorkflowSpec(
            "rendition-pack",
            "Render every typed campaign rendition without owning or duplicating campaign strategy.",
            ("accept_design_order", "compose", "render_sizes", "visual_qa", "handoff"), ("designer",), ("spielos-ui",), (),
            ("design_order", "render_report"), (),
            graph=(WorkflowStep("render_sizes", "employee", "designer",
                                produces=("render_report",), skill_ids=("spielos-ui",)),),
        ),
        WorkflowSpec(
            "video-render",
            "Render and verify a focused design-system-aligned video.",
            ("idea_lock", "brief", "script", "animate", "render", "audio_mix", "qa"),
            ("video-producer",), ("video-creation", "spielos-ui"), (),
            ("video_render", "render_report"), (),
            graph=(WorkflowStep("render", "employee", "video-producer",
                                produces=("video_render",),
                                skill_ids=("video-creation", "spielos-ui")),),
        ),
        WorkflowSpec(
            "video-order",
            "Take a video order end-to-end: intake request, lock the One Idea, generate one-persona narration, derive readable scene dwell and total duration from measured speech, render a stable hook thumbnail, verify audible narration and provenance, and deliver video/thumbnail/QA together beneath the campaign batch Artifact.",
            ("intake", "idea_lock", "scenario_script", "tts_chain", "narration_mix", "render", "qa", "deliverable"),
            ("video-producer",), ("video-creation", "spielos-ui"), (),
            ("video_render", "render_report"), (),
            graph=(WorkflowStep("render", "employee", "video-producer",
                                produces=("video_render",),
                                skill_ids=("video-creation", "spielos-ui")),),
        ),
    )
    goal_schema = {"metrics": ["approved_designs", "rendition_count", "video_renders", "video_orders"],
                   "config": {"workflow": {"enum": [w.id for w in workflows]},
                              "required_count": {"type": "integer"}}}
    evidence_metrics = {"approved_designs": ("approved_design",),
                        "rendition_count": ("render_report",),
                        "video_renders": ("video_render",),
                        "video_orders": ("video_render",)}
    workflow_agents = {"social-visual": "designer", "rendition-pack": "designer",
                       "video-render": "video-producer", "video-order": "video-producer"}
