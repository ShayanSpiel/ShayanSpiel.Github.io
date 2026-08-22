# Import Existing System

Owned by the Strategist. Unpacks **any** existing material the Human
brings — legacy harnesses, file dumps, apps, workflows, skills, sites —
and turns it into the current SpielOS abstractions. This is a general
capability, not a v1-to-v2 migration: the source lexicon grows per
source type.

## Process

1. **Inventory** — walk the source. List every meaningful item (files,
   folders, exports, configs, screenshots, links) with its kind:
   knowledge, workflow, template, data, credentials, machinery, record.
   Be explicit about what is *not* importable (secrets stay in the
   host `.env`, private data stays private).
2. **Classify per lexicon** — apply `company-mapping` to decide each
   item's target abstraction. Per-source recipes live here:
   - legacy SpielOS harness (`departments/`, `.agents/skills/`,
     kernel) → strategy / workers / skills / assets; runtime Python is
     **never ported**, only its knowledge and validation rules.
   - generic folder dumps → assets, or strategy/worker knowledge after
     mapping.
   - Notion / sheets / docs exports → structured assets or strategy.
   - Cursor rules / other agent harnesses → worker skills and
     playbooks.
   - website / SaaS exports → assets; generated output is technical
     Evidence or Artifacts at most.
   - scripts / hooks → PLAYBOOK steps for the owning Worker, never
     hidden machinery.
3. **Dry-run first** — produce the full proposed layout + mapping
   manifest before any write. The Human reviews the manifest.
4. **Execute on approval** — writes land only in the canonical
   top-levels (`company/strategy/`, `company/workers/<id>/`,
   `company/skills/`, `company/assets/`, `artifacts/`). Version
   increments apply (v1 → v2 → …); nothing is silently overwritten.
5. **Verify lean structure** — after the merge, list the tree. Any
   non-canonical top-level is a failure to fix.
6. **Hand off strategy forks** — if the material implies direction
   choices (ICP, positioning, what to pursue), the decision stays with
   the Human and the Strategist's `strategic-reasoning`; import never
   decides direction.

## Hard rules

- Never port an old runtime. Only knowledge, validation rules, and
  business-meaningful records cross over.
- Never create a new top-level directory. Lean structure is enforced,
  not hoped for.
- Business records from a foreign system are raw material for assets —
  they become business Evidence only through a valid Run observation.
- If the import needs a runtime capability that does not exist (new
  Connection kind, schema gap), that is a `system_improvement` Goal for
  the System Engineer — a separate, bounded change.