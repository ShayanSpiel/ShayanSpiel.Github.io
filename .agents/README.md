# SpielOS agents

The company harness has one authority: [`company/README.md`](company/README.md).

- `company/` — company context, Departments, Connections, and the one runtime.
- `skills/` — reusable methods used by Agents inside Workflows.

Do not add orchestration, company strategy, campaign data, or generated work at
this level. Private inputs, state, and outputs belong under `.spielos/`.
