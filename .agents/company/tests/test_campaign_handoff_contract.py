import unittest
from pathlib import Path

from company.departments.analytics.department import campaign_funnel_report
from company.departments.campaign_contract import (
    LINK_IN_BIO,
    SCHEMA_VERSION,
    SPIELOS_REMINDER,
    apply_delivery_receipts,
    apply_funnel_report,
    apply_render_report,
    approve_rendered_campaign,
    creative_signature,
    publication_package,
    record_optimization_decision,
    validate_campaign,
)
from company.departments.design.department import accept_design_order, render_report


ROOT = Path(__file__).resolve().parents[3]


def campaign_manifest():
    campaign_id = "content-leads-20260812"
    items = []
    for sequence in range(1, 6):
        item_id = f"batch-01-item-{sequence:02d}"
        renditions = {}
        for platform, asset_type, preset in (
            ("threads", "image", "threads-portrait"),
            ("youtube", "video", "youtube-shorts"),
        ):
            content_id = f"{item_id}-{platform}"
            destination = (
                f"https://spielos.xyz/services/?utm_source={platform}&utm_medium=social"
                f"&utm_campaign={campaign_id}&utm_content={content_id}"
            )
            design = {
                "template_id": "harness-architecture" if platform == "threads" else "scenario-b",
                "theme": ["gruvbox-dark", "gruvbox-light", "blue-dark", "monochrome-dark", "black-gold-dark"][sequence - 1],
                "surface": "background", "color_role": "primary", "alignment": "center",
                "layout": f"journey-variant-{sequence}", "size_preset": preset,
                "eyebrow": "SpielOS · supervised AI workflows",
                "title_lines": [f"Operational context {sequence}.", "One clear workflow."],
                "accent_line": 1,
                "supporting_text": "The title, hierarchy, and message share one campaign source.",
                "station_labels": ["Strategy", "Design", "Publish", "Measure", "Decide"],
            }
            rendition = {
                "platform": platform, "content_id": content_id,
                "copy": (
                    f"AI answers are useful. But repeated work still needs a usable workflow.\n\n"
                    f"Map the missing workflow:\n{destination}"
                    if platform == "threads" else
                    f"AI answers are useful. But repeated work still needs a usable workflow.\n\n{LINK_IN_BIO}"
                ) + (f"\n\n{SPIELOS_REMINDER}" if sequence == 5 else ""),
                "destination": destination,
                "link_placement": "caption" if platform == "threads" else "bio",
                "design": design,
            }
            if platform == "youtube":
                rendition["narration"] = {"scenes": [
                    {"id": scene, "text": text} for scene, text in (
                        ("hook", "AI answers are useful. But repeated work still needs a usable workflow."),
                        ("pain", "Context disappears across tools."),
                        ("promise", "SpielOS connects one supervised workflow."),
                        ("proof", "The decision and review stay visible."),
                        ("next", "Measure the result before scaling."),
                        ("cta", "spielos dot xyz slash services."),
                    )
                ]}
            renditions[platform] = rendition
        item = {
            "sequence": sequence, "item_id": item_id,
            "one_idea": f"One operating proof {sequence}",
            "brief": {
                "reader": "Owner of an established service business",
                "customer_moment": "Staff move repeated customer work between disconnected tools by hand.",
                "one_idea": f"One operating proof {sequence}",
                "desired_result": "Move the work faster without losing customer context.",
                "proof": "The work can be mapped from intake to result.",
            },
            "hook": {"id": f"context-hook-{sequence}", "text": "AI answers are useful. But repeated work still needs a usable workflow."},
            "cta": {"id": f"services-cta-{sequence}", "text": "Map the missing workflow."},
            "narrative_type": "spielos-reminder" if sequence == 5 else "customer-insight",
            "renditions": renditions,
        }
        if sequence == 5:
            item["reminder"] = {
                "text": SPIELOS_REMINDER,
                "proof": "The company uses SpielOS to operate its own repeatable work.",
            }
        items.append(item)
    return {
        "schema_version": SCHEMA_VERSION, "phase": "strategy",
        "campaign_id": campaign_id, "batch_id": "content-leads-20260812-batch-01",
        "batch_number": 1, "batch_size": 5,
        "daily_targets": {"threads": 50, "youtube": 50},
        "objective": {"qualified_visits_per_day": 200, "leads_per_day": 10,
                      "lead_conversion_rate": 0.05},
        "strategy": {
            "references": {
                "icp": ".agents/company/strategy/icp.md",
                "positioning": ".agents/company/strategy/positioning.md",
                "voice": ".agents/company/strategy/voice.md",
            },
            "hypothesis": "Context-first creative will attract more qualified service intent.",
            "controlled_variables": {"offer": "services", "batch_size": 5},
            "changed_variables": ["hook"],
        },
        "experiment": {
            "id": "context-hook-test-01", "test_type": "single-variable",
            "scope": "cross-channel-creative", "variables": ["hook"],
            "cells": [
                {"id": "control-hook", "role": "control", "values": {"hook": "direct-context"}},
                {"id": "variant-hook", "role": "variant", "values": {"hook": "problem-context"}},
            ],
            "assignment": {"method": "balanced", "unit": "content_id"},
            "primary_metric": "ctr", "guardrails": ["lead_conversion_rate"],
            "minimum_evidence_per_cell": 100,
            "analysis_method": "difference-in-rates",
        },
        "measurement": {"join_keys": ["campaign_id", "batch_id", "item_id", "content_id", "creative_signature"]},
        "items": items, "handoffs": [],
    }


def factorial_manifest():
    manifest = campaign_manifest()
    manifest["strategy"]["changed_variables"] = ["hook", "cta"]
    manifest["experiment"].update({
        "id": "hook-cta-factorial-01", "test_type": "factorial",
        "variables": ["hook", "cta"],
        "cells": [
            {"id": "control-both", "role": "control",
             "values": {"hook": "direct", "cta": "services"}},
            {"id": "variant-hook", "role": "variant",
             "values": {"hook": "problem", "cta": "services"}},
            {"id": "variant-cta", "role": "variant",
             "values": {"hook": "direct", "cta": "audit"}},
            {"id": "variant-both", "role": "variant",
             "values": {"hook": "problem", "cta": "audit"}},
        ],
    })
    return manifest


def measured_campaign(manifest, sample_size=250, effects=None):
    designed = accept_design_order(manifest)
    assets = [
        {"item_id": item["item_id"], "platform": platform,
         "type": "image" if platform == "threads" else "video",
         "local_path": "asset", "sha256": f"sha-{item['item_id']}-{platform}",
         "render_report_id": f"render-{item['item_id']}-{platform}"}
        for item in designed["items"] for platform in ("threads", "youtube")
    ]
    rendered = apply_render_report(designed, render_report(designed, assets))
    approvals = [
        {"item_id": item["item_id"], "platform": platform, "status": "approved",
         "approval_id": f"approval-{item['item_id']}-{platform}",
         "public_url": f"https://cdn.spielos.xyz/{item['item_id']}-{platform}.asset"}
        for item in rendered["items"] for platform in ("threads", "youtube")
    ]
    approved = approve_rendered_campaign(rendered, approvals)
    package = publication_package(approved)
    receipts = [
        {**{key: post[key] for key in ("campaign_id", "batch_id", "item_id", "content_id", "creative_signature", "platform", "approval_id")},
         "provider_post_id": f"buffer-{post['content_id']}", "verified": True, "status": "scheduled"}
        for post in package["posts"]
    ]
    delivered = apply_delivery_receipts(approved, receipts)
    report = campaign_funnel_report(delivered, {
        "content_ids": [post["content_id"] for post in package["posts"]],
        "evidence_complete": True, "evidence_window": "24h",
        "platform_views": sample_size * len(manifest["experiment"]["cells"]),
        "content_landings": 200, "service_cta_clicks": 40, "leads": 10,
        "experiment_cells": [
            {"cell_id": cell["id"], "sample_size": sample_size}
            for cell in manifest["experiment"]["cells"]
        ],
        "effects": effects or [],
    })
    return apply_funnel_report(delivered, report)


class CampaignHandoffContractTests(unittest.TestCase):
    def test_one_artifact_survives_the_complete_campaign_to_lead_journey(self):
        strategy = campaign_manifest()
        self.assertEqual(validate_campaign(strategy, "strategy"), [])

        designed = accept_design_order(strategy)
        assets = [
            {"item_id": item["item_id"], "platform": platform,
             "type": "image" if platform == "threads" else "video",
             "local_path": f".spielos/artifacts/{item['item_id']}-{platform}",
             "sha256": f"sha-{item['item_id']}-{platform}",
             "render_report_id": f"render-{item['item_id']}-{platform}"}
            for item in designed["items"] for platform in ("threads", "youtube")
        ]
        rendered = apply_render_report(designed, render_report(designed, assets))

        approvals = [
            {"item_id": item["item_id"], "platform": platform, "status": "approved",
             "approval_id": f"approval-{item['item_id']}-{platform}",
             "public_url": f"https://cdn.spielos.xyz/{item['item_id']}-{platform}.{'png' if platform == 'threads' else 'mp4'}"}
            for item in rendered["items"] for platform in ("threads", "youtube")
        ]
        approved = approve_rendered_campaign(rendered, approvals)
        package = publication_package(approved)
        self.assertEqual(len(package["posts"]), 10)
        self.assertTrue(all(post["approval_id"] for post in package["posts"]))

        receipts = [
            {**{key: post[key] for key in ("campaign_id", "batch_id", "item_id", "content_id", "creative_signature", "platform", "approval_id")},
             "provider_post_id": f"buffer-{post['content_id']}", "verified": True, "status": "scheduled"}
            for post in package["posts"]
        ]
        delivered = apply_delivery_receipts(approved, receipts)
        content_ids = [post["content_id"] for post in package["posts"]]
        report = campaign_funnel_report(delivered, {
            "content_ids": content_ids, "evidence_complete": True,
            "evidence_window": "24h", "platform_views": 4000,
            "content_landings": 200, "service_cta_clicks": 40, "leads": 10,
            "experiment_cells": [
                {"cell_id": "control-hook", "sample_size": 2000},
                {"cell_id": "variant-hook", "sample_size": 2000},
            ],
            "effects": [{"variables": ["hook"], "supported": True, "effect_size": 0.01}],
        })
        measured = apply_funnel_report(delivered, report)
        evaluated = record_optimization_decision(measured, {
            "evidence_window": "24h", "verdict": "keep context; test a clearer CTA",
            "test_type": "single-variable", "scope": "cross-channel-creative",
            "changed_variables": ["cta"],
            "next_batch_hypothesis": "A concrete workflow-audit CTA will increase service intent.",
        })
        self.assertEqual(validate_campaign(evaluated, "evaluated"), [])
        self.assertEqual(evaluated["campaign_id"], strategy["campaign_id"])
        self.assertEqual([handoff["to"] for handoff in evaluated["handoffs"]],
                         ["designed", "rendered", "approved", "delivered", "measured", "evaluated"])
        self.assertEqual(report["ctr"], 0.05)
        self.assertEqual(report["lead_conversion_rate"], 0.05)

    def test_identity_or_approval_drift_is_rejected(self):
        designed = accept_design_order(campaign_manifest())
        assets = [
            {"item_id": item["item_id"], "platform": platform,
             "type": "image" if platform == "threads" else "video",
             "local_path": "asset", "sha256": "sha", "render_report_id": "render"}
            for item in designed["items"] for platform in ("threads", "youtube")
        ]
        report = render_report(designed, assets)
        report["campaign_id"] = "wrong-campaign"
        with self.assertRaisesRegex(ValueError, "identity"):
            apply_render_report(designed, report)

    def test_renderers_consume_campaign_data_instead_of_batch_specific_copy(self):
        templates = [
            ROOT / ".agents/company/departments/design/templates/social/harness-architecture.html",
            ROOT / ".agents/company/departments/design/templates/video/scenario-b.html",
            ROOT / ".agents/company/departments/design/templates/video/scenario-c.html",
        ]
        template_source = "\n".join(path.read_text() for path in templates)
        renderer_source = "\n".join((ROOT / path).read_text() for path in
                                    ("scripts/render-design.js", "scripts/render-video.js"))
        self.assertNotIn("batch-01.json", template_source)
        self.assertIn("__applyCampaignRendition", template_source)
        self.assertIn("CAMPAIGN_MANIFEST", renderer_source)
        self.assertIn("CAMPAIGN_ITEM_ID", renderer_source)

    def test_creative_identity_is_derived_not_entered_by_a_department(self):
        manifest = campaign_manifest()
        item = manifest["items"][0]
        design = item["renditions"]["threads"]["design"]
        first = creative_signature(manifest["campaign_id"], item["item_id"], "threads", design)
        design["layout"] = "new-layout"
        second = creative_signature(manifest["campaign_id"], item["item_id"], "threads", design)
        self.assertNotEqual(first, second)

    def test_factorial_contract_declares_cells_assignment_metrics_and_analysis(self):
        manifest = factorial_manifest()
        self.assertEqual(validate_campaign(manifest, "strategy"), [])
        manifest["experiment"]["cells"][1]["values"].pop("cta")
        errors = validate_campaign(manifest, "strategy")
        self.assertTrue(any("every variable" in error for error in errors))

    def test_multi_change_requires_supported_independent_or_interaction_effects(self):
        manifest = factorial_manifest()
        measured = measured_campaign(manifest, effects=[
            {"variables": ["hook"], "supported": True, "effect_size": 0.02},
            {"variables": ["cta"], "supported": True, "effect_size": 0.01},
        ])
        decision = {
            "evidence_window": "24h", "verdict": "test both supported effects",
            "test_type": "factorial", "scope": "cross-channel-creative",
            "changed_variables": ["hook", "cta"],
            "next_batch_hypothesis": "Combining the independently supported hook and CTA will improve CTR.",
        }
        evaluated = record_optimization_decision(measured, decision)
        self.assertEqual(validate_campaign(evaluated, "evaluated"), [])
        unsupported = measured_campaign(factorial_manifest(), effects=[
            {"variables": ["hook"], "supported": True, "effect_size": 0.02},
            {"variables": ["cta"], "supported": False, "effect_size": 0.0},
        ])
        with self.assertRaisesRegex(ValueError, "independent or interaction"):
            record_optimization_decision(unsupported, decision)

    def test_sparse_evidence_narrows_next_test_to_one_variable(self):
        measured = measured_campaign(factorial_manifest(), sample_size=20, effects=[])
        with self.assertRaisesRegex(ValueError, "sparse evidence"):
            record_optimization_decision(measured, {
                "evidence_window": "24h", "verdict": "not enough evidence",
                "test_type": "factorial", "scope": "cross-channel-creative",
                "changed_variables": ["hook", "cta"],
                "next_batch_hypothesis": "Premature multi-change test.",
            })

    def test_website_cro_is_identifiable_and_retains_separate_approval(self):
        manifest = campaign_manifest()
        manifest["experiment"].update({"scope": "website-cro",
                                       "assignment": {"method": "randomized", "unit": "session"}})
        errors = validate_campaign(manifest, "strategy")
        self.assertTrue(any("separate website-mutation approval" in error for error in errors))
        manifest["experiment"]["separate_approval_required"] = True
        self.assertEqual(validate_campaign(manifest, "strategy"), [])

    def test_public_copy_rejects_internal_language_and_literal_line_breaks(self):
        manifest = campaign_manifest()
        manifest["items"][0]["renditions"]["threads"]["copy"] = (
            r"I stopped the first batch.\n\nThe review gate caught it."
        )
        errors = validate_campaign(manifest, "strategy")
        self.assertTrue(any("real line breaks" in error for error in errors))
        self.assertTrue(any("internal production language: batch" in error for error in errors))
        self.assertTrue(any("internal production language: review gate" in error for error in errors))

    def test_youtube_uses_bio_and_only_fifth_item_uses_the_reminder(self):
        manifest = campaign_manifest()
        youtube = manifest["items"][0]["renditions"]["youtube"]
        youtube["copy"] += " https://spielos.xyz/services/?utm_source=youtube"
        manifest["items"][0]["renditions"]["threads"]["copy"] += f"\n\n{SPIELOS_REMINDER}"
        manifest["items"][4]["renditions"]["youtube"]["copy"] = LINK_IN_BIO
        errors = validate_campaign(manifest, "strategy")
        self.assertTrue(any("YouTube Shorts copy must not contain a URL" in error for error in errors))
        self.assertTrue(any("must not include the fifth-item" in error for error in errors))
        self.assertTrue(any("must end with the fifth-item" in error for error in errors))

if __name__ == "__main__":
    unittest.main()
