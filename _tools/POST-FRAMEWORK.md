# Blog Post Framework

How a Shayan Spiel blog post is built. This is the framework, not a recipe — components, icons, and the visual treatment of each section are chosen to fit the content.

A post is a sequence of **rhythm blocks**. Every block has a role. The post reads as one because the rhythm blocks always appear in the same order, but the *content* and *visuals* of each block are chosen per post.

## The rhythm

```
[chrome]    breadcrumb → hero → post-meta
[body]      section → section → section → … → closer
[chrome]    end-sep → tags → related → post-cta
```

`[chrome]` is rendered automatically by `_layouts/post-shell.html`. You never write it. You write `[body]`.

Between body sections, put `<hr class="divider">`. Don't put dividers inside sections.

## Each block, what it does

### `hero`
The first thing the reader sees. You write it. Has the H1 (silver gradient, large, centered) and the lede (one sentence, max 60ch, centered, `--tx-2`). The post-shell gives you nothing here — the H1 lives in your body, in a `<section class="hero">`.

### `post-meta`
One line below the hero: category · date · author. Centered. Use `{% include components/post-meta.html %}` right after the hero closes. This is the only block the post-shell injects mid-body.

### `section`
The unit of body. Has a `section-head` (tag → title → sub) and 1–3 components. Pick the section type that fits what you're saying:

- **the trap** — sets up a contrast or wrong assumption. prose-center, then a takeaway.
- **the new model** — defines the new thing. definition card + grid-2 of old vs new.
- **the mechanism** — how it works. step-list with N items.
- **by the numbers** — real statistic + benchmark. two stat cards with a smooth prose transition.
- **the proof** — the evidence. pullquote + supporting prose.
- **the window** — why now. stat-shifts or grid-3 with current state.
- **the objection** — the honest answer. pullquote + counter.
- **what shifts** — three numbered changes for the reader. grid-3 of stat-shift cards.
- **the framework** — a deeper breakdown. multi-part grid, more components.
- **the close-of-section** — your last section can be a question, a moment, or a single sentence.

Section rule: **at least one real statistic somewhere in the body**. Either your own number, or an industry benchmark with the source named in the description.

### `takeaway`
A single line that captures the section's insight. Lightbulb icon + text, regular weight, inline. One per section, at the end. Use it sparingly — only on the most important sections.

### `closer`
The last block before chrome. Distinct from sections. A large relevant icon in a circle, a silver-gradient key line, a smaller echo line, optional minimal actions. Use once per post. The icon should be specific to the post's thesis (rocket for launch, sparkles for new, lightbulb for insight, target for goal).

## What you write vs. what the layout gives you

You write:
- The hero (H1 + lede)
- Each section's body
- The closer

Layout gives you (don't write these):
- Centered breadcrumb above the hero
- Post-meta line below the hero
- End separator (· · ·)
- Centered tag chips
- Related posts (3 cards, from `related:` → cluster → tags)
- Post-cta (the original design, auto-appended)

## Components (your palette, not your script)

These exist in `_includes/components/`. Pick what fits. Don't force the same combination twice in a row.

| Component | When it fits | Notes |
|---|---|---|
| `section-head` | First thing in every section | tag → title → sub |
| `prose-center` | Reflective text, one paragraph | max 60ch, centered |
| `takeaway` | One-line insight, end of a section | regular weight, lightbulb, inline |
| `definition` | Defining a term | term + short def. Skip the `mark` slot — keep clean |
| `step-list` | A 2–5 step process | use when order matters |
| `pullquote` | A single line of evidence | with attribution |
| `card` | A facet, example, or stat | add `icon=` for visual variety |
| `card` + `variant="stat-shift"` | Big number or shift | add `icon=` for visual variety |
| `grid-2`, `grid-3` | Side-by-side comparison | 768px breakpoint to single column |
| `data-table` | Comparison data | caption below |
| `tweet-frame` | Real X quote | lazy-load widget.js |
| `chart-box` | Real chart data | Chart.js |
| `closer` | Post closer | once per post, last block |
| `btn` | Calls to action | primary, ghost, arrow, icon variants |

## Icons

The site uses [Lucide](https://lucide.dev) icons, MIT-licensed. The full set lives in `_data/icons.yml`. Add more by appending to that file.

```liquid
{% include components/icon.html name="rocket" size=24 %}
{% include components/icon.html name="arrow-right" size=16 class="my-class" %}
```

Use icons:
- In the **closer** (always, large, in a circle)
- In **takeaway** (lightbulb, always)
- In **card** (decorative, leading)
- In **stat-shift** (decorative, above the number)
- In **btn** (leading, before the label)
- In **breadcrumbs** (home icon, small)

**Don't use icons just to use icons.** An icon that doesn't add meaning is decoration. Reach for them where they clarify, not where they fill space.

## How to turn written content into a post

1. **Read the source.** Skim first. Find the thesis sentence (the one line the post must leave the reader with).
2. **Find the rhythm blocks.** Go through and tag each paragraph: trap, model, mechanism, numbers, proof, window, objection, shifts, or none-of-the-above. Most posts have 6–8 of these.
3. **Drop what doesn't earn a section.** If a paragraph doesn't support a rhythm block, cut it.
4. **Write the hero.** Short H1 (can be punchier than the front matter title). One-sentence lede from the post's main claim.
5. **Write the closer first.** Force yourself to know the key line before writing the body. The closer is the post's thesis in one line. If you can't write it, the post isn't ready.
6. **Build each section.** section-head + 1–3 components. Pick the component that fits the section's intent, not the one that fits the rhythm. No two consecutive sections should look identical.
7. **Add the real stat.** Find one number from your own data, or one industry number with the source cited. Put it in the section where it proves the most.
8. **Wire the chrome.** Front matter: `permalink: /<3-4-word-slug>/`, `related: [3 explicit posts]`, `categories: [one]`, `tags: [3–5]`.
9. **Build, serve, look at it.** `bash scripts/build.sh` then `bundle exec jekyll serve`. Open the post in Chrome. If two sections look the same, change one. If the closer doesn't feel like a closer, rewrite it.

## Constraints

These are hard rules, not suggestions. Build fails if they're violated.

- No markdown in the post body. HTML only.
- One CTA in the whole post. That's the auto-appended post-cta. Do not add a `cta-card` in the body.
- URL must be 3–4 words max. No stop words.
- Every component partial, CSS class, and CSS variable must be in the design system manifest. If you need a new one, add it.
- Every post closes with a `closer`. No exceptions.

## See also

- `_data/components.yml` — every component, its slots, its example
- `_data/icons.yml` — every icon, with its Lucide path
- `_data/design-tokens.yml` — every color, spacing, type value
- `_data/clusters.yml` — post clusters for related-post fallback
- `/design-system/` — the live catalog, auto-generated
