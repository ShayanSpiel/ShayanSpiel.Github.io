# SpielOS Outbound — Orchestration Contract (2026-08-09)

The engine lives in `.agents/Outreach/`. The campaign directory stays in
`.agents/Outbound/` (master xlsx, `.env`, execution ICP). The legacy daemon,
`harness/`, `scripts/` (pipeline, send_batch, leadgen) were archived to
`.agents/Outbound/archive/2026-08-09-legacy/` — nothing under archive/ is read
by the engine.

## The loop (2026-08-09 — the state machine, not the old daemon)

One `python3 -m Outreach once` advances the loop as far as it can WITHOUT a
human, then parks. Manual cadence — nothing runs by itself.

```
observe → decide → prepare → validate → gate → review → execute → evaluate → hold
              ↑_______________________________________________________|  (owner GO)
```

| Phase | What happens | Parks at |
|---|---|---|
| observe | Filtered, timestamped snapshot (totals, window, gate verdict, queue, caps, providers) | — |
| decide | One intervention from the snapshot + knowledge (or hold/stop verdict) | — |
| prepare | Build the batch artifact + human preview (strict per-lead composition) | — |
| validate | Mechanical artifact rules (drop invalid emails) | — |
| gate | POLICY hard veto on a FRESH observation (bounce/spam/delivery guardrails) | — |
| review | Human approval of the preview | **review** — `approve` |
| execute | Paced sends (cap honored, provider rotation, dedupe), arm the evidence window | — |
| evaluate | Wait for evidence, then MEASURE + LEARN + GOAL CHECK + report | **evaluate** — time |
| hold | Parked; owner GO starts the next batch cycle | **hold** — `approve --next` |
| goal_met | Terminal; new goal in control.json + `reset` starts over | — |

The old loop was `SEND → STOP → CHECK → REFLECT → TWEAK → NEXT EXPERIMENT →
REPEAT` with a daemon + harness. That is dead. The new loop is the phase
machine above; reflection/experiment memory lives in the STATE knowledge store
(`Outreach/data/engine.sqlite`), not in a journal the AI edits by hand.

## Cadence (owner rule 2026-08-09)

1. `python3 -m Outreach once` — the engine streams one conversational line
   per step (`· observe — …`, `· decide — …`, `· gate — …`) so the operator
   sees exactly what is being run and evaluated as it happens.
2. At REVIEW it parks: `python3 -m Outreach approve` after checking the
   preview (`data/artifacts/preview-*.md`).
3. After EXECUTE it writes a categorized cycle entry to
   `Outreach/reports/journal.md` (sends, providers, a random example email,
   metrics, hypothesis-vs-goal analysis, leads pipeline) and prints it.
4. After the evidence window (`goal.evidence_window_hours`, default 48h),
   `once` runs EVALUATE: verdict, goal check, and an EVALUATE journal entry.
5. Between batches the loop holds; `python3 -m Outreach approve --next`
   releases it. `status` prints the full categorized report anytime.

## CLI

```
python3 -m Outreach once [--dry]      # advance the loop; streams step lines
python3 -m Outreach status            # phase + full categorized report
python3 -m Outreach approve [--next]  # review: approve batch · hold: owner GO
python3 -m Outreach stop / clear-stop # STOP kill-switch
python3 -m Outreach goal              # goal spec + knobs (data/control.json)
python3 -m Outreach reset             # fresh cycle from goal_met/hold/stopped
python3 -m Outreach record-reply <id> # log a reply (manual channel)
python3 -m Outreach stats             # campaign database stats
python3 -m Outreach verify <cmd>      # probe | probe-queue | audit | sync-bounces
python3 -m Outreach leads <cmd>       # ingest | merge | score | reclassify | lookalikes
```

## Decision authority

| Thing | Owner |
|---|---|
| Lead intake, qualification, verification, research | AI (via `leads ingest`, staging drops) |
| Per-lead content (hook, pain_hypothesis, CTA) | AI, per lead, before send |
| Variables: min_tier, cohort filters, block size, cap | Owner via `data/control.json` knobs |
| One intervention per cycle (subject rotation, cohort lever) | Engine DECIDE, evidence-based |
| Batch execution, pacing, dedupe, provider picking | Engine EXECUTE (deterministic) |
| Guardrail halts (gate) | Engine GATE on fresh observation; AI resolves |
| Verdicts (keep/reject/inconclusive) | Engine EVALUATE vs baseline batch |

## Artifacts

- `Outreach/data/status.json` — machine-readable phase/batch/hold state
- `Outreach/data/artifacts/` — snapshot / intervention / batch / preview per step
- `Outreach/reports/journal.md` — the cycle journal: one EXECUTE + one EVALUATE
  entry per batch, categorized (sends, providers, example email, metrics,
  hypothesis vs goal, guardrails, leads)
- `Outreach/reports/report-<batch>.md` + `REPORT.md` — EVALUATE verdict report
- `Outreach/reports/engine.log` — append-only engine log
- `Outreach/data/engine.sqlite` — STATE: phases, batches, knowledge (trials),
  action ledger

## The loop in one line

observe → decide → prepare → validate → gate → review → execute → evaluate →
hold → owner GO → next cycle, until the goal (reply rate 30%, 48h window) is met.
