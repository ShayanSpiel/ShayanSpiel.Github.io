"""Read-only PostHog evidence Connection used by the Analytics Department.

Read surfaces (owner directive 2026-08-17: the PostHog OAuth MCP is the read
channel). The canonical live channel is the PostHog MCP server registered in
`opencode.json` under `mcp.servers.posthog` (`type: remote`, URL
`https://mcp.posthog.com/mcp`, OAuth enabled -- the protected-resource
metadata points to authorization server `https://oauth.posthog.com`). Agents
run read-only HogQL through that server's `posthog_*` tools after the owner
completes the one-time OAuth browser authorization; credentials are stored by
OpenCode outside project config.

The server-side warehouse REST path is NOT a working live channel for this
project: `POSTHOG_PROJECT_TOKEN` is a `phc_` client-side project key and is
rejected by the MCP and the Query API (HTTP 404/401). The `PostHogClient`
HogQL helpers below are kept as the deterministic, unit-tested interface and
work only when a valid server-side credential (personal API key) is supplied;
they never hardcode credentials and never write, mutate, or forward events.
Funnel events consumed by the site funnel (see funnel.json):
content_landing -> attention, cta_clicked -> engagement,
lead_form_success -> lead. Missing counts are labeled `missing`, never zero,
because an absent event in the warehouse means the event was not captured, not
that zero people behaved that way. Events are honored only under the consented
analytics configuration (see .agents/skills/analytics/SKILL.md).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = REPO_ROOT / ".spielos" / ".env"
WAREHOUSE_API_URL = "https://us.posthog.com/api/warehouse/query/"
MCP_SERVER_URL = "https://mcp.posthog.com/mcp"
# OAuth protected-resource metadata (RFC 9728) advertised by the MCP endpoint:
# https://mcp.posthog.com/.well-known/oauth-protected-resource/mcp
MCP_OAUTH_AUTHORIZATION_SERVERS = ("https://oauth.posthog.com",)
MCP_OAUTH_SCOPES_PREFIX = "action:read, customer_analytics:read, data_catalog:read"

# Canonical site funnel events consumed per batch (funnel.json stages).
FUNNEL_EVENTS = ("content_landing", "cta_clicked", "lead_form_success")

# All funnel stage events defined by the canonical funnel contract (read-only
# reference for the analytics skill; the funnel consumes the trio above).
FUNNEL_STAGE_EVENTS = (
    "$pageview", "content_landing", "content_impression", "content_engagement",
    "cta_clicked", "lead_form_start", "lead_form_submit", "lead_form_success",
    "lead_form_error", "qualified_lead", "booked_call", "sale",
)

# Campaign-to-lead identity chain preserved on every join.
BATCH_JOIN_KEYS = ("campaign_id", "batch_id", "item_id", "content_id",
                   "creative_signature")

PLATFORMS = ("threads", "youtube")


class PostHogError(RuntimeError):
    """A safe PostHog error that never embeds credentials."""


def _env_values(path: Path = ENV_PATH) -> dict[str, str]:
    """Read dotenv assignments without executing the file as shell code."""
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key.strip()):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def posthog_token() -> str:
    """The project token from the host environment or .spielos/.env; never inline."""
    values = _env_values()
    token = (os.environ.get("POSTHOG_PROJECT_TOKEN")
             or values.get("POSTHOG_PROJECT_TOKEN") or "").strip()
    if not token:
        raise PostHogError(
            "POSTHOG_PROJECT_TOKEN is not configured; keep it only in .spielos/.env")
    return token


class PostHogClient:
    """Read-only HogQL warehouse client (https://us.posthog.com/api/warehouse/query/)."""

    def __init__(self, api_key: str | None = None,
                 api_url: str = WAREHOUSE_API_URL):
        self.api_key = api_key or posthog_token()
        self.api_url = api_url

    def query(self, hogql: str, timeout: int = 30) -> dict[str, Any]:
        """Run one read-only HogQL query and return the raw warehouse result."""
        payload = json.dumps({"query": {"kind": "HogQLQuery", "query": hogql}}).encode("utf-8")
        request = Request(self.api_url, data=payload, method="POST", headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Project-API-Key": self.api_key,
        })
        try:
            with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed HTTPS endpoint
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = ""
            try:
                detail = error.read().decode("utf-8")[:300]
            except Exception:  # noqa: BLE001 - body may be empty or binary
                pass
            suffix = f": {detail}" if detail else ""
            raise PostHogError(f"PostHog warehouse query failed with HTTP {error.code}{suffix}") from error
        except (URLError, TimeoutError) as error:
            raise PostHogError("PostHog warehouse could not be reached") from error
        if isinstance(result, dict) and result.get("error"):
            raise PostHogError("PostHog warehouse error: " + str(result["error"]))
        if not isinstance(result, dict):
            raise PostHogError("PostHog warehouse returned an unexpected response")
        return result

    def rows(self, hogql: str, timeout: int = 30) -> dict[str, Any]:
        """Run a read-only HogQL query into [{column: value}, ...] rows."""
        result = self.query(hogql, timeout=timeout)
        columns = list(result.get("columns") or [])
        rows = []
        for raw in result.get("rows") or []:
            rows.append({columns[index]: value for index, value in enumerate(raw)})
        return {"query_id": result.get("query_id"), "columns": columns, "rows": rows}

    def event_counts(self, events: tuple[str, ...] = FUNNEL_EVENTS, *,
                     since: str | None = None, until: str | None = None,
                     properties: dict[str, Any] | None = None,
                     timeout: int = 30) -> dict[str, Any]:
        """Count captured funnel events read-only; absent events are `missing`.

        Events with no captured rows are reported under `missing_events`, never
        as an invented zero count: absence means the event was not captured.
        Optional `properties` filters (e.g. utm_campaign, cta_type) must use
        lowercase keys per the event taxonomy.
        """
        wanted = tuple(events) or FUNNEL_EVENTS
        rendered = ", ".join("'" + str(item).replace("'", "\\'") + "'" for item in wanted)
        where = f"event in ({rendered})"
        if since:
            where += f" and timestamp >= '{str(since).replace(chr(39), chr(92) + chr(39))}'"
        if until:
            where += f" and timestamp < '{str(until).replace(chr(39), chr(92) + chr(39))}'"
        for key, value in (properties or {}).items():
            key = str(key).replace(chr(39), chr(92) + chr(39))
            value = str(value).replace(chr(39), chr(92) + chr(39))
            where += f" and properties['{key}'] = '{value}'"
        hogql = (f"select event, count() as c from events where {where} "
                 "group by event order by event")
        payload = self.rows(hogql, timeout=timeout)
        counts = {str(row["event"]): int(row["c"]) for row in payload["rows"]
                  if "event" in row and row.get("event") is not None}
        observed = set(counts)
        return {
            "ok": True,
            "events": {event: counts[event] for event in wanted if event in counts},
            "missing_events": sorted(set(wanted) - observed),
            "query_id": payload["query_id"],
        }


def _rendition_lines(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Every delivery identity the campaign contract requires, in order."""
    lines: list[dict[str, Any]] = []
    for item in (manifest or {}).get("items") or []:
        for platform in PLATFORMS:
            rendition = ((item or {}).get("renditions") or {}).get(platform) or {}
            lines.append({
                "item_id": (item or {}).get("item_id"),
                "platform": platform,
                "content_id": rendition.get("content_id"),
                "creative_signature": rendition.get("creative_signature"),
            })
    return lines


METRIC_KEYS = ("views", "likes", "replies", "reposts", "shares", "followers")


def _join_buffer_refresh(renditions: list[dict[str, Any]],
                         delivery_receipts: list[dict[str, Any]] | None,
                         buffer_refresh: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Attach refreshed per-post metrics to each content rendition by post id."""
    refresh_by_post = {str(post.get("post_id")): post
                       for post in (buffer_refresh or {}).get("posts") or []}
    receipt_by_content = {str(receipt.get("content_id")): receipt
                          for receipt in (delivery_receipts or [])
                          if receipt.get("content_id")}
    joined: list[dict[str, Any]] = []
    for line in renditions:
        receipt = receipt_by_content.get(str(line["content_id"]))
        post_id = str((receipt or {}).get("provider_post_id") or "")
        refreshed = refresh_by_post.get(post_id) if post_id else None
        metrics = dict((refreshed or {}).get("metrics") or {})
        joined.append({
            **line,
            "provider_post_id": post_id or None,
            "provider_status": (refreshed or {}).get("status"),
            "metrics": metrics,
            "metrics_updated_at": (refreshed or {}).get("metrics_updated_at"),
            "staleness": (refreshed or {}).get("staleness", "missing")
                          if refreshed else "missing",
            "missing_metrics": [key for key, value in metrics.items() if value is None]
                               if refreshed else sorted(METRIC_KEYS),
        })
    return joined


def _funnel_entry(value: Any, source: str, *, missing_reason: str | None = None) -> dict[str, Any]:
    """One funnel count: observed with source, or missing (never zero)."""
    if missing_reason:
        return {"value": None, "source": source, "missing": True,
                "missing_reason": missing_reason}
    return {"value": value, "source": source, "missing": False}


def consume_batch_evidence(*, manifest: dict[str, Any] | None = None,
                           campaign_id: str | None = None,
                           batch_id: str | None = None,
                           delivery_receipts: list[dict[str, Any]] | None = None,
                           buffer_refresh: dict[str, Any] | None = None,
                           posthog_events: dict[str, Any] | None = None,
                           evidence_window: dict[str, Any] | None = None,
                           join_keys: tuple[str, ...] = BATCH_JOIN_KEYS) -> dict[str, Any]:
    """Join refreshed Buffer engagement and PostHog warehouse events per batch.

    This is the funnel-analysis consumption step: one campaign batch's live
    platform engagement (Buffer) plus consented website funnel counts (PostHog
    warehouse) joined by the preserved campaign identity chain. Counts that
    could not be observed are labeled `missing` and never reported as zero.
    The rendition list comes from the delivered manifest when present,
    otherwise from the delivery receipts' content ids. The envelope is
    `technical_only` evidence; the canonical funnel_report handoff additionally
    requires complete consented business evidence before any learning
    conclusion (see the Analytics skill and README).
    """
    campaign_id = campaign_id or (manifest or {}).get("campaign_id")
    batch_id = batch_id or (manifest or {}).get("batch_id")
    if manifest:
        renditions = _rendition_lines(manifest)
    else:
        renditions = [
            {"item_id": receipt.get("item_id"), "platform": receipt.get("platform"),
             "content_id": receipt.get("content_id"),
             "creative_signature": receipt.get("creative_signature")}
            for receipt in (delivery_receipts or []) if receipt.get("content_id")
        ]
    joined = _join_buffer_refresh(renditions, delivery_receipts, buffer_refresh)

    # Buffer side: platform views must cover every rendition before a total is
    # reported; missing any rendition makes the platform total missing, not 0.
    view_values = [row["metrics"].get("views") for row in joined]
    missing_renditions = [
        f"{row['content_id']}:{key}"
        for row in joined
        for key in row["missing_metrics"]
    ]
    stale_post_ids = [str(row["provider_post_id"]) for row in joined
                      if row.get("staleness") == "stale" and row.get("provider_post_id")]
    if not renditions:
        complete_views = False
        platform_missing = "no campaign renditions to measure"
        platform_views = 0.0
    else:
        complete_views = all(isinstance(value, (int, float)) for value in view_values)
        platform_views = sum(float(value) for value in view_values
                             if isinstance(value, (int, float)))
        platform_missing = None
        if not complete_views:
            platform_missing = ("platform views incomplete; "
                                + (", ".join(missing_renditions) if missing_renditions else "no rendition reported views"))

    # PostHog side: consented count per funnel event; absent event is missing.
    events = dict((posthog_events or {}).get("events") or {})
    missing_events = sorted((posthog_events or {}).get("missing_events") or [])
    landings = events.get("content_landing")
    clicks = events.get("cta_clicked")
    leads = events.get("lead_form_success")

    funnel = {
        "platform_views": _funnel_entry(
            platform_views if complete_views else None, "buffer_refresh",
            missing_reason=platform_missing),
        "content_landings": _funnel_entry(
            landings, "posthog_warehouse",
            missing_reason="content_landing not captured in the warehouse" if landings is None else None),
        "service_cta_clicks": _funnel_entry(
            clicks, "posthog_warehouse",
            missing_reason="cta_clicked not captured in the warehouse" if clicks is None else None),
        "leads": _funnel_entry(
            leads, "posthog_warehouse",
            missing_reason="lead_form_success not captured in the warehouse" if leads is None else None),
    }
    views = funnel["platform_views"]["value"]
    landing_count = funnel["content_landings"]["value"]
    click_count = funnel["service_cta_clicks"]["value"]
    lead_count = funnel["leads"]["value"]
    funnel["ctr"] = (landing_count / views if views and landing_count is not None else None)
    funnel["service_intent_rate"] = (click_count / landing_count
                                     if landing_count and click_count is not None else None)
    funnel["lead_conversion_rate"] = (lead_count / landing_count
                                      if landing_count and lead_count is not None else None)

    return {
        "kind": "funnel_measurement_evidence",
        "schema_version": "1.3.0",
        "campaign_id": campaign_id,
        "batch_id": batch_id,
        "join_keys": list(join_keys),
        "evidence_window": dict(evidence_window or {}),
        "technical_only": True,
        "honesty_rules": [
            "Missing counts are labeled missing, never zero",
            "An absent warehouse event is not a confirmed zero",
            "Refreshed Buffer metrics are technical_only delivery evidence",
        ],
        "buffer_refresh": {
            "stale_after_hours": ((buffer_refresh or {}).get("window") or {}).get("stale_after_hours"),
            "fetched_posts": int((buffer_refresh or {}).get("count") or 0),
            "stale_post_ids": sorted(stale_post_ids),
            "missing_metric_labels": sorted(set(missing_renditions)),
            "staleness_by_rendition": {
                str(row["content_id"]): row["staleness"] for row in joined},
            "renditions": joined,
        },
        "posthog_warehouse": {
            "read_source": "https://us.posthog.com/api/warehouse/query/",
            "events": {event: events[event] for event in FUNNEL_EVENTS if event in events},
            "missing_events": missing_events,
        },
        "funnel": funnel,
    }