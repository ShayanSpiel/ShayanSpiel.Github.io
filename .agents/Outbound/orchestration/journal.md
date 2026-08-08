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
