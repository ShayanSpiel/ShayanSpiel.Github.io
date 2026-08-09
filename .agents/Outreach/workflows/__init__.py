"""Workflow contract: the seam between the loop and a domain bundle.

The engine (engine/) only knows this contract. A workflow bundle is a plain
set of callables plus its goal spec. Installing a new workflow (email,
content marketing, social, ...) means registering another bundle — the loop,
the state machine, the artifacts, and the policy substrate never change.

Contract:

  name           — unique workflow id (e.g. "email")
  goal           — domain goal spec dict: {name, metric, target,
                   evidence_window_hours, min_sample} (human-owned via
                   data/control.json)
  observe(ctx, quick=False)
                 — OBSERVE: produce a snapshot dict. quick=True skips
                   expensive collection (used by ACT's GATE for a fresh
                   re-check before execution).
  decide(ctx, snapshot)
                 — DECIDE: produce an intervention dict or None
                   (None = no action; the loop holds).
                   Intervention: {action: "prepare_batch"|"hold"|"stop",
                   variable, detail, prediction, levers}
  prepare(ctx, intervention)
                 — ACT/PREPARE: build the batch artifact dict
                   {id, hypothesis, emails: [...], skipped: [...]}.
  validate(ctx, batch)
                 — ACT/VALIDATE: mechanical artifact rules. Returns a list
                   of issues; each issue is {lead_id, code, message,
                   skippable} — skippable issues drop the email, others
                   hold the batch.
  execute(ctx, batch, dry=False)
                 — ACT/EXECUTE: run the action (paced sends, publishes,
                   API calls). Returns {sent, failed, skipped, note}.
  measure(ctx, batch)
                 — EVALUATE/MEASURE: outcome metrics + verdict vs baseline.
                   Returns {metrics, verdict: {verdict, reason, ...}}.
  learn(ctx, intervention, verdict)
                 — EVALUATE/LEARN: persist the verdict into STATE knowledge.
  goal_check(ctx, metrics)
                 — EVALUATE/GOAL CHECK: returns {"state": "achieved" |
                   "not_yet" | "blocked", "detail": "..."}.
  policy(ctx, snapshot)
                 — POLICY rules (domain guardrails). Returns {"ok": bool,
                   breaches: [...], problems: [...]}. Evaluated softly at
                   OBSERVE and enforced hard at ACT/GATE on fresh state.
  report_lines(ctx, batch, outcome)
                 — optional: extra human lines for the EVALUATE report.
  report(ctx, batch, outcome)
                 — optional: domain data for the cycle journal/report:
                   {campaign, providers, example, guardrails, window, leads}.
                   Runs on local files only; must never raise.
"""

from dataclasses import dataclass, field
from typing import Any, Callable

REGISTRY: dict[str, "Workflow"] = {}


def import_all() -> None:
    """Import every installed bundle so its workflow registers itself."""
    from . import email  # noqa: F401, E402
    _ = email  # keep the import named for linters


@dataclass
class Workflow:
    name: str
    goal: dict
    observe: Callable
    decide: Callable
    prepare: Callable
    validate: Callable
    execute: Callable
    measure: Callable
    goal_check: Callable
    policy: Callable
    learn: Callable = None
    report_lines: Callable = None
    report: Callable = None
    describe: str = ""


def register(workflow: Workflow) -> Workflow:
    REGISTRY[workflow.name] = workflow
    return workflow


def get(name: str) -> "Workflow":
    if name not in REGISTRY:
        raise KeyError(
            f"workflow '{name}' is not registered (registered: {sorted(REGISTRY)})")
    return REGISTRY[name]
