# Handoff — Receipt-Ledger narration routing enforcement (session status)

**Date:** 2026-08-30 08:40 UTC

## Goals in this session

- **Re-record goal `goal-9428806afb`** — "Videography — Receipt → Ledger capture
  re-record + postprod fix (result visibility, screens, pacing sync, better
  narration copy, invoice fixture)" — owner `videography` — **PAUSED by owner**.
- **Routing goal `goal-84e845dfed`** — "Enforce narration routing: every
  narration ask for a workflow demo routes through the demo-owner
  narration.json contract" — owner `system-improvement`, change task
  `change-27a1382b30` (approved, `change_kind=repair`) — this session's repair.

## Owner decision this session

Narration copy for the receipt-ledger re-record was **rejected twice** by the
owner. The owner stopped the copy work, stating: **"we will continue this in
another session"**. The re-record goal was therefore **paused**. No narration
copy was written this session and none should be written until the next session.

## Root cause found

- The canonical narration contract was bypassed:
  `.agents/company/departments/design/templates/video/narration.json`
  (`tone_contract`, `mix`, `scene_timing` `narration-led-v2`, `quality_gates`)
  is the required contract for all narration work.
- The v5-referenced `demo-narration.json` 11-scene structure file is
  **missing from the repo**. It was lost in the finals-only cleanup on
  **2026-08-29**, the same cleanup that also deleted the postprod `.py`
  sources and `example-invoice.png`. No `demo-narration.json` reference
  resolves anywhere under `scripts/` today.
- Drafts substituted a **made-up JSON shape** (bespoke
  `{strategy, voice, note, segments}`) instead of the demo-owned
  narration.json runtime instance shape
  (`voice, provider, model, mode, total_duration, strategy,
  segments[{index, scene, text, keywords, start, end, duration, path}],
  narration_wav`).

## Routing rule now enforced (this goal)

The videography skill now contains an explicit **narration routing** pipeline
step (between `author` and `record`, and referenced in the operating commands):
every narration ask for a workflow demo resolves the demo-owned narration
instance (`.spielos/artifacts/videography/{workflow}/narration.json`, mirrored
by `scripts/videography/scenarios/{workflow}-narration-*.json`) before drafting
any copy. The canonical contract
`.agents/company/departments/design/templates/video/narration.json` is required
reading. **No ad-hoc narration JSON shapes.** A Guard was added: "Never draft
narration copy outside the demo-owned narration.json instance shape; a
narration ask always routes through that instance."

## Environment status (verified 2026-08-30)

- ActivePieces self-hosted at `http://localhost:8080` is **live** (HTTP 200 on
  root).
- Flow `9cC7eE7Q0btMTzl99R4rt` — "Receipt — Ledger Capture & Coding" — is
  **reachable** (HTTP 200 on its form URL).
- Upload step support was **restored** by goal-63e11fe96b (recorder `upload`
  branch + tests).
- Fixture `scripts/videography/fixtures/example-invoice.png` was **recreated**:
  194KB (198,357 bytes), 1588x2246 PNG, with embedded invoice-text tEXt chunk.
- Postprod modules exist **only as `.pyc`** under
  `scripts/videography/postprod/__pycache__/` (audio_analysis, compose, config,
  narration, overlay2, etc.) — **revivable from bytecode, but `.py` sources
  are missing** and must be restored before postprod can run.

## Next session resume steps

1. **Resume goal-9428806afb** (paused — do not auto-resume; owner restart).
2. **Re-author narration copy** in the recruitment-showcase register
   (identity/intro/transitions/context per demo workflow copy, mirroring
   `flow-wJH1m-test.json` reads).
3. **Get owner Gate-1 approval BEFORE any TTS or recording** (show the
   narration copy + voice provenance).
4. Voxtral TTS (chain `gemini → voxtral → cartesia → elevenlabs`;
   `voxtral-mini-tts-latest` / `en_paul_confident`).
5. Record v6: upload fixture, result hold, **stop at `05-result`** (no Drive
   auth click/mention).
6. Postprod: `envelope` → `overlay2.render_full_overlay` →
   `compose.compose_single`.
7. Owner preview → Buffer.

## Explicitly out of scope

No invented metrics, no business conclusions, no copying lines of the rejected
drafts, no silently resuming the paused re-record goal.