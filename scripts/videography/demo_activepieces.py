"""Build the humanistic scenario for the ActivePieces demo workflow.

Target: order demo-20260826-job-brief-shortlist
  flow id BA9NmW1ddSRvBd6BQ6VPT (self-hosted instance at http://localhost:8080)

Two capture modes:
  form   — drive the published web form (login-free if form is public)
  editor — open the flow editor, run it, watch logs, show the result (needs session)

The scenario is data (JSON) by design: recording a different demo later means a
new scenario file, never new recorder code.
"""
from __future__ import annotations

import json
from pathlib import Path

ACTIVEPIECES_BASE = "http://localhost:8080"
BRIEF = (
    "Senior Backend Engineer, Manchester, UK. £70-80k. "
    "Python, Django, PostgreSQL, AWS. 5+ years. Hybrid, 2 days on-site."
)

CONFIG_PATH = Path(__file__).resolve().parents[3] / ".spielos" / "videography" / "activepieces.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {"base_url": ACTIVEPIECES_BASE, "form_url": "", "flow_id": "BA9NmW1ddSRvBd6BQ6VPT"}


def scenario_form(form_url: str) -> dict:
    return {
        "name": "activepieces-job-brief-shortlist",
        "title": "Job Brief → Candidate Shortlist (ActivePieces demo)",
        "seed": 7,
        "personality": "careful",
        "viewport": [1440, 900],
        "steps": [
            {"type": "goto", "url": form_url},
            {"type": "wait", "seconds": 1.4},
            {"type": "read", "text": "Collecting the job brief."},
            {"type": "type", "selector": "textarea", "text": BRIEF},
            {"type": "read", "text": "Brief complete. Running the workflow."},
            {"type": "click", "selector": "button[type=submit], button:has-text('Submit')", "wait_after": 1.2},
            {"type": "wait_for", "selector": "text=/shortlist|match|rank/i", "timeout_ms": 60000, "wait_after": 1.5},
            {"type": "scroll", "selector": "body"},
            {"type": "read", "text": "The shortlist is ready."},
        ],
    }


def scenario_editor(base_url: str, flow_id: str) -> dict:
    return {
        "name": "activepieces-editor-run",
        "title": "ActivePieces editor run (authenticated)",
        "seed": 11,
        "personality": "careful",
        "viewport": [1440, 900],
        "steps": [
            {"type": "goto", "url": f"{base_url}/flows/{flow_id}"},
            {"type": "wait", "seconds": 2.5},
            {"type": "read", "text": "Opening the workflow we built for Client Delivery."},
            {"type": "click", "selector": "button:has-text('Run'), button[data-testid='run-button']", "wait_after": 1.0},
            {"type": "wait_for", "selector": "text=/run|success|complete/i", "timeout_ms": 90000, "wait_after": 2.0},
            {"type": "scroll", "selector": "body"},
            {"type": "read", "text": "The workflow ran end-to-end."},
        ],
    }


if __name__ == "__main__":
    cfg = load_config()
    print(json.dumps(scenario_form(cfg.get("form_url") or "<set form_url>"), indent=2))
