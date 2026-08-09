# Orchestration Journal

Durable record of every AI orchestration cycle. Append, never rewrite.
Format: hypothesis → variables → action → data → reflection → next.

---

## Cycle 2026-08-08 (warmup day 2/14) — experiment #1: published-founder-email cohort

**Hypothesis:** Web-researched leads with *published founder/CEO emails*
(e.g. nick@lodestonerecruitment.co.uk, listed on their own site) will beat
role-address sends on open+reply, because (a) they are personal addresses the
founder actually reads, (b) they carry real research (company, segment, role).

**Variables set:**
- min_tier = plausible (new cohort is "Publicly listed; not deliverability-verified")
- throttle = 144s (unchanged — protect domain, warmup ramp)
- cohort: 24 recruitment/staffing agencies (UK 8, UAE 2, CA 9, AU 5) + 25th skipped as invalid

**Action:**
- 17:05 block: 12 old-cohort leads dispatched (executor)
- 17:15: 24 leads web-researched, ingested to master, L2-probed (23 plausible, 1 invalid)
- Now: writing per-lead content (hook + pain_hypothesis + cta) for the 24

**Data (at 17:15 UTC):** 128 sent today · bounce window 6.43% (breach, 11 bounces —
all suppressed) · open 32.7% · delivered 57.3% (bounces drag it) · 0 replies yet

**Reflection:** Bounce breach is entirely from the unverified tier; the lever will
raise min_tier=verified after this block's cycle — that is correct behavior, and the
24 new leads must earn Verified via probe/quality before they send at scale. If the
block finishes with 0 new bounces, consider releasing min_tier with a journaled reason.

**Next:** finish hooks → update master → verify compose_researched renders → block done
→ metrics → reflect → decide min_tier + next experiment (throttle or subject-bank A/B).

---

## Cycle 2026-08-08 (same day) — block 1 closed, experiment cohort live, store wired

**Hypothesis (unchanged):** published-founder-email cohort beats role-address on
open+reply — now actually being tested (block 2).

**Variables:** min_tier stayed `plausible` (the lever did NOT flip: after
sync-bounces, cycle totals exclude suppressed bounces → no breach in totals).
throttle 144s unchanged.

**Actions:**
- 17:38 block 1 closed: 12/12 sent, 0 failed (old cohort — that pool is now exhausted)
- 17:15–17:20 content pass: personalization_hook + pain_hypothesis + suggested_cta
  written for all 25 web-researched leads → compose_researched renders all (verified
  on 4 spot-checks + 23/23 unique-domain check)
- 17:45 bug found & fixed: ingest had written my CSV `source` value into the
  `language` column → English filter excluded all 25 → queue empty. Fixed 25 rows
  (language=English), re-queued, restarted daemon.
- 17:49 block 2 live: 25/25 standards, 0 skipped — the experiment cohort
- 18:05 canonical orchestration record wired: `.agents/Outreach` store seeded
  (25 leads ready, icp_score 92, research_fact + consequence + rendered message),
  goal `email-warmup-d2-200` (target 200/day, queue_target 100), policy gate
  passes all 25 (`next email` → Nicholas Brennan / Lodestone)
- Daemon hold paths now journal `EXECUTOR → AI:` markers (cap-reached /
  queue-empty / gate-blocked) instead of silently re-checking

**Data (18:05):** 128+12 sent today · block 2 at 7/25 · bounce window 6.43% (11 bounces,
all suppressed, from the old scraped tier) · 0 replies so far

**Reflection:** The language-column bug means the ingest's CSV mapping must be
checked before every cohort drop — add to checklist. Bounce lever stayed off only
because suppressed bounces drop out of totals; if ANY new bounce appears from the
experiment cohort, flip min_tier=verified immediately (journaled reason).

**Next:** block 2 done ~18:50 → metrics → reflect (cohort bounces/opens vs block 1)
→ discovery pass for next cohort (~35 slots remain under today's 200 cap) →
decide throttle experiment for day 3.

---

## Cycle 2026-08-08 (same day, 18:19 UTC) — cohort 2 discovered, ingested, ready

**Hypothesis:** same published-founder-email thesis; cohort 2 widens the test across
UK engineering/construction (11), Canada (1), Australia (7), New Zealand (7), UAE (1).

**Actions:**
- 2 web-search rounds: UK engineering/construction + UAE + NZ + AU legal/finance/tech
- Built cohort2 CSV with csv.DictWriter (guaranteed header alignment — the cohort-1
  language-column bug is a checklist item: verify alignment after every ingest)
- 27/27 ingested, 0 skipped, 0 invalid after L2 probe (all Plausible)
- Content: hooks + CTAs carried in CSV, pain_hypothesis written 27/27 via
  orchestrate_content2.py → compose_researched renders 8/8 spot-checked
- Outreach store re-seeded: 52 leads ready (cohort 1 + 2), 0 policy-blocked,
  goal email-warmup-d2-200 unchanged
- Discovered but skipped (no published personal email): Search Selection UK,
  Campbell Brown, Lily Shippen, Mackie Myers, Magellan Talent, BoldHouse,
  Richardson Executive Search, Latitude Recruitment (form-only or generic boxes)

**Data (18:19):** block 2 at 12/25 · sent today 152 · bounce window 6.43% (old tier,
suppressed) · 0 replies

**Reflection:** Cohort 2 is the same evidence class as cohort 1 (published personal
emails, niche-researched) so it stays in the same experiment — no new variables.
Queue ~27 sends left today before the ~200 cap; daemon will hold at cap-reached and
journal. If cap hits, tomorrow's capacity planning starts from the day-2 metrics.

**Next (~18:52):** block 2 metrics → reflect on cohort 1 opens/bounces → confirm
queue picks cohort 2 → cap-reached hold → journal → plan day 3 (throttle or
subject-bank A/B as the next experiment).



- **2026-08-08 22:50 UTC — AI → ENGINE (first live wake cycle):** Received the batch-done event in-session (the loop works end-to-end: daemon → log → hook → API POST → orchestrator). Post-batch routine:
  - **Observed:** refusal-loop era over — n-bug fixed (14/14 slots sent tonight, not stuck at 50). engine.json knobs live (block_size=20, throttle=120). Gate OK (bounce window healed under 2%) — only the 87 unverified / 31 unresolved data problems remain, being repaired by the metrics --force run (per-provider lookups).
  - **Found + fixed:** hook replayed 4 historical batch events on first boot (offset seeded to 0). Seeded offset to end-of-log; old hook process killed by pid (pkill -f couldn't reach it from the agent sandbox).
  - **Queue:** 49 ready (all Company website) ≈ 2.5 blocks — supply-low expected tomorrow; day-end event will decide the discovery pass.
  - **Decision:** no content experiment tonight — measurement repair first (true baseline from metrics --force), then the day-end event plans tomorrow's experiment. Failed[] reconciliation + brevo status lookups are live in the new code.

- **2026-08-08 23:10 UTC — AI → ENGINE (baseline pass):** `metrics --force` completed with two fixes: (1) Brevo endpoint corrected — `/v3/smtp/logs` returns 404 "Invalid route/method"; real endpoint is `/v3/smtp/statistics/events?messageId=...` (verified: filter scopes events correctly). Brevo sends now measurable. (2) Resend fast path — one `GET /emails?limit=100` call carries `last_event` for all recent sends (per-email lookups were ~8s each; full collect took 15+ min and was timing out). Collect now completes in minutes.
  - **TRUE BASELINE (checked 23:04, 240 all-time sends, all providers):** accepted 240/240 (100%) · delivered 190/240 = **79.2%** (old "87%+" was inflated — brevo was invisible) · bounced 12/240 = **5.0%** all-time (above 2% limit; window-check passed — early-era bounces) · spam 1/240 = **0.4%** (above 0.08% limit — 1 complaint, watchlist) · opened 86/190 = **45.3%** (strong for cold; GOAL_OPEN_RATE=0.80 default is misconfigured — real ceiling ~50%) · clicked 11/190 = **5.8%** (above 5% goal ✓) · replied **0/240** (the real gap — reply-capture verification + reply-focused experiment needed) · unresolved 31 (legacy no-id entries, Aug 7 era).
  - **Decision:** measurement repair DONE — this is the honest baseline the loop runs on. No content experiment tonight. Day-end event owns: (a) tomorrow's experiment targeting reply rate, (b) supply pass (queue 49 ≈ 2.5 blocks — need ~150 more for 200/day), (c) GOAL_OPEN_RATE → 0.50, (d) spam-complaint identification. Block status: 197/200 sent, 3 remaining → cap-hold → day-end wake pending.

- **2026-08-08 23:20 UTC — EXECUTOR → AI:** daily cap reached (200/200) — AI: decide next experiment before UTC midnight

- **2026-08-08 23:30 UTC — AI → ENGINE (DAY-END decision, warmup day 2 → 3):** Cap reached 200/200 (14-block completed, cap-hold sleeping 0.7h). Day 2 recap: refusal-loop era (n-bug) dead, 200/200 sent, true baseline landed (79.2% delivered, 45.3% open, 5.8% click, 0 replies, 5.0% bounce all-time, 1 spam complaint).
  - **Experiment for day 3 — reply-rate-r2:** attack the 0/243 reply gap. Control: researched-personal as-is (51.2% open — clear winner). Test: researched-personal-r2 (reply-focused rewrite: only-this-lead-can-answer question per Rule 3, offer sharpened to the placement-loop pilot per Rule 7, zero generic filler per Rule 4). Split 50/50 at queue build. Metric: reply rate (goal 30%); guard: open ≥ control − 10pts. Loser variants (scarcity 28.6% open, pilot/curiosity 0% opens) get no spend.
  - **Knobs (engine.json, written):** block_size 20 (keep — wake cadence), throttle_seconds 120→150 (warmup caution after 0.41% spam flag; 200 × 2.5min ≈ 8.3h → done ~08:30 UTC). experiment key documents the arm + guardrails for the loop.
  - **Supply:** 49 ready + ~67 EN eligible in master ≈ 116 of 200. Shortfall ~85. Plan: discovery session for ~85-150 researched EN leads (ICP: recruitment firms, published founder/CEO/MD emails — same shape as cohort2/webresearch files) → leads.py ingest → staging → refill; daemon refills at empty mid-day if needed.
  - **Watch items:** spam-complaint sender id (identify tomorrow from provider data); 17 n-bug-era failed sends retryable into tomorrow's cap; 31 unresolved + 1 unverified (data debt — next metrics --force after day-3 sends); GOAL_OPEN_RATE 0.80→0.50 calibration proposed (45.3% actual is strong; 80% unreachable → loop would chase ghosts).

- **2026-08-09 00:00 UTC — EXECUTOR → AI:** gate blocked: bounce rate 4.94% > 2.00%; spam rate 0.41% > 0.08% — AI: resolve (sync bounces, adjust cohort, or override with a reason)

- **2026-08-09 02:02 UTC — ENGINE → AI (reflection due):** test-batch sent 10 · skipped 3 · evidence at /Users/shayan/ShayanSpiel.Github.io/.agents/Outbound/experiments/reflection.md

- **2026-08-09 11:06 UTC — ENGINE → AI (reflection due):** test-batch sent 243 · skipped 0 · evidence at /Users/shayan/ShayanSpiel.Github.io/.agents/Outbound/experiments/reflection.md

- **2026-08-09 11:18 UTC — ENGINE → AI (reflection due):** auto-2026-08-09-b01 sent 243 · skipped 0 · evidence at /Users/shayan/ShayanSpiel.Github.io/.agents/Outbound/experiments/reflection.md

- **2026-08-09 11:18 UTC — EXECUTOR → AI:** approval needed for auto-2026-08-09-b01: review /Users/shayan/ShayanSpiel.Github.io/.agents/Outbound/scripts/experiments/auto/auto-2026-08-09-b01.preview.md and set engine.json approval before the engine sends

- **2026-08-09 11:31 UTC — ENGINE → AI (reflection due):** auto-2026-08-09-b01 sent 243 · skipped 1 · evidence at /Users/shayan/ShayanSpiel.Github.io/.agents/Outbound/experiments/reflection.md

- **2026-08-09 11:45 UTC — AI → ENGINE (architecture rebuild, owner-directed):** The engine was stopped, inventoried end-to-end, and rebuilt around the goal loop (Goal → Observe → Decide → Choose worker → Act → Measure → Reflect → Repeat/Stop). What was actually broken and fixed:
  - **Stale daemon:** the 2:10AM daemon imported harness/core.py before the spam-override landed — it had been gate-blocked for 14+ hours on dead logic while fresh code on disk passed. Engine restarted with current code.
  - **The core cycle was silently dead in the engine:** the `python3 ../harness/core.py` subprocess always died with ModuleNotFoundError (harness package not on path) and stderr was swallowed — DIAGNOSE/LEARN/APPLY never ran inside the loop. Fixed core.py's sys.path.
  - **Guardrail contradiction:** cycle judged ALL-TIME totals (old-era 4.9% bounce → clamps queue to verified) while the gate judges the 48h window with suppression → the loop fought itself. Now the GATE is the single guardrail authority; cycle diagnosis runs on window totals.
  - **Calibration:** state.json goal reply target 0.50 → 0.30 (owner goal), open target 0.80 → 0.50 (real ceiling ~46-50%; 80% made the loop chase ghosts).
  - **Observation was 15+ min per collect:** mailgun did up to 9 raw-DNS-transport calls per email; status fetches used send-grade retries. Now: mailgun single call, retries=1 for status, 48h-window bound + 1h TTL skip, progress saves every 50 emails.
  - **Content pipeline:** em dashes in research columns blocked the whole EN queue (silent fallback ban) → normalized to commas at render (guard still validates). Persian template links tripped the EN-only http rule → rule is now EN-only (FA ladder is owner-prepared copy). Queue is EN-first (market), FA tail. Duplicate domains deduped per batch (Plethora×2 caught).
  - **Reflection wired into the loop:** run_reflection evidence + preview now written BEFORE every send; approval gate: first block of an experiment sends only after the orchestrator reviews the preview (engine.json approval) — the hook wakes the session with an approval event.
  - **Goal-stop added:** reply ≥ 30% with gate OK → engine holds until midnight, orchestrator decides next goal.
  - **Dead code removed:** orchestrate_content.py / orchestrate_content2.py / discover_cohort2.py deleted (superseded); legacy batches archived to experiments/archive/batches/.
  - **State:** min_tier=plausible restored (gate OK), subject banks repaired (empty {} no longer masks defaults), batch auto-2026-08-09-b01 (49 emails) built and APPROVED by the orchestrator after preview QA. Awaiting the metrics collect to complete, then the engine re-arms and the first block sends.

- **2026-08-09 12:16 UTC — ENGINE → AI (reflection due):** auto-2026-08-09-b01 sent 244 · skipped 1 · evidence at /Users/shayan/ShayanSpiel.Github.io/.agents/Outbound/experiments/reflection.md
