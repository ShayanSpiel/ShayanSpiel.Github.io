"""Stable Tool vocabulary used by Departments."""

from ..models import ToolSpec

_TOOLS = {
    item.id: item for item in (
        ToolSpec("publishing", "Create, schedule, publish, and verify content.",
                 ("create_draft", "schedule", "publish", "verify", "fetch_metrics"),
                 ("schedule", "publish")),
        ToolSpec("analytics", "Query validated company and funnel evidence.",
                 ("query_events", "query_funnel", "query_timeseries")),
        ToolSpec("search", "Query organic search performance and indexing evidence.",
                 ("query_performance", "query_pages", "query_keywords")),
        ToolSpec("rendering", "Render and verify token-aligned visual assets.",
                 ("render_graphic", "render_video", "verify_render")),
    )
}


def tools():
    return dict(_TOOLS)
