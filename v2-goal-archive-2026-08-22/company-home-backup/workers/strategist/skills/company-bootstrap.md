# Company Bootstrap

Owned by the Strategist. Onboarding is a **lifecycle moment**, not a
Worker and not a business Goal. The Director owns the onboarding UX
(explaining, guiding, using durable state). The Strategist owns the
bootstrap itself: turning a fresh Company — or a Company that brings
existing material — into the lean `company/` structure.

## Detect

- A Company is **fresh** when `company_meta.initialized_at` is NULL
  (see `src/company/index.ts` — `isCompanyFresh`). Never infer
  freshness from zero Goals: an initialized Company can be goal-less.
- Fresh + no material → **white-label bootstrap**: propose the lean
  skeleton only when the Human wants it.
- Fresh + existing material → **import bootstrap**: run
  `import-existing-system` first, then this skill.

## Process

1. **Inventory** — enumerate everything the Human brought: folders,
   apps, exports, workflows, harnesses, skills, sites. Use
   `import-existing-system`.
2. **Map** — translate each item into a SpielOS abstraction. Use
   `company-mapping`. Nothing maps to "onboarding" — the merge belongs
   to the Company, not a new Worker.
3. **Propose the lean layout** — only the canonical top-levels:
   `company/strategy/`, `company/workers/<id>/`, `company/skills/`,
   `company/assets/`, plus `artifacts/` and the SQLite state. No new
   top-level directories.
4. **Bootstrap Workers** — any recurring specialized job revealed by
   the inventory becomes a Worker via `worker-bootstrapping` (probation
   → Human approval → promotion). Never bootstrap a Worker for a
   lifecycle moment.
5. **Human approval** — every Strategy / Skill / Playbook / Asset write
   parks for Human approval. Nothing is written silently.
6. **Mark initialized** — only after the Human approves the resulting
   structure: `bun src/cli.ts company init`. This is the Human's call,
   not a Worker's, and never a background tick's.

## Hard rules

- Onboarding is **not** a Worker. It is the Director's UX + the
  Strategist's bootstrap. Do not create an Onboarding Manager.
- Do **not** make onboarding the first business Goal. A fresh Company
  creates its first real business Goal after bootstrap, with the
  Human's direction.
- The System Engineer owns the machine only. Importing and organizing
  the Human's files/knowledge is Strategist work; only missing runtime
  capabilities (schema, adapters, connections) become
  `system_improvement` Goals for the System Engineer.
- Imported material that is generated output is at most technical
  Evidence or an Artifact — it never becomes business Evidence by
  arriving in a folder.