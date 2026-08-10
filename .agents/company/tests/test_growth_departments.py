import json
import os
import tempfile
import unittest
from pathlib import Path

from company.catalog import catalog
from company.connections.astro_blog import AstroBlogConnection
from company.connections.buffer import BufferConnection
from company.connections.posthog import PostHogConnection
from company.connections.search_console import SearchConsoleConnection
from company.models import ContentPackage, Department, EngineContext, Goal
from company.registry import engines
from company.departments.seo.keywords import build_opportunities


class GrowthDepartmentTests(unittest.TestCase):
    def test_four_production_departments_are_registered(self):
        registry = engines()
        for engine_id in ("content", "design", "analytics", "seo"):
            self.assertIn(engine_id, registry)
            self.assertIsInstance(registry[engine_id], Department)
            self.assertTrue(registry[engine_id].production_ready)

    def test_catalog_exposes_tools_connections_and_no_capability_duplicates(self):
        value = catalog()
        department_ids = [item["id"] for item in value["departments"]]
        self.assertEqual(len(department_ids), len(set(department_ids)))
        self.assertEqual({"analytics", "publishing", "rendering", "search"},
                         {item["id"] for item in value["tools"]})
        self.assertEqual({"astro-blog", "buffer", "posthog", "search-console"},
                         {item["id"] for item in value["connections"]})

    def test_content_package_is_only_a_serializable_run_artifact(self):
        item = ContentPackage("pkg-1", "goal-1", "run-1", {"idea": "one loop"},
                              ({"kind": "x_post"},), ("ev-1",), {})
        self.assertEqual("run-1", item.run_id)
        self.assertFalse(isinstance(item, Department))

    def test_department_requests_bounded_agent_then_evaluates_typed_evidence(self):
        goal = Goal("g", "graphics", "design", "rendition_count", "ge", 1, None, None, "active",
                    {"workflow": "rendition-pack"})
        ctx = EngineContext(goal, {"evidence": []}, (), lambda _: None)
        decision = engines()["design"].decide(ctx, engines()["design"].observe(ctx).payload)
        self.assertEqual("request_agent", decision.payload["action"])
        ctx = EngineContext(goal, {"evidence": [{"kind": "graphic_render"}]}, (), lambda _: None)
        decision = engines()["design"].decide(ctx, engines()["design"].observe(ctx).payload)
        self.assertEqual("evaluate", decision.payload["action"])

    def test_content_publish_is_approval_gated_and_uses_connection(self):
        goal = Goal("g", "publish", "content", "published_items", "ge", 1, None, None, "active",
                    {"workflow": "publish", "connection": "buffer", "execution_mode": "dry_run"})
        evidence = [{"kind": "content_package", "payload": {"channel_id": "channel", "text": "hello"}}]
        engine = engines()["content"]
        waiting_ctx = EngineContext(goal, {"evidence": evidence}, (), lambda _: None)
        decision = engine.decide(waiting_ctx, engine.observe(waiting_ctx).payload)
        self.assertEqual("awaiting_approval", engine.act(waiting_ctx, decision.payload).run_status.value)
        approved_ctx = EngineContext(goal, {"evidence": evidence}, (), lambda _: "approved")
        result = engine.act(approved_ctx, decision.payload)
        self.assertTrue(result.payload["publication_receipt"]["ok"])
        self.assertTrue(result.payload["publication_receipt"]["data"]["dry_run"])


class ConnectionContractTests(unittest.TestCase):
    def test_buffer_dry_run_matches_graphql_contract_without_network(self):
        result = BufferConnection().create_post(channel_id="channel", text="hello", dry_run=True)
        self.assertTrue(result.ok)
        self.assertEqual("addToQueue", result.data["variables"]["input"]["mode"])

    def test_posthog_dry_run_is_read_only_query(self):
        result = PostHogConnection().query({"kind": "HogQLQuery", "query": "select 1"}, dry_run=True)
        self.assertTrue(result.ok)
        self.assertIn("/query/", result.data["endpoint"])

    def test_search_console_caps_rows_and_encodes_domain_property(self):
        result = SearchConsoleConnection().query_performance("2026-08-01", "2026-08-02", row_limit=99999)
        self.assertEqual(25000, result.data["body"]["rowLimit"])
        self.assertIn("sc-domain%3Aspielos.xyz", result.data["endpoint"])

    def test_blog_dry_run_and_no_overwrite_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src/content/notes").mkdir(parents=True)
            connection = AstroBlogConnection(root)
            self.assertTrue(connection.publish(slug="good-slug", source="---\n---\n", dry_run=True).ok)
            self.assertFalse(connection.publish(slug="Bad Slug", source="x", dry_run=True).ok)
            target = root / "src/content/notes/existing.mdx"
            target.write_text("existing")
            self.assertFalse(connection.publish(slug="existing", source="new", dry_run=False).ok)


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
