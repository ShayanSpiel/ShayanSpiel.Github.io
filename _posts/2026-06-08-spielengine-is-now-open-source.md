---
layout: post
title: "SpielEngine is Now Open Source"
date: 2026-06-08 10:00:00 +0000
categories: ["AI & Agents"]
seo_keyword: "open source content engine for founders"
image: /assets/uploads/2026-06-08-spielengine-is-now-open-source/spielengine-github.png
tags:
  - open-source
  - ai-agents
  - content-engine
  - automation
  - positioning
---

**Updated Jun 14, 2026.** The repo has been repositioned to match the public offer. The open-source engine is now the entry layer of a two-layer system — free to clone, with a DFY Install option for founders who want the full pipeline without building it themselves. Everything below still works. [Jump to the offer structure](#the-two-layer-system) if that is what you care about.

---

Two days ago i published a post called [From Declarative Rules to Agentic Loops](/from-declarative-rules-to-agentic-loops/). It was about the architecture that finally made my LLM-operated wiki work — state machines, validation gates, and a loop instead of a prompt.

The response was: "where is the template?"

It did not exist yet. So i built it. Here it is.

**[SpielEngine](https://github.com/ShayanSpiel/SpielEngine) is the open-source entry layer of a Session-as-Content Infrastructure.** A system that turns your build sessions into publishable content — so you never need to stop working to create posts.

The state machine, the commands, the quality gates, the templates — everything that runs my daily output, packaged so you can clone it in 10 seconds and make it yours.

![The SpielEngine GitHub repo — the open-source home](../assets/uploads/2026-06-08-spielengine-is-now-open-source/spielengine-github.png)

---

## What you get

Clone [github.com/ShayanSpiel/SpielEngine](https://github.com/ShayanSpiel/SpielEngine) and you get:

- **AGENTS.md** — the state machine that governs the entire system. Two loops (wiki management + content posting), 18 states, validation gates at every transition.
- **18 slash commands** — `/extract`, `/post`, `/publish`, `/health`, `/state`, and 13 more. Each is a markdown file your LLM reads at invocation.
- **A SKILL.md** — the content engine skill that auto-injects into every opencode session.
- **16 mechanical gates** — `gates.py` enforces char limits, audience triggers, frontmatter completeness, word repetition, and 12 more checks. Runs automatically at GATE_CHECK.
- **8-step Content Engine Compiler** — the engine that extracts core insight, 6 meanings, and a selected angle from every session. Powers the DRAFTING step.
- **Agent-agnostic SETUP.md** — works in opencode, Cursor, Claude Code, Continue, Windsurf, Cline.
- **8 templates** — concept, entity, summary, comparison, query, blog, LinkedIn, X, session-log.
- **3 health scripts** — wiki-health.py (orphans, broken links, stale pages), detect-redundancy.py (content overlap), banner.py (auto-generates post banners).
- **Full directory scaffold** — raw/, concepts/, entities/, summaries/, content/queue/, content/posted/, content/sessions/, assets/screenshots/, scripts/.

---

## Step 1: Clone the repo

```bash
git clone https://github.com/ShayanSpiel/SpielEngine my-agentic-wiki
cd my-agentic-wiki
```

Replace `<your-name>` in `AGENTS.md`. Swap the placeholder templates with your own. You are live.

---

## Step 2: See the structure

The directory layout is designed for how LLMs read, not how humans organize. Flat enough to navigate, deep enough to scale.

![Finder showing the SpielEngine directory structure — raw, concepts, entities, content, templates, scripts](../assets/uploads/2026-06-08-spielengine-is-now-open-source/spielengine-finder.png)

| Directory | What it holds |
|-----------|--------------|
| `raw/` | Source materials — articles, transcripts, notes |
| `concepts/` | Evergreen wiki pages — ideas, patterns, guides |
| `entities/` | Entity pages — people, platforms, projects |
| `summaries/` | Overview/synthesis pages |
| `templates/` | Templates for pages and posts |
| `content/queue/` | Drafts awaiting review or publish |
| `content/posted/` | Published content archive |
| `content/sessions/` | Session logs |
| `assets/screenshots/` | Screenshot captures |
| `assets/banners/` | Auto-generated post banners |
| `scripts/` | Pipeline scripts, gates, health checks |
| `.config/opencode/` | opencode skill + command files |

---

## Step 3: Install in opencode

```bash
# Copy the skill
cp -r .config/opencode/skill/shayanspiel-content ~/.config/opencode/skill/

# Copy the commands
cp .config/opencode/command/* ~/.config/opencode/command/

# Register everything in opencode.jsonc
cp .config/opencode/opencode.jsonc ~/.config/opencode/opencode.jsonc
```

Restart opencode and run `/state`. You should see IDLE with 18 commands ready.

![Terminal showing /state output — IDLE, 18 commands, ready to go](../assets/uploads/2026-06-08-spielengine-is-now-open-source/spielengine-terminal-state.png)

---

## Step 4: Install in Claude Code / Cursor / Windsurf / Cline / Continue

[Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) reads `CLAUDE.md` from the project root. Create one:

```markdown
# Project Instructions

This is an agentic wiki powered by SpielEngine.
Read AGENTS.md before any other file — it defines the state machine
that governs all operations.

## Quick start
- /extract [source] — ingest a raw source → wiki page
- /post [about] — convert session work into drafts
- /health — run validation checks
- /state — show current system state
```

The same pattern works for Cursor, Windsurf, Cline, and Continue — each reads a project-level instructions file at session start. Point it at `AGENTS.md` and the same loop runs everywhere.

---

## Step 5: Run your first command

```bash
# Check the system state
/state
# State: IDLE, Ready for next command

# Ingest your first source
/extract my-first-article.md
# INGESTING → ANALYZING → RECONCILING → INDEXING → VALIDATING → COMPLETE

# Create content from your session
/post
# SESSION → STRATEGY → DRAFT → GATES → QUEUE

# Validate the wiki
/health
# Orphans: 0, Broken links: 0, Stale: 2
```

Each command follows the state machine. The model never guesses what to do next — the state machine tells it.

---

## The Two-Layer System

This repo is Layer 1. Here is the full picture.

| Layer | What | Price | Who it is for |
|-------|------|-------|---------------|
| **1. Open Source** | The repo. The methodology. The pipeline. You clone, configure, run. | Free | Founders who want to build their own system or learn the mechanism |
| **2. DFY Install** | Full pipeline installed inside your workflow. Positioning + offer + agents + templates + 30 days of review. | $2,900 one-time | Founders who want the system without building it themselves |

**Layer 1** is what you get from this repo. It is the same engine i run. Every file is production-tested. You can clone it today, customize the templates, and have a working content pipeline in an afternoon.

**Layer 2** is for founders who want to skip the setup entirely. I install the full system into their workflow — custom positioning, offer design, bio rewrite, agent configuration, templates in their voice, and 30 days of post-publish review. One install. One price. Everything handed over.

[More on the DFY Install →](https://shayanspiel.github.io/about/)

---

## What you are getting

This is not a product. It is a starting point.

- **The state machine** ([AGENTS.md](https://github.com/ShayanSpiel/SpielEngine/blob/main/AGENTS.md)) — 200 lines of markdown that governs two loops. Read it in 10 minutes. Customize it in 30.
- **The skill** ([SKILL.md](https://github.com/ShayanSpiel/SpielEngine/blob/main/.config/opencode/skill/shayanspiel-content/SKILL.md)) — 60 lines. Your content engine contract.
- **The commands** ([18 files](https://github.com/ShayanSpiel/SpielEngine/tree/main/.config/opencode/command)) — one page each. Each is a state transition in markdown.
- **The templates** ([8 files](https://github.com/ShayanSpiel/SpielEngine/tree/main/templates)) — blank slates with the right frontmatter.
- **The gates** — 16 mechanical checks + LLM-judged 4-check standalone + 10-gate extended. All parameters in `rules.yaml`.
- **The Compiler** — 8-step content engine that extracts core insight + 6 meanings + selected angle from every session.

![The AGENTS.md state machine — the government that replaces the giant prompt](../assets/uploads/2026-06-08-spielengine-is-now-open-source/spielengine-agents-md.png)

---

## Why this matters

Prompt engineering is the past. Agentic loops are the future.

A prompt is a one-shot instruction. A loop is a state machine with validation at every transition. Loops catch errors. Loops enforce sequence. Loops can run for days without drift.

SpielEngine is the concrete implementation of that idea. The state machine, the gates, the cross-loop feedback — they are all in that repo.

The insight is the same as the previous post: you should never "go create content." Your work should already contain it. The engine extracts what is already there.

---

Note: i built this for myself first. The repo was extracted from my working vault after months of iteration. The templates are the ones i use every day. The commands are the ones i ship with. There is no theory in this repo — every file has been tested in production.

Are you going to try it? Star the repo, drop a comment, or open an issue on GitHub. If you want the full system without the setup, [DM me on X](https://x.com/ShayanSpiel) for the DFY Install.

