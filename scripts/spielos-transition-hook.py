#!/usr/bin/env python3
"""SpielOS website transition hook (repo-local user layer).

This script restores, OUTSIDE the runtime, the exact post-transition behavior
that used to be compiled into ``company.runtime.loop`` before the website was
decoupled from the harness (audit 2026-08-23 §2a / task 17):

1. Regenerate the committed /live snapshots by running
   ``scripts/sync-live-timeline.py`` (hard-bounded at SYNC_TIMEOUT_S seconds).
2. When SPIELOS_LIVE_PUSH is enabled (env var first, then .spielos/.env),
   the fingerprint (runtime state + terminal goals + completed/failed runs)
   changed since the marker, and at least LIVE_PUSH_DEBOUNCE_S seconds passed,
   commit and push the snapshot files: git add -> commit -> push origin HEAD,
   then a best-effort fast-forward push of HEAD to origin main so GitHub
   Pages deploys. The marker (.spielos/state/.live_push_state.json) is
   written only after a successful push.

Debounce/fingerprint/marker semantics live HERE, never in the runtime. The
runtime only invokes this script via SPIELOS_TRANSITION_HOOK:

  SPIELOS_TRANSITION_HOOK=python3 <repo>/scripts/spielos-transition-hook.py {event} {payload_json}

Usage: spielos-transition-hook.py EVENT PAYLOAD_JSON
Every failure is non-fatal: exit code 0 unless the sync itself fails badly;
the goal transition that triggered us must never break.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync-live-timeline.py"
SYNC_DB = REPO_ROOT / ".spielos" / "state" / "company.sqlite"
SYNC_OUT = REPO_ROOT / "src" / "data" / "live-goals.json"
SYNC_STATE_OUT = REPO_ROOT / "public" / "live-state.json"
SYNC_TIMEOUT_S = 15

LIVE_PUSH_ENV = "SPIELOS_LIVE_PUSH"
LIVE_PUSH_ENV_FILE = REPO_ROOT / ".spielos" / ".env"
LIVE_PUSH_MARKER = REPO_ROOT / ".spielos" / "state" / ".live_push_state.json"
LIVE_PUSH_DEBOUNCE_S = 120
GIT_TIMEOUT_S = 20


def log(message: str) -> None:
    print(f"transition-hook: {message}", file=sys.stderr)


def env_file_value(path: Path, key: str) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, _, value = stripped.partition("=")
        if name.strip() == key:
            return value.strip()
    return None


def live_push_gate() -> bool:
    raw = __import__("os").environ.get(LIVE_PUSH_ENV)
    if raw is None:
        raw = env_file_value(LIVE_PUSH_ENV_FILE, LIVE_PUSH_ENV)
    return raw is not None and raw.strip().lower() in {"1", "true", "yes", "on"}


def completed_failed_runs(db_path: Path) -> int:
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
        try:
            row = conn.execute(
                "SELECT count(*) FROM runs WHERE status IN ('completed', 'failed')"
            ).fetchone()
            return int(row[0]) if row else 0
        finally:
            conn.close()
    except Exception as exc:
        log(f"fingerprint run-count read skipped (non-fatal): {exc}")
        return 0


def live_fingerprint(snapshot: dict) -> str | None:
    runtime_state = snapshot.get("runtime_state") or {}
    totals = snapshot.get("totals") or {}
    state = runtime_state.get("state")
    if not state:
        return None
    terminal_goals = int(totals.get("goals_achieved", 0) or 0) + int(
        totals.get("goals_abandoned", 0) or 0)
    return f"{state}|{terminal_goals}|{completed_failed_runs(SYNC_DB)}"


def read_marker() -> dict:
    try:
        data = json.loads(MARKER_PLACEHOLDER.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def push_allowed(marker: dict) -> bool:
    pushed_at = marker.get("pushed_at")
    if not pushed_at:
        return True
    try:
        parsed = datetime.fromisoformat(str(pushed_at).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return time.time() - parsed.timestamp() >= LIVE_PUSH_DEBOUNCE_S
    except ValueError:
        return True


def run_git(args: list[str], check: bool = True):
    return subprocess.run(args, capture_output=True, text=True, check=check,
                          timeout=GIT_TIMEOUT_S)


def git_push_sequence() -> bool:
    candidates = [str(path) for path in (SYNC_OUT, SYNC_STATE_OUT) if path.is_file()]
    if not candidates:
        log("live push skipped: no snapshot files to stage")
        return False
    run_git(["git", "-C", str(REPO_ROOT), "add", *candidates])
    staged = run_git(["git", "-C", str(REPO_ROOT), "diff", "--cached", "--quiet"],
                     check=False)
    if staged.returncode == 0:
        log("live push skipped: nothing to commit")
        return False
    if staged.returncode != 1:
        raise RuntimeError(f"git diff --cached --quiet exited {staged.returncode}")
    run_git(["git", "-C", str(REPO_ROOT), "commit", "-m", "live: sync runtime state"])
    run_git(["git", "-C", str(REPO_ROOT), "push", "origin", "HEAD"])
    # Best-effort GitHub Pages trigger: a rejected/hung HEAD:main push must
    # never fail the hook — the snapshot is already committed and pushed.
    try:
        run_git(["git", "-C", str(REPO_ROOT), "push", "origin", "HEAD:main"])
    except Exception as exc:
        log(f"live push to origin main skipped (non-fatal): {exc}")
    return True


def write_marker(fingerprint: str) -> None:
    MARKER_PLACEHOLDER.parent.mkdir(parents=True, exist_ok=True)
    MARKER_PLACEHOLDER.write_text(json.dumps(
        {"fingerprint": fingerprint,
         "pushed_at": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n",
        encoding="utf-8")


def main(argv: list[str]) -> int:
    event = argv[1] if len(argv) > 1 else "goal_transition"
    try:
        payload = json.loads(argv[2]) if len(argv) > 2 else {}
    except ValueError:
        payload = {}

    # 1. Snapshot sync (bounded).
    try:
        completed = subprocess.run(
            [sys.executable, "-B", str(SYNC_SCRIPT), "--quiet"], cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=SYNC_TIMEOUT_S)
        if completed.returncode != 0:
            log(f"sync exited {completed.returncode} (non-fatal)")
            return 0
    except subprocess.TimeoutExpired:
        log(f"sync timed out after {SYNC_TIMEOUT_S}s (non-fatal)")
        return 0
    except Exception as exc:
        log(f"sync failed (non-fatal): {exc}")
        return 0

    # 2. Debounced push when enabled.
    if not live_push_gate():
        return 0
    try:
        snapshot = json.loads(SYNC_OUT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    fingerprint = live_fingerprint(snapshot if isinstance(snapshot, dict) else {})
    if fingerprint is None:
        return 0
    marker = read_marker()
    if marker.get("fingerprint") == fingerprint:
        return 0
    if not push_allowed(marker):
        log(f"live push skipped: debounce window ({LIVE_PUSH_DEBOUNCE_S}s) not elapsed")
        return 0
    try:
        if not git_push_sequence():
            return 0
        write_marker(fingerprint)
    except Exception as exc:
        log(f"live push skipped (non-fatal): {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
