"""Host-first logical Connections used by Department workflows."""

from ..runtime.models import ConnectionSpec


_CONNECTIONS = {
    item.id: item for item in (
        ConnectionSpec(
            "buffer",
            "Social publishing through the active Codex app or OpenCode MCP.",
            ("create_draft", "schedule", "publish", "verify"),
        ),
        ConnectionSpec(
            "posthog",
            "Product and funnel analytics through the active host Connection.",
            ("query_events", "query_funnel", "query_timeseries"),
        ),
        ConnectionSpec(
            "search-console",
            "Organic search evidence through the active host Connection.",
            ("query_performance", "query_pages", "query_keywords"),
        ),
        ConnectionSpec(
            "website",
            "Repository publishing through the active coding host.",
            ("create_article", "publish_article", "modify_site", "verify"),
        ),
        ConnectionSpec(
            "web-research",
            "Public web research through the active Codex or OpenCode host.",
            ("search", "open_page", "collect_public_evidence"),
        ),
        ConnectionSpec(
            "email-delivery",
            "Direct provider delivery required by unattended Outbound runs.",
            ("send", "delivery_events", "reply_events"),
            ("direct",), True, ("EMAIL_PROVIDER",),
        ),
    )
}


def connections() -> dict[str, ConnectionSpec]:
    return dict(_CONNECTIONS)


def connection(connection_id: str) -> ConnectionSpec:
    try:
        return _CONNECTIONS[connection_id]
    except KeyError as exc:
        raise KeyError(f"unknown Connection: {connection_id}") from exc
