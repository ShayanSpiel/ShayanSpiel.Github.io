---
name: department-runner
description: Run one SpielOS Department independently against a durable runtime-owned goal. Use when the user wants outbound or another production-ready Department without company-level Director orchestration.
---

# Department Runner

Use the shared runtime in `.agents/company/`; do not create channel-specific
state machines. Inspect the Department/workflow/agent catalog with
`python3 -B -m company catalog`
using `PYTHONPATH=.agents` and `PYTHONDONTWRITEBYTECODE=1`.

Create or select one measurable Department goal, then use `once`, `status`,
`approve`, `pause`, `resume`, and `report`. Preserve the four-stage contract and
surface every suspension. A Department supplies domain observation, diagnosis,
artifacts, guardrails, execution and measurement; the runtime owns transitions,
all goals, state, leases, approvals and events.

Every execution must preserve a typed run, hypothesis, Department version, config
snapshot, controlled and changed variables, evidence validity, decision, and
evaluation. A technical system test can validate machinery but cannot establish
market or positioning truth.

Never select `execution_mode: live` on the user's behalf. Never treat generated
copy or an executed action as evidence that the business goal was achieved.
