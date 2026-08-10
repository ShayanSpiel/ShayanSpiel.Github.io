# SpielOS Outbound — Execution (implements the canonical ICP)

The buyer profile, exclusions, and positioning live in the canonical file:
**`../../strategy/icp.md`**. This file only contains what the Department needs on top of it —
target countries, verification tiers, and lead flow. Never redefine the buyer here.

## Target countries

United Kingdom · United Arab Emirates · Canada · Australia · United
States · Germany · France · Netherlands · Sweden · Norway · Denmark ·
Finland · Ireland · Saudi Arabia · Qatar.

## Never targets (matches canonical exclusions, regardless of score)

- AI companies / AI agencies / AI consultancies / agent builders
- Software / development agencies and studios (they build — not buyers)
- Open-source / coding-agent audiences, harness builders, technical founders
- Enterprise (>250 employees)
- Tiny pre-revenue startups and creators with no operational workload
- Free-mail domains (gmail/yahoo/outlook/hotmail/proton) — personal mail,
  not a business buyer

## Lead quality ladder (the verification tiers)

| Tier | Meaning | Queue priority |
|---|---|---|
| Verified | Apollo "Verified" + MX, or L2 SMTP probe accepted (250/251/252) | 0 — send first |
| Catch-all; unverified | Domain accepts everything; mailbox unknowable | 1 |
| Publicly listed; not deliverability-verified | Real MX, non-disposable; may open/click (proven); probe pending | 2 |
| Bounced; suppressed | Provider bounce event, or L1 fail (syntax/disposable/no-MX) | NEVER |

The engine never sends to the bottom tier. Bounce events auto-downgrade
(sync-bounces); L2 probing upgrades in idle time.

## Scoring (deterministic, in scripts/leads.py)

Base 40 · segment present +15 · targeted segment +25 · employees 5–50 +20
(51–250 +12, <5 +4, >250 −15) · revenue ≥ $1M +15 (revenue < $1M −10) ·
target country +10 · ranked title up to +20 · research hook +10.

- ≥70 → "Ready to personalized"
- ≥45 → "Routing email only"
- else → "Backup; wait"

`scripts/leads.py` is the only place scoring is implemented; this file and
`../../strategy/icp.md` are its specification.

## Lead flow

1. Research (assistant websearch + site visits, or owner Apollo export)
   → CSV into `scripts/leads/staging/`
2. Daemon ingests (≤30 min): dedupe vs master+log, score, L1-verify,
   Apollo verification fields mapped → tier
3. Queue consumes tiers in order; idle time = L2 probe time
4. Bounce events downgrade the email forever
