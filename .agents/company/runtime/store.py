"""SQLite is the runtime authority; chat sessions are only clients."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

TERMINAL_GOAL_STATUSES = ("achieved", "abandoned", "expired")
ACTIONABLE_NOTIFICATION_KINDS = (
    "approval_required", "action_required", "blocked", "failed",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def format_utc(value) -> str:
    """Render an ISO-8601 timestamp as a plain UTC wall-clock string."""
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _why_next_for_run(run_status: str, goal_status: str, resume_at,
                      data: dict | None) -> str | None:
    """Plain-language why/next line for a run in the compact projection.

    Machine tokens remain available unchanged; this adds one human-readable
    line that makes suspended states self-explanatory.
    """
    data = data or {}
    action = data.get("action_result") or {}
    if run_status == "waiting":
        parts = ["waiting"]
        deadline = action.get("evidence_deadline")
        if deadline:
            parts.append(f"evidence window open until {format_utc(deadline)}")
        if resume_at:
            parts.append(f"next automatic check {format_utc(resume_at)}")
        if len(parts) == 1:
            parts.append("awaiting evidence or a state change")
        return parts[0] + (" — " + "; ".join(parts[1:]) if len(parts) > 1 else "")
    if run_status == "blocked":
        task = action.get("task") or {}
        if task.get("status") == "approved":
            return "blocked — needs coding executor"
        capability = ((data.get("observation") or {}).get("attention") or {}).get("capability")
        if capability:
            return f"blocked — needs {capability}"
        return "blocked — needs action or remediation"
    if run_status == "awaiting_approval":
        return "awaiting_approval — prepared action needs your approval"
    if run_status == "completed":
        return {"achieved": "completed — goal achieved",
                "abandoned": "completed — goal abandoned",
                "expired": "completed — goal expired"}.get(
                    goal_status, "completed — run finished; the next run needs approval to start")
    if run_status == "failed":
        return "failed — needs investigation; retry with `company retry <goal>`"
    if run_status == "idle":
        return "active — run ready to advance"
    return None


def _why_next_for_kind(kind: str, payload: dict | None = None) -> str | None:
    """Plain-language why/next wording for a notification kind."""
    payload = payload or {}
    attention = payload.get("attention") or {}
    if kind == "approval_required":
        return "approval needed — prepared action needs your approval"
    if kind == "blocked":
        result = payload.get("result") or {}
        task = (attention.get("task") or (result.get("metrics") or {}).get("task")
                or (payload.get("action_result") or {}).get("task") or {})
        if task.get("status") == "approved":
            return "blocked — needs coding executor"
        capability = attention.get("capability")
        if capability:
            return f"blocked — needs {capability}"
        return "blocked — needs action or remediation"
    if kind == "action_required":
        capability = attention.get("capability")
        if capability:
            return f"action needed — {capability} required"
        required = payload.get("required_user_action")
        if required:
            return f"action needed — {required}"
        return "action needed — a capability or input is missing"
    if kind == "failed":
        return "failed — needs investigation; retry with `company retry <goal>`"
    if kind == "run_completed":
        return "run completed — review the result; the next run needs approval to start"
    if kind == "goal_achieved":
        return "goal completed — outcome achieved"
    if kind == "goal_abandoned":
        return "goal abandoned — closed without reaching the outcome"
    if kind == "goal_expired":
        return "goal expired — deadline passed before reaching the target"
    return None


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
            self._migrate_v5(con)
            con.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, owner_id TEXT NOT NULL,
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id TEXT NOT NULL,
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
                    owner_id TEXT NOT NULL, owner_version TEXT NOT NULL,
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
                CREATE TABLE IF NOT EXISTS owner_versions (
                    owner_id TEXT NOT NULL, version TEXT NOT NULL, code_ref TEXT,
                    status TEXT NOT NULL, test_summary_json TEXT NOT NULL,
                    created_at TEXT NOT NULL, deployed_at TEXT,
                    PRIMARY KEY(owner_id, version)
                );
                CREATE TABLE IF NOT EXISTS change_tasks (
                    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL REFERENCES goals(id),
                    run_id TEXT NOT NULL REFERENCES runs(id), owner_id TEXT NOT NULL,
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
                SELECT c.id,c.goal_id,'execution',NULL,NULL,g.owner_id,'unversioned',NULL,
                       g.config_json,'{}','{}','business',NULL,NULL,c.run_status,c.created_at,c.updated_at
                FROM cycles c JOIN goals g ON g.id=c.goal_id""")
            self._repair_terminal_states(con)
            self._repair_attention_states(con)

    @staticmethod
    def _migrate_v5(con: sqlite3.Connection) -> None:
        """Rename internal v4 storage without rewriting historical evidence."""

        tables = {row[0] for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if "engine_versions" in tables and "owner_versions" not in tables:
            con.execute("ALTER TABLE engine_versions RENAME TO owner_versions")
            tables.remove("engine_versions")
            tables.add("owner_versions")
        for table, old, new in (
            ("goals", "engine_id", "owner_id"),
            ("memory", "engine_id", "owner_id"),
            ("runs", "engine_id", "owner_id"),
            ("runs", "engine_version", "owner_version"),
            ("owner_versions", "engine_id", "owner_id"),
            ("change_tasks", "engine_id", "owner_id"),
        ):
            if table not in tables:
                continue
            columns = {row[1] for row in con.execute(f"PRAGMA table_info({table})")}
            if old in columns and new not in columns:
                con.execute(f"ALTER TABLE {table} RENAME COLUMN {old} TO {new}")

    @staticmethod
    def _repair_terminal_states(con: sqlite3.Connection) -> None:
        """Make terminal goals non-actionable while preserving their audit data."""

        placeholders = ",".join("?" for _ in TERMINAL_GOAL_STATUSES)
        con.execute(f"""UPDATE cycles SET run_status='completed',resume_at=NULL
            WHERE id IN (
                SELECT c.id FROM cycles c JOIN goals g ON g.id=c.goal_id
                WHERE g.goal_status IN ({placeholders})
                  AND c.sequence=(SELECT MAX(c2.sequence) FROM cycles c2 WHERE c2.goal_id=g.id)
            ) AND run_status!='completed'""", TERMINAL_GOAL_STATUSES)
        con.execute(f"""UPDATE runs SET status='completed'
            WHERE id IN (
                SELECT c.id FROM cycles c JOIN goals g ON g.id=c.goal_id
                WHERE g.goal_status IN ({placeholders})
                  AND c.sequence=(SELECT MAX(c2.sequence) FROM cycles c2 WHERE c2.goal_id=g.id)
            ) AND status!='completed'""", TERMINAL_GOAL_STATUSES)
        terminal_marks = ",".join("?" for _ in TERMINAL_GOAL_STATUSES)
        action_marks = ",".join("?" for _ in ACTIONABLE_NOTIFICATION_KINDS)
        con.execute(f"""UPDATE notifications SET status='delivered',delivered_at=COALESCE(delivered_at,?)
            WHERE status='pending' AND kind IN ({action_marks})
              AND goal_id IN (SELECT id FROM goals WHERE goal_status IN ({terminal_marks}))""",
                    (now(), *ACTIONABLE_NOTIFICATION_KINDS, *TERMINAL_GOAL_STATUSES))

    @staticmethod
    def _repair_attention_states(con: sqlite3.Connection) -> None:
        """Keep only attention that matches the run's current suspension."""

        marks = ",".join("?" for _ in ACTIONABLE_NOTIFICATION_KINDS)
        con.execute(f"""UPDATE notifications AS n
            SET status='delivered',delivered_at=COALESCE(delivered_at,?)
            WHERE n.status='pending' AND n.kind IN ({marks}) AND NOT EXISTS (
                SELECT 1 FROM goals g JOIN cycles c ON c.id=n.run_id
                WHERE g.id=n.goal_id AND g.goal_status='active' AND (
                    (c.run_status='awaiting_approval' AND n.kind='approval_required') OR
                    (c.run_status='blocked' AND n.kind IN ('blocked','action_required')) OR
                    (c.run_status='failed' AND n.kind='failed')
                )
            )""", (now(), *ACTIONABLE_NOTIFICATION_KINDS))

    @staticmethod
    def _decode(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        out = dict(row)
        for key in tuple(out):
            if key.endswith("_json"):
                out[key[:-5]] = Store._normalize(json.loads(out.pop(key)))
        return out

    @staticmethod
    def _normalize(value: Any) -> Any:
        """Read v4 JSON snapshots through the v5 vocabulary."""

        if isinstance(value, list):
            return [Store._normalize(item) for item in value]
        if not isinstance(value, dict):
            return "create_department" if value == "create_engine" else value
        aliases = {"engine_id": "owner_id", "engine_version": "owner_version",
                   "engine_spec": "department_spec"}
        return {aliases.get(key, key): Store._normalize(item) for key, item in value.items()}

    def create_goal(self, *, name: str, owner_id: str, metric: str,
                    operator: str, target: Any, deadline: str | None = None,
                    parent_id: str | None = None, config: dict | None = None,
                    goal_id: str | None = None, run_type: str = "execution",
                    owner_version: str = "unversioned", hypothesis: dict | None = None,
                    parent_run_id: str | None = None, triggered_by_run_id: str | None = None,
                    controlled_variables: dict | None = None, changed_variables: dict | None = None,
                    evidence_validity: str = "business", resume_run_id: str | None = None) -> dict:
        goal_id = goal_id or f"goal-{uuid.uuid4().hex[:10]}"
        stamp = now()
        with self.connect() as con:
            con.execute("""INSERT INTO goals VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
                goal_id, name, owner_id, metric, operator, json.dumps(target), deadline,
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
                owner_id, owner_version, hypothesis_id, json.dumps(config or {}),
                json.dumps(controlled_variables or {}), json.dumps(changed_variables or {}),
                evidence_validity, None, resume_run_id, "idle", stamp, stamp))
            con.execute("INSERT INTO events(goal_id,cycle_id,kind,payload_json,created_at) VALUES (?,?,?,?,?)",
                        (goal_id, cycle_id, "goal.created", json.dumps({"owner_id": owner_id}), stamp))
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

    def goal_summaries(self, *, statuses: tuple[str, ...] | None = None,
                       limit: int = 20, goal_id: str | None = None) -> list[dict]:
        """Return bounded operational projections, never stored payload bodies."""

        clauses, parameters = [], []
        if statuses:
            clauses.append(f"g.goal_status IN ({','.join('?' for _ in statuses)})")
            parameters.extend(statuses)
        if goal_id:
            clauses.append("g.id=?")
            parameters.append(goal_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(max(1, min(int(limit), 100)))
        with self.connect() as con:
            rows = con.execute(f"""SELECT
                    g.id,g.name,g.owner_id,g.metric,g.operator,g.target_json,g.deadline,
                    g.parent_id,g.goal_status,g.created_at,g.updated_at,
                    c.id AS run_id,c.sequence,c.stage,c.step,c.run_status,c.resume_at,
                    c.data_json,c.updated_at AS runtime_updated_at,r.run_type,r.evidence_validity,
                    (SELECT COUNT(*) FROM evidence ev WHERE ev.run_id=c.id) AS evidence_count,
                    (SELECT verdict FROM evaluations e WHERE e.goal_id=g.id
                        ORDER BY e.created_at DESC LIMIT 1) AS verdict,
                    (SELECT goal_met FROM evaluations e WHERE e.goal_id=g.id
                        ORDER BY e.created_at DESC LIMIT 1) AS goal_met
                FROM goals g
                JOIN cycles c ON c.goal_id=g.id AND c.sequence=(
                    SELECT MAX(c2.sequence) FROM cycles c2 WHERE c2.goal_id=g.id)
                JOIN runs r ON r.id=c.id
                {where}
                ORDER BY g.updated_at DESC,g.id DESC LIMIT ?""", parameters).fetchall()
        values = []
        for row in rows:
            item = dict(row)
            item["target"] = self._normalize(json.loads(item.pop("target_json")))
            data = self._normalize(json.loads(item.pop("data_json")))
            item["why_next"] = _why_next_for_run(item["run_status"], item["goal_status"],
                                                 item.get("resume_at"), data)
            if item.get("goal_met") is not None:
                item["goal_met"] = bool(item["goal_met"])
            values.append(item)
        return values

    def goal_counts(self) -> dict[str, int]:
        with self.connect() as con:
            rows = con.execute(
                "SELECT goal_status,COUNT(*) AS count FROM goals GROUP BY goal_status"
            ).fetchall()
        values = {status: 0 for status in (
            "proposed", "active", "paused", "achieved", "abandoned", "expired")}
        values.update({row["goal_status"]: row["count"] for row in rows})
        values["total"] = sum(row["count"] for row in rows)
        return values

    def attention(self, limit: int = 10) -> list[dict]:
        """Return only unresolved notifications belonging to active goals."""

        marks = ",".join("?" for _ in ACTIONABLE_NOTIFICATION_KINDS)
        with self.connect() as con:
            rows = con.execute(f"""SELECT n.id,n.goal_id,n.run_id,n.kind,n.created_at,
                    n.payload_json,g.name,g.owner_id,c.stage,c.step,c.run_status
                FROM notifications n JOIN goals g ON g.id=n.goal_id
                JOIN cycles c ON c.id=n.run_id
                WHERE n.status='pending' AND g.goal_status='active' AND n.kind IN ({marks})
                ORDER BY n.created_at,n.id LIMIT ?""",
                (*ACTIONABLE_NOTIFICATION_KINDS, max(1, min(int(limit), 100)))).fetchall()
        values = []
        for row in rows:
            item = dict(row)
            payload = self._normalize(json.loads(item.pop("payload_json")))
            item["message"] = (payload.get("result") or {}).get("message")
            item["required_user_action"] = payload.get("required_user_action")
            why_next = _why_next_for_kind(item["kind"], payload)
            if why_next:
                item["why_next"] = why_next
            values.append(item)
        return values

    def unread_results(self, limit: int = 5) -> list[dict]:
        with self.connect() as con:
            rows = con.execute("""SELECT n.id,n.goal_id,n.run_id,n.kind,n.created_at,
                    g.name,g.owner_id,g.goal_status
                FROM notifications n JOIN goals g ON g.id=n.goal_id
                WHERE n.status='pending' AND n.kind IN (
                    'run_completed','goal_achieved','goal_abandoned','goal_expired')
                ORDER BY n.created_at DESC,n.id DESC LIMIT ?""",
                (max(1, min(int(limit), 100)),)).fetchall()
        values = [dict(row) for row in rows]
        for item in values:
            why_next = _why_next_for_kind(item["kind"])
            if why_next:
                item["why_next"] = why_next
        return values

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
                metadata.get("triggered_by_run_id", previous["id"]), goal["owner_id"],
                metadata.get("owner_version", previous_run["owner_version"]), hypothesis_id,
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

    def register_owner_version(self, owner_id: str, version: str, status: str = "deployed",
                               code_ref: str | None = None, test_summary: dict | None = None) -> None:
        stamp = now()
        with self.connect() as con:
            con.execute("""INSERT INTO owner_versions VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(owner_id,version) DO UPDATE SET status=excluded.status,
                code_ref=COALESCE(excluded.code_ref,owner_versions.code_ref),
                test_summary_json=excluded.test_summary_json,deployed_at=excluded.deployed_at""", (
                owner_id, version, code_ref, status, json.dumps(test_summary or {}), stamp,
                stamp if status == "deployed" else None))

    def owner_versions(self, owner_id: str | None = None) -> list[dict]:
        with self.connect() as con:
            if owner_id:
                rows = con.execute("SELECT * FROM owner_versions WHERE owner_id=? ORDER BY created_at", (owner_id,)).fetchall()
            else:
                rows = con.execute("SELECT * FROM owner_versions ORDER BY owner_id,created_at").fetchall()
        return [self._decode(row) for row in rows]

    def create_change_task(self, *, goal_id: str, run_id: str, owner_id: str,
                           from_version: str, target_version: str, problem: str,
                           allowed_files: list, acceptance_tests: list,
                           originating_run_id: str | None = None,
                           change_kind: str = "repair",
                           specification: dict | None = None) -> dict:
        task_id, stamp = f"change-{uuid.uuid4().hex[:10]}", now()
        with self.connect() as con:
            con.execute("""INSERT INTO change_tasks(
                id,goal_id,run_id,owner_id,from_version,target_version,problem,
                allowed_files_json,acceptance_tests_json,status,result_json,
                originating_run_id,created_at,updated_at,change_kind,specification_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                task_id, goal_id, run_id, owner_id, from_version, target_version, problem,
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
            stamp = now()
            con.execute("UPDATE goals SET goal_status=?,updated_at=? WHERE id=?", (status, stamp, goal_id))
            if status in TERMINAL_GOAL_STATUSES:
                con.execute("""UPDATE cycles SET run_status='completed',resume_at=NULL,updated_at=?
                    WHERE goal_id=? AND sequence=(SELECT MAX(sequence) FROM cycles WHERE goal_id=?)""",
                    (stamp, goal_id, goal_id))
                con.execute("""UPDATE runs SET status='completed',updated_at=? WHERE id=(
                    SELECT id FROM cycles WHERE goal_id=? ORDER BY sequence DESC LIMIT 1)""",
                    (stamp, goal_id))
                marks = ",".join("?" for _ in ACTIONABLE_NOTIFICATION_KINDS)
                con.execute(f"""UPDATE notifications SET status='delivered',delivered_at=?
                    WHERE goal_id=? AND status='pending' AND kind IN ({marks})""",
                    (stamp, goal_id, *ACTIONABLE_NOTIFICATION_KINDS))

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

    def resolve_actionable_notifications(self, goal_id: str, run_id: str) -> None:
        """Close attention items when the run has moved to a new state."""

        marks = ",".join("?" for _ in ACTIONABLE_NOTIFICATION_KINDS)
        stamp = now()
        with self.connect() as con:
            con.execute(f"""UPDATE notifications SET status='delivered',delivered_at=?
                WHERE goal_id=? AND run_id=? AND status='pending' AND kind IN ({marks})""",
                (stamp, goal_id, run_id, *ACTIONABLE_NOTIFICATION_KINDS))

    def notifications(self, status: str | None = None, limit: int = 100) -> list[dict]:
        with self.connect() as con:
            if status:
                rows = con.execute("""SELECT * FROM notifications WHERE status=?
                    ORDER BY created_at,id LIMIT ?""", (status, limit)).fetchall()
            else:
                rows = con.execute("SELECT * FROM notifications ORDER BY created_at,id LIMIT ?", (limit,)).fetchall()
        values = []
        for row in rows:
            item = self._decode(row)
            why_next = _why_next_for_kind(item["kind"], item.get("payload") or {})
            if why_next:
                item["why_next"] = why_next
            values.append(item)
        return values

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
        self.resolve_actionable_notifications(goal_id, cycle_id)

    def approval(self, goal_id: str, cycle_id: str, key: str) -> str | None:
        with self.connect() as con:
            row = con.execute("SELECT status FROM approvals WHERE goal_id=? AND cycle_id=? AND approval_key=?",
                              (goal_id, cycle_id, key)).fetchone()
        return row[0] if row else None

    def memories(self, owner_id: str, goal_id: str) -> tuple[dict, ...]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM memory WHERE owner_id=? AND (goal_id=? OR goal_id IS NULL) ORDER BY id DESC LIMIT 50",
                               (owner_id, goal_id)).fetchall()
        return tuple(self._decode(r) for r in rows)

    def learn(self, owner_id: str, goal_id: str, claim: str, evidence: dict, confidence: float) -> None:
        with self.connect() as con:
            con.execute("INSERT INTO memory(owner_id,goal_id,claim,evidence_json,confidence,created_at) VALUES (?,?,?,?,?,?)",
                        (owner_id, goal_id, claim, json.dumps(evidence), confidence, now()))

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
