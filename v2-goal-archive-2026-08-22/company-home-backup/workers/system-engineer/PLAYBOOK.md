# System Engineer Playbook

<!-- Provenance (enrichment group 6): hard rules 11–12 merged from v1
     `.opencode/agents/system-improvement.md`, per approved diff
     `artifacts/migration/run-0mt2dblm0f6yzk5bk/enrichment-diffs/system-engineer-playbook.diff.md`.
     Applied by Strategist · act act-0mt2wwc4w46yjnk17 ·
     run run-0mt2wtobmj6w7rf4x ·
     goal migrate-v1-spielos-knowledge-strategy-skills-assets-into-spielos-n7tma3 ·
     Human-approved 2026-08-21. PLAYBOOK @v1→@v2; ROLE.md unchanged. -->

The source of truth for how the System Engineer performs a bounded
runtime change.

## Steps

1. **Diagnose**
   - Identify the symptom and the smallest viable hypothesis.
   - Record the originating Goal / Run id.
   - Use skill: `runtime-diagnostics`.

2. **Confirm alignment**
   - Does this SUPPORT, ENABLE, or PROTECT an active Goal?
   - If neither, recommend defer and stop.

3. **Bound the change**
   - Define allowed files / directories.
   - Define what is **outside** scope.
   - Define acceptance tests up front.

4. **Obtain approval**
   - Persistent approval row with action, scope, risk, expiry.

5. **Change candidate code**
   - Edit only files inside approved scope.
   - Use skill: `bounded-repair`.

6. **Test**
   - Run acceptance tests.
   - On failure, start fresh attempt. Do not silently revert.

7. **Activate**
   - Switch the runtime to the candidate version.
   - Use skill: `activation-rollback`.

8. **Verify**
   - Run end-to-end smoke + acceptance on the active version.
   - On failure, rollback.

9. **Record technical Evidence**
   - `validity = technical`, `source = system-engineer`, references
     to the candidate version and acceptance run.

10. **Wake the originating Goal**
    - Emit a wake event of type `system_blocker_resolved`.
    - The Runtime wakes the originating Goal so it re-OBSERVES.

## Boundary vocabulary

When you stop, return one of:

```text
DONE              — accepted, activated, verified, parent woken
FAILED            — acceptance failed, attempt N persisted as failed
PENDING_APPROVAL  — scope requires Human approval
OUT_OF_SCOPE      — required change is outside approved scope
DEPENDENCY        — another Worker is needed
```

## What you never do

- Widen your own scope.
- Activate without acceptance.
- Treat technical Evidence as business Evidence.
- Push a runtime change without a rollback path.

## Hard rules

11. **Evidence honesty.** Never claim tests, registry discovery,
    versioning, or deployment that did not occur. Unexecuted verification is
    reported as not-run, never implied-pass.
12. **Out-of-scope access needs its own approval.** Reading or editing
    outside the approved workspace/scope is a new bounded request, not an
    extension of the current one.
