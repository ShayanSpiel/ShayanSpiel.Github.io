"""Durable pull worker that turns persisted state into an active company loop."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from .runtime import Runtime


class Runner:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    def tick(self, goal_id: str | None = None, max_advances: int = 100) -> dict:
        advanced = []
        for _ in range(max_advances):
            candidates = self._candidates(goal_id)
            if not candidates:
                break
            progress = False
            for candidate in candidates:
                before = self._signature(candidate)
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
            result = self.tick(goal_id)
            pending = tuple(item["id"] for item in result["pending_notifications"])
            if result["advanced"] or pending != previous_pending:
                yield result
            previous_pending = pending
            ticks += 1
            if max_ticks is None or ticks < max_ticks:
                time.sleep(interval_seconds)

    def _candidates(self, goal_id: str | None) -> list[str]:
        rows = self.runtime.list_goals()
        if goal_id:
            descendants = self._descendants(goal_id, rows)
            ancestors = self._ancestors(goal_id, rows)
            allowed = descendants | ancestors | {goal_id}
            rows = [row for row in rows if row["goal"]["id"] in allowed]
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
            return False
        if status == "awaiting_approval":
            return self.runtime.store.approval(
                row["goal"]["id"], cycle["id"], "execute") == "approved"
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
