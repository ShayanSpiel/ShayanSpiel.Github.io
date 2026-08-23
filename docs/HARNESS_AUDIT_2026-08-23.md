# SpielOS Harness Audit — Full Report

**Date:** 2026-08-23 · **Scope:** `.agents/company/`, `.agents/skills/`, `.opencode/`, `.codex/`, `.spielos/`, root glue files (`agents.md`, scripts, tests). Website source (`src/`) excluded except where it couples into the harness.
**Verified evidence:** 621 tests executed → **600 pass / 21 fail**, git index inspected, all cited lines read from disk.

---

## 0. Executive summary

The harness core (Goal → OBSERVE → DECIDE → ACT → EVALUATE loop, SQLite persistence, approvals, work orders, memory, evals) is real and mostly works: 600 of 621 tests pass, state is transactional, isolation guards exist. But it currently lives **inside the website repo with hard couplings in both directions**, ships **zero packaging mechanism**, and carries **your identity baked into its generic spine** (metrics, domains, goal IDs, supervisor alerts).

Three classes of problems, in priority order:

1. **Privacy incident (fix today):** live company SQLite DBs + goal archives are committed to this public GitHub Pages repo.
2. **Structural split never happened:** website deploy logic runs *inside* the runtime's hot path; strategy/metrics/domain constants are hardcoded into "generic" modules; skills are one undifferentiated pool.
3. **Drift rot:** the Cal-retirement directive broke 21 tests + live email signatures; docs promise plugin behavior that was removed; stale duplicate state roots can mislead any observer.

---

## 1. 🔴 Privacy incident — private state tracked in a public repo

Confirmed via `git ls-files`:

| Tracked file | What it is |
|---|---|
| `v2-goal-archive-2026-08-22/company-home-backup/spielos.db` (+`-shm`, `-wal`) | Live company database backup |
| `v2-goal-archive-2026-08-22/{goals.json, acts.json, goals.sql}` | Full V1/V2 goal history |
| `v2-goal-archive-2026-08-22/…/workers/strategist/PLAYBOOK.md` | Worker playbook |
| `.agents/company.db`, `.agents/company.sqlite` | Stray runtime databases at `.agents/` root |
| `.spielos/.env.example` | Example env (low risk, but sits beside ignored real secrets) |

Referenced by nothing; not covered by `.gitignore`. Also untracked-but-unignored: `.pytest_cache/`.

**Action:** purge from repo AND from git history (`git filter-repo`), delete the stray DBs, extend `.gitignore` (`.agents/*.db`, `.agents/*.sqlite*`, `.pytest_cache/`, archive dirs). If lead data reached those DBs, treat as exposed.

---

## 2. Isolation audit — where website and harness bleed into each other

### 2a. Harness → website (worst offender: the runtime hot path)

Every goal transition executes your website's deploy pipeline from inside the generic loop:

| Coupling | Location |
|---|---|
| Writes into Astro `src/data/live-goals.json` | `runtime/loop.py:55` |
| Writes into site `public/live-state.json` | `loop.py:67` |
| Git add/commit/**push to origin main** on every transition (triggers GitHub Pages deploy) | `loop.py:209-252` |
| `_sync_live_snapshot()` called after every persist | `loop.py:488, 660-709` |
| Website funnel metrics hardcoded in business-truth gating (`reply_rate, services_leads, daily_visits, booked_calls, sales`) | `truth.py:12-15`, `director.py:21` |
| Literal goal id `goal-content-leads-20260812` in the generic truth module | `truth.py:20-23` |
| Email/reply evaluator hardcoded into the loop | `loop.py:1168-1178` |
| Outbound filesystem layout scanned by generic runner watchdog | `runner.py:682-751` |
| PostHog MCP (website analytics) embedded in host config | `opencode.json:7-18` |
| `scripts/sync-live-timeline.py` computes a "northstar" by substring-matching goal ids `-primary-` | script lines 27–31 |

### 2b. Website → harness

- Root `agents.md` (~525 lines) is titled "SpielOS Website" but contains the company operating-runtime constitution, funnel doctrine, strategy authority, and mixed skills registry.
- Website skills (`seo`, `analytics`, `translation-fa`, `copywriting-*`) reach back into `../../company/strategy/icp.md` and department code via relative paths.
- `install.py:248-250` treats ALL of `.agents/skills/*` as one installable namespace — a department package could legally bind to `spielos-ui`.
- `test/site.test.mjs` enforces the retired Cal/waitlist funnel — cannot pass against the current site.

### 2c. Stale duplicate state root

`.agents/.spielos/state/` is a dead parallel world (heartbeat 5 days old, launched with a wrong project-root resolution), containing its own `company.sqlite` + WAL. Any observer reading the wrong root sees "no active goals" while 30 are live. Nothing fences or deletes it. Delete after confirming.

---

## 3. Runtime core bugs (verified, with locations)

**Correctness:**
1. Naive-vs-aware datetime crash risk on legacy `resume_at` at `runner.py:484`, `loop.py:427`, `director.py:394` — kills whole tick on TypeError.
2. Supervisor records `restarted` before checking success (`supervisor.py:288-295`); failed restarts burn the cooldown and lie in `supervisor.json`.
3. Continuation/retry decisions happen **outside** the store lease (`loop.py:361-371`); concurrent clients race; loser gets raw `IntegrityError` instead of idempotent no-op — contradicts plan §7.2's own atomicity claim.
4. Unreachable branch in `continuation.py:69-71` (validity already filtered above).
5. Machine graph nodes with no `produces` silently skipped (`interpreter.py:109-118`).
6. Comparator inconsistency: `interpreter.compare` raises KeyError on unknown operator while `loop.py:1270` / `director.py:345` default False.
7. Integer-target assumption truncates float targets (`interpreter.py:179,262`).
8. Goal status written **before** its justifying evidence/decisions/evaluations (`loop.py:573-633`) — audit trail shows achievement preceding proof.
9. Director emits duplicate observation evidence every cycle (`director.py:28-32`).
10. Custom `--db` breaks the stop switch: automation flag checked next to DB, written next to project root (`service.py:18-21` vs `runner.py:387`).
11. `async_dispatch.DISPATCH_DIR` is cwd-relative while runner derives it from store path — two modules disagree (`async_dispatch.py:16` vs `runner.py:682+`).
12. Foreground `once/next/retry/approve` never check `automation_enabled`; only daemon tick does — `/stop` doesn't stop manual commands.
13. Notification upsert resets `delivered_at=NULL`, resurrecting old notifications as pending (`store.py:886-899`).
14. Migration backfill fabricates historical run rows copying *current* goal config as their snapshot (`store.py:358-361`).
15. Multi-work-order runs can never be completed by unlinked evidence (`store.py:1290-1306`).
16. Repair scans run on **every** Store construction; relies on undocumented run-id == cycle-id invariant (`store.py:362-427`).

**Dead code (callers verified absent):**
`Store.cancel_open_work_orders` (`store.py:1267`), `registry.get` (`registry.py:50`), `contracts.is_department` (`contracts.py:228`), `errors.retry_after` (`errors.py:52`), `notifications.deliver/dispatch` (`notifications.py:160-167`), `alignment.batch_exposure` + `pursuit_kind` (test-only), `truth.is_current_business_truth` + false-achievements registry (test-only), unreachable `continuation.py:69-71`, unused `install.py:654` local.

**Architecture smells:**
- `loop.py` god-file: stage driver + approval policy + alignment judge + notifications + work-order broker + **website deployer** + email evaluator in one module.
- Three copies of the comparator, two copies of state signature, two copies of resource-conflict channel logic (`store.py:546` vs `continuation.py:33` — they can disagree), three copies of automation-flag parsing, three notification payload shapes.
- Presentation strings (`why_next`) embedded in storage layer.
- Watchdog thresholds duplicated with different values across runner/supervisor (45s/75s vs 90s), enforced nowhere.

**Plan-vs-code gaps (`STRATEGIC_COGNITION_PLAN.md`):**
- P2.5E Batch exposure: exists only in tests, never in production paths.
- "Atomic continuation": false (bug 3).
- Fairness scheduling: only depth-then-created sort exists.
- Plan embeds manually-edited test counts ("256/309 green") — status ledger, not derived truth.

---

## 4. Test suite results (executed)

```
600 passed, 21 failed, 26 subtests passed (74s)
```

Failure clusters:
1. **Cal-retirement drift (biggest):** outbound email signatures still render `"Book a FREE Discovery Call"` → hardcoded `https://spielos.xyz/book/` in production compose code; 6+ tests assert either old cal.com links or new no-booking expectations. **This means live outbound emails are being sent right now with a CTA that contradicts the owner's 2026-08-22/23 directives.** Files: `outbound/workflows/email/compose.py` (SIGNATURE_HTML), `templates.py`, tests `test_outbound_compose/email/send_path_idempotency/campaign_handoff/buffer_connection`.
2. **Content eval-gate cluster:** 8 failures across `test_content_campaign_contract`, `test_content_attribution_contract`, `test_evals_framework`, `test_content_department`, `test_lego_behavior` — content campaign schema 1.1 / attribution events / auto-discovery broken together.
3. One actor RuntimeError surfaced in `email/actor.py:307` during collection.

Also: ~60% of the suite is SpielOS-specific acceptance/regression history (dated repair goals like `test_concurrent_send_store_20260817`), not portable harness coverage — fine as doctrine, wrong for a distributable package.

---

## 5. Departments layer

| Department | State |
|---|---|
| **Outbound** (11k lines incl. email workflow) | Most mature; bespoke email stage is the documented exception. Contains live-drift bug above. `calcom_sync.py` (567 lines) + `crm_sync.py` remain wired though Cal CTAs were retired from funnel — verify whether Cal sync is still wanted at all. |
| **Content** | Declared eval suites enforced via `eval_report` gate (`department.py:210-259`) but that gate's test cluster is failing today. Hardcodes `spielos.xyz/services|contact` destinations and "item 5 must link /live/" — user-specific policy inside department validation. |
| **Design** | Declares 3 eval suites but **never enforces eval gates** (no consumer of its `eval_suites` — asymmetric with Content). Brand strings in `evals.py:25-37`. |
| **Analytics** | Thin wrapper over `posthog.py` (546 lines) reading the website's PostHog — website-coupled by nature; fine, but belongs to the "user layer," not the spine. |
| **SEO** | 72-line department + 19-line keywords stub — near-vacant lego; candidate for consolidation or explicit deprecation. |

`campaign_contract.py` (746 lines) hardcodes `netloc != "spielos.xyz"` destination validation — company policy compiled into contract code.

---

## 6. Evals / connections / strategy / assets

- **Evals engine works** (kernel hash-enforced strategy loading verified live at `strategy.py:95-120`); Design-side enforcement missing; Content-side gate failing tests.
- **Connections:** README claim verified — `.env.example` exists (146 lines). Buffer connection has a hardcoded org id (`buffer.py:54`). `.env.example` still documents Cal booking signature while funnel is Apply-first.
- **Strategy kernel:** fully resolves, hashes enforced. Docs drift: `positioning.md` commercial paths not updated for Apply-first directive.
- **Assets:** `assets/outbound-proof-*.md` contain real prospect names/emails/phones — user-layer PII sitting inside what should be the packaged spine.
- **Agents roster:** all 12 skill_ids resolve correctly.

---

## 7. Host adapters & skills

- Plugin (`spielos-notifications.ts`) calls only real CLI commands ✓. But: **`/stop` story is broken** — V2 plugin dropped the stop hook, yet `commands/stop.md:6` and `company/README.md:70-72` still claim the hook disables automation automatically. Nothing does.
- Approval surfacing waits for a session-idle event; parked approvals invisible before first idle.
- OpenCode agents carry machine-enforced permissions; Codex TOMLs are prose-only (asymmetric safety). Both agent sets are clean of user specifics ✓ (but tests assert exact wording — edits will break `test_runtime.py:660-678`).
- Skills split: **harness-clean** = director, department-runner, system-improvement, outbound, outbound-email. **Website-bound** = spielos-ui (contains personal path `~/Desktop/projects/spielos`), seo, analytics, translation-fa, copywriting-en/fa, video-creation. Stale refs: `seo/SKILL.md:128` (`/about/` route doesn't exist), `seo/SKILL.md:388` + `analytics/SKILL.md:310` (retired waitlist), GA4 ID duplicated in prose against its own rule.

---

## 8. Packaging verdict — can another user install this in 1 click?

**No. Nothing installable exists today.**

Missing entirely:
- No `pyproject.toml`/entry point; requires `PYTHONPATH=.agents python3 -B -m company`.
- No `company init/bootstrap`: nothing scaffolds `.agents/`, `.spielos/`, host adapters, gitignore, starter department.
- Host adapter templates (~490-line plugin) must be hand-copied.
- Layout assumptions hardcoded everywhere (`__main__.py:15-16`, `service.py:18-21`).
- Your identity is compiled into the spine: funnel metrics in `truth.py`/`director.py`, literal goal IDs, `spielos.xyz` in contracts/compose/design evals, macOS osascript alerts titled "SpielOS supervisor", LinkedIn/X URLs in email templates, PII proof assets.

**Reusable spine (what goes in the package):** store schema+CRUD, models, errors, loop mechanics, interpreter, contracts machinery, continuation, repair iteration, memory, strategy kernel loader, evals framework, install/package validators, supervisor/service mechanics, host plugin, director/department-runner/system-improvement skills + agent definitions, generic tests.

**User layer (stays with you):** all departments' domain content, strategy/ (ICP, positioning, voice), assets/, `.spielos/` data/state/artifacts, funnel metrics config, brand strings, outbound campaign data, v2 archive, website skills, website repo itself.

---

## 9. Cleanup & fixing plan (aggressive, ordered)

**Phase 0 — today (privacy + lies):**
1. Purge `v2-goal-archive-2026-08-22/`, `.agents/company.{db,sqlite}` from git + history; extend `.gitignore`.
2. Delete stale `.agents/.spielos/` mirror.
3. Fix outbound email signature to match current funnel directive; update or retire the 6 booking-signature tests.
4. Reconcile the `/stop` hook story (reimplement disable-on-stop or fix `stop.md` + README).

**Phase 1 — correctness sprint (runtime bugs):**
5. Normalize `resume_at` parsing (3 sites); wrap continuation/retry creation in lease or compare-and-insert transaction; reorder terminal-state writes so evidence precedes status; fix supervisor restart bookkeeping; unify comparator; fix `--db` stop switch and cwd-relative dispatch dir; make foreground commands respect automation flag.

**Phase 2 — decouple website from harness:**
6. Extract `_sync_live_snapshot`/git-push behind a post-tick hook interface implemented by the website repo (or external cron); remove site paths from `loop.py`.
7. Move funnel metrics, capability maps, channel groupings, reserved-owner lists, supervisor alert copy out of generic modules into a `company.config` / department-declared layer.
8. Split root `agents.md` into WEBSITE doc + HARNESS doc; move funnel doctrine into company strategy; split `.agents/skills/` into `skills/website/` + `skills/company/` namespaces and enforce the boundary in `validate_department_spec`.

**Phase 3 — departments cleanup:**
9. Fix the content eval-gate failure cluster (8 tests); give Design the same eval-gate enforcement as Content (or drop its declared suites); decide SEO department's fate; confirm Cal sync retirement; replace hardcoded `spielos.xyz` validations with configured brand policy.

**Phase 4 — package the spine ("spielos-harness"):**
10. Create distributable repo: pyproject + `spielos init` scaffolding command (tree, `.env.example`, gitignore, host adapters, one starter lego department); move generic tests into the package; parameterize every identity constant; strip PII/user assets; then 1-click = clone template repo OR `pipx install spielos-harness && spielos init`.

**Phase 5 — debt deletion:**
11. Remove all confirmed-dead symbols (§3 list); deduplicate comparator/signature/resource-key/automation-parsing; rewrite `test/site.test.mjs` for the current funnel; fix stale skill references; remove personal path from `spielos-ui/SKILL.md`; correct plan-file claims or convert them to generated status.
