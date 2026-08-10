import json
import unittest
from pathlib import Path

from company.connections import connection, connections
from company.departments.seo.keywords import build_opportunities
from company.runtime.catalog import catalog
from company.runtime.models import ContentPackage, Department, GoalContext, Goal
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
        self.assertEqual({"buffer", "posthog", "search-console", "website", "web-research",
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

    def test_content_package_is_only_a_serializable_run_artifact(self):
        item = ContentPackage("pkg-1", "goal-1", "run-1", {"idea": "one loop"},
                              ({"kind": "x_post"},), ("ev-1",), {})
        self.assertEqual("run-1", item.run_id)
        self.assertFalse(isinstance(item, Department))

    def test_department_requests_agent_then_evaluates_typed_evidence(self):
        goal = Goal("g", "graphics", "design", "rendition_count", "ge", 1,
                    None, None, "active", {"workflow": "rendition-pack"})
        department = departments()["design"]
        ctx = GoalContext(goal, {"evidence": []}, (), lambda _: None)
        decision = department.decide(ctx, department.observe(ctx).payload)
        self.assertEqual("request_agent", decision.payload["action"])
        ctx = GoalContext(goal, {"evidence": [{"kind": "graphic_render"}]}, (), lambda _: None)
        decision = department.decide(ctx, department.observe(ctx).payload)
        self.assertEqual("evaluate", decision.payload["action"])

    def test_content_publish_is_approval_gated_then_requests_host_connection(self):
        goal = Goal("g", "publish", "content", "published_items", "ge", 1,
                    None, None, "active",
                    {"workflow": "publish", "connection": "buffer", "execution_mode": "dry_run"})
        evidence = [{"kind": "content_package", "payload": {"channel_id": "channel", "text": "hello"}}]
        department = departments()["content"]
        waiting = GoalContext(goal, {"evidence": evidence}, (), lambda _: None)
        decision = department.decide(waiting, department.observe(waiting).payload)
        self.assertEqual("awaiting_approval", department.act(waiting, decision.payload).run_status.value)
        approved = GoalContext(goal, {"evidence": evidence}, (), lambda _: "approved")
        result = department.act(approved, decision.payload)
        self.assertEqual("blocked", result.run_status.value)
        self.assertEqual("buffer", result.payload["connection_request"]["connection_id"])
        self.assertEqual("publication_receipt", result.payload["connection_request"]["required_evidence"])


class ConnectionContractTests(unittest.TestCase):
    def test_interactive_connections_are_host_first(self):
        for connection_id in ("buffer", "posthog", "search-console", "website", "web-research"):
            item = connection(connection_id)
            self.assertEqual(("codex", "opencode"), item.hosts)
            self.assertFalse(item.unattended)
            self.assertEqual((), item.required_environment)

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

    def test_keyword_research_marks_unmeasured_demand_unknown(self):
        values = build_opportunities(["AI department", "company harness"],
            [{"keys": ["company harness software"], "impressions": 40, "clicks": 3}])
        self.assertEqual("unknown", values[0]["demand_status"])
        self.assertIsNone(values[0]["impressions"])
        self.assertEqual("measured", values[1]["demand_status"])


if __name__ == "__main__":
    unittest.main()
