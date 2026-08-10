"""Read-only PostHog query Connection."""

import os
from .base import ConnectionResult, json_request


class PostHogConnection:
    id = "posthog"

    def ready(self):
        return bool(os.getenv("POSTHOG_PERSONAL_API_KEY") and os.getenv("POSTHOG_PROJECT_ID"))

    def query(self, query, *, dry_run=True):
        project = os.getenv("POSTHOG_PROJECT_ID", "PROJECT_ID")
        host = os.getenv("POSTHOG_API_HOST", "https://us.posthog.com").rstrip("/")
        body = {"query": query}
        if dry_run:
            return ConnectionResult(True, self.id, "query", {"dry_run": True, "endpoint": f"{host}/api/projects/{project}/query/", "body": body})
        token = os.getenv("POSTHOG_PERSONAL_API_KEY")
        if not self.ready():
            return ConnectionResult(False, self.id, "query", error="Set POSTHOG_PERSONAL_API_KEY and POSTHOG_PROJECT_ID")
        try:
            data = json_request(f"{host}/api/projects/{project}/query/", token=token, body=body)
            return ConnectionResult(True, self.id, "query", data)
        except Exception as error:
            return ConnectionResult(False, self.id, "query", error=str(error))
