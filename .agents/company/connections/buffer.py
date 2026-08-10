"""Buffer GraphQL publishing Connection."""

import os
from .base import ConnectionResult, json_request


class BufferConnection:
    id = "buffer"
    endpoint = "https://api.buffer.com"

    def ready(self):
        return bool(os.getenv("BUFFER_API_KEY"))

    def create_post(self, *, channel_id, text, mode="addToQueue", scheduling_type="automatic",
                    due_at=None, assets=(), dry_run=True):
        variables = {"input": {"channelId": channel_id, "text": text,
                               "mode": mode, "schedulingType": scheduling_type}}
        if due_at:
            variables["input"]["dueAt"] = due_at
        if assets:
            variables["input"]["assets"] = list(assets)
        if dry_run:
            return ConnectionResult(True, self.id, "create_post", {"dry_run": True, "variables": variables})
        token = os.getenv("BUFFER_API_KEY")
        if not token:
            return ConnectionResult(False, self.id, "create_post", error="Set BUFFER_API_KEY")
        query = """mutation CreatePost($input: CreatePostInput!) { createPost(input: $input) { ... on PostActionSuccess { post { id text dueAt status } } ... on MutationError { message } } }"""
        try:
            data = json_request(self.endpoint, token=token, body={"query": query, "variables": variables})
            return ConnectionResult(not data.get("errors"), self.id, "create_post", data,
                                    str(data.get("errors")) if data.get("errors") else None)
        except Exception as error:
            return ConnectionResult(False, self.id, "create_post", error=str(error))
