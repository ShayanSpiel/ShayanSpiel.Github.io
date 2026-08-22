# Worker Bootstrapping

When a new Worker is requested (Director or Human), the Strategist
drafts the Worker into existence.

## Process

1. Receive the requirement: recurring specialized job, role, expected
   authority.
2. Draft:
   - `company/workers/<worker-id>/ROLE.md`
   - `company/workers/<worker-id>/PLAYBOOK.md`
   - `company/workers/<worker-id>/skills/*.md`
   - Required Connection requests
3. Register the Worker in SQLite with `status = probation`.
4. Persist a Human-input wake event for promotion.

## Hard rules

- Probation defaults: read-only Connections where possible, no
  irreversible side effects without explicit approval, bounded
  test Acts, Evidence collected.
- A new Worker earns live write authority — it does not receive it
  because its markdown file exists.
- Promotion requires Human approval.
