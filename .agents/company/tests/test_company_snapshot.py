import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from company.__main__ import main
from company.runtime.loop import Runtime
from company.runtime.models import GoalStatus
from company.runtime.store import Store


class CompanySnapshotTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.db = Path(self.directory.name) / "company.sqlite"
        self.runtime = Runtime(self.db)

    def tearDown(self):
        self.directory.cleanup()

    def goal(self, goal_id, name="Snapshot goal"):
        return self.runtime.create_goal(
            goal_id=goal_id, name=name, owner_id="content",
            metric="content_packages", operator="ge", target=1,
            config={"workflow": "content-package", "allowed_files": ["x" * 10_000]},
        )

    def capture(self, *arguments):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["--db", str(self.db), *arguments])
        self.assertEqual(0, code)
        return output.getvalue()

    def test_default_status_is_bounded_and_human_readable(self):
        self.goal("goal-active")
        output = self.capture("status")
        self.assertIn("# SpielOS company", output)
        self.assertIn("Snapshot goal", output)
        self.assertIn("Open work orders", output)
        self.assertNotIn("allowed_files", output)
        self.assertNotIn("x" * 100, output)
        self.assertLess(len(output), 5_000)

    def test_status_and_tasks_surface_open_work_orders(self):
        goal = self.goal("goal-work-order")
        blocked = self.runtime.once(goal["id"])
        self.assertEqual("blocked", blocked["cycle"]["run_status"])
        orders = self.runtime.store.work_orders(status="open", goal_id=goal["id"])
        self.assertEqual(1, len(orders))
        self.assertEqual("content-strategist", orders[0]["employee_id"])
        output = self.capture("status")
        self.assertIn(orders[0]["id"], output)
        self.assertIn("content-strategist", output)
        tasks = self.capture("tasks")
        self.assertIn(orders[0]["id"], tasks)
        self.assertIn("content-strategist", tasks)

    def test_raw_status_remains_an_explicit_full_audit_escape_hatch(self):
        self.goal("goal-raw")
        output = self.capture("status", "--raw")
        self.assertIn('"allowed_files"', output)
        self.assertIn("x" * 100, output)

    def test_single_goal_status_is_compact_and_actionable(self):
        goal = self.goal("goal-one")
        cycle = self.runtime.store.cycle(goal["id"])
        self.runtime.store.update_cycle(
            cycle["id"], stage="ACT", step="review",
            run_status="awaiting_approval", data={"large": "x" * 10_000})
        self.runtime.store.notify(goal["id"], cycle["id"], "approval_required", {
            "result": {"message": "Review the package"},
            "required_user_action": "Approve the exact package",
            "approval_interaction": {
                "question": "Approve this package?", "action": "Publish package",
                "artifact": "batch-1", "destination": "Threads", "scope": "one batch",
                "risk": "Public post", "consequence": "Nothing publishes",
                "fallback_command": "company approve goal-one",
            },
            "large": "x" * 10_000,
        })
        output = self.capture("status", goal["id"])
        self.assertIn("Approve the exact package", output)
        self.assertIn("awaiting_approval", output)
        self.assertIn("Approve this package?", output)
        self.assertIn("company approve goal-one", output)
        self.assertNotIn("x" * 100, output)
        self.assertLess(len(output), 5_000)

    def test_history_is_bounded_by_limit(self):
        for index in range(3):
            goal = self.goal(f"goal-history-{index}", f"History {index}")
            self.runtime.set_goal_status(goal["id"], GoalStatus.ABANDONED)
        output = self.capture("status", "--history", "--limit", "2")
        self.assertEqual(2, output.count("(`goal-history-"))


class TerminalStateTests(unittest.TestCase):
    def test_store_initialization_removes_attention_from_previous_run_state(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "company.sqlite"
            runtime = Runtime(db)
            goal = runtime.create_goal(
                goal_id="goal-current-attention", name="Attention", owner_id="content",
                metric="content_packages", operator="ge", target=1,
                config={"workflow": "content-package"})
            cycle = runtime.store.cycle(goal["id"])
            runtime.store.update_cycle(cycle["id"], stage="ACT", step="work",
                                       run_status="blocked", data={})
            runtime.store.notify(goal["id"], cycle["id"], "approval_required", {})
            runtime.store.notify(goal["id"], cycle["id"], "blocked", {})
            repaired = Store(db)
            self.assertEqual(["blocked"], [item["kind"] for item in repaired.attention()])

    def test_terminal_transition_closes_run_and_actionable_notifications(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory) / "company.sqlite")
            goal = runtime.create_goal(
                goal_id="goal-terminal", name="Terminal", owner_id="content",
                metric="content_packages", operator="ge", target=1,
                config={"workflow": "content-package"})
            cycle = runtime.store.cycle(goal["id"])
            runtime.store.update_cycle(cycle["id"], stage="ACT", step="review",
                                       run_status="awaiting_approval", data={})
            note = runtime.store.notify(goal["id"], cycle["id"], "approval_required", {})
            runtime.set_goal_status(goal["id"], GoalStatus.ABANDONED)
            self.assertEqual("completed", runtime.store.cycle(goal["id"])["run_status"])
            self.assertEqual("completed", runtime.store.run(cycle["id"])["status"])
            delivered = {item["id"]: item for item in runtime.store.notifications("delivered")}
            self.assertIn(note["id"], delivered)
            self.assertEqual([], runtime.store.attention())

    def test_store_initialization_repairs_legacy_terminal_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "company.sqlite"
            runtime = Runtime(db)
            goal = runtime.create_goal(
                goal_id="goal-drift", name="Drift", owner_id="content",
                metric="content_packages", operator="ge", target=1,
                config={"workflow": "content-package"})
            cycle = runtime.store.cycle(goal["id"])
            runtime.store.notify(goal["id"], cycle["id"], "blocked", {})
            with sqlite3.connect(db) as con:
                con.execute("UPDATE goals SET goal_status='abandoned' WHERE id=?", (goal["id"],))
                con.execute("UPDATE cycles SET run_status='blocked' WHERE id=?", (cycle["id"],))
                con.execute("UPDATE runs SET status='blocked' WHERE id=?", (cycle["id"],))
            repaired = Store(db)
            self.assertEqual("completed", repaired.cycle(goal["id"])["run_status"])
            self.assertEqual("completed", repaired.run(cycle["id"])["status"])
            self.assertEqual([], repaired.attention())


class DirectorRetrievalContractTests(unittest.TestCase):
    def test_director_keeps_autonomy_but_avoids_routine_history_scans(self):
        root = Path(__file__).resolve().parents[3]
        director = (root / ".opencode/agents/director.md").read_text()
        command = (root / ".opencode/commands/status.md").read_text()
        self.assertIn("This is retrieval discipline, not a loss of autonomy", director)
        self.assertIn("compact projection as authoritative", command)
        self.assertIn("retain full autonomy to drill down", command)
        self.assertIn("--raw", command)


if __name__ == "__main__":
    unittest.main()
