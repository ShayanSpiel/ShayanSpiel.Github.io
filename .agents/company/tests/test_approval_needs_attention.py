"""Fixture-based acceptance tests for change-bd93769493 (approval attention repair).

Reproduces the batch-6 condition: a goal with multiple cycles where
cycle-1 is parked at ``awaiting_approval`` and carries a pending
``approval_required`` notification, while cycle-2 has advanced to a
different state.  The old ``_repair_attention_states`` query only checked
the latest cycle (via ``c.id = n.run_id`` in the first NOT EXISTS
clause), so it would incorrectly close the notification.

Four acceptance criteria from the change task:
  1. surface-needs-attention
  2. pending-until-resolved
  3. no-false-positives
  4. approve-still-releases
"""

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from company.runtime.store import Store, _REPAIR_SCANNED_DBS
from company.runtime.loop import Runtime


class ApprovalNeedsAttentionTests(unittest.TestCase):
    """Fixture: one goal, two cycles.  Cycle-1 is awaiting_approval with a
    pending approval_required notification; cycle-2 is completed."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "company.sqlite"

    def _create_fixture(self):
        """Build the multi-cycle fixture and return (runtime, goal, cycle1_id)."""
        runtime = Runtime(self.db)
        goal = runtime.create_goal(
            name="Multi-cycle approval test",
            owner_id="system-improvement",
            metric="acceptance_tests_passed",
            operator="eq",
            target=True,
            config={
                "owner_id": "system-improvement",
                "from_version": "6.2.5",
                "target_version": "6.2.6",
                "problem": "test fixture",
                "allowed_files": ["x.py"],
                "acceptance_tests": ["echo ok"],
            },
        )
        goal_id = goal["id"]

        # Cycle 1: park at awaiting_approval
        cycle1 = runtime.store.cycle(goal_id)
        runtime.store.update_cycle(
            cycle1["id"], stage="ACT", step="review",
            run_status="awaiting_approval", data={},
        )
        # Create a pending approval_required notification tied to cycle 1
        note = runtime.store.notify(
            goal_id, cycle1["id"], "approval_required",
            {"result": {"message": "action needs approval"}},
        )

        # Cycle 2: advance to completed (simulates a subsequent run)
        cycle2 = runtime.store.new_cycle(goal_id)
        runtime.store.update_cycle(
            cycle2["id"], stage="EVALUATE", step="goal_check",
            run_status="completed", data={},
        )
        return runtime, goal, cycle1["id"], note

    # ── acceptance test 1 ────────────────────────────────────────────
    def test_surface_needs_attention(self):
        """approval_required notification for an awaiting_approval cycle
        must appear under 'Needs attention' (store.attention())."""
        runtime, goal, cycle1_id, note = self._create_fixture()
        attention = runtime.store.attention()
        kinds = [item["kind"] for item in attention]
        goal_ids = [item["goal_id"] for item in attention]
        self.assertIn("approval_required", kinds,
                       "approval_required must surface in attention()")
        self.assertIn(goal["id"], goal_ids,
                       "the goal must be present in attention()")

    # ── acceptance test 2 ────────────────────────────────────────────
    def test_pending_until_resolved(self):
        """The approval_required notification must stay pending until
        the approval is explicitly granted."""
        runtime, goal, cycle1_id, note = self._create_fixture()
        pending = [n for n in runtime.store.notifications("pending")
                   if n["id"] == note["id"]]
        self.assertEqual(1, len(pending),
                         "notification must be pending after fixture creation")

        # Simulate opening a new Store (fresh process) — repair runs
        store_module = __import__("company.runtime.store", fromlist=["store"])
        store_module._REPAIR_SCANNED_DBS.discard(str(self.db.resolve()))
        repaired = Store(self.db)
        still_pending = [n for n in repaired.notifications("pending")
                         if n["id"] == note["id"]]
        self.assertEqual(1, len(still_pending),
                         "repair must NOT close an approval_required notification "
                         "when any cycle of the goal is still awaiting_approval")

    # ── acceptance test 3 ────────────────────────────────────────────
    def test_no_false_positives(self):
        """A blocked+action_required notification on a different cycle
        that no longer matches the run state MUST be closed by repair,
        while the approval_required one stays open."""
        runtime, goal, cycle1_id, note = self._create_fixture()
        cycle2 = runtime.store.cycle(goal["id"])
        # Add a blocked notification on cycle-2 (which is completed, not blocked)
        runtime.store.notify(
            goal["id"], cycle2["id"], "blocked",
            {"result": {"message": "old blocker"}},
        )
        # Reset repair guard so re-open triggers repair
        store_module = __import__("company.runtime.store", fromlist=["store"])
        store_module._REPAIR_SCANNED_DBS.discard(str(self.db.resolve()))
        repaired = Store(self.db)
        kinds = [n["kind"] for n in repaired.attention()
                 if n["goal_id"] == goal["id"]]
        self.assertIn("approval_required", kinds,
                       "approval_required must survive repair")
        self.assertNotIn("blocked", kinds,
                         "stale blocked notification must be closed by repair")

    # ── acceptance test 4 ────────────────────────────────────────────
    def test_approve_still_releases(self):
        """After approval, the pending notification must be resolved
        and the goal must be advanceable."""
        runtime, goal, cycle1_id, note = self._create_fixture()

        # Approve cycle-1
        runtime.store.approve(goal["id"], cycle1_id, "execute", "lgtm")

        # The notification must now be delivered
        all_notes = runtime.store.notifications()
        note_status = next(
            (n["status"] for n in all_notes if n["id"] == note["id"]), None)
        self.assertEqual("delivered", note_status,
                         "notification must be delivered after approval")

        # attention() must no longer include this goal
        attention = runtime.store.attention()
        goal_ids = [item["goal_id"] for item in attention]
        self.assertNotIn(goal["id"], goal_ids,
                         "goal must leave attention after approval")


if __name__ == "__main__":
    unittest.main()
