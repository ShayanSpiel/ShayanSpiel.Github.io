# Handoff — Receipt Ledger Capture & Coding demo — REDO FROM SCRATCH

**Date:** 2026-08-29 12:30 UTC  
**Owner request:** Full redo. Current cut is fucked — sync early, audio volume/quality broken (amix normalization), Google auth inbox leaked on tail, copy not good. Do not patch. Start clean.

## What this workflow is (real delivered workflow)

- **Project:** `rw568MTpQWxjZAQXFOYu5` / Flow `9cC7eE7Q0btMTzl99R4rt` — "Receipt — Ledger Capture & Coding"
- **Trigger:** Form `http://localhost:8080/forms/9cC7eE7Q0btMTzl99R4rt?useDraft=true` (NOT /projects/.../flows), hidden file input `#receiptImage` with fixture `scripts/videography/fixtures/example-invoice.png`
- **Steps (must be shown step-by-step, with scroll):** Upload → Pixtral/AI extract vendor/amount/date/line items → AI map each line to GL chart of accounts → log to ledger Table → archive file to Drive → return summary with "Receipt captured" + "Open archived receipt"
- **Stand-in note (mandatory narration):** Ledger step uses **ActivePieces Table as stand-in for Xero / QuickBooks / Sage** — narration must call this out verbatim. Same fields, swapped in real client build.
- **ICP:** Segment #5 — Mid-market finance / heavy AP (100-1000 employees, 100s-1000s invoices/mo, buyer CFO/Controller/AP Director)

## What failed this round (save progress / do not repeat)

1. **Voice:** Used `say -v Daniel` (macOS). Correct is **Voxtral** via `scripts/tts-providers.js` → `voxtral-mini-tts-latest` / `en_paul_confident` (masculine low-register, master persona Charon). Chain is `gemini → voxtral → cartesia → elevenlabs`, keys in `.spielos/.env`. Voxtral test passed (`synthesize('mistral')` OK, 24kHz wav).
2. **Copy:** Improvised hook "Hi I'm Shayan, recept capture and blah blah" — meaningless. Correct method is `.agents/skills/company/copywriting-en` + `.agents/company/strategy/voice.md` + `icp.md`/`positioning.md` + `focus.md` → simulation → human_reality → discovery → draft. Must be pain-first (40 PDFs at 9am, copy-paste vendor/date/VAT, switch Outlook→PDF→ERP, remember GL codes, hunt PO), not founder intro.
3. **Timeline:** Original 164.6s raw, 2× sped to 82.37s, then trimmed to 63s + retimed narration 84s → final 84.07s. Target was 45s → owner corrected to **≥65s for Buffer** (whole video). Raw needs post-prod speed, not hardcoded 50s trim, not raw 164s.
4. **Sync:** Narration started 15s before Submit click (`seg5 38.2s` vs click 53.2s sped), 6s before processing. Fixed once by retiming (`seg5 44.84`, `seg6 53.46`, `seg7 65.92`) but audio mix broke.
5. **Audio quality:** Retimed `amix` without normalization → volume fucked. Previous Voxtral 77.42s direct concat was clean. Must use proper mix (no `amix` normalization loss, keep LUFS -16 / -1 dBTP as in `.agents/company/departments/design/templates/video/narration.json`).
6. **Privacy:** `click_same_tab` "Open archived receipt" navigated to real Drive auth and rendered inbox. Purged `demo-05b-drive-file.png`, trimmed tail. Next capture must **stop at `05-result` (Receipt captured)** — do not click Drive link. Stub Drive archiving as Table + summary only for demo.
7. **Artifacts state (as of 2026-08-29 12:30):**
   - `demo.mp4` 164.6s, `demo.webm`, `demo.steps.json` (159.3s log), `demo-sped-2x.mp4` 82.37s, `demo-sped-trimmed.mp4` 63.0s
   - `postprod/narration.json` 84.04s (retimed Voxtral), `narration.wav` (retimed amix, volume broken), `narration-voxtral-orig.wav` (clean 77.42s), `envelope.json`, `overlay-fix/` 2521 frames, `final-hybrid.mp4` 84.07s (current, broken audio), `final-hybrid.pre-voxtral.mp4` deleted
   - Scenarios: `receipt-ledger-narration-v3.json` (clean copy, 77.42s source), `receipt-ledger-narration-v3-retimed.json` (retimed schedule), `receipt-ledger-narration-v2.json` (old)

## Instructions update required

Current `.agents/skills/company/videography/SKILL.md` pipeline is `resolve → author → record → render` with no ordering for copy/narration vs recording and no 65s floor or sync contract. Update to:

**Proposed pipeline (owner order):**
1. **Scenario — mouse moves, workflow showcase, results step-by-step defined.** Author humanistic scenario JSON with explicit scroll to show all steps, mouse/cursor moves, shot names (`01-flow-overview`, `02-flow-steps`, `03-form-open`, `04-file-uploaded`, `05-result`), and no Drive auth click. Duration target ≥65s total (Buffer minimum). If not, trim speed post-prod, never by cutting narration sentences (`narration-led-v2` contract: measured clip durations + speech_lead 0.65s + minimum_visual_dwell).
2. **Copy + narration scenario — reproduce based on real workflow, show for confirmation.** Run `copywriting-en` simulation on real workflow (not generic), draft 10-segment script (≈70-85s, pain-first, stand-in note preserved), get owner confirmation before any TTS. Then synthesize via **Voxtral** chain only (`tts-providers.js`), provenance in `narration.json`.
3. **Record video from scratch.** `session.py` → `recorder.py --scenario <new> --out .spielos/artifacts/videography/receipt-ledger-capture-v2` — start by showcasing workflow (full scroll of steps), describe each step in sync with narration (narration drives timing, not wpm reads).
4. **Trim video speed, put narration on it, post-prod, done.** `setpts` speed to land ≥65s (e.g., 2× if raw >120s), trim tail before auth, regenerate `envelope.json` → `overlay2.render_full_overlay` → `compose.compose_single` (hybrid border 1440×900). Verify `ffprobe` h264 1440×900 / aac, duration ≥65s.

Add to Guards: never use `say`, never `amix` without loudness normalization, never publish Drive auth frame.

## Handoff for new session — steps to execute

### Step 1 — Reproduce copy & narration scenario (no render yet)
- Read: `icp.md` #5, `positioning.md`, `voice.md`, `focus.md`, `copywriting-en/SKILL.md`, `design/templates/video/narration.json` (tone_contract: masculine ALWAYS, no music, measured durations)
- Simulate real workflow (upload → extract → code → ledger Table → summary), write human_reality (what controller checks/copies/switches/waits/fixes/remembers), derive discovery, draft 10-segment copy (pain-first, stand-in note, no "Hi I'm Shayan" opener, compact)
- Write `scripts/videography/scenarios/receipt-ledger-narration-v4.json` + `receipt-ledger-scenario-v4.json` (scenario with scroll Steps 01-05, no Drive click)
- Synthesize **Voxtral** dry-run clips to `.spielos/artifacts/videography/receipt-ledger-capture-v2/postprod/` and present `narration.json` + text preview for owner **CONFIRMATION** — do not record until approved

### Step 2 — Show for confirmation (human gate)
- Post the 10 lines + total_duration + voice provenance (`en_paul_confident / voxtral-mini-tts-latest`) and the scenario JSON step list. Await owner "go".

### Step 3 — Record from scratch
- `python3 scripts/videography/session.py --url http://localhost:8080 --out .spielos/videography/activepieces-state.json` (owner login)
- `python3 scripts/videography/recorder.py --scenario scripts/videography/scenarios/receipt-ledger-scenario-v4.json --out .spielos/artifacts/videography/receipt-ledger-capture-v2 --headful --storage-state .spielos/videography/activepieces-state.json`
- `python3 scripts/videography/render.py .spielos/artifacts/videography/receipt-ledger-capture-v2.webm --out .spielos/artifacts/videography/receipt-ledger-capture-v2.mp4`
- Verify `demo.steps.json` (cursor, typed len, result_visible) + `ffprobe` duration

### Step 4 — Trim, sync, post-prod
- Speed: `ffmpeg -i demo.mp4 -filter:v "setpts=0.5*PTS" -an -r 30 demo-sped.mp4` (or tuned to hit ≥65s with narration)
- If raw tail contains Drive auth, `ffmpeg -t` trim to `05-result`
- Rebuild narration wav with correct delays (use `adelay` per segment start from approved schedule, then loudness-normalize to -16 LUFS, not raw amix)
- `audio_analysis.write_envelope` → `overlay2.render_full_overlay` (hybrid, 1440×900) → `compose.compose_single` → `final-hybrid.mp4`
- Verify `ffprobe` duration ≥65s, size, h264/aac, no auth frame, audio not clipped

## Files to carry over / discard

Carry: `example-invoice.png` fixture, Voxtral keys, `PostConfig` (hybrid), `voice.md` contract
Discard: `demo-05b-drive-file.png`, `demo-sped-2x.mp4` (recreate), broken `narration.wav` (use `narration-voxtral-orig.wav` as reference only), `final-hybrid.mp4` 84.07s (volume broken) — keep as `pre-redo` backup if needed

## Owner approval gates

1. Copy + narration scenario text (Step 1) — **MUST show, do not proceed to record**
2. Final MP4 preview (Step 4) — **MUST show, do not upload to Buffer**

