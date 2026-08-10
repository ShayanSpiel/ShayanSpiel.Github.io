"""Canonical company agent catalog.

Codex and OpenCode manifests are client adapters. These records are the stable
company identities that Departments reference in durable workflow requests.
"""

from ..models import AgentSpec


AGENTS = {
    item.id: item for item in (
        AgentSpec(
            id="lead-researcher",
            description="Finds, qualifies, researches, and records prospects against the canonical ICP.",
            skill_ids=("outbound-email",),
            permissions=("read_public_sources", "write_lead_evidence"),
            produces=("social_prospect", "email_prospect", "lead_dossier"),
        ),
        AgentSpec(
            id="social-researcher",
            description="Researches qualified LinkedIn and X prospects and recent public signals without bulk messaging.",
            skill_ids=("outbound-email", "outreach-engine"),
            permissions=("read_public_sources", "write_social_evidence"),
            produces=("social_prospect", "social_signal"),
        ),
        AgentSpec(
            id="outreach-writer",
            description="Writes and validates personalized email and platform-native DM drafts.",
            skill_ids=("outbound-email", "copywriting-en", "copywriting-fa"),
            permissions=("read_strategy", "read_lead_evidence", "write_drafts"),
            produces=("email_draft", "dm_draft"),
        ),
        AgentSpec(
            id="content-strategist",
            description="Maps approved company evidence and strategy into one lean cross-format content package.",
            skill_ids=("copywriting-en", "seo", "analytics"),
            permissions=("read_strategy", "read_company_evidence", "write_briefs"),
            produces=("content_package", "content_brief"),
        ),
        AgentSpec(
            id="content-writer",
            description="Turns approved company work and evidence into buyer-relevant written content.",
            skill_ids=("copywriting-en", "copywriting-fa", "translation-fa"),
            permissions=("read_strategy", "read_approved_assets", "write_drafts"),
            produces=("content_draft",),
        ),
        AgentSpec(
            id="designer",
            description="Produces token-aligned graphics and rendition packs from approved design templates.",
            skill_ids=("spielos-ui",),
            permissions=("read_design_system", "read_approved_assets", "render_graphics"),
            produces=("approved_design", "graphic_render", "render_report"),
        ),
        AgentSpec(
            id="video-producer",
            description="Builds and verifies videos from approved HTML templates and source assets.",
            skill_ids=("video-creation", "copywriting-en"),
            permissions=("read_strategy", "read_approved_assets", "render_video"),
            produces=("video", "poster", "render_report"),
        ),
        AgentSpec(
            id="publisher",
            description="Validates, dispatches, and verifies approved content through registered publishing Connections.",
            skill_ids=("copywriting-en", "analytics"),
            permissions=("read_content_packages", "request_publish_approval", "use_publishing_connections"),
            produces=("publication_receipt",),
        ),
        AgentSpec(
            id="analytics-operator",
            description="Validates and reports company, funnel, attribution, and Department metrics.",
            skill_ids=("analytics",),
            permissions=("read_analytics", "query_posthog", "write_metric_evidence"),
            produces=("company_scorecard", "funnel_report", "department_evidence"),
        ),
        AgentSpec(
            id="cro-optimizer",
            description="Turns a validated funnel drop-off into one bounded conversion experiment.",
            skill_ids=("analytics", "copywriting-en", "spielos-ui"),
            permissions=("read_analytics", "propose_site_changes"),
            produces=("cro_experiment",),
        ),
        AgentSpec(
            id="seo-researcher",
            description="Builds ICP-aligned keyword opportunity maps and briefs from measured search evidence.",
            skill_ids=("seo", "analytics"),
            permissions=("read_strategy", "query_search_console", "write_seo_briefs"),
            produces=("keyword_opportunity", "seo_brief"),
        ),
        AgentSpec(
            id="seo-operator",
            description="Audits and improves search performance using the canonical strategy and measured evidence.",
            skill_ids=("seo", "analytics"),
            permissions=("read_strategy", "read_analytics", "propose_site_changes"),
            produces=("seo_audit", "seo_change_brief", "seo_evidence"),
        ),
    )
}


def agents():
    return dict(AGENTS)
