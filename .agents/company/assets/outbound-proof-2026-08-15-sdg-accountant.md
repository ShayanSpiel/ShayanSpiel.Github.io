# Outbound proof — qualified inbound reply (2026-08-15)

Owner-confirmed 2026-08-15. CRM-ready record (import when the CRM is set up).

## Reply record

| Field | Value |
|---|---|
| Lead ID | EN-1358 |
| Contact | Sami Ghaith |
| Title | Founder & Managing Director |
| Company | SDG Accountant |
| Segment (owner-confirmed) | Accounting & bookkeeping |
| Country | Canada |
| Email | sami@sdgaccountant.com |
| Outbound subject | Manual loop at SDG Accountant |
| Outbound variant | researched-personal (offer-1) |
| Sent | 2026-08-14T03:39:17+00:00 via Brevo |
| Reply received | 2026-08-14T13:31:06+00:00 |
| Reply (verbatim, owner-relayed) | "Can you build it out using our Ring Central?" |
| Classification | Interested — implementation/stack-viability question (Q-class) |
| Ledger evidence | `.spielos/state/outbound/metrics.json` → `replies` (EN-1358, `kind: reply`) |
| Next action | Owner replies in-thread (build-on-stack answer); candidate for booked-calls pipeline |

## Why this is proof

1. **Real human reply from the ICP** — an owner-operator of an established
   accounting firm asked to build SpielOS on his existing stack (RingCentral).
   That is a buying-behavior question (implementation viability), not a courtesy
   pass: the buyer is post-fit.
2. **The researched single-loop hook converted.** The subject named ONE discovered
   operational loop — "Manual loop at SDG Accountant" (generic-workflow subject
   bank; live `content_variables.json`). Variant `researched-personal` (offer-1):
   per-lead hook + pain hypothesis + supervised-agents offer + soft CTA + founder
   sign-off — the architecture locked 2026-08-11.
3. **Segment validated:** accounting & bookkeeping firms fit the canonical ICP —
   high-volume manual financial loops (client intake, bookkeeping runs,
   reconciliations, payroll, filing), owner-operator buyer. Added to
   `.agents/company/strategy/icp.md` main business types.

## Locked (owner directive 2026-08-15: "lock in that kind of research and content")

1. Keep the per-lead researched single manual loop as the default hook for
   professional-service segments: subject family "Manual loop at {company}" /
   "One workflow at {company}" / "Repetitive work at {company}", with the pain
   paragraph naming that company's actual loop.
2. Every new lead records its ONE most manual operational loop at qualification
   (department strategy research rule 5; feeds `research_fact` scoring +10).
3. Until a CRM exists, every qualified reply is recorded here (proof entry) and
   in `.agents/company/assets/outbound-feedback.md` (classification), with the
   runtime ledger keeping header-level capture.
