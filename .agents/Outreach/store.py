"""SQLite-backed STATE substrate.

Machine-written loop state lives here and only here:

  engine_state — phase, current batch/snapshot/intervention references,
                 batch cycle counter, evidence deadline, hold reason
  batches      — one row per prepared batch (artifact refs, metrics, verdict)
  knowledge    — per-variable experiment history (verdicts, trials)
  actions      — append-only per-lead action ledger (channel-neutral)
  goals        — workflow goal rows
  leads        — channel-neutral lead store (future social workflows; the
                 email bundle keeps its own master list — see
                 workflows/email/outbound.py)

Human-written state (goal spec, approvals, knobs) lives in data/control.json
(engine/control.py): the owner edits JSON, the machine writes SQLite.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Lead, LeadState, WorkflowGoal


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OutreachStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS leads (
                lead_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                company TEXT NOT NULL,
                role TEXT,
                location TEXT,
                channels TEXT NOT NULL DEFAULT '[]',
                profile_url TEXT,
                company_url TEXT,
                state TEXT NOT NULL,
                icp_score INTEGER NOT NULL DEFAULT 0,
                research_fact TEXT,
                operational_consequence TEXT,
                message TEXT,
                source_urls TEXT NOT NULL DEFAULT '[]',
                exclusion_reason TEXT,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                action TEXT NOT NULL,
                result TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(lead_id) REFERENCES leads(lead_id)
            );
            CREATE TABLE IF NOT EXISTS goals (
                workflow_id TEXT PRIMARY KEY,
                channel TEXT NOT NULL,
                action TEXT NOT NULL,
                target INTEGER NOT NULL,
                min_icp_score INTEGER NOT NULL,
                queue_target INTEGER NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS engine_state (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS batches (
                id TEXT PRIMARY KEY,
                workflow TEXT NOT NULL,
                phase TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                intervention_json TEXT,
                batch_json TEXT,
                metrics_json TEXT,
                verdict_json TEXT,
                preview_path TEXT,
                report_path TEXT
            );
            CREATE TABLE IF NOT EXISTS knowledge (
                variable TEXT PRIMARY KEY,
                tried_json TEXT NOT NULL DEFAULT '[]',
                verdict TEXT,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_leads_state ON leads(state);
            CREATE INDEX IF NOT EXISTS idx_actions_channel ON actions(channel);
            CREATE INDEX IF NOT EXISTS idx_batches_phase ON batches(phase);
            """
        )
        self.db.commit()

    # ── engine_state ──────────────────────────────────────────────────────────

    def get_state(self, key: str, default: Any = None) -> Any:
        row = self.db.execute(
            "SELECT value FROM engine_state WHERE key=?", (key,)).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except (TypeError, ValueError):
            return default

    def set_state(self, key: str, value: Any) -> None:
        payload = json.dumps(value, default=str)
        self.db.execute(
            """INSERT INTO engine_state(key, value) VALUES(?,?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
            (key, payload))
        self.db.commit()

    def phase(self) -> str:
        return str(self.get_state("phase", "observe"))

    def set_phase(self, phase: str) -> None:
        self.set_state("phase", phase)

    def cycle(self) -> int:
        return int(self.get_state("batch_cycle", 0))

    def bump_cycle(self) -> int:
        n = self.cycle() + 1
        self.set_state("batch_cycle", n)
        return n

    def current_batch_id(self) -> str | None:
        return self.get_state("current_batch")

    def set_current_batch(self, batch_id: str | None) -> None:
        self.set_state("current_batch", batch_id)

    def evidence_due(self) -> str | None:
        return self.get_state("evidence_due")

    def set_evidence_due(self, ts: str | None) -> None:
        self.set_state("evidence_due", ts)

    def hold_reason(self) -> str | None:
        return self.get_state("hold_reason")

    def set_hold_reason(self, reason: str | None) -> None:
        self.set_state("hold_reason", reason)

    def last_snapshot_path(self) -> str | None:
        return self.get_state("last_snapshot")

    def set_last_snapshot_path(self, path: str) -> None:
        self.set_state("last_snapshot", path)

    def last_intervention_path(self) -> str | None:
        return self.get_state("last_intervention")

    def set_last_intervention_path(self, path: str) -> None:
        self.set_state("last_intervention", path)

    # ── batches ───────────────────────────────────────────────────────────────

    def upsert_batch(self, batch: dict) -> None:
        self.db.execute(
            """INSERT INTO batches(id, workflow, phase, created_at, updated_at,
               intervention_json, batch_json, metrics_json, verdict_json,
               preview_path, report_path)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET phase=excluded.phase,
                 updated_at=excluded.updated_at, batch_json=excluded.batch_json,
                 metrics_json=excluded.metrics_json,
                 verdict_json=excluded.verdict_json,
                 preview_path=excluded.preview_path,
                 report_path=excluded.report_path""",
            (batch["id"], batch.get("workflow", ""), batch.get("phase", "prepare"),
             batch.get("created_at") or utc_now(),
             batch.get("updated_at") or utc_now(),
             json.dumps(batch.get("intervention") or {}, default=str),
             json.dumps(batch.get("batch") or {}, default=str),
             json.dumps(batch.get("metrics") or {}, default=str),
             json.dumps(batch.get("verdict") or {}, default=str),
             batch.get("preview_path"), batch.get("report_path")))
        self.db.commit()

    def get_batch(self, batch_id: str) -> dict | None:
        row = self.db.execute(
            "SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
        if row is None:
            return None

        def _load(key):
            try:
                return json.loads(row[key] or "{}")
            except (TypeError, ValueError):
                return {}

        return {
            "id": row["id"], "workflow": row["workflow"], "phase": row["phase"],
            "created_at": row["created_at"], "updated_at": row["updated_at"],
            "intervention": _load("intervention_json"),
            "batch": _load("batch_json"),
            "metrics": _load("metrics_json"),
            "verdict": _load("verdict_json"),
            "preview_path": row["preview_path"],
            "report_path": row["report_path"],
        }

    def update_batch_phase(self, batch_id: str, phase: str) -> None:
        self.db.execute(
            "UPDATE batches SET phase=?, updated_at=? WHERE id=?",
            (phase, utc_now(), batch_id))
        self.db.commit()

    def update_batch_metrics(self, batch_id: str, metrics: dict, verdict: dict | None = None) -> None:
        self.db.execute(
            "UPDATE batches SET metrics_json=?, verdict_json=?, updated_at=? WHERE id=?",
            (json.dumps(metrics, default=str),
             json.dumps(verdict or {}, default=str), utc_now(), batch_id))
        self.db.commit()

    def update_batch_report(self, batch_id: str, report_path: str) -> None:
        self.db.execute(
            "UPDATE batches SET report_path=?, updated_at=? WHERE id=?",
            (report_path, utc_now(), batch_id))
        self.db.commit()

    def latest_batch(self) -> dict | None:
        row = self.db.execute(
            "SELECT id FROM batches ORDER BY created_at DESC LIMIT 1").fetchone()
        return self.get_batch(row["id"]) if row else None

    # ── knowledge (LEARN) ─────────────────────────────────────────────────────

    def record_trial(self, variable: str, trial: dict) -> None:
        row = self.db.execute(
            "SELECT tried_json FROM knowledge WHERE variable=?",
            (variable,)).fetchone()
        tried = []
        if row:
            try:
                tried = json.loads(row["tried_json"] or "[]")
            except (TypeError, ValueError):
                tried = []
        tried.append(trial)
        self.db.execute(
            """INSERT INTO knowledge(variable, tried_json, verdict, updated_at)
               VALUES(?,?,?,?)
               ON CONFLICT(variable) DO UPDATE SET tried_json=excluded.tried_json,
                 verdict=excluded.verdict, updated_at=excluded.updated_at""",
            (variable, json.dumps(tried, default=str),
             trial.get("verdict") or "", utc_now()))
        self.db.commit()

    def knowledge_for(self, variable: str) -> dict:
        row = self.db.execute(
            "SELECT tried_json, verdict FROM knowledge WHERE variable=?",
            (variable,)).fetchone()
        if row is None:
            return {"tried": [], "verdict": None}
        try:
            tried = json.loads(row["tried_json"] or "[]")
        except (TypeError, ValueError):
            tried = []
        return {"tried": tried, "verdict": row["verdict"] or None}

    def all_knowledge(self) -> dict:
        rows = self.db.execute("SELECT variable, tried_json, verdict FROM knowledge").fetchall()
        out = {}
        for row in rows:
            try:
                tried = json.loads(row["tried_json"] or "[]")
            except (TypeError, ValueError):
                tried = []
            out[row["variable"]] = {"tried": tried, "verdict": row["verdict"] or None}
        return out

    # ── leads / actions / goals (channel-neutral store) ──────────────────────

    def upsert_leads(self, leads) -> int:
        rows = list(leads)
        now = utc_now()
        for lead in rows:
            self.db.execute(
                """INSERT INTO leads VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(lead_id) DO UPDATE SET
                  name=excluded.name, company=excluded.company, role=excluded.role,
                  location=excluded.location, channels=excluded.channels,
                  profile_url=excluded.profile_url, company_url=excluded.company_url,
                  icp_score=excluded.icp_score, research_fact=excluded.research_fact,
                  operational_consequence=excluded.operational_consequence,
                  message=excluded.message, source_urls=excluded.source_urls,
                  exclusion_reason=excluded.exclusion_reason, metadata=excluded.metadata,
                  updated_at=excluded.updated_at""",
                (lead.lead_id, lead.name, lead.company, lead.role, lead.location,
                 json.dumps(lead.channels), lead.profile_url, lead.company_url,
                 lead.state.value, lead.icp_score, lead.research_fact,
                 lead.operational_consequence, lead.message,
                 json.dumps(lead.source_urls), lead.exclusion_reason,
                 json.dumps(lead.metadata), now, now))
        self.db.commit()
        return len(rows)

    def add_goal(self, goal: WorkflowGoal) -> None:
        self.db.execute(
            """INSERT INTO goals VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(workflow_id) DO UPDATE SET channel=excluded.channel,
            action=excluded.action, target=excluded.target,
            min_icp_score=excluded.min_icp_score, queue_target=excluded.queue_target,
            enabled=excluded.enabled""",
            (goal.workflow_id, goal.channel, goal.action, goal.target,
             goal.min_icp_score, goal.queue_target, int(goal.enabled)))
        self.db.commit()

    def get_lead(self, lead_id: str) -> Lead | None:
        row = self.db.execute(
            "SELECT * FROM leads WHERE lead_id=?", (lead_id,)).fetchone()
        return self._lead(row) if row else None

    def ready_queue(self, channel: str, limit: int = 50, min_score: int = 75) -> list:
        rows = self.db.execute(
            """SELECT * FROM leads WHERE state='ready' AND icp_score>=?
            AND channels LIKE ? ORDER BY icp_score DESC, updated_at ASC LIMIT ?""",
            (min_score, f'%"{channel}"%', limit)).fetchall()
        return [self._lead(row) for row in rows]

    def record_action(self, lead_id: str, channel: str, action: str, result: str, note: str = "") -> None:
        self.db.execute(
            "INSERT INTO actions(lead_id,channel,action,result,note,created_at) VALUES(?,?,?,?,?,?)",
            (lead_id, channel, action, result, note, utc_now()))
        new_state = LeadState.ACTIONED.value if result in {"sent", "connection_sent", "published"} else result
        self.db.execute(
            "UPDATE leads SET state=?, updated_at=? WHERE lead_id=?",
            (new_state, utc_now(), lead_id))
        self.db.commit()

    def action_count(self, channel: str, action: str, result: str | None = None) -> int:
        query = "SELECT COUNT(*) FROM actions WHERE channel=? AND action=?"
        args: list = [channel, action]
        if result:
            query += " AND result=?"
            args.append(result)
        return int(self.db.execute(query, args).fetchone()[0])

    def counts(self) -> dict:
        rows = self.db.execute("SELECT state, COUNT(*) AS n FROM leads GROUP BY state").fetchall()
        return {row["state"]: row["n"] for row in rows}

    def close(self) -> None:
        self.db.close()

    @staticmethod
    def _lead(row: sqlite3.Row) -> Lead:
        return Lead(
            lead_id=row["lead_id"], name=row["name"], company=row["company"],
            role=row["role"] or "", location=row["location"] or "",
            channels=json.loads(row["channels"] or "[]"), profile_url=row["profile_url"] or "",
            company_url=row["company_url"] or "", state=LeadState(row["state"]),
            icp_score=row["icp_score"], research_fact=row["research_fact"] or "",
            operational_consequence=row["operational_consequence"] or "",
            message=row["message"] or "", source_urls=json.loads(row["source_urls"] or "[]"),
            exclusion_reason=row["exclusion_reason"] or "",
            metadata=json.loads(row["metadata"] or "{}"))
