---
layout: post
title: "SpielEngine is Now Open Source"
date: 2026-06-08 10:00:00 +0000
categories: ["AI & Agents"]
seo_keyword: "session as content infrastructure"
image: /assets/uploads/2026-06-08-spielengine-is-now-open-source/spielengine-github.png
tags:
  - open-source
  - ai-agents
  - content-engine
  - automation
  - positioning
---

**Updated Jun 14, 2026.** Repositioned to match the public offer. The open-source engine is now the entry layer of a two-layer system — free to clone, with a DFY Install for founders who want the full pipeline without building it.

---

The previous post was about the architecture. The response was: "where is the template?"

Here it is.

**[SpielEngine](https://github.com/ShayanSpiel/SpielEngine) turns your build sessions into publishable content, so you never need to stop working to create posts.**

## Here is what that looks like

A two-hour debugging session becomes a post. The founder never opens a writing tool.

**Session log (2 minutes of notes):**

```
Spent 2 hours fixing context drift in a LangGraph workflow.
Root cause: too many hidden state transitions between nodes.
Fix: explicit state schema with required fields per transition.
```

**Generated post:**

```
Most AI agents don't fail because of prompting.
They fail because nobody knows what state they're in.

Every hidden transition is a drift point.
Every drift point is a silent bug.

Make the state explicit.
The agent will thank you.
```

Same session, different frame — extracted, not written. That is the mechanism.

---

## What you get

Clone the repo and you get a pipeline that turns every work session into drafts — blog, LinkedIn, X — each in the right format, each passing quality checks before it reaches you.

Session → session log → compiler → platform drafts → automated gates → you review and publish.

Everything that runs my daily output, packaged so you can clone it in 10 seconds and make it yours.

![The SpielEngine GitHub repo — the open-source home](../assets/uploads/2026-06-08-spielengine-is-now-open-source/spielengine-github.png)

---

## Step 1: Clone

```bash
git clone https://github.com/ShayanSpiel/SpielEngine my-wiki
cd my-wiki
```

Replace placeholder content with your own. You are live.

---

## Step 2: Install

Works in opencode, Cursor, Claude Code, Windsurf, Cline, Continue. Setup is copying files:

```bash
cp -r .config/opencode/skill/* ~/.config/opencode/skill/
cp .config/opencode/command/* ~/.config/opencode/command/
cp .config/opencode/opencode.jsonc ~/.config/opencode/opencode.jsonc
```

Restart and run `/state`. You should see IDLE.

![Terminal showing /state output — IDLE, 18 commands, ready to go](../assets/uploads/2026-06-08-spielengine-is-now-open-source/spielengine-terminal-state.png)

---

## Step 3: Run your first command

```bash
# Ingest raw material
/extract my-notes.md

# Generate posts from your session
/post

# Check health
/health
```

Each command follows a state machine. The model never guesses what to do next — the state machine tells it.

---

## The Two-Layer System

This repo is Layer 1.

| Layer | What | Price |
|-------|------|-------|
| **1. Open Source** | The repo, methodology, pipeline — clone and customize | Free |
| **2. DFY Install** | Full system installed in your workflow, positioned to your voice, with 30 days of review | $2,900 one-time |

**Layer 1** is the engine I run daily. Clone it today, swap the templates, and have a working pipeline in an afternoon.

**Layer 2** is for founders who want to skip the setup. I install the full pipeline — positioning, offer design, agents, templates in your voice, bio rewrite, post-publish review — inside your workflow. One install. One price. You own everything.

**The stack (what a DFY Install includes):**

```
✓ Positioning Strategy — ICP, category, differentiation
✓ Offer Design — value equation, awareness mapping, stack + guarantee + scarcity
✓ Bio Rewrite — X bio, LinkedIn headline, website tagline
✓ Pipeline Installation — agents, commands, templates, gates
✓ Workflow Design — session capture → /post → queue → review → publish
✓ 3 Sample Pillars in your voice, ready to publish
✓ 30 Days of Post-Publish Review — I read every draft, give feedback, refine the engine

Total value: $11,200 — Your investment: $2,900
```

The guarantee: if after 30 days you've run 5 sessions and don't have 5 gated drafts in your queue, I refund 100% — and you keep the system.

**3 slots per month.** Hard cap.

[Apply for DFY Install →](/contact/)

---

## What you are actually getting

- **AGENTS.md** — the state machine that governs two loops (wiki + content). Modify it in 30 minutes.
- **8 templates** — blog, LinkedIn, X, concept, entity, summary, comparison, session-log.
- **`/post` command** — reads your session log, runs the compiler, outputs platform drafts to a queue.
- **Automated gates** — length, repetition, hook strength, audience triggers, frontmatter completeness. Failing drafts don't enter the queue.
- **Health scripts** — detect orphans, broken links, stale pages, content redundancy.

This is not a product. It is a starting point — extracted from the system I use daily.

![The AGENTS.md state machine — the government that replaces the giant prompt](../assets/uploads/2026-06-08-spielengine-is-now-open-source/spielengine-agents-md.png)

---

## Note

I built this for myself first. The repo was extracted from my working vault after months of iteration. The templates are the ones I use every day. The commands are the ones I ship with. There is no theory here — every file has been tested in production.

Are you going to try it? Star the repo, open an issue, or [DM me on X](https://x.com/ShayanSpiel) if you want the full system without building it yourself.
