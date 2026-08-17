import unittest
from pathlib import Path

from company.connections.buffer import BufferClient
from company.departments.campaign_contract import SCHEMA_VERSION, validate_campaign
from company.departments.content.department import validate_campaign_package
from company.tests.test_campaign_handoff_contract import campaign_manifest


ROOT = Path(__file__).resolve().parents[3]


class ContentCampaignContractTests(unittest.TestCase):
    def test_current_authority_is_campaign_contract(self):
        manifest = campaign_manifest()
        self.assertEqual(manifest["schema_version"], SCHEMA_VERSION)
        self.assertEqual(validate_campaign(manifest, "strategy"), [])
        self.assertEqual(validate_campaign_package(manifest), [])

    def test_legacy_package_is_rejected_by_current_authority(self):
        errors = validate_campaign_package({
            "campaign": "content-leads-20260812",
            "one_idea": "Visible operating proof beats generic AI claims",
            "platform_packages": [],
        })
        self.assertTrue(any("legacy campaign package is retired" in error for error in errors))
        self.assertTrue(any(SCHEMA_VERSION in error for error in errors))

    def test_legacy_batch_shape_is_not_current_authority(self):
        errors = validate_campaign_package({
            "campaign": "content-leads-20260812", "batch_number": 1, "batch_size": 5,
            "daily_targets": {"threads": 50, "youtube": 50},
            "batch_items": [{"batch_item": 1, "narrative_type": "live-journey"}],
        })
        self.assertTrue(any("legacy campaign package is retired" in error for error in errors))

    def test_buffer_capacity_uses_live_daily_limits(self):
        client = BufferClient.__new__(BufferClient)
        client.posting_limits = lambda ids: [
            {"channelId": "threads", "limit": 10, "scheduled": 3},
            {"channelId": "youtube", "limit": 5, "scheduled": 5},
        ]
        self.assertEqual(client.available_capacity(["threads", "youtube"]), {"threads": 7, "youtube": 0})

    def test_buffer_preserves_an_explicitly_unlimited_channel(self):
        client = BufferClient.__new__(BufferClient)
        client.posting_limits = lambda ids: [{"channelId": "youtube", "limit": None, "scheduled": 0, "isAtLimit": False}]
        self.assertEqual(client.available_capacity(["youtube"]), {"youtube": None})

    def test_registered_platform_sizes_and_quality_gate_are_present(self):
        presets = (ROOT / ".agents/company/departments/design/presets.json").read_text()
        content = (ROOT / ".agents/company/departments/content/department.py").read_text()
        self.assertIn('"youtube-shorts"', presets)
        self.assertIn('"threads-portrait"', presets)
        self.assertIn("content-campaign", content)
        self.assertIn("dailyPostingLimits", (ROOT / ".agents/company/connections/buffer.py").read_text())

    def test_dispatch_is_publish_commitment_with_final_receipt(self):
        """The clean workflow contract: scheduled == published, final receipt."""
        content = (ROOT / ".agents/company/departments/content/department.py").read_text()
        buffer = (ROOT / ".agents/company/connections/buffer.py").read_text()
        self.assertIn('version = "3.4.0"', content)
        self.assertIn("PUBLICATION_RECEIPT_CONTRACT", content)
        self.assertIn("scheduled == published", content)
        self.assertIn("commitment_type", content)
        self.assertIn("ok:true", content)
        self.assertIn("duplicate_guard", buffer)
        self.assertIn("--queue", buffer)
        self.assertIn("commitment_type", buffer)


if __name__ == "__main__":
    unittest.main()
