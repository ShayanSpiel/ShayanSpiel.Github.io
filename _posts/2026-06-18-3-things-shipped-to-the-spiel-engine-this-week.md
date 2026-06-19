---
layout: post
title: "3 things shipped to the Spiel Engine this week"
date: 2026-06-18 09:00:00 +0000
description: "The Spiel Engine is a pipeline that turns a build session into a publishable post. The gap that kept showing up was not the writing. It was the publishing, the last 20% that takes 80% of the energy."
seo_keyword: "Spiel Engine product update"
categories:
  - Spiel Engine
tags:
  - Spiel Engine
  - product update
  - building in public
image:
  path: /assets/banners/2026-06-18-x-3-features.png
  width: 1200
  height: 630
---

This week I shipped 3 things that close that gap.

## 1. One API call. Three platforms.

The Buffer integration posts to X, LinkedIn, and Threads in a single call. No copy-paste between tabs. No 3 separate logins. No scheduling tool with its own auth flow.

It is built on @Buffer's multi-platform API. The free tier is genuinely generous: 3 channels, 10 posts in the queue at a time, 3,000 API calls a month. That covers one post a day across three platforms with headroom.

If you outgrow the free tier, the tool falls back to direct X and LinkedIn APIs automatically. No config change. No tool switch. The dispatch handles it.

The marginal cost of "shipped a build" to "published across 3 platforms" is now near zero. The constraint shifts from effort to what is worth saying.

## 2. One config. Custom banners. No Node.

The banner tool generates post visuals from a config file and an HTML template. Open one command. A real HTML file opens in your browser. Edit a CSS variable. Hit refresh. See the new banner.

No Node setup. No Puppeteer. No Chrome path fixes. No shell-out dance. The engine is Playwright + system Chrome. The templates use CSS variables in a `:root` block. Change a color, save, render.

14 unit tests + 1 snapshot regression keep the output stable. If a banner drifts more than 2% pixel-wise, the test fails. Drift is caught before it ships.

A post without a banner looks half-finished. The lack of a visual is the single most common reason a builder skips posting. This tool removes that excuse.

## 3. Five strategy docs polished. Voice matched.

The docs the pipeline reads to write in your voice got a structural rewrite. Clean frontmatter. Version history. Status markers. Supersedes lineage. A clear source-of-truth declaration for every concept.

When the docs are clean, the output is clean. When they drift, the output drifts. The polish is not cosmetic → it is the input contract for the entire pipeline.

Here's what I learned: removing friction from publishing is worth more than adding another feature. These 3 ships don't add power. They remove steps. When the marginal cost of publish is near zero, the only question left is what's worth saying.

## How to try it

The repo is open source. Clone it. Drop the setup prompt into any LLM agent. Walk through the 14-question setup. The five strategy docs get filled with your strategy. Then every build session becomes:

```
session log → 2 minutes of capture
              → pipeline compiles, drafts, gates
              → drafts land in queue
              → you review. you publish. you keep building.
```

No editorial calendar. No "what should I post" loops. No blank pages.

→ You build. The pipeline posts. You stay a builder.

Clone the repo. Run the setup. Reply with what you'd ship. The full [open source announcement](/spielengine-is-now-open-source/) has the architecture details.
