"""Production Design Department."""

from .._evidence import EvidenceDepartment
from ...runtime.models import Department, WorkflowSpec


class DesignDepartment(EvidenceDepartment, Department):
    id = department_id = "design"
    version = "1.0.0"
    description = "Produces token-aligned graphics, banners, article visuals, and videos in verified channel sizes."
    agent_ids = ("designer", "video-producer")
    production_ready = True
    workflows = (
        WorkflowSpec("social-visual", "Render a platform-ready social graphic.",
                     ("brief", "compose", "render", "qa"), ("designer",), ("spielos-ui",), (),
                     ("design_brief", "render_report"), ()),
        WorkflowSpec("rendition-pack", "Render one design in every registered size.",
                     ("compose", "render_sizes", "visual_qa", "package"), ("designer",), ("spielos-ui",), (),
                     ("render_report",), ()),
        WorkflowSpec("video-render", "Render and verify a design-system-aligned video.",
                     ("brief", "script", "animate", "render", "qa"), ("video-producer",),
                     ("video-creation", "spielos-ui"), (), ("video_render", "render_report"), ()),
    )
    goal_schema = {"metrics": ["approved_designs", "rendition_count", "video_renders"],
                   "config": {"workflow": {"enum": [w.id for w in workflows]},
                              "required_count": {"type": "integer"}}}
    evidence_metrics = {"approved_designs": ("approved_design",),
                        "rendition_count": ("graphic_render",),
                        "video_renders": ("video_render",)}
    workflow_agents = {"social-visual": "designer", "rendition-pack": "designer",
                       "video-render": "video-producer"}
