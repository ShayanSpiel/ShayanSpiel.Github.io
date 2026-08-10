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
| `/status [goal]` | Show outcomes, evidence, approvals, and blockers |
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

## Runtime commands

The Director and OpenCode commands call one portable internal CLI:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company departments
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company catalog
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company status
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company runner status
```

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

Runtime or Department changes use one bounded `system_improvement` Goal with:

- `owner_id`, current and target version;
- problem and allowed files;
- exact acceptance commands;
- `change_kind: repair` or `create_department`;
- a `department_spec` when creating a Department.

The executor edits only approved files, records actual test evidence, and never
marks deployment unless deployment happened.
