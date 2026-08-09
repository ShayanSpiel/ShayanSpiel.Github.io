#!/usr/bin/env python3
"""
Harness — state: the single memory (experiments/state.json).

The whole loop's context lives in one file:
  meta       — goal, supporting KPIs, guardrails (human-owned targets)
  variables  — current lever values (engine-owned, applied at render time)
  knowledge  — per-lever history: tried? verdict? when? (kept/rejected/inconclusive)
  batches    — append-only records of every batch: hypothesis, lever, cohort,
               metrics, verdict

The AI reads this file before any decision; the engine writes it after every
measurement. No context lives only in a conversation.
"""

import json
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUTBOUND_DIR = os.path.dirname(HERE)
STATE_PATH = os.path.join(OUTBOUND_DIR, "experiments", "state.json")

# Human-owned targets (single source; env still overrides for the sending
# layer, but the goal engine reads these to compute distance to goal).
META = {
    "goal": {"name": "reply rate", "metric": "reply_rate", "target": 0.50},
    "supporting_kpis": [
        {"name": "delivered rate", "metric": "delivered_rate", "target": 0.99},
        {"name": "open rate", "metric": "open_rate", "target": 0.80},
        {"name": "click rate", "metric": "click_rate", "target": 0.05},
    ],
    "guardrails": [
        {"name": "bounce rate", "metric": "bounce_rate", "max": 0.02},
        {"name": "spam rate", "metric": "spam_rate", "max": 0.0008},
    ],
}


def default_state() -> dict:
    return {
        "version": 1,
        "meta": META,
        "variables": {
            "subject_patterns": {},      # segment -> active subject pattern id
            "cohort_filters": {},        # e.g. {"skip_unverified": false}
            "providers": [],             # active provider order
            "notes": {},                 # AI notes per variable (why)
        },
        "knowledge": {},                 # variable -> {"tried": [...], "verdict": ...}
        "batches": [],                   # append-only batch records
        "updated_at": None,
    }


def load() -> dict:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH) as f:
                state = json.load(f)
            state.setdefault("meta", META)
            state.setdefault("variables", {})
            state.setdefault("knowledge", {})
            state.setdefault("batches", [])
            return state
        except Exception:
            pass
    return default_state()


def save(state: dict) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, default=str)


def append_batch(state: dict, record: dict) -> None:
    state.setdefault("batches", []).append(record)
    save(state)


def last_batch(state: dict) -> dict | None:
    batches = state.get("batches") or []
    return batches[-1] if batches else None


def first_batch(state: dict) -> dict | None:
    batches = state.get("batches") or []
    return batches[0] if batches else None


def get_variable(state: dict, name: str, default=None):
    return state.get("variables", {}).get(name, default)


def set_variable(state: dict, name: str, value, note: str = "") -> None:
    state.setdefault("variables", {})[name] = value
    if note:
        state.setdefault("variables", {}).setdefault("notes", {})[name] = (
            f"{datetime.now(timezone.utc).isoformat(timespec='minutes')} — {note}"
        )
    save(state)


def record_knowledge(state: dict, variable: str, trial: dict) -> None:
    """Append a trial outcome to a variable's history:
    {"at", "from", "to", "target_metric", "before", "after", "verdict"}"""
    k = state.setdefault("knowledge", {}).setdefault(variable, {"tried": [], "verdict": None})
    k.setdefault("tried", []).append(trial)
    k["verdict"] = trial.get("verdict")
    save(state)


def knowledge_for(state: dict, variable: str) -> dict:
    return state.get("knowledge", {}).get(variable, {"tried": [], "verdict": None})
