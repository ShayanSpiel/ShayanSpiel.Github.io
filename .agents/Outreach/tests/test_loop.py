"""Loop tests: the state machine over a FAKE workflow.

The fake workflow is a content-marketing-style stub — it proves the loop is
domain-free: no email vocabulary anywhere in the engine, and a different
bundle drives the identical machine. Tests cover the manual cadence:
  observe → decide → prepare → validate → gate → review (await approval)
  → execute → evaluate (await evidence) → hold (await owner GO) → next cycle
plus gate-blocked, STOP, dry-run, and the goal_met terminal.
"""

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Outreach import workflows  # noqa: E402
from Outreach.engine.artifacts import Artifacts  # noqa: E402
from Outreach.engine.context import Context  # noqa: E402
from Outreach.engine.control import Control  # noqa: E402
from Outreach.engine.loop import Loop  # noqa: E402
from Outreach.engine.policy import Policy  # noqa: E402
from Outreach.store import OutreachStore  # noqa: E402


class FakeWorkflow:
    name = "fake"
    describe = "a content-marketing-style stub for the seam test"

    def observe(self, ctx, quick=False):
        return {
            "at": datetime.now(timezone.utc).isoformat(),
            "totals": {"sent": 10, "reply_rate": 0.1},
            "window_totals": {"sent": 10, "reply_rate": 0.1},
            "gate": {"ok": True, "breaches": [], "problems": []},
            "cap": {"cap": 200, "sent_today": 0, "remaining": 200, "phase": "test"},
            "queue": {"size": 50, "english": 50, "persian": 0},
            "meta": {"goal": {"metric": "reply_rate", "target": 0.3}},
            "goal_status": [], "problems": [], "providers": [],
            "knowledge": {}, "last_batch": None,
        }

    def decide(self, ctx, snapshot):
        return {"action": "prepare_batch", "variable": None,
                "detail": "test intervention", "prediction": "keep going",
                "levers": {}}

    def prepare(self, ctx, intervention):
        return {"id": intervention["batch_id"], "hypothesis": "test",
                "emails": [{"lead_id": "L1", "subject": "S",
                            "body_html": "<p>t</p>", "body_text": "t"}],
                "skipped": []}

    def validate(self, ctx, batch):
        return []

    def execute(self, ctx, batch, dry=False):
        return {"sent": 1, "failed": 0, "deduped": 0, "note": "fake send"}

    def measure(self, ctx, batch):
        return {"metrics": {"sent": 11, "reply_rate": 0.12},
                "verdict": {"verdict": "inconclusive", "reason": "test"}}

    def learn(self, ctx, intervention, verdict):
        ctx.store.record_trial(intervention.get("variable") or "none",
                               {"verdict": verdict.get("verdict")})

    def goal_check(self, ctx, metrics):
        return {"state": "not_yet", "detail": "0.12 vs 0.30 (window)"}

    def policy(self, ctx, snapshot):
        return {"ok": True, "breaches": [], "problems": []}

    def report_lines(self, ctx, batch, outcome):
        return ["- fake metrics line"]


class BlockedPolicy(FakeWorkflow):
    def policy(self, ctx, snapshot):
        return {"ok": False, "breaches": [{"name": "bounce rate", "current": 0.05, "max": 0.02}],
                "problems": []}


class AchievedGoal(FakeWorkflow):
    def goal_check(self, ctx, metrics):
        return {"state": "achieved", "detail": "0.32 >= 0.30 (window)"}


def make_ctx(workflow: FakeWorkflow, stop: bool = False):
    tmp = Path(tempfile.mkdtemp())
    store = OutreachStore(tmp / "engine.sqlite")
    control = Control(tmp / "control.json")
    artifacts = Artifacts(tmp / "data", tmp / "reports", tmp / "logs")
    ctx = Context(store=store, control=control, workflow=workflow,
                  artifacts=artifacts, policy=Policy(workflow),
                  stop_file=tmp / "STOP", data_dir=tmp / "data",
                  reports_dir=tmp / "reports")
    if stop:
        (tmp / "STOP").touch()
    return ctx


class LoopTests(unittest.TestCase):
    def setUp(self):
        workflows.REGISTRY.clear()

    def test_manual_cadence_full_cycle(self):
        ctx = make_ctx(FakeWorkflow())
        loop = Loop(ctx)

        r = loop.advance()
        self.assertEqual(r["phase"], "review")
        self.assertTrue(any("AWAITING APPROVAL" in m for m in r["msgs"]))
        batch_id = ctx.store.current_batch_id()
        self.assertTrue(batch_id.startswith("FAKE-"))

        r = loop.advance()
        self.assertEqual(r["phase"], "review")

        ctx.control.approve_batch(batch_id)
        r = loop.advance()
        self.assertEqual(r["phase"], "evaluate")
        self.assertTrue(any("EXECUTED" in m for m in r["msgs"]))
        self.assertIsNotNone(ctx.store.evidence_due())

        r = loop.advance()
        self.assertEqual(r["phase"], "evaluate")
        self.assertTrue(any("WAITING FOR EVIDENCE" in m for m in r["msgs"]))

        due = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        ctx.store.set_evidence_due(due)
        r = loop.advance()
        self.assertEqual(r["phase"], "hold")
        self.assertTrue(any("HOLD" in m for m in r["msgs"]))
        self.assertIn("owner GO", ctx.store.hold_reason())

        batch = ctx.store.latest_batch()
        self.assertIsNotNone(batch["metrics"])
        self.assertEqual(batch["verdict"]["verdict"], "inconclusive")
        self.assertTrue(batch["report_path"] and Path(batch["report_path"]).exists())
        self.assertTrue(Path(ctx.reports_dir / "REPORT.md").exists())

        ctx.control.approve_next()
        r = loop.advance()
        self.assertEqual(r["phase"], "review")
        self.assertTrue(any("OWNER GO" in m for m in r["msgs"]))

    def test_dry_run_stops_at_review_without_approval(self):
        ctx = make_ctx(FakeWorkflow())
        r = Loop(ctx).advance(dry=True)
        self.assertEqual(r["phase"], "review")
        self.assertTrue(any("DRY RUN" in m for m in r["msgs"]))
        self.assertFalse(ctx.control.is_batch_approved(ctx.store.current_batch_id()))

    def test_gate_blocked_holds(self):
        ctx = make_ctx(BlockedPolicy())
        r = Loop(ctx).advance()
        self.assertEqual(r["phase"], "hold")
        self.assertIn("gate blocked", ctx.store.hold_reason())

    def test_stop_file_stops_the_loop(self):
        ctx = make_ctx(FakeWorkflow(), stop=True)
        r = Loop(ctx).advance()
        self.assertEqual(r["phase"], "stopped")

    def test_goal_met_is_terminal_then_reset(self):
        ctx = make_ctx(AchievedGoal())
        loop = Loop(ctx)
        r = loop.advance()
        self.assertEqual(r["phase"], "review")
        ctx.control.approve_batch(ctx.store.current_batch_id())
        r = loop.advance()
        self.assertEqual(r["phase"], "evaluate")
        ctx.store.set_evidence_due((datetime.now(timezone.utc) - timedelta(hours=1)).isoformat())
        r = loop.advance()
        self.assertEqual(r["phase"], "goal_met")
        self.assertTrue(any("GOAL MET" in m for m in r["msgs"]))

        r = loop.advance()
        self.assertEqual(r["phase"], "goal_met")

    def test_step_artifacts_persisted(self):
        ctx = make_ctx(FakeWorkflow())
        Loop(ctx).advance()
        self.assertIsNotNone(ctx.store.last_snapshot_path())
        self.assertIsNotNone(ctx.store.last_intervention_path())
        self.assertTrue(Path(ctx.store.last_snapshot_path()).exists())
        self.assertTrue(Path(ctx.store.last_intervention_path()).exists())
        batch = ctx.store.get_batch(ctx.store.current_batch_id())
        self.assertTrue(batch["preview_path"] and Path(batch["preview_path"]).exists())
        preview = Path(batch["preview_path"]).read_text()
        self.assertIn("L1", preview)
        self.assertIn("ready for review", preview)

    def test_step_lines_streamed_via_say(self):
        ctx = make_ctx(FakeWorkflow())
        seen = []
        loop = Loop(ctx)
        loop.advance(say=seen.append)
        ctx.control.approve_batch(ctx.store.current_batch_id())
        loop.advance(say=seen.append)
        for fragment in ("observe", "decide", "prepare", "validate", "gate",
                         "review", "execute", "evaluate"):
            self.assertTrue(any(fragment in line for line in seen),
                            f"no step line containing {fragment!r} in {seen}")

    def test_cycle_journal_written_after_execute_and_evaluate(self):
        ctx = make_ctx(FakeWorkflow())
        loop = Loop(ctx)
        loop.advance()
        ctx.control.approve_batch(ctx.store.current_batch_id())
        loop.advance()
        self.assertEqual(loop.phase, "evaluate")
        journal = Path(ctx.reports_dir) / "journal.md"
        self.assertTrue(journal.exists())
        body = journal.read_text()
        self.assertIn("EXECUTE", body)
        self.assertIn("## ", body)
        self.assertIn("### Sends", body)
        self.assertIn("### Hypothesis vs goal", body)
        ctx.store.set_evidence_due((datetime.now(timezone.utc) - timedelta(hours=1)).isoformat())
        loop.advance()
        body = journal.read_text()
        self.assertIn("EVALUATE", body)
        self.assertIn("verdict", body)


if __name__ == "__main__":
    unittest.main()
