import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from company.connections.buffer import BufferClient, BufferError, _env_values, _public_https_url


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
    def test_private_asset_rejected_before_request(self):
        client = BufferClient()
        with self.assertRaises(BufferError):
            client.create_post(channel_id="channel-1", text="check", assets=[{"type": "video", "url": "https://10.0.0.1/a.mp4"}])


if __name__ == "__main__":
    unittest.main()
