# SpielOS Outbound — Orchestration Contract (2026-08-08)

## The engine has two parts, and the AI is part of it

1. **AI Orchestrator (the manager)** — prepares, decides, and reflects:
   - Lead work: check, qualify, research, verify, ingest (web research + staging drops)
   - Content: per-lead research → `personalization_hook`, `pain_hypothesis`,
     `suggested_cta` → composed per lead by `compose_researched()`
   - Experiments: form a hypothesis, set variables (throttle, min_tier, variants,
     segment focus, subject banks), run, pull data, reflect, tweak, next experiment
   - Every cycle is journaled in `orchestration/journal.md`
2. **Daemon (the executor)** — deterministic only:
   - Runs blocks (queue → content guard → send_batch pacing → metrics → core cycle)
   - Never decides strategy. It holds when it cannot send (gate, empty queue, cap)
     and says so in `status.json` / emails — the orchestrator acts on that
   - Supervisor (`supervise.sh`) only keeps the executor alive; it never decides

## Cadence (owner rule 2026-08-08)

SEND → STOP → CHECK → REFLECT → TWEAK → NEXT EXPERIMENT → REPEAT, until goal.
Goal: 200/day capacity within the warmup ramp, reply rate trending up, bounce < 2%.

- Blocks: BLOCK_SIZE emails @ THROTTLE_SECONDS (~2h)
- After each block the orchestrator (AI) pulls metrics, reads report.md,
  journals a reflection, sets the next experiment's variables
- The AI checks in every 1-2h, or whenever status.json changes

## Decision authority

| Thing | Owner |
|---|---|
| Lead intake, qualification, verification | AI |
| Per-lead content | AI |
| Variables: min_tier, throttle, variants, subject banks, experiment params | AI (via state.json + journal) |
| Batch execution, pacing, dedupe, provider picking | Daemon (deterministic) |
| Guardrail halts (gate) | Daemon triggers; AI resolves (fix data, adjust cohort) |
| Bounce lever / min_tier flips | Engine applies evidence-based lever; AI can override with a journaled reason |

## Artifacts

- `orchestration/journal.md` — every AI cycle: hypothesis, variables, data, reflection, next action
- `experiments/report.md` — metrics + goal status
- `harness/state.json` — variables the engine reads (min_tier, cohort_filters, notes)
- `scripts/experiments/auto/pipeline.log` — executor log
- `scripts/experiments/auto/status.json` — live status (emails surface on change)

## The loop in one line

AI researches + qualifies + writes content + designs experiment → daemon executes the
batch → AI pulls data, reflects, journals, tweaks → repeat until the goal is hit.
