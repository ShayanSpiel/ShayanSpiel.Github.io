"""Durable pull worker that turns persisted state into an active company loop."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from .alignment import approval_key
from .loop import Runtime
from .service import automation_enabled

# Watchdog constants. The runner is its own watchdog: the watch loop stamps a
# heartbeat file every cycle so external readers (the OpenCode notifications
# plugin) can distinguish a dead daemon from an idle one, and a rate-limited
# stall scan emits actionable stuck_goal notifications instead of parking
# silently (2026-08-15 incident: daemon crash went unnoticed for ~34 minutes).
HEARTBEAT_FILENAME = "runner.heartbeat"
STALL_CHECK_INTERVAL_SECONDS = 60   # how often the watchdog scan runs
STALL_GRACE_SECONDS = 90            # resume_at may be this late before alerting
DISPATCH_STALE_SECONDS = 3600       # mirrors runtime.async_dispatch threshold


def heartbeat_age(heartbeat_path, now=None) -> float | None:
    """Seconds since the last watch tick; None when missing or unparsable."""
    try:
        data = json.loads(Path(heartbeat_path).read_text(encoding="utf-8"))
        last_tick = data.get("last_tick")
        if not last_tick:
            return None
        parsed = datetime.fromisoformat(str(last_tick).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return max(0.0, (now - parsed).total_seconds())
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def runner_down_signal(heartbeat_path, max_age_seconds: float, now=None) -> dict | None:
    """The runner_down watchdog payload when the heartbeat is stale, else None.

    A missing or unparsable heartbeat yields None: a freshly installed runner
    (or one that predates the heartbeat) must not false-positive. This is the
    primary dead-daemon detector; the watch loop's own death notification is
    only a best-effort secondary signal.
    """
    age = heartbeat_age(heartbeat_path, now=now)
    if age is None or age <= max_age_seconds:
        return None
    return {
        "signal": "runner_down",
        "heartbeat_age_seconds": age,
        "max_age_seconds": max_age_seconds,
    }


class Runner:
    def __init__(self, runtime: Runtime, *,
                 stall_check_interval_seconds: float = STALL_CHECK_INTERVAL_SECONDS,
                 stall_grace_seconds: float = STALL_GRACE_SECONDS,
                 dispatch_stale_seconds: float = DISPATCH_STALE_SECONDS):
        self.runtime = runtime
        self._stall_check_interval_seconds = stall_check_interval_seconds
        self._stall_grace_seconds = stall_grace_seconds
        self._dispatch_stale_seconds = dispatch_stale_seconds
        self._last_stall_check = 0.0
        self._active_goal_id = None
        self._cycle = 0

    def heartbeat_path(self) -> Path:
        """The heartbeat file lives beside the runtime database (.spielos/state)."""
        return self.runtime.store.path.parent / HEARTBEAT_FILENAME

    def write_heartbeat(self) -> None:
        """Stamp the watch cycle so external readers detect a dead daemon.

        Only the daemon watch loop calls this; standalone `tick()` calls (the
        plugin's fallback tick, manual CLI ticks) must NOT refresh the file or
        they would mask a dead daemon. Best-effort: a failed write is the
        signal.
        """
        self._cycle += 1
        payload = {
            "pid": os.getpid(),
            "last_tick": datetime.now(timezone.utc).isoformat(),
            "cycle": self._cycle,
        }
        try:
            path = self.heartbeat_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        except OSError:  # pragma: no cover - defensive; stale heartbeat is the signal
            pass

    def heartbeat_age(self, now=None) -> float | None:
        return heartbeat_age(self.heartbeat_path(), now=now)

    def runner_down(self, max_age_seconds: float = STALL_GRACE_SECONDS,
                    now=None) -> dict | None:
        return runner_down_signal(self.heartbeat_path(), max_age_seconds, now=now)

    def tick(self, goal_id: str | None = None, max_advances: int = 100) -> dict:
        if not automation_enabled(self.runtime.store.path.parent):
            return {"advanced": [], "pending_notifications": [],
                    "quiescent": True, "stopped": True}
        advanced = []
        self._active_goal_id = None
        for _ in range(max_advances):
            candidates = self._candidates(goal_id)
            if not candidates:
                break
            progress = False
            for candidate in candidates:
                before = self._signature(candidate)
                self._active_goal_id = candidate
                state = self.runtime.once(candidate, holder="company-runner")
                after = self._signature(candidate)
                if after != before:
                    progress = True
                    advanced.append({"goal_id": candidate, "state": after})
            if not progress:
                break
        return {
            "advanced": advanced,
            "pending_notifications": self.runtime.store.notifications("pending"),
            "quiescent": not self._candidates(goal_id),
        }

    def watch(self, interval_seconds: float = 2.0, goal_id: str | None = None,
              max_ticks: int | None = None):
        ticks, previous_pending = 0, None
        while max_ticks is None or ticks < max_ticks:
            self.write_heartbeat()
            try:
                result = self.tick(goal_id)
                pending = tuple(item["id"] for item in result["pending_notifications"])
                if result["advanced"] or pending != previous_pending:
                    yield result
                previous_pending = pending
                ticks += 1
                self._check_stalled(goal_id)
            except Exception as exc:
                # Best-effort: tell the world the watch loop is dying before
                # the daemon exits. The heartbeat reader remains the primary
                # dead-daemon detector.
                self._emit_runner_down(exc)
                raise
            if max_ticks is None or ticks < max_ticks:
                time.sleep(interval_seconds)

    def _candidates(self, goal_id: str | None) -> list[str]:
        rows = self.runtime.list_goals()
        rows = self._scope_rows(goal_id, rows)
        runnable = [row for row in rows if self._runnable(row)]
        runnable.sort(key=lambda row: (-self._depth(row["goal"], rows), row["goal"]["created_at"]))
        return [row["goal"]["id"] for row in runnable]

    def _runnable(self, row: dict) -> bool:
        if row["goal"]["goal_status"] != "active":
            return False
        cycle = row["cycle"]
        status = cycle["run_status"]
        if status == "idle":
            return True
        if status == "completed":
            return self.runtime.continuation_decision(row["goal"]["id"])["eligible"]
        if status in {"blocked", "failed"}:
            return self.runtime.repair_iteration_decision(row["goal"]["id"])["eligible"]
        if status == "awaiting_approval":
            return self.runtime.store.approval(
                row["goal"]["id"], cycle["id"], approval_key(cycle)) == "approved"
        if status == "running":
            # Mid-flight cycle whose client died (no live lease) must stay
            # resumable, or the goal parks invisibly until a manual `once`.
            return self.runtime.store.live_lease(row["goal"]["id"]) is None
        if status != "waiting" or not cycle.get("resume_at"):
            return False
        return datetime.fromisoformat(cycle["resume_at"]) <= datetime.now(timezone.utc)

    def _signature(self, goal_id: str):
        state = self.runtime.status(goal_id)
        return (state["goal"]["goal_status"], state["cycle"]["id"],
                state["cycle"]["stage"], state["cycle"]["step"],
                state["cycle"]["run_status"], state["cycle"].get("resume_at"),
                len(state["evidence"]), bool(state["evaluation"]))

    @staticmethod
    def _descendants(goal_id: str, rows: list[dict]) -> set[str]:
        found, frontier = set(), {goal_id}
        while frontier:
            children = {row["goal"]["id"] for row in rows
                        if row["goal"].get("parent_id") in frontier}
            children -= found
            found |= children
            frontier = children
        return found

    @staticmethod
    def _ancestors(goal_id: str, rows: list[dict]) -> set[str]:
        parents = {row["goal"]["id"]: row["goal"].get("parent_id") for row in rows}
        found, parent = set(), parents.get(goal_id)
        while parent:
            found.add(parent)
            parent = parents.get(parent)
        return found

    @staticmethod
    def _depth(goal: dict, rows: list[dict]) -> int:
        parents = {row["goal"]["id"]: row["goal"].get("parent_id") for row in rows}
        depth, parent = 0, goal.get("parent_id")
        while parent:
            depth += 1
            parent = parents.get(parent)
        return depth

    def _scope_rows(self, goal_id: str | None, rows: list[dict]) -> list[dict]:
        """Rows restricted to a goal plus its descendants/ancestors (None = all)."""
        if not goal_id:
            return rows
        descendants = self._descendants(goal_id, rows)
        ancestors = self._ancestors(goal_id, rows)
        allowed = descendants | ancestors | {goal_id}
        return [row for row in rows if row["goal"]["id"] in allowed]

    def _check_stalled(self, goal_id: str | None = None) -> list[str]:
        """Watchdog scan: stalled waiting goals and stale async dispatches.

        Emits ``action_required`` notifications whose payload carries
        ``watchdog.signal == "stuck_goal"`` plus the goal id, run id, why, and
        what to do. Rate-limited so a healthy daemon does not hammer the store
        on every tick; the store's (goal_id, run_id, kind) upsert keeps one
        row per stuck goal and the plugin's re-prompt throttle bounds chat
        spam.
        """
        if time.monotonic() - self._last_stall_check < self._stall_check_interval_seconds:
            return []
        self._last_stall_check = time.monotonic()
        emitted: list[str] = []
        rows = self._scope_rows(goal_id, self.runtime.list_goals())
        for row in rows:
            goal = row["goal"]
            if goal["goal_status"] != "active":
                continue
            cycle = row["cycle"]
            if cycle["run_status"] != "waiting" or not cycle.get("resume_at"):
                continue
            resume_at = self._parse_dt(cycle.get("resume_at"))
            if resume_at is None:
                continue
            due_since = (datetime.now(timezone.utc) - resume_at).total_seconds()
            if due_since < self._stall_grace_seconds:
                continue
            updated_at = self._parse_dt(cycle.get("updated_at"))
            if updated_at is not None and updated_at > resume_at:
                # The cycle advanced after resume_at passed; not stalled.
                continue
            self._emit_stuck_goal(goal, cycle, reason="resume_at passed without advancement",
                                  detail={"resume_at": cycle.get("resume_at"),
                                          "cycle_updated_at": cycle.get("updated_at"),
                                          "due_seconds_ago": due_since})
            emitted.append(goal["id"])
        for dispatch_goal_id, batch_id, started_at in self._stale_dispatch_files():
            try:
                goal = self.runtime.store.goal(dispatch_goal_id)
                cycle = self.runtime.store.cycle(dispatch_goal_id)
            except KeyError:
                continue  # dispatch file for a goal that no longer exists
            if goal["goal_status"] != "active":
                continue
            self._emit_stuck_goal(goal, cycle, reason="async dispatch pending beyond stale threshold",
                                  detail={"batch_id": batch_id, "started_at": started_at,
                                          "stale_threshold_seconds": self._dispatch_stale_seconds})
            emitted.append(dispatch_goal_id)
        return emitted

    def _stale_dispatch_files(self) -> list[tuple[str, str, str]]:
        """(goal_id, batch_id, started_at) for pending async dispatch files
        older than the stale threshold. Missing directory -> no dispatches."""
        dispatch_dir = self.runtime.store.path.parent / "outbound" / "async"
        if not dispatch_dir.is_dir():
            return []
        stale = []
        now = datetime.now(timezone.utc)
        for path in dispatch_dir.glob("*/*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("status") != "pending":
                continue
            started_at = data.get("started_at")
            started = self._parse_dt(started_at)
            if started is None:
                # Parity with async_dispatch._is_stale: no usable started_at
                # is treated as stale so the workflow can recover.
                stale.append((path.parent.name, path.stem, started_at))
                continue
            if (now - started).total_seconds() > self._dispatch_stale_seconds:
                stale.append((path.parent.name, path.stem, started_at))
        return stale

    @staticmethod
    def _parse_dt(value):
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _emit_stuck_goal(self, goal: dict, cycle: dict, *, reason: str,
                         detail: dict) -> dict:
        message = (f"goal {goal['id']} ({goal['name']}) is stuck: {reason} "
                   f"(run {cycle['id']})")
        return self.runtime.store.notify(goal["id"], cycle["id"], "action_required", {
            "watchdog": {
                "signal": "stuck_goal",
                "reason": reason,
                "detected_at": datetime.now(timezone.utc).isoformat(),
                **detail,
            },
            "goal": {"id": goal["id"], "name": goal["name"]},
            "run": {"id": cycle["id"]},
            "result": {"message": message},
            "required_user_action": (
                f"Inspect and resume goal {goal['id']}: `company status {goal['id']}` "
                f"then `company once {goal['id']}`"),
            "next_trigger": f"company once {goal['id']}",
        })

    def _emit_runner_down(self, exc: Exception) -> None:
        """Best-effort action_required notification when the watch loop dies.

        Attached to the goal being processed (or the first active goal) only
        because notifications are foreign-keyed to a goal/run; the payload is
        about the runner, not the goal. Never raises.
        """
        goal_id = self._active_goal_id
        if goal_id is None:
            for row in self.runtime.list_goals():
                if row["goal"]["goal_status"] == "active":
                    goal_id = row["goal"]["id"]
                    break
        if goal_id is None:
            return
        try:
            cycle = self.runtime.store.cycle(goal_id)
            goal = self.runtime.store.goal(goal_id)
        except KeyError:
            return
        try:
            self.runtime.store.notify(goal_id, cycle["id"], "action_required", {
                "watchdog": {
                    "signal": "runner_down",
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                },
                "goal": {"id": goal_id, "name": goal["name"]},
                "run": {"id": cycle["id"]},
                "result": {"message": f"runner watch loop died: {type(exc).__name__}: {exc}"},
                "required_user_action": "Restart the runner daemon: `company runner start`",
                "next_trigger": "company runner start",
            })
        except Exception:  # pragma: no cover - best-effort; never mask the death
            pass
