"""SQLite-backed state store. Runtime state stays out of source files."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

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
            CREATE INDEX IF NOT EXISTS idx_leads_state ON leads(state);
            CREATE INDEX IF NOT EXISTS idx_actions_channel ON actions(channel);
            """
        )
        self.db.commit()

    def upsert_leads(self, leads: Iterable[Lead]) -> int:
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
                 lead.operational_consequence, lead.message, json.dumps(lead.source_urls),
                 lead.exclusion_reason, json.dumps(lead.metadata), now, now),
            )
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
             goal.min_icp_score, goal.queue_target, int(goal.enabled)),
        )
        self.db.commit()

    def get_lead(self, lead_id: str) -> Lead | None:
        row = self.db.execute("SELECT * FROM leads WHERE lead_id=?", (lead_id,)).fetchone()
        return self._lead(row) if row else None

    def ready_queue(self, channel: str, limit: int = 50, min_score: int = 75) -> list[Lead]:
        rows = self.db.execute(
            """SELECT * FROM leads WHERE state='ready' AND icp_score>=?
            AND channels LIKE ? ORDER BY icp_score DESC, updated_at ASC LIMIT ?""",
            (min_score, f'%"{channel}"%', limit),
        ).fetchall()
        return [self._lead(row) for row in rows]

    def record_action(self, lead_id: str, channel: str, action: str, result: str, note: str = "") -> None:
        self.db.execute(
            "INSERT INTO actions(lead_id,channel,action,result,note,created_at) VALUES(?,?,?,?,?,?)",
            (lead_id, channel, action, result, note, utc_now()),
        )
        new_state = LeadState.ACTIONED.value if result in {"sent", "connection_sent", "published"} else result
        self.db.execute("UPDATE leads SET state=?, updated_at=? WHERE lead_id=?", (new_state, utc_now(), lead_id))
        self.db.commit()

    def action_count(self, channel: str, action: str, result: str | None = None) -> int:
        query = "SELECT COUNT(*) FROM actions WHERE channel=? AND action=?"
        args: list[str] = [channel, action]
        if result:
            query += " AND result=?"
            args.append(result)
        return int(self.db.execute(query, args).fetchone()[0])

    def counts(self) -> dict[str, int]:
        rows = self.db.execute("SELECT state, COUNT(*) AS n FROM leads GROUP BY state").fetchall()
        return {row["state"]: row["n"] for row in rows}

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
            metadata=json.loads(row["metadata"] or "{}"),
        )
