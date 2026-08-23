"""Acceptance tests: surgical live-push hook (goal-79f1303194).

Proves the transition hook's push sequence:
  1. publishes ONLY the snapshot files (unrelated local commits stay local),
  2. never clobbers a concurrent writer who advanced origin/main,
  3. leaves the shared working tree's index and HEAD untouched.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HOOK = REPO / "scripts" / "spielos-transition-hook.py"

SNAP_A = Path("src/data/live-goals.json")
SNAP_B = Path("public/live-state.json")


def git(cwd: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, check=check)
    return proc.stdout.strip()


def load_hook(sandbox: Path):
    spec = importlib.util.spec_from_file_location("hook_under_test", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.REPO_ROOT = sandbox
    mod.SYNC_OUT = sandbox / SNAP_A
    mod.SYNC_STATE_OUT = sandbox / SNAP_B
    mod.LIVE_PUSH_MARKER = sandbox / ".spielos" / "state" / ".live_push_state.json"
    return mod


class LivePushHookTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.origin = root / "origin.git"
        self.work = root / "work"
        git(root, "init", "--bare", "-q", "-b", "main", str(self.origin))
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.work)],
                       check=True, capture_output=True)
        (self.work / "README.md").write_text("base\n")
        git(self.work, "add", "-A")
        git(self.work, "-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-qm", "base")
        git(self.work, "push", "-q", "origin", "HEAD:main")

    tearDown = lambda self: self._tmp.cleanup()

    def _write_snapshots(self, tag: str):
        for rel in (SNAP_A, SNAP_B):
            path = self.work / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'{{"tag": "{tag}"}}\n')

    def test_pushes_only_snapshots_and_keeps_local_commits_local(self):
        mod = load_hook(self.work)
        # another session's unfinished local commit — must NOT be published
        (self.work / "wip.txt").write_text("half-done work\n")
        git(self.work, "add", "-A")
        git(self.work, "-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-qm", "WIP from another session")
        self._write_snapshots("v1")

        self.assertTrue(mod.git_push_sequence())

        base = git(self.work, "rev-parse", "origin/main^")
        changed = git(self.work, "diff", "--name-only", base, "origin/main")
        self.assertEqual(
            sorted(changed.splitlines()), sorted([str(SNAP_A), str(SNAP_B)]),
            "remote must contain exactly the snapshot files")
        self.assertNotIn("wip.txt",
                         git(self.work, "ls-tree", "-r", "--name-only", "origin/main"),
                         "unrelated local files must never be published")

    def test_never_clobbers_concurrent_writer(self):
        mod = load_hook(self.work)
        third = Path(self._tmp.name) / "third"
        subprocess.run(["git", "clone", "-q", str(self.origin), str(third)],
                       check=True, capture_output=True)

        real_git = mod._git
        raced = {"done": False}

        def racing_git(*args, check=True):
            out = real_git(*args, check=check)
            if args and args[0] == "fetch" and not raced["done"]:
                raced["done"] = True  # concurrent writer lands AFTER our fetch
                (third / "other.txt").write_text("concurrent\n")
                git(third, "add", "-A")
                git(third, "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "concurrent writer")
                git(third, "push", "-q", "origin", "HEAD:main")
            return out

        mod._git = racing_git
        self._write_snapshots("v1")
        self.assertFalse(mod.git_push_sequence(),
                         "lease must reject when origin/main moved")
        tip = git(self.work, "rev-parse", "origin/main")
        self.assertIn("concurrent writer", git(self.work, "log", "-1", "--format=%s", tip),
                      "the concurrent commit must survive untouched")

        # next transition (fresh fetch) lands the snapshots ON TOP of it
        mod._git = real_git
        self.assertTrue(mod.git_push_sequence())
        self.assertIn("concurrent writer",
                      git(self.work, "log", "--format=%s", "-3", "origin/main"))

    def test_shared_working_tree_untouched(self):
        mod = load_hook(self.work)
        (self.work / "tracked.txt").write_text("dirty\n")
        git(self.work, "add", "tracked.txt")  # staged, like a live session
        head_before = git(self.work, "rev-parse", "HEAD")
        status_before = git(self.work, "status", "--porcelain")
        self._write_snapshots("v1")

        self.assertTrue(mod.git_push_sequence())

        self.assertEqual(git(self.work, "rev-parse", "HEAD"), head_before)
        self.assertEqual(git(self.work, "status", "--porcelain"), status_before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
