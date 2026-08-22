# Company Mapping

Owned by the Strategist. The lexicon from any foreign concept to the
current SpielOS abstraction. Keeping the mapping explicit prevents each
import from re-inventing the architecture.

## Canonical abstractions (targets)

| SpielOS | Meaning |
|---|---|
| `strategy/` | chosen direction — where the Company wants to go (ICP, positioning, voice, measurement) |
| `workers/<id>/` | a persistent specialized role: `ROLE.md` + `PLAYBOOK.md` + `skills/*.md` |
| `skills/` | reusable detailed know-how referenced by workers |
| `assets/` | approved reusable inputs (facts, proof, brand, templates) |
| `artifacts/` | outputs produced by Runs |
| Goals / Runs / Acts / Evidence / Memory / Approvals / Connections | durable runtime state in SQLite |

## Source → abstraction (lexicon)

| Foreign concept | SpielOS abstraction | Explicitly not |
|---|---|---|
| Department / division | Worker(s) (`company/workers/<id>/`) | a lifecycle stage |
| Workflow / pipeline | Worker PLAYBOOK + scheduler Acts | new machinery |
| Skill / method library | Worker skills (`company/workers/<id>/skills/*.md`) | a new top-level |
| Template / preset | Asset of the owning Worker | runtime code |
| Agent / executor identity | Worker (probation → promotion) | another orchestration layer |
| Kernel / concept map / index | `spielos_index` semantic index (strategy refs) | a second store |
| Harness runtime (Python/JS/etc.) | **not ported** — extract knowledge + validation rules only | — |
| Eval / quality gate | Worker skill + `eval_report` Evidence contract | hidden engine |
| Lead/CRM/data files | Connection + assets; data stays in its bound source | a copy of the store |
| Old DB / run history | read-only archive; never merged into SpielOS SQLite | schema merge |
| Generated output (drafts, renders, reports) | Artifact / technical Evidence | business Evidence |

## Lean-folder rule

A Company tree may contain exactly:

```text
company/COMPANY.md
company/strategy/            ← direction
company/workers/<id>/        ← roles + playbooks + skills
company/skills/              ← cross-worker reusable know-how
company/assets/              ← reusable inputs
artifacts/                   ← run outputs
```

Nothing else at the top level. If a mapping would create a new
top-level directory, the mapping is wrong — redesign until it fits an
existing abstraction.