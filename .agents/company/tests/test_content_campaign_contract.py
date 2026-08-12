import unittest
from pathlib import Path

from company.connections.buffer import BufferClient
from company.departments.content.department import SPIELOS_NOTE, ready_campaign_package, validate_campaign_package


ROOT = Path(__file__).resolve().parents[3]


def platform_package(platform, asset_type, preset, destination):
    return {
        "platform": platform,
        "text": f"A focused buyer insight. {destination}\n\n{SPIELOS_NOTE}",
        "destination": destination,
        "asset": {"type": asset_type, "url": f"https://cdn.spielos.xyz/{platform}.{ 'mp4' if asset_type == 'video' else 'png'}"},
        "creative_variation": {
            "format": "single-idea", "layout": "centered-journey", "theme": "gruvbox-dark",
            "background": "panel-deep", "color_role": "primary", "alignment": "center", "size_preset": preset,
        },
    }


def paired_idea(index):
    threads = platform_package("threads", "image", "threads-portrait", f"https://spielos.xyz/services/?utm_source=threads&utm_medium=social&utm_campaign=content-leads-20260812&utm_content=batch-01-threads-{index}")
    youtube = platform_package("youtube", "video", "youtube-shorts", f"https://spielos.xyz/services/?utm_source=youtube&utm_medium=social&utm_campaign=content-leads-20260812&utm_content=batch-01-youtube-{index}")
    threads["text"] = f"An established business with repetitive customer work needs context before advice. {threads['destination']}\n\n{SPIELOS_NOTE}"
    youtube["text"] = f"SpielOS helps an established business improve one supervised AI workflow. {youtube['destination']}\n\n{SPIELOS_NOTE}"
    threads["creative_variation"]["layout"] = f"left-journey-{index}"
    youtube["creative_variation"]["layout"] = f"portrait-journey-{index}"
    item = {
        "batch_item": index, "one_idea": f"Operational proof {index}",
        "hook": f"If your operation repeats manual work {index}, this is what SpielOS helps fix.",
        "operator_context": "Established businesses with repetitive knowledge work.",
        "spielos_role": "A supervised AI operating system for one real workflow.",
        "cta": "Talk through your workflow at SpielOS services.",
        "platform_packages": [threads, youtube],
    }
    if index == 5:
        item["narrative_type"] = "live-journey"
        item["live_story"] = {
            "trigger": "An unclear cold-audience hook was rejected.",
            "tension": "Advice without context assumes the reader knows SpielOS.",
            "decision": "Require the operator situation and SpielOS role before advice.",
            "tradeoff": "Less clever wording, more immediate clarity.",
            "harness_rule": "Goal, review gate, and measured next step.",
            "next_step": "Compare qualified visits and services CTA clicks.",
            "proof_url": "https://spielos.xyz/live/",
        }
    return item


def valid_batch():
    return {
        "campaign": "content-leads-20260812", "batch_number": 1, "batch_size": 5,
        "daily_targets": {"threads": 50, "youtube": 50},
        "batch_items": [paired_idea(index) for index in range(1, 6)],
    }


class ContentCampaignContractTests(unittest.TestCase):
    def test_valid_campaign_requires_distinct_platform_renditions_and_tracking(self):
        package = {
            "campaign": "content-leads-20260812", "one_idea": "Visible operating proof beats generic AI claims",
            "platform_packages": [
                platform_package("threads", "image", "threads-portrait", "https://spielos.xyz/services/?utm_source=threads&utm_medium=social&utm_campaign=content-leads-20260812&utm_content=threads-proof-01"),
                platform_package("youtube", "video", "youtube-shorts", "https://spielos.xyz/services/?utm_source=youtube&utm_medium=social&utm_campaign=content-leads-20260812&utm_content=youtube-proof-01"),
            ],
        }
        self.assertEqual(validate_campaign_package(package), [])
        ready = ready_campaign_package(package)
        self.assertEqual(len(ready["posts"]), 2)
        self.assertTrue(all(item["creative_signature"] for item in ready["posts"]))

    def test_duplicate_or_untracked_creative_is_rejected(self):
        destination = "https://spielos.xyz/services/?utm_source=threads&utm_medium=social&utm_campaign=content-leads&utm_content=threads-proof-01"
        package = {"one_idea": "Proof", "platform_packages": [
            platform_package("threads", "image", "threads-portrait", destination),
            platform_package("youtube", "video", "youtube-shorts", "https://spielos.xyz/contact/?utm_source=youtube&utm_medium=social&utm_campaign=content-leads&utm_content=youtube-proof-01"),
        ]}
        prior = ready_campaign_package(package)
        errors = validate_campaign_package(package, [prior])
        self.assertTrue(any("repeats" in error for error in errors))
        package["platform_packages"][0]["destination"] = "https://spielos.xyz/?utm_source=threads"
        errors = validate_campaign_package(package)
        self.assertTrue(any("tracked" in error for error in errors))

    def test_five_item_batch_requires_context_and_live_company_story(self):
        batch = valid_batch()
        self.assertEqual(validate_campaign_package(batch), [])
        ready = ready_campaign_package(batch)
        self.assertEqual(len(ready["posts"]), 10)
        self.assertTrue(ready["review_required"])
        self.assertEqual(ready["learning_manifest"][-1]["narrative_type"], "live-journey")

    def test_batch_rejects_wrong_size_or_missing_context_first_story(self):
        batch = valid_batch()
        batch["batch_size"] = 4
        batch["batch_items"][0].pop("operator_context")
        batch["batch_items"][4].pop("live_story")
        errors = validate_campaign_package(batch)
        self.assertTrue(any("exactly five" in error for error in errors))
        self.assertTrue(any("context-first operator_context" in error for error in errors))
        self.assertTrue(any("live-journey" in error for error in errors))

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


if __name__ == "__main__":
    unittest.main()
