"""Direct, approval-gated Buffer GraphQL Connection.

Buffer accepts public media URLs rather than binary uploads. This module keeps
the credential local, validates that constraint before a request, and exposes a
small explicit surface for the Content publisher and connection self-tests.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ..departments.campaign_contract import (
    SCHEMA_VERSION as CAMPAIGN_SCHEMA_VERSION,
    publication_package,
)


API_URL = "https://api.buffer.com"
REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = REPO_ROOT / ".spielos" / ".env"
DEFAULT_ORGANIZATION_ID = "62f24e9ed7fef68ddf794937"


class BufferError(RuntimeError):
    """A safe Buffer error message that never embeds credentials."""


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


def environment() -> dict[str, str]:
    values = _env_values()
    return {**values, **{key: value for key, value in os.environ.items() if value}}


def _public_https_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise BufferError("Buffer media must use a stable public HTTPS URL")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".local"):
        raise BufferError("Buffer media URL must be publicly reachable")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return value
    if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
        raise BufferError("Buffer media URL must not target a private address")
    return value


def _graphql_string(value: str) -> str:
    return json.dumps(str(value))


def _rate_limits(headers: Any) -> dict[str, str]:
    items = headers.items() if hasattr(headers, "items") else []
    return {str(key): str(value) for key, value in items
            if "rate" in str(key).lower() or "limit" in str(key).lower()}


class BufferClient:
    def __init__(self, api_key: str | None = None, organization_id: str | None = None):
        values = environment()
        self.api_key = api_key or values.get("BUFFER_API_KEY", "")
        self.organization_id = (organization_id or values.get("BUFFER_ORGANIZATION_ID")
                                or DEFAULT_ORGANIZATION_ID)
        if not self.api_key:
            raise BufferError("BUFFER_API_KEY is not configured")
        self.last_rate_limits: dict[str, str] = {}

    def graphql(self, query: str) -> dict[str, Any]:
        payload = json.dumps({"query": query}).encode("utf-8")
        request = Request(API_URL, data=payload, method="POST", headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}",
        })
        try:
            with urlopen(request, timeout=30) as response:  # nosec B310: fixed HTTPS endpoint
                self.last_rate_limits = _rate_limits(response.headers)
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            self.last_rate_limits = _rate_limits(error.headers)
            raise BufferError(f"Buffer request failed with HTTP {error.code}") from error
        except (URLError, TimeoutError) as error:
            raise BufferError("Buffer request could not reach the API") from error
        if result.get("errors"):
            raise BufferError("Buffer GraphQL error: " + "; ".join(
                str(item.get("message", "unknown error")) for item in result["errors"]))
        return result.get("data") or {}

    def channels(self) -> list[dict[str, Any]]:
        query = """query GetChannels {
          channels(input: { organizationId: %s }) { id name displayName service isQueuePaused }
        }""" % _graphql_string(self.organization_id)
        return list(self.graphql(query).get("channels") or [])

    def channel(self, service: str) -> dict[str, Any] | None:
        expected = service.lower()
        return next((item for item in self.channels()
                     if str(item.get("service", "")).lower() == expected), None)

    def post(self, post_id: str) -> dict[str, Any] | None:
        query = """query GetPost {
          post(input: { id: %s }) { id text channelId dueAt status metrics { type name value unit } metricsUpdatedAt }
        }""" % _graphql_string(post_id)
        return self.graphql(query).get("post")

    def create_post(self, *, channel_id: str, text: str, mode: str = "draft",
                    due_at: str | None = None, assets: list[dict[str, str]] | None = None) -> dict[str, Any]:
        modes = {"draft": "addToQueue", "queue": "addToQueue", "scheduled": "customScheduled", "now": "shareNow"}
        if mode not in modes:
            raise BufferError("Buffer mode must be draft, queue, scheduled, or now")
        if mode == "scheduled" and not due_at:
            raise BufferError("A scheduled Buffer post needs an ISO-8601 due_at timestamp")
        fields = [f"text: {_graphql_string(text)}", f"channelId: {_graphql_string(channel_id)}",
                  "schedulingType: automatic", f"mode: {modes[mode]}"]
        if mode == "draft":
            fields.append("saveToDraft: true")
        if due_at:
            fields.append(f"dueAt: {_graphql_string(due_at)}")
        rendered_assets = []
        for asset in assets or []:
            kind = str(asset.get("type", "")).lower()
            if kind not in {"image", "video"}:
                raise BufferError("Buffer assets must be image or video URLs")
            url = _public_https_url(str(asset.get("url", "")))
            rendered_assets.append(f"{{ {kind}: {{ url: {_graphql_string(url)} }} }}")
        if rendered_assets:
            fields.append("assets: [" + ", ".join(rendered_assets) + "]")
        query = """mutation CreatePost {
          createPost(input: { %s }) {
            ... on PostActionSuccess { post { id text channelId dueAt status assets { id mimeType source } } }
            ... on InvalidInputError { message }
            ... on LimitReachedError { message }
            ... on UnauthorizedError { message }
            ... on UnexpectedError { message }
          }
        }""" % ", ".join(fields)
        result = self.graphql(query).get("createPost") or {}
        post = result.get("post")
        if not post:
            raise BufferError("Buffer rejected post: " + str(result.get("message", "unknown error")))
        return post

    def delete_post(self, post_id: str) -> str:
        query = """mutation DeletePost {
          deletePost(input: { id: %s }) {
            ... on DeletePostSuccess { id }
            ... on VoidMutationError { message }
          }
        }""" % _graphql_string(post_id)
        result = self.graphql(query).get("deletePost") or {}
        deleted = result.get("id")
        if not deleted:
            raise BufferError("Buffer could not delete the post: " + str(result.get("message", "unknown error")))
        return str(deleted)

    def posting_limits(self, channel_ids: list[str]) -> list[dict[str, Any]]:
        ids = ", ".join(_graphql_string(item) for item in channel_ids)
        query = """query DailyPostingLimits {
          dailyPostingLimits(input: { channelIds: [%s] }) { channelId isAtLimit limit scheduled sent }
        }""" % ids
        return list(self.graphql(query).get("dailyPostingLimits") or [])

    def available_capacity(self, channel_ids: list[str]) -> dict[str, int | None]:
        """Return remaining daily post capacity from Buffer, never a guessed quota."""
        limits = self.posting_limits(channel_ids)
        capacity: dict[str, int | None] = {}
        for item in limits:
            channel_id = str(item.get("channelId") or "")
            if item.get("limit") is None:
                # Buffer reports no per-day cap for this channel. `None` is an
                # explicit unlimited capacity, not an invented numeric quota.
                capacity[channel_id] = 0 if item.get("isAtLimit") else None
                continue
            try:
                limit = int(item["limit"])
                scheduled = int(item.get("scheduled") or 0)
            except (KeyError, TypeError, ValueError):
                continue
            capacity[channel_id] = max(0, limit - scheduled)
        return capacity

    def health_check(self) -> dict[str, Any]:
        channels = self.channels()
        services = {str(item.get("service", "")).lower() for item in channels}
        return {"ok": "threads" in services and "youtube" in services,
                "organization_id": self.organization_id, "channels": channels,
                "services": sorted(services), "rate_limits": self.last_rate_limits,
                "posting_limits": self.posting_limits([str(item["id"]) for item in channels
                                                       if str(item.get("service", "")).lower() in {"threads", "youtube"}])}


def _delivery_posts(package: dict[str, Any], client: BufferClient) -> list[dict[str, Any]]:
    posts = list(package.get("posts") or [package])
    if not posts:
        raise BufferError("Approved Buffer package needs one or more posts")
    resolved: list[dict[str, Any]] = []
    shared_campaign = package.get("schema_version") == CAMPAIGN_SCHEMA_VERSION
    if shared_campaign:
        for field in ("campaign_id", "batch_id"):
            if not package.get(field):
                raise BufferError(f"Approved campaign package needs {field}")
        if package.get("approval_required") is not True:
            raise BufferError("Campaign package must preserve the explicit approval gate")
    for item in posts:
        if not isinstance(item, dict):
            raise BufferError("Approved Buffer posts must be structured packages")
        post = dict(item)
        channel_id = str(post.get("channel_id") or post.get("channelId") or "")
        if not channel_id and post.get("platform"):
            channel = client.channel(str(post["platform"]))
            channel_id = str((channel or {}).get("id") or "")
        text = str(post.get("text") or post.get("description") or "")
        if not channel_id or not text:
            raise BufferError("Approved Buffer post needs a connected channel and text")
        if shared_campaign:
            for field in ("campaign_id", "batch_id", "item_id", "content_id",
                          "creative_signature", "platform", "approval_id"):
                if not post.get(field):
                    raise BufferError(f"Approved campaign post needs {field}")
            if post["campaign_id"] != package["campaign_id"] or post["batch_id"] != package["batch_id"]:
                raise BufferError("Campaign post identity does not match its package")
            if not list(post.get("assets") or []):
                raise BufferError("Approved campaign post needs its Design rendition")
        post["channel_id"] = channel_id
        post["text"] = text
        resolved.append(post)
    return resolved


def _publication_input(package: dict[str, Any]) -> dict[str, Any]:
    """Turn one already-approved batch handoff into the Buffer input.

    Batch review is the sole owner authorization. The asset-promotion step
    carries that decision into per-rendition IDs for provenance; this helper
    refuses anything that has not completed that promotion.
    """
    manifest = package.get("campaign_manifest") if isinstance(package, dict) else None
    if manifest is None:
        return package
    if package.get("review_required") is not True:
        raise BufferError("Campaign handoff must preserve the explicit batch approval gate")
    if not isinstance(manifest, dict) or manifest.get("phase") != "approved":
        raise BufferError("Campaign handoff needs the hosted approved campaign Artifact")
    try:
        return publication_package(manifest)
    except ValueError as error:
        raise BufferError(str(error)) from error


def dispatch(package: dict[str, Any], execution_mode: str) -> dict[str, Any]:
    """Dispatch an already-approved publisher package; never infer a channel or text."""
    if execution_mode != "live":
        return {"ok": False, "message": "Buffer dispatch is a dry run; no post was created"}
    client = BufferClient()
    publication = _publication_input(package)
    posts = _delivery_posts(publication, client)
    channel_ids = [str(item["channel_id"]) for item in posts]
    capacity = client.available_capacity(sorted(set(channel_ids)))
    requested = {channel_id: channel_ids.count(channel_id) for channel_id in set(channel_ids)}
    unavailable = {channel_id: count for channel_id, count in requested.items()
                   if capacity.get(channel_id, 0) is not None and capacity.get(channel_id, 0) < count}
    if unavailable:
        return {"ok": False, "message": "Buffer daily posting capacity is unavailable for this package",
                "capacity": capacity, "requested": unavailable}
    created = []
    receipts = []
    for item in posts:
        created_post = client.create_post(channel_id=item["channel_id"], text=item["text"],
                                          mode=str(item.get("mode") or "draft"),
                                          due_at=item.get("due_at") or item.get("dueAt"),
                                          assets=list(item.get("assets") or []))
        created.append(created_post)
        receipts.append({
            "campaign_id": item.get("campaign_id"), "batch_id": item.get("batch_id"),
            "item_id": item.get("item_id"), "content_id": item.get("content_id"),
            "creative_signature": item.get("creative_signature"),
            "platform": item.get("platform"), "approval_id": item.get("approval_id"),
            "provider_post_id": created_post.get("id"), "verified": bool(created_post.get("id")),
            "status": created_post.get("status"),
        })
    limits = client.posting_limits(sorted(set(channel_ids)))
    return {"ok": True, "post": created[0] if len(created) == 1 else None, "posts": created,
            "campaign_id": publication.get("campaign_id"), "batch_id": publication.get("batch_id"),
            "delivery_receipts": receipts,
            "rate_limits": client.last_rate_limits, "posting_limits": limits, "capacity_before_dispatch": capacity}


def _probe_draft(client: BufferClient) -> dict[str, Any]:
    channel = client.channel("threads")
    if not channel:
        raise BufferError("No Threads channel is connected to Buffer")
    post = client.create_post(channel_id=str(channel["id"]),
                              text="SpielOS Buffer connection check — delete this draft.", mode="draft")
    verified = client.post(str(post["id"]))
    deleted_id = client.delete_post(str(post["id"]))
    return {"ok": True, "draft_id": post["id"], "verified": bool(verified),
            "deleted_id": deleted_id, "rate_limits": client.last_rate_limits}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe direct Buffer Connection")
    parser.add_argument("--check", action="store_true", help="List connected channels; never writes")
    parser.add_argument("--probe-draft", action="store_true", help="Create, verify, and delete one Threads draft")
    args = parser.parse_args(argv)
    if not args.check and not args.probe_draft:
        parser.error("choose --check or --probe-draft")
    try:
        client = BufferClient()
        result = _probe_draft(client) if args.probe_draft else client.health_check()
    except BufferError as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
