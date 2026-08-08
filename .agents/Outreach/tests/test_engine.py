import tempfile
import unittest
from pathlib import Path

from Outreach.models import Action, Lead, LeadState, WorkflowGoal
from Outreach.store import OutreachStore
from Outreach.workflow import OutreachLoop


class OutreachEngineTests(unittest.TestCase):
    def make_store(self):
        self.tmp = tempfile.TemporaryDirectory()
        return OutreachStore(Path(self.tmp.name) / "outreach.sqlite")

    def test_discovery_and_ready_queue_are_separate_from_actions(self):
        store = self.make_store()
        store.upsert_leads([Lead(
            lead_id="lead-1", name="A", company="Company", role="COO",
            channels=["linkedin"], state=LeadState.READY, icp_score=90,
            research_fact="The company added a new delivery line.",
            operational_consequence="The added handoffs create repeated coordination work.",
        )])
        loop = OutreachLoop(store, WorkflowGoal("linkedin-dm", "linkedin", "send_dm", 30))
        self.assertEqual(loop.status()["ready_queue"], 1)
        self.assertEqual(store.action_count("linkedin", "send_dm"), 0)

    def test_x_unsolicited_dm_is_blocked(self):
        store = self.make_store()
        store.upsert_leads([Lead(
            lead_id="lead-2", name="B", company="Company", role="CEO",
            channels=["x"], state=LeadState.READY, icp_score=90,
            research_fact="The company launched a new service.",
            operational_consequence="The launch increases repeated customer questions.",
        )])
        loop = OutreachLoop(store, WorkflowGoal("x-dm", "x", "send_dm", 30))
        work = loop.next_work()
        self.assertEqual(work.action, Action.SEND_DM)
        self.assertIn("unsolicited", work.reason)


if __name__ == "__main__":
    unittest.main()
