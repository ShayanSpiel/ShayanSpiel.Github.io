# SpielOS Company Runtime

Durable operating layer for business goals. Codex, OpenCode, and humans are
clients of the same state; no chat session owns the truth.

```text
GOAL -> OBSERVE -> DECIDE -> ACT -> EVALUATE
          ^                            |
          +----------------------------+
```

Every runtime engine/Department adapter implements the four stages. `stage`, internal `step`, and
`run_status` are independent. Waiting and approval are statuses, not stages.

## One-minute map

- `models.py` — stable engine contract.
- `runtime.py` — transitions, leases, approvals and state authority.
- `runner.py` — automatic due/evidence/parent continuation.
- `service.py` — repository-local background runner lifecycle.
- `store.py` — SQLite goals, cycles, events, memory, approvals and leases.
- `engines/` — thin runtime adapters for the Director and Departments.
- `departments/` — business workflows, policies, domain adapters, and assets.
- `tools/` — stable operations such as publish, query, and render.
- `connections/` — replaceable Buffer, blog, PostHog, and Search Console adapters.
- `strategy/` — company-wide ICP, positioning, voice, and measurement authority.
- `assets/` — approved reusable company inputs.
- `agents/` — canonical bounded executor identities.
- `/.spielos/state/` — ignored runtime data, never source code.
- `.agents/skills/director/` — conversational operating procedure.

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company engines
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company catalog
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company goal create --name "Get replies" --engine outbound \
  --metric reply_rate --operator ge --target 0.30 \
  --config '{"workflow":"email-outreach","execution_mode":"dry_run","evidence_window_hours":48}'
```

The production Departments are Outbound, Content, Design, Analytics, and SEO.
Director and System Improvement are control engines; `email` remains only as a
compatibility ID for persisted historical goals.

`ContentPackage` is a run artifact grouping one brief and its coordinated
deliverables. It is not an extra Department, engine, workflow, agent, or skill.

For a company goal, create a `director` goal and engine goals whose `--parent`
is that goal ID. Any child remains directly runnable with `once CHILD_GOAL_ID`.
Child transitions wake a waiting parent automatically. Approvals and evidence
commands continue the current goal tree; they do not require a second manual
`once`. Evaluation completes and parks the run. `company next GOAL_ID` is the
only operation that accepts the proposed experiment and creates another run.

Outbound email has no execution default: a persisted goal must explicitly select
`dry_run` or `live`, and execution always parks for approval first.

Live email runs poll provider evidence while their evidence window is open.
Use `observer_interval_seconds` to set the cadence. Controlled inbox tests must
declare `reply_capture: manual_inbox` or `reply_capture: resend_inbound`.
`resend_inbound` refuses to send unless `REPLY_TO` is configured; that address
must belong to a Resend receiving-enabled domain. Provider delivery/open/bounce
events and matched inbound replies are persisted as run evidence, deduplicated
by provider event or received-email ID. Manual evidence never satisfies an
automatic-capture test.

## Typed runs and self-improvement

The four-stage runtime is shared by six run types: `business_experiment`,
`execution`, `diagnostic`, `system_improvement`, `evaluation`, and
`system_test`. Every run pins its hypothesis, engine version, configuration,
controlled/changed variables, evidence validity, decisions, and evaluation.

When infrastructure invalidates an experiment, mark the evidence contaminated
and create a bounded `system_improvement` child. That child requires approval,
allowed files, acceptance commands, and a target engine version. Successful
validation returns control to the originating run without changing its business
variables.

Use `change_kind: create_engine`, `from_version: new`, and `engine_spec` to
commission a new engine through the same bounded system-improvement path.

## Active loop and reporting

`company runner start` launches a repository-local worker whose PID and log live
under `.spielos/state/`. It advances idle runs, resumes due waiting runs,
processes approved actions, and wakes Director parents when children change.
Hard approvals, event-only evidence waits, blockers, failures, and completed
runs remain parked. The runner never silently creates the next experiment.

Approval, evaluation, blocker, failure, and terminal reports enter the durable
notification outbox. Codex/OpenCode read this outbox and acknowledge a notice
only after communicating it. External evidence still requires an adapter: for
example, inbox reply capture must record a `reply` event before the runner can
evaluate it.

OpenCode loads `.opencode/plugins/spielos-notifications.ts`. While an OpenCode
session is open, the hook performs safe runner ticks, watches the same durable
outbox, shows a toast, and wakes the Director in the active session. If OpenCode
is closed, nothing is lost; pending notifications are delivered when it opens.
Codex uses its scheduled Director heartbeat against the same outbox.

Outbound email runs require a complete eligible queue for their configured `batch_size`.
A shortfall emits a typed `action_required` notification with the exact number
of qualified, researched leads needed. The Director coordinates lead research,
verifies the queue evidence, and retries the same run without changing its
business hypothesis.
