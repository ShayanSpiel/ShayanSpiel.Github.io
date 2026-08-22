# SpielOS2

One durable Company. One Director. Many Workers. One canonical loop.

## What this is

This is the company the runtime is currently serving. The Company owns
durable truth. Sessions, executors, and host UIs may come and go;
the Company does not forget what is true.

## Identity

- **Name:** SpielOS2
- **Cycle:** `OBSERVE → DECIDE → ACT → EVALUATE`
- **Director:** one orchestrator, logically persistent, computationally
  stateless.
- **Predefined Workers:** `strategist`, `system-engineer`.
- **All other Workers** are created by the Company itself via
  Strategist-drafted probation cycles.

## Knowledge

The harness ships only the bootstrap knowledge needed for the runtime
to start. Strategy / skills / assets / extra Workers are produced by
the Company itself as it runs.

```text
company/                       # harness-owned bootstrap (this repo)
  COMPANY.md                   ← this file
  WORKSPACES.json              ← local workspace roots the Company can read
  workers/                     ← canonical Workers (runtime-owned)
    strategist/
    system-engineer/

migration/                     # v1 carry-over — NOT loaded by the harness
  README.md                    ← what this is and what to do with it
  departments/                 ← five v1 departments as Worker skeletons
  strategy/                    ← v1 strategy markdown (provenance)
  skills/                      ← v1 skill specs
  assets/                      ← v1 asset facts and proof records
```

## Conventions

- The Director decides **what** must happen.
- Workers decide **how** to do specialized work.
- The runtime decides **when** something is allowed.
- No metric auto-promotes to a Goal.
- No semantic frontier may ever decide what is true.
- No irreversible side effect runs without an explicit `approval`.
- No Company-knowledge write is silent — version-checked, wake on change.
- The harness is small on purpose. v1 carry-over lives in `migration/`,
  not in the running Company, so users can `git pull` the harness
  without touching their migration.
