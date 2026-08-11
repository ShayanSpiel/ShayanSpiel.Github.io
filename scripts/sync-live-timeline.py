#!/usr/bin/env python3
"""Generate the committed static /live timeline snapshot.

Reads the SpielOS company runtime sqlite database READ-ONLY and writes a
deterministic, idempotent JSON snapshot to src/data/live-goals.json:

  {
    "totals": { goals_total, goals_active, goals_achieved, goals_abandoned,
                runs, evidence, decisions, approvals, hypotheses,
                memory_claims },
    "goals":  [ { id, name, owner_id, goal_status, metric, operator,
                  target (decoded), created_at, updated_at,
                  stage (latest cycle stage when present) }, ... ]
  }

Deterministic: goals are ordered by (created_at, id); keys are sorted.
Idempotent: when the serialized output equals the current file content the
file is NOT rewritten, so the committed snapshot has no mtime churn.

The function sync_live(db_path, out_path, quiet=False) is importable — the
runtime runner calls it after every goal transition (goal-15bc547456).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = REPO_ROOT / ".spielos" / "state" / "company.sqlite"
DEFAULT_OUT = REPO_ROOT / "src" / "data" / "live-goals.json"

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


def sync_live(
    db_path: Optional[str] = None,
    out_path: Optional[str] = None,
    quiet: bool = False,
) -> Dict[str, Any]:
    """Read the runtime DB and write the deterministic /live snapshot.

    Returns the snapshot dict. Writes the output file only when its
    content changed (no mtime churn when the state is unchanged).
    """
    db = Path(db_path) if db_path else DEFAULT_DB
    out = Path(out_path) if out_path else DEFAULT_OUT
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
        }
    finally:
        conn.close()

    serialized = json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    changed = True
    if out.exists() and out.read_text(encoding="utf-8") == serialized:
        changed = False
    if changed:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(serialized, encoding="utf-8")

    if not quiet:
        action = "wrote" if changed else "unchanged (deterministic snapshot, no mtime churn)"
        print(
            f"sync-live-timeline: {action} {out.relative_to(REPO_ROOT)} "
            f"({totals['goals_total']} goals, {totals['runs']} runs, "
            f"{totals['evidence']} evidence)"
        )
    return snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate the deterministic /live timeline snapshot."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), help="path to company.sqlite")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="output JSON path")
    parser.add_argument("--quiet", action="store_true", help="suppress summary output")
    args = parser.parse_args()
    try:
        sync_live(args.db, args.out, args.quiet)
    except Exception as exc:  # pragma: no cover - CLI error surface
        print(f"sync-live-timeline: ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
