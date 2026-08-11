#!/usr/bin/env python3
"""Generate the committed static /live timeline snapshot.

Reads the SpielOS company runtime sqlite database READ-ONLY and writes two
deterministic, idempotent JSON snapshots:

  1. src/data/live-goals.json (imported by the /live page at build time):
       {
         "totals": { goals_total, goals_active, goals_achieved, goals_abandoned,
                     runs, evidence, decisions, approvals, hypotheses,
                     memory_claims },
         "goals":  [ { id, name, owner_id, goal_status, metric, operator,
                       target (decoded), created_at, updated_at,
                       stage (latest cycle stage when present) }, ... ],
         "runtime_state": { state ("running" | "resting"),
                            current_run (most recently updated in-flight
                            cycle: run_id, goal_id, goal_name, owner_id,
                            stage, run_status, created_at, updated_at) or
                            null, heartbeat (the active BUSINESS goal with
                            the most recently updated in-flight cycle:
                            goal_id, goal_name, metric, operator, target,
                            stage, run_status, updated_at) or null,
                            last_activity_at (max updated_at across
                            goals and cycles), last_sync_at (ISO) },
         "heartbeat": same heartbeat object at the snapshot top level }

  2. public/live-state.json (served at /live-state.json, polled by the page):
       { state, current_run, heartbeat, last_activity_at, last_sync_at,
         totals }

  state is "running" when any cycle joined to an active goal has run_status
  in ("idle", "waiting"), otherwise "resting". heartbeat is the active
  business goal (goal_status = "active", owner_id in director/email/outbound)
  whose most recently updated cycle has run_status in ("idle", "waiting"),
  or null when no business goal is in flight.

Deterministic: goals are ordered by (created_at, id); keys are sorted.
Idempotent: when the serialized output equals the current file content the
file is NOT rewritten, so the committed snapshots have no mtime churn.
last_sync_at only advances when the state actually changes — an unchanged
runtime keeps its previous stamp, so re-running the sync produces byte-
identical files.

The function sync_live(db_path, out_path, quiet=False, state_path=None) is
importable — the runtime runner calls it after every goal transition
(goal-15bc547456).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = REPO_ROOT / ".spielos" / "state" / "company.sqlite"
DEFAULT_OUT = REPO_ROOT / "src" / "data" / "live-goals.json"
DEFAULT_STATE = REPO_ROOT / "public" / "live-state.json"

_GOAL_COLUMNS = (
    "id, name, owner_id, goal_status, metric, operator, "
    "target_json, created_at, updated_at"
)


def _connect(db_path: Path) -> sqlite3.Connection:
    """Open the runtime database read-only with a busy timeout."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.row_factory = sqlite3.Row
    return conn


def _decode_target(raw: str) -> Any:
    """Decode target_json (e.g. \"0.3\" -> 0.3, \"true\" -> True)."""
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return raw


def _latest_stages(conn: sqlite3.Connection) -> Dict[str, str]:
    """Map goal_id -> stage of its highest-sequence cycle, when present."""
    latest: Dict[str, str] = {}
    for row in conn.execute(
        "SELECT goal_id, stage FROM cycles ORDER BY goal_id, sequence DESC"
    ):
        if row["goal_id"] not in latest:
            latest[row["goal_id"]] = row["stage"]
    return latest


def _count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def _runtime_state(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Compute the live Running/Resting runtime state.

    state is "running" when any cycle of an active goal has run_status in
    ("idle", "waiting"), otherwise "resting". current_run is the most
    recently updated in-flight (not completed) cycle, or null. heartbeat is
    the active BUSINESS goal with the most recently updated in-flight
    cycle, or null. last_activity is the max updated_at across goals and
    cycles.
    """
    running = conn.execute(
        "SELECT 1 FROM cycles c JOIN goals g ON g.id = c.goal_id "
        "WHERE g.goal_status = 'active' AND c.run_status IN ('idle', 'waiting') "
        "LIMIT 1"
    ).fetchone()
    state = "running" if running else "resting"

    current_run: Optional[Dict[str, Any]] = None
    row = conn.execute(
        "SELECT c.id AS run_id, c.goal_id, g.name AS goal_name, g.owner_id, "
        "c.stage, c.run_status, c.created_at, c.updated_at "
        "FROM cycles c JOIN goals g ON g.id = c.goal_id "
        "WHERE c.run_status != 'completed' "
        "ORDER BY c.updated_at DESC, c.id DESC LIMIT 1"
    ).fetchone()
    if row:
        current_run = {
            "run_id": row["run_id"],
            "goal_id": row["goal_id"],
            "goal_name": row["goal_name"],
            "owner_id": row["owner_id"],
            "stage": row["stage"],
            "run_status": row["run_status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    last_activity = conn.execute(
        "SELECT max(updated_at) AS m FROM ("
        "SELECT updated_at FROM goals UNION ALL SELECT updated_at FROM cycles)"
    ).fetchone()["m"]

    return {
        "state": state,
        "current_run": current_run,
        "heartbeat": _heartbeat(conn),
        "last_activity_at": last_activity,
        "last_sync_at": datetime.now(timezone.utc).isoformat(),
    }


_BUSINESS_OWNERS = ("director", "email", "outbound")


def _heartbeat(conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    """The active BUSINESS goal with the most recently updated in-flight cycle.

    Business goals are owned by director/email/outbound. In-flight means the
    goal's cycle has run_status in ("idle", "waiting"). Returns null when no
    business goal is in flight.
    """
    row = conn.execute(
        "SELECT g.id AS goal_id, g.name AS goal_name, g.metric, g.operator, "
        "g.target_json, c.stage, c.run_status, c.updated_at "
        "FROM cycles c JOIN goals g ON g.id = c.goal_id "
        "WHERE g.goal_status = 'active' AND g.owner_id IN (?, ?, ?) "
        "AND c.run_status IN ('idle', 'waiting') "
        "ORDER BY c.updated_at DESC, c.id DESC LIMIT 1",
        _BUSINESS_OWNERS,
    ).fetchone()
    if row is None:
        return None
    return {
        "goal_id": row["goal_id"],
        "goal_name": row["goal_name"],
        "metric": row["metric"],
        "operator": row["operator"],
        "target": _decode_target(row["target_json"]),
        "stage": row["stage"],
        "run_status": row["run_status"],
        "updated_at": row["updated_at"],
    }


def _strip_last_sync(value: Any) -> Any:
    """Deep-copy value with every last_sync_at key removed."""
    if isinstance(value, dict):
        return {k: _strip_last_sync(v) for k, v in value.items() if k != "last_sync_at"}
    if isinstance(value, list):
        return [_strip_last_sync(v) for v in value]
    return value


def _restore_last_sync(payload: Any, previous: Any) -> None:
    """Copy last_sync_at values from previous into payload (same shape)."""
    if isinstance(payload, dict) and isinstance(previous, dict):
        if "last_sync_at" in payload and isinstance(previous.get("last_sync_at"), str):
            payload["last_sync_at"] = previous["last_sync_at"]
        for key, value in payload.items():
            if key != "last_sync_at" and isinstance(value, (dict, list)):
                _restore_last_sync(value, previous.get(key))
    elif isinstance(payload, list) and isinstance(previous, list):
        for item, prev_item in zip(payload, previous):
            if isinstance(item, (dict, list)):
                _restore_last_sync(item, prev_item)


def _has_stamp(value: Any) -> bool:
    """True when value contains a last_sync_at key at any depth."""
    if isinstance(value, dict):
        if "last_sync_at" in value:
            return True
        return any(_has_stamp(v) for v in value.values())
    if isinstance(value, list):
        return any(_has_stamp(v) for v in value)
    return False


def _write_json(path: Path, payload: Dict[str, Any], quiet: bool, summary: str) -> bool:
    """Deterministically serialize payload to path; skip writes when unchanged.

    last_sync_at is preserved from the previous file (at any nesting level)
    when every other field matches, so an unchanged runtime produces no mtime
    churn. Returns True when the file was actually written.
    """
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing is not None:
        try:
            previous = json.loads(existing)
        except ValueError:
            previous = None
        if isinstance(previous, dict) and _has_stamp(previous):
            if _strip_last_sync(payload) == _strip_last_sync(previous):
                _restore_last_sync(payload, previous)
                serialized = (
                    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
                    + "\n"
                )
    changed = existing != serialized
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")

    if not quiet:
        action = "wrote" if changed else "unchanged (deterministic snapshot, no mtime churn)"
        print(
            f"sync-live-timeline: {action} {path.relative_to(REPO_ROOT)} {summary}"
        )
    return changed


def sync_live(
    db_path: Optional[str] = None,
    out_path: Optional[str] = None,
    quiet: bool = False,
    state_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Read the runtime DB and write the deterministic /live snapshots.

    Writes src/data/live-goals.json (totals + goals + runtime_state) and
    public/live-state.json (runtime state + totals for client polling).
    Files are written only when their content changed (no mtime churn when
    the state is unchanged). Returns the goals snapshot dict.
    """
    db = Path(db_path) if db_path else DEFAULT_DB
    out = Path(out_path) if out_path else DEFAULT_OUT
    state_out = Path(state_path) if state_path else DEFAULT_STATE
    if not db.exists():
        raise FileNotFoundError(f"runtime database not found: {db}")

    conn = _connect(db)
    try:
        goals = conn.execute(
            f"SELECT {_GOAL_COLUMNS} FROM goals ORDER BY created_at, id"
        ).fetchall()
        stages = _latest_stages(conn)

        status_counts: Dict[str, int] = {}
        for row in goals:
            status_counts[row["goal_status"]] = (
                status_counts.get(row["goal_status"], 0) + 1
            )

        totals = {
            "goals_total": len(goals),
            "goals_active": status_counts.get("active", 0),
            "goals_achieved": status_counts.get("achieved", 0),
            "goals_abandoned": status_counts.get("abandoned", 0),
            "runs": _count(conn, "runs"),
            "evidence": _count(conn, "evidence"),
            "decisions": _count(conn, "decisions"),
            "approvals": _count(conn, "approvals"),
            "hypotheses": _count(conn, "hypotheses"),
            "memory_claims": _count(conn, "memory"),
        }

        runtime_state = _runtime_state(conn)

        snapshot = {
            "totals": totals,
            "goals": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "owner_id": row["owner_id"],
                    "goal_status": row["goal_status"],
                    "metric": row["metric"],
                    "operator": row["operator"],
                    "target": _decode_target(row["target_json"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "stage": stages.get(row["id"]),
                }
                for row in goals
            ],
            "runtime_state": runtime_state,
            "heartbeat": runtime_state["heartbeat"],
        }
    finally:
        conn.close()

    live_state = {
        "state": runtime_state["state"],
        "current_run": runtime_state["current_run"],
        "heartbeat": runtime_state["heartbeat"],
        "last_activity_at": runtime_state["last_activity_at"],
        "last_sync_at": runtime_state["last_sync_at"],
        "totals": totals,
    }

    current_run_label = (
        runtime_state["current_run"]["run_id"]
        if runtime_state["current_run"]
        else "none"
    )
    _write_json(
        out,
        snapshot,
        quiet,
        f"({totals['goals_total']} goals, {totals['runs']} runs, "
        f"{totals['evidence']} evidence)",
    )
    _write_json(
        state_out,
        live_state,
        quiet,
        f"(state={runtime_state['state']}, current_run={current_run_label}, "
        f"last_activity_at={runtime_state['last_activity_at']})",
    )
    return snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate the deterministic /live timeline snapshots."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), help="path to company.sqlite")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="output JSON path")
    parser.add_argument(
        "--state", default=str(DEFAULT_STATE), help="live-state JSON output path"
    )
    parser.add_argument("--quiet", action="store_true", help="suppress summary output")
    args = parser.parse_args()
    try:
        sync_live(args.db, args.out, args.quiet, args.state)
    except Exception as exc:  # pragma: no cover - CLI error surface
        print(f"sync-live-timeline: ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
