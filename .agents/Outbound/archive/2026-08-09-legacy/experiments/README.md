# Outbound Experiments — memory for the hourly feedback loop

Goal: raise the single-touch reply rate to 30% (user target) or exhaust the
English sendable queue. Every hour: send 6 → wait 60 min → `metrics --force` →
append an experiment entry → apply ONE tweak → next batch.

## Files

- `experiment_log.json` — append-only log; each entry auto-attaches the real
  aggregate metrics (sent, delivered, open, click, reply rates; caps in force)
  plus `by_variant` breakdown, and the hypothesis text. Written by:
  `python3 outbound.py experiment --text "<hypothesis + what the data showed + next tweak>"`
- `batches/batch-*.json` — the send payloads (subject + full HTML/text bodies
  per lead) plus the batch hypothesis. Sent by:
  `python3 send_batch.py batches/batch-*.json [--dry]`
- `batches/batch-*.log` — live send output for each batch.

## Deterministic cadence (SKILL.md Part 4)

- 6 emails per batch, 1 email per 600 s (10 min) → ~60 min per batch.
- Daily cap: 50 during warmup (day ≤ 14), 60 (day 15–28), 100 (provider hard
  cap). Refuses to exceed; check `outbound.py` `daily_cap()`.
- After each batch: `metrics --force` → `experiment` → ONE tweak → next batch.
- Halt: bounce ≥ 2%, spam ≥ 0.08%, delivery < 99%, provider 429.

## English queue reality (2026-08-08)

- 38 sent before the loop started (Aug 7).
- Batch 1: 4 named researched leads (EN-002/003/030/043) + 2 routing-only
  (EN-001/084). After this batch the "Ready to personalize" / "Research and
  verify first" English tier is exhausted.
- Remaining English: ~152 routing-only (no names), 24 backup, 16 do-not-automate.
  Next decision point: expand to routing-only inboxes with team-greeting copy.
