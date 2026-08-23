---
name: devto-publisher
description: Design and operate the SpielOS publishing process for dev.to — adapt canonical site content into dev.to-native articles, apply the SEO strategy (canonical URLs, tags, backlinks), and publish through the guarded API with owner approval before anything goes live.
---

# Dev.to Publisher

## Authority

- The canonical ICP is `.agents/company/strategy/icp.md`; voice rules are
  `.agents/company/strategy/voice.md` and the copywriting skills. Never restate
  the ICP here.
- Content that exists on spielos.xyz is **canonical**. A dev.to post is a
  distribution surface pointing back to it — never a second home for it.
- The API key lives in `.spielos/.env` as `DEVTO_API_KEY` (gitignored). Never
  commit it, never echo it into logs or artifacts.

## When to use

Use when a published note, landing page, launch, or lesson should be
distributed to the dev.to audience. Do not use dev.to to target the canonical
ICP directly (owner-operators are not dev.to's core reader); use it when the
material legitimately serves builders AND carries a path back to SpielOS
(open-source workers, AI-implementation lessons, build-in-public proof).

## Publishing process

### 1 · Select and map

| Site artifact | Dev.to treatment |
| --- | --- |
| Note (`src/content/notes/*.mdx`) | Full adapted article |
| Landing page | Launch/announcement post linking to it |
| Open-source release | Tutorial-style walkthrough of the repo |

One idea per post. If the source covers several, split or pick one.

### 2 · Adapt (never paste)

- Rewrite the opening for dev.to scanning habits: short paragraphs, one-line
  hooks, code blocks where real.
- Keep product truth identical to the site. Remove site-only components
  (`SectionHead`, CTAs) and express their function in markdown.
- Persian notes do not go to dev.to. English only.

### 3 · SEO strategy

1. **Canonical URL** — set `canonical_url` to the spielos.xyz original
   (e.g. `https://spielos.xyz/notes/<slug>/`). This transfers discovery to our
   domain instead of splitting ranking between the two.
2. **Title** — keyword-first, ≤ 60 chars, understandable without the article.
   No clickbait the body cannot cash.
3. **Description** — 120–160 chars, primary keyword in the first sentence.
4. **Tags** — exactly 4, chosen for search volume inside dev.to, mixing one
   broad tag (`#ai`, `#automation`) with specific ones (`#leadgeneration`,
   `#claudecode`). Verify tags exist via `GET /api/tags` before using.
5. **Cover image** — must be hosted on spielos.xyz under
   `/assets/uploads/`, referenced by absolute URL. Never hotlink artifacts.
6. **Backlinks** — every post links, in body text (not just footer):
   - the canonical note or landing page (primary),
   - the relevant conversion page (`/apply/`) only when the post earns it,
   - the GitHub repo for open-source work,
   - 1–2 related spielos.xyz pages with descriptive anchors.
   Anchor text describes the destination; never "click here".
7. **First 48 hours** — engagement (comments, reactions) is part of the
   record; reply from the founder account, not automation.

### 4 · Publish with approval

```sh
source .spielos/.env
# 1 · Create as DRAFT (published: false)
curl -s -X POST https://dev.to/api/articles \
  -H "api-key: $DEVTO_API_KEY" -H "Content-Type: application/json" \
  -d @payload.json
```

- Payload uses `article: { title, published, body_markdown, tags, description,
  canonical_url, cover_image }`.
- Always create with `"published": false` first. Surface the draft preview URL
  (`https://dev.to/<username>/<slug>`) to the owner.
- Only flip to live (`PATCH` with `"published": true`) after explicit owner
  approval. Never auto-publish.

### 5 · Record

Store the payload and API response under `.spielos/artifacts/devto/`
(`<date>-<slug>.json`): article id, URL, tags used, canonical target. The
runtime owns the goal state; this folder is evidence, not strategy.
