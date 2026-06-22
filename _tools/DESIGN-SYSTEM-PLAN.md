# Design System Plan — ShayanSpiel

> Status: approved, Phase 0–4 sequence. Source of truth for the migration from markdown posts + scoped post layout to fully composed HTML posts + a token-driven, single-source-of-truth design system.

---

## Diagnosis

- The site is Jekyll + hand-rolled token CSS in `assets/css/main.css`. The `:root` block (`main.css:13`) is already a token system. The component classes (`.card`, `.btn`, `.section`, `.grid`, `.post-card`, `.blog-row`, `.tag-chip`, etc.) are already a component system.
- The GLM5.2 page (`llm-cost-leaderboard.html`) renders correctly because it uses `layout: default` — no `.post-article` wrapper, no descendant selectors fighting its custom HTML.
- Real posts use `layout: post` (`_layouts/post.html:14`) which wraps content in `<article class="post-article">`. The CSS at `main.css:684-719` cascades scoped styles (`.post-article p`, `.post-article h2`, `.post-article table`, etc.) into any custom HTML inside the post, breaking layout.
- Markdown's auto-`<p>` wrappers + the scoped styles = the styling conflict.

## "Shadcn totally" — honest take

shadcn is React + Tailwind + Radix + a copy-paste component philosophy. Installing it on this site would mean ripping out `main.css`, adding Tailwind + a JS build, and rebuilding every component. It would break the GitHub Pages deploy and contradicts "keep current styling completely."

**What we are actually building** is shadcn's methodology layered on the current stack: components we own, token-driven, variant-based, documented in-repo. No framework swap.

## On "components single source of truth"

For a static Jekyll site the equivalent of shadcn's "copy-paste components you own" is:

- **One HTML partial per component** in `_includes/components/` — `hero.html`, `card.html`, `section.html`, `stat-card.html`, `pullquote.html`, `step-list.html`, `tweet-embed.html`, `data-table.html`, `bar-chart.html`, `callout-arrow.html`, `cta-card.html`, etc. The partial IS the canonical HTML. Posts compose these with `{% include components/card.html title="..." %}`.
- **One CSS block per component** in `assets/css/components.css`, kept structurally aligned with a comment showing the matching partial. Component CSS only targets the structure the partial emits.
- **Tokens drive all values** — every color, spacing, radius, type size in component CSS comes from `var(--...)` defined in `assets/css/tokens.css`, generated from `_data/design-tokens.yml`. Change a token, every component follows.
- **`_data/components.yml`** is the manifest: `name`, `partial`, `variants`, `slots`, `description`. `_tools/sync-design-system.py` regenerates `/design-system/` from this manifest.
- **Build-time validation** — `sync-design-system.py` runs before `jekyll build` and fails the build if any component CSS selector has no matching partial, any partial in the manifest is missing, or any token used in component CSS does not resolve to a `--var` in `tokens.css`. That is the single-source-of-truth guarantee.

This directly enables the future state: each redesigned post (GLM-style, bite-sized, research-based, interactive) is a unique composition of the same library.

---

## Phase 0 — Stop the conflict (framework, no content changes)

- Create `_layouts/post-shell.html` — chrome only (breadcrumb, meta, title, lede, optional hero, tags, related, CTA) and a content slot. **No descendant selectors on the content.**
- Remove `.post-article p / h2 / h3 / ul / ol / li / blockquote / code / pre / img` from `main.css:684-719`. Promote the global rules (p, h*, table, blockquote) to `base.css`. They only apply outside design-system components.
- `layout: post` becomes an alias for `post-shell` (no break for any post still in markdown).
- Add `_data/components.yml` (empty manifest, ready to grow).
- Add `_tools/sync-design-system.py` (manifest → catalog page + selector validation + token resolution check). Wire as the build gate in `Makefile` / `README`.

## Phase 1 — Split the design system into files

- `assets/css/tokens.css` — `:root` block only (and `:root[data-theme="light"]` if/when a light mode is added).
- `assets/css/base.css` — reset + global typography (p, h*, table, blockquote, lists, code, img, hr, link defaults).
- `assets/css/components.css` — `.card`, `.btn`, `.section`, `.grid`, `.post-card`, `.blog-row`, `.tag-chip`, `.post-cta`, `.related-posts`, `.breadcrumb`, `.filter-btn`, `.stat-big`, `.pullquote`, `.step-list`, `.callout-arrow`, `.cta-card`, `.tweet-frame`, `.data-table`, `.bar-chart`, `.source-list`, etc.
- `assets/css/layout.css` — nav, footer, wrap, post-shell, page.
- `assets/css/main.css` becomes the entry that `@import`s the four files (or is removed in favor of four `<link>` tags in `head.html` — pick one when implementing).
- `_data/design-tokens.yml` is canonical. `sync-design-system.py` writes the `:root` block of `tokens.css` from the YAML.

## Phase 2 — Build the component library (formalize what GLM already does)

- Create `_includes/components/`: `hero.html`, `section-head.html`, `section.html`, `card.html`, `grid.html`, `stat-card.html`, `prose-center.html`, `divider.html`, `tweet-embed.html`, `bar-chart.html`, `data-table.html`, `source-list.html`, `breadcrumbs.html`, `post-meta.html`, `tag-chip.html`, `cta-card.html`, `related-posts.html`, `pullquote.html`, `callout-arrow.html`, `step-list.html`, `point-list.html`, `definition-card.html`.
- Each partial has a `{% comment %}` block documenting its `include` parameters.
- Component CSS in `components.css` is grouped by component, with a header comment showing the partial's emit structure so CSS and HTML are visually tied together.
- `sync-design-system.py` parses `_includes/components/*.html` for `{% include ... %}` parameters, regenerates `/design-system/` from `_data/components.yml`, and validates selector↔partial alignment.

## Phase 3 — Convert non-post pages to HTML (one batch)

- Convert: `index.md` → `index.html`, `about.md` → `about.html`, `contact.md` → `contact.html`, `posts.md` → `posts.html`, `categories.md` → `categories.html`, `tags.md` → `tags.html`, `sitemap.md` → `sitemap.html`. `404.html` stays.
- Each becomes a pure HTML composition of the new components.
- Front matter stays identical. Permalinks stay identical. Zero SEO/URL impact.
- Markdown rendering is fully retired from the site after this.

## Phase 4 — Migrate posts one at a time via the `/post` skill

- For each `_posts/*.md`: use the `/post` skill to redesign it as a custom HTML post (centered title + lede, bite-sized sections, evidence blocks, interactive components from the Phase 2 library). Skill output is `_posts/YYYY-MM-DD-slug.html` with `layout: post-shell`.
- Old markdown file is removed after the new HTML post is verified.
- Each post is its own PR-sized change. The user approves each one before the next is started.

---

## Decision log

| Decision                            | Choice                                                                                  |
|-------------------------------------|-----------------------------------------------------------------------------------------|
| Shadcn scope                        | Methodology upgrade, keep stack. No React, no Tailwind, no Radix, no Vite.               |
| Migration mode                      | One at a time via `/post` skill                                                         |
| Page format                         | Convert every page (including non-post pages) to HTML                                   |
| Token source                        | `_data/design-tokens.yml` is canonical; `sync-design-system.py` generates `tokens.css`  |
| Component source of truth           | HTML partial in `_includes/components/` + matching CSS block in `components.css` + manifest entry in `_data/components.yml`. Build fails if any of the three drift. |
| Future post design                  | GLM-style: centered title + lede, bite-sized sections, research/evidence-based, interactive components composed from the library |

## What this gets us

- Every page on the site composes the same design-system components. No drift between `/SpielEngine`, the GLM post, and any future post.
- Markdown is fully gone — the styling conflict is structurally impossible because there is no markdown processor in the post pipeline.
- A new interactive component (e.g. `comparison-slider`, `data-viz-card`) is added once as a partial + CSS block, then every post that needs it can use it.
- The `/design-system/` page is the living catalog (what ui.shadcn.com does, but in-repo, served from the site).
- Token changes (brand color, type scale) happen in one YAML file and propagate. Single source of truth, literal sense.

## What we will NOT do

- No React, no Tailwind, no Radix, no Vite. Jekyll stays. GitHub Pages deploy stays.
- No visual changes on first pass. Every existing page and post keeps its current look.
- No premature redesign of posts. Phase 4 is post-by-post, user-driven.
