import tempfile
import unittest
from pathlib import Path

from company.departments.outbound.workflows import social
from company.runtime.catalog import catalog
from company.runtime.loop import Runtime


ROOT = Path(__file__).resolve().parents[3]


class CatalogTests(unittest.TestCase):
    def test_catalog_has_one_loop_and_resolvable_composition(self):
        value = catalog()
        self.assertEqual(value["runtime"]["loop"],
                         ["GOAL", "OBSERVE", "DECIDE", "ACT", "EVALUATE"])
        departments = {item["id"]: item for item in value["departments"]}
        self.assertEqual({"outbound", "content", "design", "analytics", "seo"},
                         set(departments))
        agents = {item["id"] for item in value["agents"]}
        skills = {item["id"] for item in value["skills"]}
        for department in departments.values():
            for workflow in department["workflows"]:
                self.assertTrue(set(workflow["agents"]).issubset(agents))
                self.assertTrue(set(workflow["skills"]).issubset(skills))

    def test_lean_layout_has_one_authority_and_no_duplicate_layers(self):
        self.assertTrue((ROOT / ".agents/company/README.md").is_file())
        self.assertTrue((ROOT / ".agents/company/strategy/icp.md").is_file())
        self.assertFalse((ROOT / ".agents/company/engines").exists())
        self.assertFalse((ROOT / ".agents/company/tools").exists())
        self.assertFalse((ROOT / ".agents/Outbound").exists())
        self.assertFalse((ROOT / ".agents/Outreach").exists())
        commands = {path.stem for path in (ROOT / ".opencode/commands").glob("*.md")}
        self.assertEqual({"start", "stop", "status", "approve", "help"}, commands)

    def test_canonical_video_templates_stay_with_design(self):
        root = ROOT / ".agents/company/departments/design/templates/video"
        self.assertTrue((root / "scenario-b.html").is_file())
        self.assertTrue((root / "scenario-c.html").is_file())


class SocialWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.prospect = {
            "lead_id": "lead-1", "name": "Alex Operator", "company": "Example Ops",
            "role": "COO", "channel": "linkedin",
            "profile_url": "https://linkedin.com/in/alex-operator", "icp_score": 88,
            "research_fact": "Expanded the staffing operation into Germany",
            "operational_consequence": "More cross-border candidate handoffs",
            "source_urls": ["https://example.com/news/germany"],
        }

    def test_social_prospect_requires_icp_research_and_sources(self):
        self.assertIsNotNone(social.normalize_prospect(self.prospect))
        self.assertIsNone(social.normalize_prospect({**self.prospect, "source_urls": []}))

    def test_dm_must_link_to_research_and_fit_channel(self):
        prospect = social.normalize_prospect(self.prospect)
        draft = {"lead_id": "lead-1", "channel": "linkedin",
                 "message": "The Germany expansion probably adds candidate handoffs. Is that routing still manual?"}
        self.assertIsNotNone(social.normalize_dm(draft, {"lead-1": prospect}))
        self.assertIsNone(social.normalize_dm({**draft, "message": "Generic AI pitch"}, {"lead-1": prospect}))

    def test_outbound_social_goal_requests_agent_then_evaluates_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(Path(tmp) / "company.sqlite")
            goal = runtime.create_goal(
                name="Research one social prospect", owner_id="outbound",
                metric="qualified_social_leads", operator="ge", target=1,
                deadline=None, config={"workflow": "social-lead-research", "required_count": 1},
                goal_id="goal-social-test", run_type="system_test",
                evidence_validity="technical_only")
            blocked = runtime.once(goal["id"])
            self.assertEqual(blocked["cycle"]["run_status"], "blocked")
            self.assertEqual(blocked["cycle"]["data"]["action_result"]["agent_id"], "social-researcher")
            open_orders = runtime.store.work_orders(status="open", goal_id=goal["id"])
            self.assertEqual(1, len(open_orders))
            self.assertEqual("social-researcher", open_orders[0]["employee_id"])
            self.assertEqual(["social_prospect"], open_orders[0]["accepts_evidence"])
            self.assertEqual(1, open_orders[0]["needed"])
            runtime.add_evidence(goal["id"], kind="social_prospect", source="social-researcher",
                                 payload=self.prospect, validity="technical_only")
            self.assertEqual([], runtime.store.work_orders(status="open", goal_id=goal["id"]))
            done = runtime.store.work_orders(status="done", goal_id=goal["id"])
            self.assertEqual(1, len(done))
            self.assertEqual(1, len(done[0]["result_evidence_ids"]))
            runtime.retry(goal["id"])
            completed = runtime.once(goal["id"])
            self.assertEqual(completed["goal"]["goal_status"], "achieved")
            self.assertEqual(completed["evaluation"]["metrics"]["qualified_social_leads"], 1)


if __name__ == "__main__":
    unittest.main()
