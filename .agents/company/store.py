"""SQLite is the runtime authority; chat sessions are only clients."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _init(self) -> None:
        with self.connect() as con:
            con.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, engine_id TEXT NOT NULL,
                    metric TEXT NOT NULL, operator TEXT NOT NULL, target_json TEXT NOT NULL,
                    deadline TEXT, parent_id TEXT REFERENCES goals(id),
                    goal_status TEXT NOT NULL, config_json TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cycles (
                    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL REFERENCES goals(id),
                    sequence INTEGER NOT NULL, stage TEXT NOT NULL, step TEXT NOT NULL,
                    run_status TEXT NOT NULL, resume_at TEXT, data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    UNIQUE(goal_id, sequence)
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id TEXT NOT NULL,
                    cycle_id TEXT, kind TEXT NOT NULL, payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS approvals (
                    goal_id TEXT NOT NULL, cycle_id TEXT NOT NULL, approval_key TEXT NOT NULL,
                    status TEXT NOT NULL, note TEXT NOT NULL, updated_at TEXT NOT NULL,
                    PRIMARY KEY(goal_id, cycle_id, approval_key)
                );
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, engine_id TEXT NOT NULL,
                    goal_id TEXT, claim TEXT NOT NULL, evidence_json TEXT NOT NULL,
                    confidence REAL NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS leases (
                    goal_id TEXT PRIMARY KEY, holder TEXT NOT NULL, expires_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS hypotheses (
                    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL REFERENCES goals(id),
                    statement TEXT NOT NULL, variable TEXT, prediction TEXT,
                    status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL REFERENCES goals(id),
                    run_type TEXT NOT NULL, parent_run_id TEXT, triggered_by_run_id TEXT,
                    engine_id TEXT NOT NULL, engine_version TEXT NOT NULL,
                    hypothesis_id TEXT, config_snapshot_json TEXT NOT NULL,
                    controlled_variables_json TEXT NOT NULL, changed_variables_json TEXT NOT NULL,
                    evidence_validity TEXT NOT NULL, contamination_reason TEXT,
                    resume_run_id TEXT, status TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL REFERENCES goals(id),
                    run_id TEXT NOT NULL REFERENCES runs(id), kind TEXT NOT NULL,
                    source TEXT NOT NULL, payload_json TEXT NOT NULL,
                    validity TEXT NOT NULL, observed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL REFERENCES goals(id),
                    run_id TEXT NOT NULL REFERENCES runs(id), decision_type TEXT NOT NULL,
                    rationale TEXT NOT NULL, evidence_ids_json TEXT NOT NULL,
                    next_run_type TEXT, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evaluations (
                    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL REFERENCES goals(id),
                    run_id TEXT NOT NULL REFERENCES runs(id), verdict TEXT NOT NULL,
                    goal_met INTEGER NOT NULL, metrics_json TEXT NOT NULL,
                    validity TEXT NOT NULL, contamination_reason TEXT,
                    next_experiment_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS engine_versions (
                    engine_id TEXT NOT NULL, version TEXT NOT NULL, code_ref TEXT,
                    status TEXT NOT NULL, test_summary_json TEXT NOT NULL,
                    created_at TEXT NOT NULL, deployed_at TEXT,
                    PRIMARY KEY(engine_id, version)
                );
                CREATE TABLE IF NOT EXISTS change_tasks (
                    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL REFERENCES goals(id),
                    run_id TEXT NOT NULL REFERENCES runs(id), engine_id TEXT NOT NULL,
                    from_version TEXT NOT NULL, target_version TEXT NOT NULL,
                    problem TEXT NOT NULL, allowed_files_json TEXT NOT NULL,
                    acceptance_tests_json TEXT NOT NULL, status TEXT NOT NULL,
                    result_json TEXT NOT NULL, originating_run_id TEXT,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    change_kind TEXT NOT NULL DEFAULT 'repair',
                    specification_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL REFERENCES goals(id),
                    run_id TEXT NOT NULL REFERENCES runs(id), kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL, status TEXT NOT NULL,
                    created_at TEXT NOT NULL, delivered_at TEXT,
                    UNIQUE(goal_id,run_id,kind)
                );
            """)
            change_columns = {row[1] for row in con.execute("PRAGMA table_info(change_tasks)")}
            if "change_kind" not in change_columns:
                con.execute("ALTER TABLE change_tasks ADD COLUMN change_kind TEXT NOT NULL DEFAULT 'repair'")
            if "specification_json" not in change_columns:
                con.execute("ALTER TABLE change_tasks ADD COLUMN specification_json TEXT NOT NULL DEFAULT '{}'")
            con.execute("""INSERT OR IGNORE INTO runs
                SELECT c.id,c.goal_id,'execution',NULL,NULL,g.engine_id,'unversioned',NULL,
                       g.config_json,'{}','{}','business',NULL,NULL,c.run_status,c.created_at,c.updated_at
                FROM cycles c JOIN goals g ON g.id=c.goal_id""")

    @staticmethod
    def _decode(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        out = dict(row)
        for key in tuple(out):
            if key.endswith("_json"):
                out[key[:-5]] = json.loads(out.pop(key))
        return out

    def create_goal(self, *, name: str, engine_id: str, metric: str,
                    operator: str, target: Any, deadline: str | None = None,
                    parent_id: str | None = None, config: dict | None = None,
                    goal_id: str | None = None, run_type: str = "execution",
                    engine_version: str = "unversioned", hypothesis: dict | None = None,
                    parent_run_id: str | None = None, triggered_by_run_id: str | None = None,
                    controlled_variables: dict | None = None, changed_variables: dict | None = None,
                    evidence_validity: str = "business", resume_run_id: str | None = None) -> dict:
        goal_id = goal_id or f"goal-{uuid.uuid4().hex[:10]}"
        stamp = now()
        with self.connect() as con:
            con.execute("""INSERT INTO goals VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
                goal_id, name, engine_id, metric, operator, json.dumps(target), deadline,
                parent_id, "active", json.dumps(config or {}), stamp, stamp))
            cycle_id = f"run-{uuid.uuid4().hex[:10]}"
            hypothesis_id = None
            if hypothesis:
                hypothesis_id = f"hyp-{uuid.uuid4().hex[:10]}"
                con.execute("INSERT INTO hypotheses VALUES (?,?,?,?,?,?,?,?)", (
                    hypothesis_id, goal_id, hypothesis["statement"], hypothesis.get("variable"),
                    hypothesis.get("prediction"), "active", stamp, stamp))
            con.execute("""INSERT INTO cycles VALUES (?,?,?,?,?,?,?,?,?,?)""", (
                cycle_id, goal_id, 1, "OBSERVE", "collect", "idle", None,
                json.dumps({}), stamp, stamp))
            con.execute("""INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                cycle_id, goal_id, run_type, parent_run_id, triggered_by_run_id,
                engine_id, engine_version, hypothesis_id, json.dumps(config or {}),
                json.dumps(controlled_variables or {}), json.dumps(changed_variables or {}),
                evidence_validity, None, resume_run_id, "idle", stamp, stamp))
            con.execute("INSERT INTO events(goal_id,cycle_id,kind,payload_json,created_at) VALUES (?,?,?,?,?)",
                        (goal_id, cycle_id, "goal.created", json.dumps({"engine_id": engine_id}), stamp))
        return self.goal(goal_id)

    def goal(self, goal_id: str) -> dict:
        with self.connect() as con:
            row = con.execute("SELECT * FROM goals WHERE id=?", (goal_id,)).fetchone()
        value = self._decode(row)
        if not value:
            raise KeyError(f"unknown goal: {goal_id}")
        return value

    def goals(self, parent_id: str | None = None) -> list[dict]:
        with self.connect() as con:
            if parent_id is None:
                rows = con.execute("SELECT * FROM goals ORDER BY created_at").fetchall()
            else:
                rows = con.execute("SELECT * FROM goals WHERE parent_id=? ORDER BY created_at", (parent_id,)).fetchall()
        return [self._decode(r) for r in rows]

    def cycle(self, goal_id: str) -> dict:
        with self.connect() as con:
            row = con.execute("SELECT * FROM cycles WHERE goal_id=? ORDER BY sequence DESC LIMIT 1", (goal_id,)).fetchone()
        value = self._decode(row)
        if not value:
            raise KeyError(f"goal has no cycle: {goal_id}")
        return value

    def update_cycle(self, cycle_id: str, *, stage: str, step: str, run_status: str,
                     data: dict, resume_at: str | None = None) -> None:
        with self.connect() as con:
            con.execute("""UPDATE cycles SET stage=?,step=?,run_status=?,resume_at=?,data_json=?,updated_at=? WHERE id=?""",
                        (stage, step, run_status, resume_at, json.dumps(data), now(), cycle_id))

    def new_cycle(self, goal_id: str, metadata: dict | None = None) -> dict:
        previous = self.cycle(goal_id)
        previous_run = self.run(previous["id"])
        goal = self.goal(goal_id)
        metadata = metadata or {}
        stamp = now()
        cycle_id = f"run-{uuid.uuid4().hex[:10]}"
        with self.connect() as con:
            con.execute("INSERT INTO cycles VALUES (?,?,?,?,?,?,?,?,?,?)", (
                cycle_id, goal_id, previous["sequence"] + 1, "OBSERVE", "collect", "idle", None,
                json.dumps({}), stamp, stamp))
            hypothesis_id = None
            hypothesis = metadata.get("hypothesis")
            if hypothesis:
                hypothesis_id = f"hyp-{uuid.uuid4().hex[:10]}"
                con.execute("INSERT INTO hypotheses VALUES (?,?,?,?,?,?,?,?)", (
                    hypothesis_id, goal_id, hypothesis["statement"], hypothesis.get("variable"),
                    hypothesis.get("prediction"), "active", stamp, stamp))
            con.execute("""INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                cycle_id, goal_id, metadata.get("run_type", previous_run["run_type"]),
                metadata.get("parent_run_id", previous["id"]),
                metadata.get("triggered_by_run_id", previous["id"]), goal["engine_id"],
                metadata.get("engine_version", previous_run["engine_version"]), hypothesis_id,
                json.dumps(metadata.get("config_snapshot", goal["config"])),
                json.dumps(metadata.get("controlled_variables", previous_run["controlled_variables"])),
                json.dumps(metadata.get("changed_variables", {})),
                metadata.get("evidence_validity", previous_run["evidence_validity"]),
                None, metadata.get("resume_run_id"), "idle", stamp, stamp))
        return self.cycle(goal_id)

    def run(self, run_id: str) -> dict:
        with self.connect() as con:
            row = con.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        value = self._decode(row)
        if not value:
            raise KeyError(f"unknown run: {run_id}")
        return value

    def update_run(self, run_id: str, *, status: str | None = None,
                   validity: str | None = None, contamination_reason: str | None = None,
                   resume_run_id: str | None = None) -> None:
        current = self.run(run_id)
        with self.connect() as con:
            con.execute("""UPDATE runs SET status=?,evidence_validity=?,contamination_reason=?,
                resume_run_id=?,updated_at=? WHERE id=?""", (
                status or current["status"], validity or current["evidence_validity"],
                contamination_reason if contamination_reason is not None else current["contamination_reason"],
                resume_run_id if resume_run_id is not None else current["resume_run_id"], now(), run_id))

    def add_evidence(self, goal_id: str, run_id: str, kind: str, source: str,
                     payload: dict, validity: str = "business") -> dict:
        evidence_id = f"ev-{uuid.uuid4().hex[:12]}"
        with self.connect() as con:
            con.execute("INSERT INTO evidence VALUES (?,?,?,?,?,?,?,?)", (
                evidence_id, goal_id, run_id, kind, source, json.dumps(payload), validity, now()))
        return self.evidence(run_id)[-1]

    def evidence(self, run_id: str) -> list[dict]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM evidence WHERE run_id=? ORDER BY observed_at,id", (run_id,)).fetchall()
        return [self._decode(row) for row in rows]

    def add_decision(self, goal_id: str, run_id: str, decision: dict) -> dict:
        decision_id = f"dec-{uuid.uuid4().hex[:12]}"
        with self.connect() as con:
            con.execute("INSERT INTO decisions VALUES (?,?,?,?,?,?,?,?,?)", (
                decision_id, goal_id, run_id, decision.get("type", "intervention"),
                decision.get("rationale", ""), json.dumps(decision.get("evidence_ids", [])),
                decision.get("next_run_type"), json.dumps(decision.get("payload", {})), now()))
        return self.decisions(run_id)[-1]

    def decisions(self, run_id: str) -> list[dict]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM decisions WHERE run_id=? ORDER BY created_at,id", (run_id,)).fetchall()
        return [self._decode(row) for row in rows]

    def add_evaluation(self, goal_id: str, run_id: str, evaluation: dict) -> dict:
        evaluation_id = f"eval-{uuid.uuid4().hex[:12]}"
        with self.connect() as con:
            con.execute("INSERT INTO evaluations VALUES (?,?,?,?,?,?,?,?,?,?)", (
                evaluation_id, goal_id, run_id, evaluation.get("verdict", "inconclusive"),
                int(bool(evaluation.get("goal_met"))), json.dumps(evaluation.get("metrics", {})),
                evaluation.get("validity", "business"), evaluation.get("contamination_reason"),
                json.dumps(evaluation.get("next_experiment", {})), now()))
        return self.evaluation(run_id)

    def evaluation(self, run_id: str) -> dict | None:
        with self.connect() as con:
            row = con.execute("SELECT * FROM evaluations WHERE run_id=? ORDER BY created_at DESC LIMIT 1", (run_id,)).fetchone()
        return self._decode(row)

    def latest_evaluation_for_goal(self, goal_id: str) -> dict | None:
        with self.connect() as con:
            row = con.execute("SELECT * FROM evaluations WHERE goal_id=? ORDER BY created_at DESC LIMIT 1",
                              (goal_id,)).fetchone()
        return self._decode(row)

    def register_engine_version(self, engine_id: str, version: str, status: str = "deployed",
                                code_ref: str | None = None, test_summary: dict | None = None) -> None:
        stamp = now()
        with self.connect() as con:
            con.execute("""INSERT INTO engine_versions VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(engine_id,version) DO UPDATE SET status=excluded.status,
                code_ref=COALESCE(excluded.code_ref,engine_versions.code_ref),
                test_summary_json=excluded.test_summary_json,deployed_at=excluded.deployed_at""", (
                engine_id, version, code_ref, status, json.dumps(test_summary or {}), stamp,
                stamp if status == "deployed" else None))

    def engine_versions(self, engine_id: str | None = None) -> list[dict]:
        with self.connect() as con:
            if engine_id:
                rows = con.execute("SELECT * FROM engine_versions WHERE engine_id=? ORDER BY created_at", (engine_id,)).fetchall()
            else:
                rows = con.execute("SELECT * FROM engine_versions ORDER BY engine_id,created_at").fetchall()
        return [self._decode(row) for row in rows]

    def create_change_task(self, *, goal_id: str, run_id: str, engine_id: str,
                           from_version: str, target_version: str, problem: str,
                           allowed_files: list, acceptance_tests: list,
                           originating_run_id: str | None = None,
                           change_kind: str = "repair",
                           specification: dict | None = None) -> dict:
        task_id, stamp = f"change-{uuid.uuid4().hex[:10]}", now()
        with self.connect() as con:
            con.execute("""INSERT INTO change_tasks(
                id,goal_id,run_id,engine_id,from_version,target_version,problem,
                allowed_files_json,acceptance_tests_json,status,result_json,
                originating_run_id,created_at,updated_at,change_kind,specification_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                task_id, goal_id, run_id, engine_id, from_version, target_version, problem,
                json.dumps(allowed_files), json.dumps(acceptance_tests), "proposed", json.dumps({}),
                originating_run_id, stamp, stamp, change_kind, json.dumps(specification or {})))
        return self.change_task(task_id)

    def change_task(self, task_id: str) -> dict:
        with self.connect() as con:
            row = con.execute("SELECT * FROM change_tasks WHERE id=?", (task_id,)).fetchone()
        value = self._decode(row)
        if not value:
            raise KeyError(f"unknown change task: {task_id}")
        return value

    def change_tasks_for_run(self, run_id: str) -> list[dict]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM change_tasks WHERE run_id=? ORDER BY created_at", (run_id,)).fetchall()
        return [self._decode(row) for row in rows]

    def complete_change_task(self, task_id: str, status: str, result: dict) -> dict:
        with self.connect() as con:
            con.execute("UPDATE change_tasks SET status=?,result_json=?,updated_at=? WHERE id=?",
                        (status, json.dumps(result), now(), task_id))
        return self.change_task(task_id)

    def set_goal_status(self, goal_id: str, status: str) -> None:
        with self.connect() as con:
            con.execute("UPDATE goals SET goal_status=?,updated_at=? WHERE id=?", (status, now(), goal_id))

    def event(self, goal_id: str, cycle_id: str | None, kind: str, payload: dict) -> None:
        with self.connect() as con:
            con.execute("INSERT INTO events(goal_id,cycle_id,kind,payload_json,created_at) VALUES (?,?,?,?,?)",
                        (goal_id, cycle_id, kind, json.dumps(payload), now()))

    def notify(self, goal_id: str, run_id: str, kind: str, payload: dict) -> dict:
        notification_id = f"note-{uuid.uuid4().hex[:12]}"
        with self.connect() as con:
            con.execute("""INSERT OR IGNORE INTO notifications
                (id,goal_id,run_id,kind,payload_json,status,created_at,delivered_at)
                VALUES (?,?,?,?,?,'pending',?,NULL)""",
                (notification_id, goal_id, run_id, kind, json.dumps(payload), now()))
            row = con.execute("""SELECT * FROM notifications
                WHERE goal_id=? AND run_id=? AND kind=?""", (goal_id, run_id, kind)).fetchone()
        return self._decode(row)

    def notifications(self, status: str | None = None, limit: int = 100) -> list[dict]:
        with self.connect() as con:
            if status:
                rows = con.execute("""SELECT * FROM notifications WHERE status=?
                    ORDER BY created_at,id LIMIT ?""", (status, limit)).fetchall()
            else:
                rows = con.execute("SELECT * FROM notifications ORDER BY created_at,id LIMIT ?", (limit,)).fetchall()
        return [self._decode(row) for row in rows]

    def acknowledge_notification(self, notification_id: str) -> dict:
        stamp = now()
        with self.connect() as con:
            con.execute("UPDATE notifications SET status='delivered',delivered_at=? WHERE id=?",
                        (stamp, notification_id))
            row = con.execute("SELECT * FROM notifications WHERE id=?", (notification_id,)).fetchone()
        value = self._decode(row)
        if not value:
            raise KeyError(f"unknown notification: {notification_id}")
        return value

    def wake_goal(self, goal_id: str, reason: str) -> bool:
        cycle = self.cycle(goal_id)
        if cycle["run_status"] != "waiting":
            return False
        stamp = now()
        with self.connect() as con:
            con.execute("UPDATE cycles SET resume_at=?,updated_at=? WHERE id=?",
                        (stamp, stamp, cycle["id"]))
        self.event(goal_id, cycle["id"], "run.woken", {"reason": reason})
        return True

    def events(self, goal_id: str, limit: int = 20) -> list[dict]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM events WHERE goal_id=? ORDER BY id DESC LIMIT ?", (goal_id, limit)).fetchall()
        return [self._decode(r) for r in rows]

    def approve(self, goal_id: str, cycle_id: str, key: str, note: str = "") -> None:
        with self.connect() as con:
            con.execute("""INSERT INTO approvals VALUES (?,?,?,?,?,?)
                ON CONFLICT(goal_id,cycle_id,approval_key) DO UPDATE SET status=excluded.status,note=excluded.note,updated_at=excluded.updated_at""",
                (goal_id, cycle_id, key, "approved", note, now()))
        self.event(goal_id, cycle_id, "approval.granted", {"key": key, "note": note})

    def approval(self, goal_id: str, cycle_id: str, key: str) -> str | None:
        with self.connect() as con:
            row = con.execute("SELECT status FROM approvals WHERE goal_id=? AND cycle_id=? AND approval_key=?",
                              (goal_id, cycle_id, key)).fetchone()
        return row[0] if row else None

    def memories(self, engine_id: str, goal_id: str) -> tuple[dict, ...]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM memory WHERE engine_id=? AND (goal_id=? OR goal_id IS NULL) ORDER BY id DESC LIMIT 50",
                               (engine_id, goal_id)).fetchall()
        return tuple(self._decode(r) for r in rows)

    def learn(self, engine_id: str, goal_id: str, claim: str, evidence: dict, confidence: float) -> None:
        with self.connect() as con:
            con.execute("INSERT INTO memory(engine_id,goal_id,claim,evidence_json,confidence,created_at) VALUES (?,?,?,?,?,?)",
                        (engine_id, goal_id, claim, json.dumps(evidence), confidence, now()))

    def acquire(self, goal_id: str, holder: str, seconds: int = 60) -> bool:
        expires = (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()
        stamp = now()
        with self.connect() as con:
            con.execute("DELETE FROM leases WHERE expires_at<=?", (stamp,))
            try:
                con.execute("INSERT INTO leases VALUES (?,?,?)", (goal_id, holder, expires))
                return True
            except sqlite3.IntegrityError:
                return False

    def release(self, goal_id: str, holder: str) -> None:
        with self.connect() as con:
            con.execute("DELETE FROM leases WHERE goal_id=? AND holder=?", (goal_id, holder))
