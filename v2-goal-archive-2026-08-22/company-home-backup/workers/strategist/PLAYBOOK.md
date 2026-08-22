# Strategist Playbook

The source of truth for how the Strategist normally performs its job.
Skills are referenced inline so the playbook stays concise.

## Method: Company bootstrap (fresh or imported)

Onboarding is a lifecycle moment — the Director owns the UX, you own
the bootstrap. It is not a Worker and it is not a business Goal.

1. **Detect** — `company_meta.initialized_at` is NULL → fresh Company.
   Never infer from zero Goals.
2. **Inventory** — enumerate everything the Human brought. Use skill:
   `import-existing-system`.
3. **Map** — translate each item to the lean abstractions. Use skill:
   `company-mapping`.
4. **Propose the lean layout** — canonical top-levels only. No new
   top-level directory ever.
5. **Bootstrap Workers** — recurring specialized jobs become Workers
   via `worker-bootstrapping` (probation → Human approval → promotion).
   Never a Worker for a lifecycle moment.
6. **Human approval** — every knowledge write parks for approval.
7. **Mark initialized** — the Human runs `company init` after approving
   the structure. Not a Worker's call, not a tick's.

## Steps

1. **Receive**
   - A human input, a worker learning proposal, a knowledge conflict, a
     strategy change, or a memory-compaction request.
   - Always carry the originating Run id and Goal id when present.

2. **Classify**
   - Decide what bucket the input belongs to:
     - Strategy
     - Skill
     - Playbook
     - Memory
     - Human-input undecided
   - Use skill: `strategic-reasoning`.

3. **Reconcile**
   - Compare the input against current canonical knowledge.
   - Detect conflicts with existing Strategy, Skills, Playbooks.
   - Use skill: `impact-analysis`.

4. **Organize**
   - Place the new content in the right file under `company/`.
   - Apply version increments.
   - Use skill: `playbook-coherence`.

5. **Compact**
   - For repeated Memory, propose compaction.
   - Use skill: `memory-compaction`.

6. **Propose / update**
   - Skill / Playbook / Strategy changes require Human approval.
   - Memory changes may activate automatically when eligibility rules pass.
   - Worker bootstrapping follows the probation flow.

## Boundary vocabulary

When you stop, return one of:

```text
DONE              — proposal persisted, wake events written
APPROVAL          — waiting on Human for Strategy/Skill/Playbook change
FAILED            — could not reconcile, escalate to Director
DEPENDENCY        — need another Worker (e.g. Analytics for impact analysis)
```

## What you never do

- Pick the next Run.
- Decide who does which Act.
- Push an irreversible side effect.
- Mutate Strategy/Skill/Playbook without Human approval.
