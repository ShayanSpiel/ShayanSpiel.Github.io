# SpielOS Company Harness

SpielOS runs the company through one durable loop:

```text
GOAL -> OBSERVE -> DECIDE -> ACT -> EVALUATE
          ^                            |
          +----------------------------+
```

The runtime owns every Goal, transition, approval, run, status, and evidence
record. A Department supplies business behavior; it never creates another loop.
Codex, OpenCode, and humans are clients of the same persisted state.

## Universal vocabulary

| Word | Meaning | Example |
|---|---|---|
| Goal | Measurable outcome owned by the runtime | Reach 30% qualified reply rate |
| Department | Durable business capability | Outbound, Content, Design, Analytics, SEO |
| Workflow | Repeatable playbook inside a Department | Email outreach, article, keyword research |
| Agent | Bounded executor for Workflow steps | Lead Researcher, Publisher |
| Skill | Reusable method an Agent follows | Copywriting, SEO, video creation |
| Connection | Access to an external or local system | Buffer, PostHog, Search Console, website |
| Artifact | Output or evidence produced by a run | Draft, report, graphic, video, receipt |

`ContentPackage` is an Artifact manifest that groups one brief with its related
post, article, graphic, video, evidence, and publication receipts. It is not a
new architectural layer. It lives at
`.spielos/artifacts/{goal}/{run}/content-package.json`.

## Structure

```text
.agents/company/
  runtime/                 one loop, persistence, supervision, controls
  strategy/                ICP, positioning, voice, measurement
  assets/                  approved reusable facts, proof, brand references
  departments/
    outbound/              lead research, email, social research, DMs
    content/               packages, posts, articles, publishing
    design/                graphics, renditions, video, templates
    analytics/             scorecards, funnels, CRO
    seo/                   keywords, briefs, audits, improvements
  connections/             host-first Connection declarations
  agents/                  bounded executor identities

.agents/skills/            reusable methods
.spielos/.env              private credentials (ignored)
.spielos/data/             private operational inputs (ignored)
.spielos/state/            durable runtime state (ignored)
.spielos/artifacts/        generated run outputs (ignored)
public/                    intentionally published website assets
```

Each Department keeps its runtime implementation in `department.py`, its
Workflows beside it, and its channel templates inside its own folder. There is
no separate public adapter or Tool layer.

## Five OpenCode commands

| Command | Meaning |
|---|---|
| `/start [request or goal]` | Create, resume, or continue one Goal |
| `/stop [goal]` | Persistently stop automation; optionally pause one Goal |
| `/status [goal]` | Show the compact Company Snapshot or one Goal |
| `/approve <goal>` | Approve exactly one displayed parked action |
| `/help` | Explain this vocabulary and command surface |

Escape cancels the current OpenCode response. `/stop` is different: its plugin
hook immediately disables durable company automation, preventing idle hooks or
background supervision from starting more work. `/start` enables it again.

## Connections

Workflows declare logical Connections. Interactive work uses the active Codex
app/plugin or OpenCode MCP first. A direct API implementation is added only when
the Workflow must run unattended without a chat host. Today direct email
delivery is retained for unattended Outbound; Buffer, PostHog, Search Console,
and website publishing are host-resolved.

Connection credentials use the single example contract at
`.agents/company/.env.example`. Real values live only in `.spielos/.env`.
Outbound lead data lives only in `.spielos/data/outbound/`.

Buffer is a direct unattended Connection for approved content packages. Its
GraphQL API takes stable public HTTPS URLs for image and video assets; it does
not accept binary uploads. `python3 -B -m company.connections.buffer --check`
lists connected channels without printing credentials. `--probe-draft` creates,
verifies, and deletes one Threads draft only; it never schedules or publishes.

## Runtime commands

The Director and OpenCode commands call one portable internal CLI:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company departments
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company catalog
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company status
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company status GOAL_ID
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company status --history --limit 10
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company tasks
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company runner status
```

Open employee assignments are durable **work orders** in SQLite. When a run
blocks on `request_agent` (or a known capability handoff), the runtime writes
one open work order any Codex/OpenCode/host client can pick up. Matching
evidence closes it; `company retry GOAL_ID` continues the goal.

Installed employees execute through this one portable contract—no generated
host adapter per employee:

```sh
python3 -B -m company tasks --status active
python3 -B -m company tasks WORK_ORDER_ID --claim HOST_WORKER_ID
python3 -B -m company tasks WORK_ORDER_ID --complete HOST_WORKER_ID \
  --evidence '[{"kind":"accepted_kind","payload":{"artifact":"…"}}]'
```

Claiming is atomic, evidence is linked to the exact assignment, and successful
completion closes the work order and advances the Goal to its next real
suspension. This is also the concurrency boundary for multiple hosts and
cross-Department execution.

Work-order fields (employee, accepted evidence kinds, skills, connections) are
resolved from the Department `WorkflowSpec` catalog via
`runtime/contracts.py`. `goal create` validates metric and workflow against
that catalog and fills a default workflow when omitted.

### Department Lego packages

Growth Departments are declarative packages:

- `WorkflowSpec` — playbook labels + optional executable `graph` of `WorkflowStep`
- `WorkflowStep` kinds — `employee` | `approval` | `connection` | `machine`
- `runtime/interpreter.py` — shared OBSERVE→DECIDE→ACT→EVALUATE for packages
- `runtime/package.py` — `package_spec` / `validate_package` for install checks

A Department folder only needs package data (workflows, agents, metrics,
evidence_metrics). Custom stage code is reserved for special paths (live email).
`company catalog` marks packages with `"lego": true` when validation passes.

### Install path

```sh
# Validate a package JSON (short brief or full package_spec)
python3 -B -m company department validate --spec '{"id":"partnerships","purpose":"…","metrics":["meetings"]}'

# Write departments/{id}/ and reload via discovery
python3 -B -m company department install --spec '…' [--force]
python3 -B -m company department list
```

`system-improvement` goals with `change_kind: create_department` and a
`department_spec` install the package automatically after approval (no separate
coding executor for pure Lego packages).

Briefs expand through templates (`artifact`, `research`, `publish`, `pipeline`)
into multi-step graphs. Install also writes employee roster entries under
`.agents/company/agents/installed/*.json` (merged into `company.agents`).
Install stages and validates the whole package before swapping it into the live
catalog; failure restores the previous Department and employee records.

One approval authorizes the ordinary actions in its run. The runtime pauses
again only for an explicit `approval` Workflow node. Separate explicit nodes
remain independently auditable; employee and machine steps never invent extra
approval prompts.

The default status is a bounded Company Snapshot: automation, genuine active
attention, active and paused Goals, unread results, recent terminal results,
and counts. It never embeds configurations, observations, evidence bodies, or
historical task payloads. `status GOAL_ID` is a compact single-Goal projection.
`status --raw` is the explicit full-audit escape hatch. Terminal Goals are
closed transactionally, so they cannot remain operationally blocked or awaiting
approval even though their complete audit history remains in SQLite.

Create a Department goal with `--owner`, for example:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company goal create \
  --name "Research 10 qualified prospects" --owner outbound \
  --metric qualified_social_leads --operator ge --target 10 \
  --config '{"workflow":"social-lead-research","required_count":10}'
```

Internal CLI operations such as `runner tick`, `change complete`, evidence
recording, and notification acknowledgement are runtime plumbing. They are not
additional user-facing concepts or slash commands.

## Safety and system improvement

Live external actions always park for approval. Generated material is not
business evidence. Technical-only, contaminated, or invalid evidence cannot
support a market conclusion.

Every `approval_required` notification carries one typed
`approval_interaction`: question, action, artifact, destination, scope, risk,
consequence, separate Approve/Reject choices, and the exact fallback command.
Host adapters must render it through their native question control (`question`
in OpenCode and `request_user_input` in Codex when exposed). They never combine
parked actions or auto-approve. Hosts without that control must show the same
fields as a prominent blocking question; Reject leaves the action parked.

Runtime or Department changes use one bounded `system_improvement` Goal with:

- `owner_id`, current and target version;
- problem and allowed files;
- exact acceptance commands;
- `change_kind: repair` or `create_department`;
- a `department_spec` when creating a Department.

The executor edits only approved files, records actual test evidence, and never
marks deployment unless deployment happened.

## OpenCode permission policy

Company agents run with free-run shell permissions in OpenCode (V2
`permissions` rules in `.opencode/agents/*.md`). The Director and Department
executors never edit repository files; `system-improvement` is the only editing
agent and is bounded by its persisted goal. OpenCode-level prompting is thereby
limited to OpenCode defaults (`.env` reads, external directories); the runtime's
parked approvals are the single gate for live external and customer-facing
actions. Do not reintroduce per-command `ask` rules for company agents.
