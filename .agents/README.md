# SpielOS Company Harness

## Read this first

```text
strategy authority   .agents/company/strategy/
runtime authority    .agents/company/
runtime state        .spielos/state/ (ignored)
reusable abilities   .agents/skills/
departments           .agents/company/departments/
approved assets       .agents/company/assets/ + department assets/
email data/secrets   .agents/Outbound/ (local/ignored where sensitive)
```

The company runtime is the only orchestration loop and the only owner of goals,
approvals, runs, and evidence. A Department is the human-facing business unit;
an engine class is only its runtime adapter. Workflows are named playbooks,
agents execute bounded steps, skills explain how, and adapters touch external
systems. None may create a second state machine.

## Current runtime units

- `director` — coordinates persisted company and Department goals.
- `outbound` — production Department for lead research, email, social research,
  and DM drafting.
- `email` — temporary compatibility engine for persisted email goals.
- `system-improvement` — bounded code repair, tests, version evidence, and
  return to the originating run.

Content and SEO are cataloged Departments but remain `production_ready: false`
until their publishing/measurement adapters provide real evidence. Video is a
Content workflow; its canonical HTML sources live with Content assets.

Inspect the complete composition with:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company catalog
```
