#!/usr/bin/env python3
"""
Harness — variables: the lever registry (engine-owned, data not code).

The engine can ONLY touch things declared here. Every lever has: a storage
location (scripts/content_variables.json for copy, state.json for filters),
bounds, and a change log. This is the anti-drift contract: a variable change
is a one-key edit to a JSON the renderer reads — never a code rewrite.

Levers today (emails):
  subject          — active subject patterns per segment (rotated per lead)
  body             — body variant set per segment (reserved)
  cta              — question/close variant per segment (reserved)
  cohort_unverified— include/exclude unverified emails in the queue
  providers        — active provider order
"""

import json
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUTBOUND_DIR = os.path.dirname(HERE)
CONTENT_FILE = os.path.join(OUTBOUND_DIR, "scripts", "content_variables.json")

REGISTRY = {
    "subject": {
        "file": CONTENT_FILE,
        "key": "subject_patterns",
        "bounds": {"min_active": 2},
        "changed_at": None,
        "note": "active subject patterns per segment; renderer rotates per lead",
    },
    "body": {
        "file": CONTENT_FILE,
        "key": "body_variants",
        "bounds": {"min_active": 1},
        "changed_at": None,
        "note": "reserved: body variant sets per segment",
    },
    "cta": {
        "file": CONTENT_FILE,
        "key": "cta_variants",
        "bounds": {"min_active": 1},
        "changed_at": None,
        "note": "reserved: question/close variants per segment",
    },
    "cohort_unverified": {
        "file": None,  # lives in state.json variables
        "key": "cohort_filters:skip_unverified",
        "bounds": {"type": "bool"},
        "changed_at": None,
        "note": "exclude 'Publicly listed; not deliverability-verified' emails",
    },
    "providers": {
        "file": None,
        "key": "providers",
        "bounds": {"type": "list"},
        "changed_at": None,
        "note": "active provider order (from .env SEND_PROVIDERS)",
    },
}

DEFAULT_CONTENT = {
    "subject_patterns": {
        "recruitment-workflow": [
            "Staffing loop at {company}",
            "Recruiting ops at {company}",
            "Screening loop at {company}",
            "Shortlist stage at {company}",
        ],
        "agency-delivery": [
            "Delivery loop at {company}",
            "Client work at {company}",
            "Handoff time at {company}",
            "Drafts at {company}",
        ],
        "saas-ops": [
            "Support loop at {company}",
            "Inbox triage at {company}",
            "Request queue at {company}",
        ],
        "generic-workflow": [
            "One workflow at {company}",
            "Manual loop at {company}",
            "Repetitive work at {company}",
        ],
    },
    "body_variants": {},
    "cta_variants": {},
}


def load_content() -> dict:
    if os.path.exists(CONTENT_FILE):
        try:
            with open(CONTENT_FILE) as f:
                data = json.load(f)
            # Anti-drift merge: an EMPTY bank must not mask the defaults —
            # an empty subject_patterns {} silently disables the subject
            # lever (the renderer falls back to generic subjects forever).
            for k, v in DEFAULT_CONTENT.items():
                if k not in data or not data[k]:
                    data[k] = v
            return data
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_CONTENT))


def save_content(data: dict) -> None:
    with open(CONTENT_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def active_subjects(segment_key: str) -> list:
    data = load_content()
    bank = data.get("subject_patterns", {}).get(segment_key)
    if not bank:
        bank = data.get("subject_patterns", {}).get("generic-workflow", [])
    return bank


def set_subject_bank(segment_key: str, patterns: list, note: str = "") -> None:
    data = load_content()
    data.setdefault("subject_patterns", {})[segment_key] = patterns
    save_content(data)
    if note:
        REGISTRY["subject"]["changed_at"] = datetime.now(timezone.utc).isoformat()
        REGISTRY["subject"]["note"] = note


def subject_bank_for(label: str, content: dict | None = None) -> list:
    """Map pipeline segment labels to the subject bank; fall back to the
    generic bank so the renderer never crashes on an unknown segment."""
    data = content or load_content()
    return data.get("subject_patterns", {}).get(label) or data.get(
        "subject_patterns", {}).get("generic-workflow", [])
