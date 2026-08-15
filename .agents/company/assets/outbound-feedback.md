# Outbound reply feedback — classified outcomes (durable knowledge)

Each entry = one real human reply, classified for research + copy direction.
Ledger of record: `.spielos/state/outbound/metrics.json` -> `replies`.

## Replies to date (2026-08-11)

### 1. ACCEPTED — demo request
- Lead EN-1157 · Rhys, Founder & MD · Sigma Recruitment (recruitment)
- Outcome: accepted — "happy to have a demo" (2026-08-10)
- Email variant that converted: researched-personal (per-lead hook + pain +
  supervised-agents offer + soft CTA) — locked as campaign default.

### 2. REJECTED — class R1 (no external solution now)
- Lead AP-7d1096 · Tony Turquet, Founder & CEO · Web Katalyst (UAE)
- Outcome: rejected — "We're not looking to bring in an external solution
  for this workflow at the moment, so I'll pass for now." (owner-forwarded
  2026-08-11; real reply; earlier bot/away event kept separate as auto)
- Company type (owner-confirmed): **software agency** — the segment label
  "Agency & marketing services" is too coarse; classification corrected in
  the master row Notes.
- Email in thread: agency-delivery variant (pre-research-lock, generic
  salutation "Hi Web Katalyst team") — still produced a real human reply:
  domain-specific pain framing works even in generic form.
- Lesson: this rejection is a fit/timing signal, not a copy failure.
  Web Katalyst can build internally (software agency) — the build-vs-buy
  objection. Future research must capture external-solution readiness
  (see department strategy "Reply feedback & lead classification v1").

## Rejection class taxonomy (R1–R5)
- R1 not looking for an external solution at the moment (in-house/timing)
- R2 generic pass, no reason
- R3 budget / cost objection
- R4 wrong fit (segment mismatch)
- R5 follow-up later / revisit

## Research-side rules (wired into department strategy 2026-08-11)
1. Company-type precision at qualification (what the company actually sells).
2. External-solution readiness captured in Need / Buying Signals.
3. Replies update the lead's Notes (outcome + class + date).
4. Reply ledger stays the single source for reply-rate measurement
   (kind=reply only; auto/away and TEST never count).

### 3-4. OUT-OF-OFFICE auto-replies (data capture 2026-08-11)
- EN-1152 Jay Plant / Wentworth James Group — OOO (away, limited access;
  returned Mon 2026-08-10). Alt given: accounts@wentworthjames.co.uk — role
  inbox, out of policy (flagged). Deliverability confirmed by OOO.
- EN-1153 Jack Weeden / VR Group — OOO (on leave, no access; no return date).
  Alt given: Josh Barlow, Group Candidate Manager (07508 535621,
  jbarlow@vr-group.co.uk) — role confirmed on vr-group.co.uk/about.
  Deliverability confirmed by OOO.
- New lead created from OOO intel: EN-1279 Josh Barlow @ VR Group (Verified,
  Ready to personalized, 2026-08-11).
- Rule: OOO reply = live-mailbox proof (status upgrade); named alternatives
  with published emails become leads; role inboxes stay out of policy.

### 5. DELIVERABILITY lesson — verified cohort hard-bounce (2026-08-11)
- 6/29 hard bounces (21%) from the "Verified" cohort despite published-source +
  MX + partial re-confirmation: EN-1248 Linear Search (killian.dixon@),
  EN-1252 Amelies (jessica@), EN-1270 Textile Centre (shahbanaziz@),
  EN-1276 Yourshield (matt@), EN-1277 Jambo Tours (david@),
  EN-1278 Underoutfit (felix@). All suppressed immediately.
- Pattern: firstname@-style mailboxes at small/startup domains dominate the
  bounces; corporate-domain deliveries held up. Published+Mx evidence is
  NECESSARY but NOT SUFFICIENT for deliverability.
- Rule: expect ~20% hard bounce even in the verified class; size slices
  accordingly; suppress every bounce immediately (gate downgrade then stays
  green); prefer corporate domains with established MX for future cohorts.
- Gate behavior validated end-to-end: block on breach -> owner remediation
  (suppression) -> downgrade -> continue. No reputation damage.

### 6. INTERESTED — implementation-viability question (qualified inbound)
- Lead EN-1358 · Sami Ghaith, Founder & Managing Director · SDG Accountant
  (Canada, accounting & bookkeeping — owner-confirmed segment)
- Outcome: interested — "Can you build it out using our Ring Central?"
  (received 2026-08-14T13:31:06+00:00 UTC; owner-relayed 2026-08-15)
- Email in thread: "Manual loop at SDG Accountant" (researched-personal /
  offer-1, sent 2026-08-14T03:39:17+00:00 UTC via Brevo, generic-workflow
  subject bank) — the researched single-loop hook.
- Classification: Q1 / implementation-viability — buyer wants SpielOS built
  on their stack; post-fit signal, candidate for booked-calls pipeline.
- Company kind (owner-confirmed): accounting & bookkeeping firm — added to
  canonical ICP main business types (2026-08-15).
- Lesson: a specific named operational loop converts ("Manual loop at X").
  Locked as research rule 5 (per-lead manual-loop hook) — see
  `.agents/company/departments/outbound/strategy.md`.
- Full CRM-ready record: `assets/outbound-proof-2026-08-15-sdg-accountant.md`.
