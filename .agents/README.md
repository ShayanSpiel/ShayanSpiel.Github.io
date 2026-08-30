# SpielOS agents

The company harness has one authority: [`company/README.md`](company/README.md).

- `company/` — company context, Departments, Connections, and the one runtime.
- `skills/company/` — reusable harness-operation methods (director,
  department-runner, system-improvement, outbound, outbound-email).
- `skills/website/` — site-bound methods (spielos-ui, seo, analytics,
  translation-fa, copywriting/fa, video-creation). Departments may only
  bind skills under `skills/company/`; this is enforced by
  `install.py::validate_department_spec`.

Do not add orchestration, company strategy, campaign data, or generated work at
this level. Private inputs, state, and outputs belong under `.spielos/`.
