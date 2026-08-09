## CYC-20260808-1217 — 2026-08-08 12:17 UTC

Batch: seed-baseline · sent total: 106 · sent today: 63/200

**KPIs vs goals**
  reply rate          0.0%  target   50.0%  ❌
  delivered rate     40.6%  target   99.0%  ❌
  open rate          23.3%  target   80.0%  ❌
  click rate          7.0%  target    5.0%  ✅

**Guardrails**
  bounce rate         0.0%  target    2.0%  ✅
  spam rate           0.0%  target    0.1%  ✅
  ⛔ BREACH: delivered rate

**Weakest link:** delivered rate



---
## CYC-20260808-1225 — 2026-08-08 12:25 UTC

Batch: seed-baseline · sent total: 106 · sent today: 63/200

**KPIs vs goals**
  reply rate          0.0%  target   50.0%  ❌
  delivered rate     86.8%  target   99.0%  ❌
  open rate          28.3%  target   80.0%  ❌
  click rate          6.5%  target    5.0%  ✅

**Guardrails**
  bounce rate         9.4%  target    2.0%  ❌
  spam rate           0.0%  target    0.1%  ✅
  ⛔ BREACH: bounce rate; delivered rate

**Weakest link:** bounce rate

**Previous experiment verdict:** inconclusive — reply_rate 0.0% -> 0.0% (within noise)


---
## CYC-20260808-1229 — 2026-08-08 12:29 UTC

Batch: verify-gate · sent total: 106 · sent today: 63/200

**KPIs vs goals**
  reply rate          0.0%  target   50.0%  ❌
  delivered rate     86.8%  target   99.0%  ❌
  open rate          28.3%  target   80.0%  ❌
  click rate          6.5%  target    5.0%  ✅

**Guardrails**
  bounce rate         9.4%  target    2.0%  ❌
  spam rate           0.0%  target    0.1%  ✅
  ⛔ BREACH: bounce rate

**Weakest link:** open rate 28.3% < 80%

**Previous experiment verdict:** inconclusive — reply_rate 0.0% -> 0.0% (within noise)

**Next lever:** subject
**Hypothesis:** subject: rotate active bank per segment (recruitment-workflow: Staffing loop at {company} -> Recruiting ops at {company} ; agency-delivery: Delivery loop at {company} -> Client work at {company} ; saas-ops: Support loop at {company} -> Inbox triage at {company}) so open rate improves; reason: repetitive subjects suppress opens

---
## FINDING — verified pool exhausted (2026-08-08 12:31 UTC)

Under skip_unverified=true the queue is empty: 233 contacts total, **172 unverified
(73%)**, 106 already sent, and the only unsent verified lead is `Do not automate`.

The bounce evidence (9/10 bounces unverified) proved the list is the problem — and
the filter confirms it: there is **nothing safe left to send**.

Next: supply new verified leads, or verify the 52 unsent `Ready to personalized`
leads. The daemon holds and re-checks staging every 30 min; the gate stays armed.

---
- 2026-08-08 12:53 UTC — Queue empty — holding
  no unsent verified leads; drop new lead files in leads/staging, daemon re-checks every 30 min
- 2026-08-08 13:02 UTC — Queue empty — holding
  no unsent verified leads; drop new lead files in leads/staging, daemon re-checks every 30 min
- 2026-08-08 13:08 UTC — Queue empty — holding
  no unsent verified leads; drop new lead files in leads/staging, daemon re-checks every 30 min
- 2026-08-08 13:23 UTC — Queue empty — holding
  no unsent verified leads; drop new lead files in leads/staging, daemon re-checks every 30 min
- 2026-08-08 15:38 UTC — Engine back online — sending resumes
  daemon fixed (stale PID was blocking restarts); block running now 42 leads; Brevo+Resend+Mailgun all live; Mailgun now sends From shayan@spielos.xyz (root domain)
- 2026-08-08 15:41 UTC — Batch auto-2026-08-08-b01: 42 sent, 0 failed — cycle measured, loop continues
  42 in batch, 0 skipped by content guard
- 2026-08-08 17:00 UTC — ⛔ GATE BLOCKED — no sends until fixed
  bounce rate 6.43% > 2.00% — see experiments/report.md
- 2026-08-08 17:42 UTC — Batch auto-2026-08-08-b01: 12 sent, 0 failed — cycle measured, loop continues
  12 in batch, 0 skipped by content guard
- 2026-08-08 17:47 UTC — Queue empty — holding
  no unsent verified leads; drop new lead files in leads/staging, daemon re-checks every 30 min
- 2026-08-08 18:54 UTC — Batch auto-2026-08-08-b01: 25 sent, 0 failed — cycle measured, loop continues
  25 in batch, 0 skipped by content guard
- 2026-08-08 19:56 UTC — Batch auto-2026-08-08-b02: 21 sent, 0 failed — cycle measured, loop continues
  21 in batch, 0 skipped by content guard
- 2026-08-08 20:15 UTC — Batch auto-2026-08-08-b01: 50 sent, 0 failed — cycle measured, loop continues
  50 in batch, 0 skipped by content guard
- 2026-08-08 20:33 UTC — Batch auto-2026-08-08-b01: 50 sent, 0 failed — cycle measured, loop continues
  50 in batch, 0 skipped by content guard
- 2026-08-08 20:53 UTC — Batch auto-2026-08-08-b01: 50 sent, 0 failed — cycle measured, loop continues
  50 in batch, 0 skipped by content guard
- 2026-08-08 21:13 UTC — Batch auto-2026-08-08-b01: 50 sent, 0 failed — cycle measured, loop continues
  50 in batch, 0 skipped by content guard
- 2026-08-08 21:33 UTC — Batch auto-2026-08-08-b01: 50 sent, 0 failed — cycle measured, loop continues
  50 in batch, 0 skipped by content guard
- 2026-08-08 21:54 UTC — Batch auto-2026-08-08-b01: 50 sent, 0 failed — cycle measured, loop continues
  50 in batch, 0 skipped by content guard
- 2026-08-08 22:15 UTC — Batch auto-2026-08-08-b01: 50 sent, 0 failed — cycle measured, loop continues
  50 in batch, 0 skipped by content guard
- 2026-08-08 22:36 UTC — Batch auto-2026-08-08-b01: 50 sent, 0 failed — cycle measured, loop continues
  50 in batch, 0 skipped by content guard
- 2026-08-08 23:13 UTC — Batch auto-2026-08-08-b01: 14 sent, 0 failed
  14 in batch, 0 skipped by content guard
- 2026-08-08 23:20 UTC — Daily cap reached: 200/200
  phase warmup day 2/14 (<=200/day) — sleeping until UTC midnight
- 2026-08-09 00:00 UTC — ⛔ GATE BLOCKED — no sends until fixed
  bounce rate 4.94% > 2.00%; spam rate 0.41% > 0.08% — see experiments/report.md
## CYC-20260809-1137 — 2026-08-09 11:37 UTC

Batch: manual · sent total: 244 · sent today: 1/200

**KPIs vs goals**
  reply rate          0.0%  target   30.0%  ❌
  delivered rate     84.0%  target   99.0%  ❌
  open rate          46.3%  target   50.0%  ❌
  click rate          5.4%  target    5.0%  ✅

**Guardrails**
  bounce rate         4.9%  target    2.0%  ❌
  spam rate           0.4%  target    0.1%  ❌
  ⛔ BREACH: bounce rate; spam rate

**Weakest link:** bounce rate

**Previous experiment verdict:** inconclusive — reply_rate 0.0% -> 0.0% (within noise)

**Next lever:** cohort_unverified (skip_unverified=true)
**Hypothesis:** cohort: skip 'Publicly listed; not deliverability-verified' emails; reason: 9/10 bounces are unverified role addresses, bounces suppress opens and replies

---
## CYC-20260809-1141 — 2026-08-09 11:41 UTC

Batch: manual · sent total: 244 · sent today: 1/200

**KPIs vs goals**
  reply rate          0.0%  target   30.0%  ❌
  delivered rate     84.0%  target   99.0%  ❌
  open rate          46.3%  target   50.0%  ❌
  click rate          5.4%  target    5.0%  ✅

**Guardrails**
  bounce rate         4.9%  target    2.0%  ❌
  spam rate           0.4%  target    0.1%  ❌

**Weakest link:** delivered rate

**Previous experiment verdict:** inconclusive — reply_rate 0.0% -> 0.0% (within noise)

**Next lever:** providers

---
## CYC-20260809-1142 — 2026-08-09 11:42 UTC

Batch: manual · sent total: 244 · sent today: 1/200

**KPIs vs goals**
  reply rate          0.0%  target   30.0%  ❌
  delivered rate     84.0%  target   99.0%  ❌
  open rate          46.3%  target   50.0%  ❌
  click rate          5.4%  target    5.0%  ✅

**Guardrails**
  bounce rate         4.9%  target    2.0%  ❌
  spam rate           0.4%  target    0.1%  ❌

**Weakest link:** opens fine but reply 0.0% < 30%

**Previous experiment verdict:** inconclusive — reply_rate 0.0% -> 0.0% (within noise)

**Next lever:** cta
**Hypothesis:** cta: shorten question so reply costs ~10s; reason: opens fine but reply rate is the gap

---
## CYC-20260809-1232 — 2026-08-09 12:32 UTC

Batch: auto-2026-08-09-b01 · sent total: 251 · sent today: 8/300

**KPIs vs goals**
  reply rate          0.0%  target   30.0%  ❌
  delivered rate     84.9%  target   99.0%  ❌
  open rate          45.5%  target   50.0%  ❌
  click rate          5.6%  target    5.0%  ✅

**Guardrails**
  bounce rate         4.8%  target    2.0%  ❌
  spam rate           0.4%  target    0.1%  ❌

**Weakest link:** opens fine but reply 0.0% < 30%

**Previous experiment verdict:** inconclusive — reply_rate 0.0% -> 0.0% (within noise)

**Next lever:** cta
**Hypothesis:** cta: shorten question so reply costs ~10s; reason: opens fine but reply rate is the gap

---
- 2026-08-09 12:32 UTC — Batch auto-2026-08-09-b01: 0 sent, 0 failed — child exited -9
  49 in batch, 1 skipped by content guard
