import os
import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from company.connections.buffer import (
    BufferClient, BufferError, _env_values, _publication_input, _public_https_url,
)
from company.departments.campaign_contract import apply_render_report, approve_rendered_campaign
from company.departments.design.department import accept_design_order, render_report
from company.tests.test_campaign_handoff_contract import campaign_manifest


class BufferConnectionTests(unittest.TestCase):
    def test_dotenv_parser_never_executes_shell_syntax(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("BUFFER_API_KEY='safe-token'\nBAD $(echo nope)\n")
            self.assertEqual({"BUFFER_API_KEY": "safe-token"}, _env_values(path))

    def test_media_requires_public_https_url(self):
        self.assertEqual("https://cdn.example.com/video.mp4", _public_https_url("https://cdn.example.com/video.mp4"))
        for value in ("http://cdn.example.com/a.jpg", "https://localhost/a.jpg", "https://127.0.0.1/a.jpg"):
            with self.assertRaises(BufferError):
                _public_https_url(value)

    @patch.dict(os.environ, {"BUFFER_API_KEY": "test-token", "BUFFER_ORGANIZATION_ID": "org-1"}, clear=False)
    def test_draft_mutation_and_rate_headers(self):
        client = BufferClient()
        seen = {}
        def fake_graphql(query):
            seen["query"] = query
            client.last_rate_limits = {"x-ratelimit-remaining": "99"}
            return {"createPost": {"post": {"id": "post-1", "status": "draft"}}}
        client.graphql = fake_graphql
        post = client.create_post(channel_id="channel-1", text="check", mode="draft")
        self.assertEqual("post-1", post["id"])
        self.assertIn("saveToDraft: true", seen["query"])
        self.assertEqual("99", client.last_rate_limits["x-ratelimit-remaining"])

    @patch.dict(os.environ, {"BUFFER_API_KEY": "test-token"}, clear=False)
    def test_caption_normalizes_literal_line_break_markers_before_graphql(self):
        client = BufferClient()
        seen = {}

        def fake_graphql(query):
            seen["query"] = query
            return {"createPost": {"post": {"id": "post-1", "status": "draft"}}}

        client.graphql = fake_graphql
        client.create_post(channel_id="channel-1", text=r"First paragraph\n\n• one\n• two", mode="draft")
        serialized = re.search(r"text: (.*?), channelId:", seen["query"]).group(1)
        self.assertEqual("First paragraph\n\n• one\n• two", json.loads(serialized))

    @patch.dict(os.environ, {"BUFFER_API_KEY": "test-token"}, clear=False)
    def test_private_asset_rejected_before_request(self):
        client = BufferClient()
        with self.assertRaises(BufferError):
            client.create_post(channel_id="channel-1", text="check", assets=[{"type": "video", "url": "https://10.0.0.1/a.mp4"}])

    def test_hosted_approved_batch_handoff_becomes_buffer_package(self):
        designed = accept_design_order(campaign_manifest())
        assets = [
            {"item_id": item["item_id"], "platform": platform,
             "type": "image" if platform == "threads" else "video",
             "local_path": "asset", "sha256": "sha", "render_report_id": "render"}
            for item in designed["items"] for platform in ("threads", "youtube")
        ]
        rendered = apply_render_report(designed, render_report(designed, assets))
        approved = approve_rendered_campaign(rendered, [
            {"item_id": item["item_id"], "platform": platform, "status": "approved",
             "approval_id": f"batch-review-{item['item_id']}-{platform}",
             "public_url": f"https://spielos.xyz/campaign-assets/batch/{item['item_id']}-{platform}"}
            for item in rendered["items"] for platform in ("threads", "youtube")
        ])
        package = _publication_input({"campaign_manifest": approved, "review_required": True})
        self.assertEqual(10, len(package["posts"]))
        self.assertTrue(all(item["approval_id"].startswith("batch-review-") for item in package["posts"]))

    def test_rendered_batch_cannot_bypass_approval(self):
        with self.assertRaisesRegex(BufferError, "hosted approved"):
            _publication_input({"campaign_manifest": {"phase": "rendered"}, "review_required": True})


if __name__ == "__main__":
    unittest.main()
