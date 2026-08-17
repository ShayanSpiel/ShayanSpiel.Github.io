import json
import unittest
from pathlib import Path

from company.connections import connection, connections
from company.departments.seo.keywords import build_opportunities
from company.runtime.catalog import catalog
from company.runtime.models import Department, GoalContext, Goal
from company.runtime.registry import departments


class GrowthDepartmentTests(unittest.TestCase):
    def test_five_departments_are_discovered_from_their_own_folders(self):
        installed = departments()
        self.assertEqual({"outbound", "content", "design", "analytics", "seo"},
                         set(installed))
        self.assertTrue(all(isinstance(item, Department) for item in installed.values()))

    def test_catalog_exposes_only_universal_building_blocks(self):
        value = catalog()
        self.assertNotIn("tools", value)
        self.assertNotIn("control_engines", value)
        self.assertEqual("interpreter", value["runtime"]["department_runtime"])
        self.assertEqual({"attio", "buffer", "posthog", "search-console", "website", "web-research",
                          "email-delivery"},
                         {item["id"] for item in value["connections"]})
        known_connections = {item["id"] for item in value["connections"]}
        referenced = {
            connection_id
            for department in value["departments"]
            for workflow in department["workflows"]
            for connection_id in workflow["connections"]
        }
        self.assertLessEqual(referenced, known_connections)
        lego = {item["id"] for item in value["departments"] if item.get("lego")}
        self.assertTrue({"content", "design", "analytics", "seo"}.issubset(lego))

    def test_representative_departments_share_frozen_lego_contract(self):
        value = catalog()
        representatives = {
            item["id"]: item for item in value["departments"]
            if item["id"] in {"content", "analytics", "outbound"}
        }
        self.assertEqual({"content", "analytics", "outbound"}, set(representatives))
        package_fields = {
            "id", "version", "description", "agent_ids", "workflow_agents",
            "evidence_metrics", "metrics", "config_schema", "workflows",
            "package_defects", "lego",
        }
        workflow_fields = {
            "id", "description", "steps", "agents", "skills", "approvals",
            "evidence", "connections", "graph",
        }
        step_fields = {
            "id", "kind", "employee_id", "produces", "requires", "skill_ids",
            "connection_ids",
        }
        for department in representatives.values():
            self.assertEqual([], department["package_defects"])
            self.assertTrue(department["lego"])
            self.assertEqual(package_fields, set(department))
            self.assertTrue(department["metrics"])
            self.assertTrue(department["evidence_metrics"])
            self.assertTrue(department["workflows"])
            for workflow in department["workflows"]:
                self.assertEqual(workflow_fields, set(workflow))
                self.assertTrue(workflow["steps"])
                self.assertTrue(workflow["agents"])
                self.assertTrue(workflow["evidence"])
                for step in workflow["graph"]:
                    self.assertEqual(step_fields, set(step))
                    self.assertIn(step["kind"], {"employee", "approval", "connection", "machine"})

    def test_department_requests_agent_then_evaluates_typed_evidence(self):
        goal = Goal("g", "graphics", "design", "approved_designs", "ge", 1,
                    None, None, "active", {"workflow": "social-visual"})
        department = departments()["design"]
        ctx = GoalContext(goal, {"evidence": []}, (), lambda _: None)
        decision = department.decide(ctx, department.observe(ctx).payload)
        self.assertEqual("request_agent", decision.payload["action"])
        self.assertEqual("designer", decision.payload["agent_id"])
        self.assertEqual(["approved_design"], decision.payload["accepted_evidence_kinds"])
        self.assertEqual(["spielos-ui"], decision.payload["skill_ids"])
        self.assertEqual("social-visual", decision.payload["workflow_id"])
        ctx = GoalContext(goal, {"evidence": [{"kind": "approved_design"}]}, (), lambda _: None)
        decision = department.decide(ctx, department.observe(ctx).payload)
        self.assertEqual("evaluate", decision.payload["action"])

    def test_content_publish_is_approval_gated_then_uses_direct_buffer_connection(self):
        goal = Goal("g", "publish", "content", "published_items", "ge", 1,
                    None, None, "active",
                    {"workflow": "publish", "connection": "buffer", "execution_mode": "dry_run"})
        evidence = [{"kind": "content_package", "payload": {"channel_id": "channel", "text": "hello"}}]
        department = departments()["content"]
        waiting = GoalContext(goal, {"evidence": evidence}, (), lambda _: None)
        observation = department.observe(waiting).payload
        decision = department.decide(waiting, observation)
        self.assertEqual("request_approval", decision.payload["action"])
        self.assertEqual("awaiting_approval", department.act(waiting, decision.payload).run_status.value)
        approved = GoalContext(goal, {"evidence": evidence}, (), lambda _: "approved")
        advanced = department.act(approved, decision.payload)
        self.assertEqual("DECIDE", advanced.next_stage.value)
        next_decision = department.decide(approved, department.observe(approved).payload)
        self.assertEqual("connection_dispatch", next_decision.payload["action"])
        # Connection dispatch also requires approval before direct delivery.
        self.assertEqual("awaiting_approval",
                         department.act(waiting, next_decision.payload).run_status.value)
        result = department.act(approved, next_decision.payload)
        self.assertEqual("blocked", result.run_status.value)
        self.assertEqual("Buffer dispatch is a dry run; no post was created",
                         result.payload["connection_request"]["message"])


class ConnectionContractTests(unittest.TestCase):
    def test_interactive_connections_are_host_first_except_direct_buffer_delivery(self):
        for connection_id in ("posthog", "search-console", "website", "web-research"):
            item = connection(connection_id)
            self.assertEqual(("codex", "opencode"), item.hosts)
            self.assertFalse(item.unattended)
            self.assertEqual((), item.required_environment)
        item = connection("buffer")
        self.assertEqual(("direct",), item.hosts)
        self.assertTrue(item.unattended)
        self.assertEqual(("BUFFER_API_KEY",), item.required_environment)

    def test_only_email_delivery_requires_unattended_direct_credentials(self):
        item = connections()["email-delivery"]
        self.assertTrue(item.unattended)
        self.assertEqual(("direct",), item.hosts)
        self.assertEqual(("EMAIL_PROVIDER",), item.required_environment)


class DesignContractTests(unittest.TestCase):
    def test_presets_cover_landscape_square_portrait_and_story(self):
        path = Path(__file__).parents[1] / "departments/design/presets.json"
        presets = json.loads(path.read_text())
        ratios = {(value["width"] > value["height"], value["width"] == value["height"],
                   value["width"] < value["height"]) for value in presets.values()}
        self.assertIn((True, False, False), ratios)
        self.assertIn((False, True, False), ratios)
        self.assertIn((False, False, True), ratios)

    def test_campaign_video_templates_are_restored_batch1_flat_with_still_thumbnail_titles(self):
        root = Path(__file__).parents[3]
        sources = "\n".join((root / path).read_text() for path in (
            ".agents/company/departments/design/templates/video/scenario-b.html",
            ".agents/company/departments/design/templates/video/scenario-c.html",
        ))
        # Owner order 2026-08-13: revert the contrast/placement experiment.
        # Templates are batch-1 flat again: no campaign scene machinery, no
        # visual.* contract fields, no stale legacy fixed scene copy.
        for stale in ("Employees using AI separately", "Repeated prompts, copied context",
                      "One assistant doing everything", "Hire a role", "AI directs"):
            self.assertNotIn(stale, sources)
        for field in ("visual.headline", "visual.supporting_text", "visual.component",
                      "visual.icon", "visual.labels"):
            self.assertNotIn(field, sources)
        for machinery in ("campaign-scene", "campaign-label", "__applyCampaignRendition",
                          "spoken_display_alignment"):
            self.assertNotIn(machinery, sources)
        for marker in ("hook-main", "cta-url", "spielos.xyz/services",
                       "thumb-title", "__setStillTitle"):
            self.assertIn(marker, sources)
        tts = (root / "scripts/tts-gemini.js").read_text()
        self.assertNotIn("SpielOS (pronounced", tts)
        self.assertIn('[/SpielOS/g, "Shpeel O S"]', tts)
        self.assertIn('spoken_display_alignment === "url-pronunciation"', tts)
        self.assertIn('displayed === "spielos.xyz/services"', tts)
        self.assertIn('spoken === "go to spielos dot xyz slash services."', tts)

    def test_keyword_research_marks_unmeasured_demand_unknown(self):
        values = build_opportunities(["AI department", "company harness"],
            [{"keys": ["company harness software"], "impressions": 40, "clicks": 3}])
        self.assertEqual("unknown", values[0]["demand_status"])
        self.assertIsNone(values[0]["impressions"])
        self.assertEqual("measured", values[1]["demand_status"])


if __name__ == "__main__":
    unittest.main()
