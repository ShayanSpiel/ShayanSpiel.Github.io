---
name: system-improvement
description: Execute a bounded SpielOS engine repair or new-engine build created by the Director, with allowed-file scope, acceptance tests, engine versioning, and return to the originating goal. Use when a persisted system-improvement goal is approved and waiting for a coding executor.
---

# System Improvement

Read the persisted goal, run, and change task before editing anything. The task
must specify `change_kind`, engine, problem or capability, allowed files,
acceptance commands, version before, and target version.

1. Refuse an unbounded or incomplete task.
2. Modify only `allowed_files`. Do not opportunistically refactor.
3. Preserve the originating business hypothesis and controlled variables.
4. Run every acceptance command exactly as recorded.
5. Record failure honestly if any acceptance command fails.
6. On success, call `company change complete` with the actual test evidence.
7. Mark deployed only after deployment actually happened.
8. Return control to the originating run. Never convert machinery evidence into
   a market or positioning conclusion.

The business run remains suspended or contaminated during this work. Never
silently resume it with different business variables.

For `change_kind: create_engine`, also require `engine_spec` with purpose,
supported metrics, configuration contract, external actions, approval points,
evidence sources, and acceptance behavior. Use `from_version: new`, implement
the shared four-stage engine contract, add contract tests, and prove registry
discovery before recording version `1.0.0` or later. A new engine is a durable
business capability, not a renamed prompt or subagent.
