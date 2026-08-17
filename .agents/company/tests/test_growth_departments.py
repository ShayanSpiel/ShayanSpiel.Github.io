import json
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from company.connections import connection, connections
from company.departments.analytics.posthog import (
    PostHogClient, PostHogError, consume_batch_evidence, posthog_token,
)
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


class PostHogWarehouseTests(unittest.TestCase):
    """Read-only PostHog warehouse wiring (v1.3.0)."""

    def test_posthog_token_is_never_hardcoded_in_source(self):
        source = Path(__file__).parents[1] / "departments/analytics/posthog.py"
        self.assertNotIn("phc_1osIFVXYDFr7Z00RN5gRaF4kRfZ1safm9c7NswRfKpm",
                         source.read_text())

    @patch.dict("os.environ", {"POSTHOG_PROJECT_TOKEN": "phc_test"}, clear=False)
    def test_posthog_token_reads_from_environment_or_env_file(self):
        self.assertEqual("phc_test", posthog_token())

    @patch.dict("os.environ", {"POSTHOG_PROJECT_TOKEN": "phc_test"}, clear=False)
    def test_posthog_client_sends_read_only_warehouse_request(self):
        captured = {}

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({
                    "columns": ["event", "c"],
                    "rows": [["content_landing", 4]],
                    "types": ["string", "UInt64"], "query_id": "q1",
                }).encode("utf-8")

        def fake_urlopen(request, timeout=30):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["key"] = next(
                (value for name, value in request.header_items()
                 if name.lower() == "x-project-api-key"), None)
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse()

        client = PostHogClient()
        with patch("company.departments.analytics.posthog.urlopen",
                   side_effect=fake_urlopen):
            rows = client.rows("select event, count() as c from events group by event")

        self.assertEqual("https://us.posthog.com/api/warehouse/query/", captured["url"])
        self.assertEqual("POST", captured["method"])
        self.assertEqual("phc_test", captured["key"])
        self.assertEqual("HogQLQuery", captured["body"]["query"]["kind"])
        self.assertEqual([{"event": "content_landing", "c": 4}], rows["rows"])
        self.assertEqual("q1", rows["query_id"])

    @patch.dict("os.environ", {"POSTHOG_PROJECT_TOKEN": "phc_test"}, clear=False)
    def test_event_counts_labels_missing_events_never_zero(self):
        client = PostHogClient()
        client.rows = lambda hogql, timeout=30: {
            "query_id": "q1", "columns": ["event", "c"],
            "rows": [{"event": "content_landing", "c": 3}],
        }

        result = client.event_counts()

        self.assertTrue(result["ok"])
        self.assertEqual({"content_landing": 3}, result["events"])
        self.assertEqual(["cta_clicked", "lead_form_success"], result["missing_events"])
        self.assertNotIn("lead_form_success", result["events"])

    @patch.dict("os.environ", {"POSTHOG_PROJECT_TOKEN": "phc_test"}, clear=False)
    def test_warehouse_http_error_raises_safe_read_only_error(self):
        client = PostHogClient()

        def boom(request, timeout=30):
            raise HTTPError("https://us.posthog.com/api/warehouse/query/",
                            401, "Unauthorized", {}, None)

        with patch("company.departments.analytics.posthog.urlopen",
                   side_effect=boom):
            with self.assertRaisesRegex(PostHogError, "HTTP 401"):
                client.query("select 1")


class FunnelConsumptionTests(unittest.TestCase):
    """funnel-analysis consumes refreshed Buffer + PostHog warehouse per batch."""

    @staticmethod
    def _refresh(posts):
        return {"ok": True, "count": len(posts),
                "window": {"stale_after_hours": 6.0},
                "posts": posts, "rate_limits": {}}

    def test_consume_batch_evidence_joins_buffer_and_posthog_on_join_keys(self):
        receipts = [
            {"item_id": "batch-01-item-01", "platform": "threads",
             "content_id": "batch-01-item-01-threads",
             "creative_signature": "sig-t", "provider_post_id": "post-1"},
            {"item_id": "batch-01-item-01", "platform": "youtube",
             "content_id": "batch-01-item-01-youtube",
             "creative_signature": "sig-y", "provider_post_id": "post-2"},
        ]
        refresh = self._refresh([
            {"post_id": "post-1", "status": "sent", "channel_service": "threads",
             "metrics": {"views": 60, "likes": 1, "replies": 0, "reposts": None,
                         "shares": None, "followers": 1},
             "metrics_updated_at": "2026-08-17T09:00:00Z", "staleness": "fresh",
             "missing_metrics": ["reposts", "shares"]},
            {"post_id": "post-2", "status": "sent", "channel_service": "youtube",
             "metrics": {"views": 70, "likes": 2, "replies": 0, "reposts": None,
                         "shares": None, "followers": None},
             "metrics_updated_at": "2026-08-17T09:00:00Z", "staleness": "fresh",
             "missing_metrics": ["reposts", "shares", "followers"]},
        ])
        events = {"events": {"content_landing": 5, "cta_clicked": 1,
                             "lead_form_success": 1}, "missing_events": []}

        evidence = consume_batch_evidence(
            campaign_id="content-leads-20260812", batch_id="batch-01",
            delivery_receipts=receipts, buffer_refresh=refresh,
            posthog_events=events,
            evidence_window={"since": "2026-08-17T00:00:00Z",
                             "until": "2026-08-18T00:00:00Z"})

        self.assertEqual(
            ["campaign_id", "batch_id", "item_id", "content_id", "creative_signature"],
            evidence["join_keys"])
        self.assertEqual(130, evidence["funnel"]["platform_views"]["value"])
        self.assertFalse(evidence["funnel"]["platform_views"]["missing"])
        self.assertEqual(5, evidence["funnel"]["content_landings"]["value"])
        self.assertEqual(1, evidence["funnel"]["service_cta_clicks"]["value"])
        self.assertEqual(1, evidence["funnel"]["leads"]["value"])
        self.assertEqual(5 / 130, evidence["funnel"]["ctr"])
        self.assertTrue(evidence["technical_only"])
        self.assertIn("Missing counts are labeled missing, never zero",
                      evidence["honesty_rules"])
        self.assertEqual("buffer_refresh", evidence["funnel"]["platform_views"]["source"])
        self.assertEqual("posthog_warehouse", evidence["funnel"]["leads"]["source"])

    def test_consume_batch_evidence_never_invents_zero_counts(self):
        receipts = [
            {"item_id": "batch-01-item-01", "platform": "threads",
             "content_id": "batch-01-item-01-threads",
             "creative_signature": "sig-t", "provider_post_id": "post-1"},
        ]
        refresh = self._refresh([
            {"post_id": "post-1", "status": "sent", "channel_service": "threads",
             "metrics": {"views": None, "likes": None, "replies": None,
                         "reposts": None, "shares": None, "followers": None},
             "metrics_updated_at": None, "staleness": "missing",
             "missing_metrics": ["views", "likes", "replies", "reposts",
                                 "shares", "followers"]},
        ])
        events = {"events": {}, "missing_events": ["content_landing", "cta_clicked",
                                                   "lead_form_success"]}

        evidence = consume_batch_evidence(
            campaign_id="content-leads-20260812", batch_id="batch-01",
            delivery_receipts=receipts, buffer_refresh=refresh,
            posthog_events=events)

        funnel = evidence["funnel"]
        self.assertTrue(funnel["platform_views"]["missing"])
        self.assertIsNone(funnel["platform_views"]["value"])
        self.assertTrue(funnel["leads"]["missing"])
        self.assertIsNone(funnel["leads"]["value"])
        self.assertIsNone(funnel["ctr"])
        self.assertEqual(["content_landing", "cta_clicked", "lead_form_success"],
                         evidence["posthog_warehouse"]["missing_events"])
        self.assertIn("batch-01-item-01-threads:views",
                      evidence["buffer_refresh"]["missing_metric_labels"])
        self.assertEqual({"batch-01-item-01-threads": "missing"},
                         evidence["buffer_refresh"]["staleness_by_rendition"])

    def test_consume_batch_evidence_marks_stale_refreshes(self):
        receipts = [
            {"item_id": "batch-01-item-01", "platform": "youtube",
             "content_id": "batch-01-item-01-youtube",
             "creative_signature": "sig-y", "provider_post_id": "post-2"},
        ]
        refresh = self._refresh([
            {"post_id": "post-2", "status": "sent", "channel_service": "youtube",
             "metrics": {"views": 23, "likes": None, "replies": None,
                         "reposts": None, "shares": None, "followers": None},
             "metrics_updated_at": "2026-08-13T08:00:00Z", "staleness": "stale",
             "missing_metrics": ["likes", "replies", "reposts", "shares",
                                 "followers"]},
        ])
        events = {"events": {"content_landing": 2}, "missing_events": ["cta_clicked",
                                                                      "lead_form_success"]}

        evidence = consume_batch_evidence(
            campaign_id="content-leads-20260812", batch_id="batch-01",
            delivery_receipts=receipts, buffer_refresh=refresh,
            posthog_events=events)

        self.assertEqual(["post-2"], evidence["buffer_refresh"]["stale_post_ids"])
        self.assertEqual("stale",
                         evidence["buffer_refresh"]["staleness_by_rendition"]["batch-01-item-01-youtube"])


if __name__ == "__main__":
    unittest.main()
