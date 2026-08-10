"""Connection registry. Add adapters here without changing Department workflows."""

from ..models import ConnectionSpec

_CONNECTIONS = {
    item.id: item for item in (
        ConnectionSpec("buffer", "publishing", "Buffer GraphQL social publishing adapter.",
                       ("create_draft", "schedule", "publish", "verify"), ("BUFFER_API_KEY",)),
        ConnectionSpec("astro-blog", "publishing", "Local Astro notes publishing adapter.",
                       ("create_draft", "publish", "verify")),
        ConnectionSpec("posthog", "analytics", "Read-only PostHog query adapter.",
                       ("query_events", "query_funnel", "query_timeseries"),
                       ("POSTHOG_PERSONAL_API_KEY", "POSTHOG_PROJECT_ID")),
        ConnectionSpec("search-console", "search", "Read-only Google Search Console adapter.",
                       ("query_performance", "query_pages", "query_keywords"),
                       ("SEARCH_CONSOLE_ACCESS_TOKEN", "SEARCH_CONSOLE_SITE_URL")),
    )
}


def connections():
    return dict(_CONNECTIONS)
