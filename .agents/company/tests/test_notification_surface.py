"""Acceptance tests for goal-notification-surface-repair-20260815 (change_kind=repair).

Problem statement (the spec): "The runner-persistence change
(goal-runner-persistence-20260815) marks every pending notification delivered on
each watch tick; the OpenCode notifications plugin
(.opencode/plugins/spielos-notifications.ts) surfaces only --status pending
notifications, so the chat confirmation channel is starved (runner log shows
notifications_delivered: 51 draining the backlog; new notes delivered within
seconds of creation). The plugin also runs `company runner tick` every 5s while
the daemon watch loop ticks, causing lease races (already running in another
client). Fix: plugin queries recent reportable notifications across
pending+delivered with the existing 5-minute re-prompt throttle, and skips its
own tick when the runner daemon state is running; add a static-contract
acceptance test for the plugin behavior."

Intended API contract (implementer must make every test pass by editing ONLY
`.opencode/plugins/spielos-notifications.ts` and this module):

1. The plugin check reads BOTH `--status pending` and `--status delivered`
   notifications, merges them by id (pending wins on duplicates), keeps the
   REPORTABLE kind filter, the 300_000 ms (5-minute) per-id re-prompt throttle,
   the approval_required wake-up, and the toast.
2. The plugin skips its own `company runner tick` while the runner daemon is
   running (`runner status --json` reports `running: true`), keeping the
   `enabled === false` guard; the notifications read still happens when the
   daemon is running.
3. The plugin lifecycle (dispose, session.idle event, command.execute.before
   stop/start hooks) is unchanged in intent.

This suite is hermetic and static: it only reads the plugin source file from
the repo and asserts the required behaviors exist in the source. No network, no
subprocesses, no live state is touched.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_RELATIVE = Path(".opencode/plugins/spielos-notifications.ts")


def indent_of(line):
    return len(line) - len(line.lstrip())


class NotificationSurfaceContractTests(unittest.TestCase):
    """Static-contract checks for the OpenCode notifications surfacing plugin."""

    @classmethod
    def setUpClass(cls):
        cls.plugin_path = REPO_ROOT / PLUGIN_RELATIVE
        cls.source = cls.plugin_path.read_text(encoding="utf-8")
        cls.lines = cls.source.splitlines()

    def check_body(self):
        """Lines of the `check` function only (where the queries live)."""
        start = next(
            i for i, line in enumerate(self.lines)
            if line.startswith("  const check = async () => {"))
        end = next(
            i for i, line in enumerate(self.lines)
            if line.startswith("  const timer = setInterval(check"))
        return self.lines[start:end]

    def test_plugin_source_file_exists(self):
        self.assertTrue(
            self.plugin_path.is_file(),
            "plugin source missing: %s" % self.plugin_path)

    def test_check_queries_both_pending_and_delivered(self):
        body = "\n".join(self.check_body())
        self.assertIn("--status pending", body)
        self.assertIn("--status delivered", body)

    def test_pending_and_delivered_merged_by_id_with_pending_winning(self):
        self.assertIn("byID.set(item.id, item)", self.source)
        # The pending spread must come after the delivered spread so a pending
        # entry overwrites a delivered entry with the same id.
        self.assertGreater(
            self.source.index("JSON.parse(pendingRaw)"),
            self.source.index("JSON.parse(deliveredRaw)"),
        )

    def test_reprompt_throttle_constant_present(self):
        self.assertIn("300_000", self.source)
        # The throttle is applied as the existing 5-minute re-prompt window.
        self.assertIn("> 300_000", self.source)

    def test_tick_skipped_when_daemon_state_running(self):
        body = self.check_body()
        tick_index = next(
            i for i, line in enumerate(body) if "company runner tick" in line)
        guard_index = next(
            i for i, line in enumerate(body[:tick_index])
            if "running" in line and line.strip().startswith("if ("))
        guard = body[guard_index]
        self.assertIn("status.running", guard)
        # The tick is nested inside the running-state guard...
        self.assertGreater(
            indent_of(body[tick_index]), indent_of(guard),
            "tick invocation must sit inside the running-state guard")
        # ...and the enabled===false guard is retained.
        self.assertTrue(
            any("status.enabled === false" in line for line in body),
            "enabled === false guard must be retained")

    def test_notifications_read_still_happens_when_daemon_running(self):
        body = self.check_body()
        guard_index = next(
            i for i, line in enumerate(body)
            if "status.running" in line and line.strip().startswith("if ("))
        guard_indent = indent_of(body[guard_index])
        for needle in ("--status pending", "--status delivered"):
            query_index = next(i for i, line in enumerate(body) if needle in line)
            # Queries run after the guard, at the check-body indent level, so
            # they are NOT skipped when the daemon is running.
            self.assertGreater(query_index, guard_index)
            self.assertEqual(indent_of(body[query_index]), guard_indent)

    def test_reportable_kind_set_unchanged(self):
        block = self.source[self.source.index("const REPORTABLE"):]
        block = block[:block.index("])") + 1]
        for kind in ("approval_required", "blocked", "failed",
                     "run_completed", "goal_achieved"):
            self.assertIn('"%s"' % kind, block)
        self.assertIn("REPORTABLE.has(item.kind)", self.source)

    def test_approval_required_wakeup_intact(self):
        self.assertIn('item.kind === "approval_required"', self.source)
        self.assertIn("client.session.promptAsync", self.source)
        self.assertIn('agent: "director"', self.source)
        self.assertIn(
            "Immediately invoke the native question tool", self.source)
        self.assertIn("approval_interaction", self.source)

    def test_toast_and_lifecycle_contract_intact(self):
        self.assertIn("client.tui.showToast", self.source)
        self.assertIn("dispose", self.source)
        self.assertIn("clearInterval(timer)", self.source)
        self.assertIn("session.idle", self.source)
        self.assertIn("command.execute.before", self.source)
        self.assertIn("company runner stop", self.source)
        self.assertIn("company runner enable", self.source)


if __name__ == "__main__":
    unittest.main()
