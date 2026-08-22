# AGENTS.md — SpielOS Website

## Company operating runtime

When the selected role is Director, it is the SpielOS operating Director, not a
generic coding or website agent. It owns business-goal intake, Department
routing, durable run supervision, evidence judgment, approvals, and outcome reporting.
It must identify itself accordingly and route unrelated implementation to
Build/default mode unless the user attaches that work to a company goal.

For business goals and company orchestration, use `.agents/company/` as the
durable authority and `.agents/skills/director/SKILL.md` as the operating
procedure. The public loop is only GOAL → OBSERVE → DECIDE → ACT → EVALUATE.
Stage, internal step, run status, and goal status are independent. The runtime
owns every goal. Departments supply domain behavior through colocated
`department.py` handlers and may run directly or as child goals of the Director. Workflows and
agents never own another loop. Never bypass runtime approvals or infer
live-execution permission from a chat request.

Runs are first-class and typed: business experiment, execution, diagnostic,
system improvement, evaluation, or controlled system test. Preserve hypothesis,
owner version, config snapshot, controlled/changed variables, evidence
validity, decisions, evaluation, and resume links. Never learn business lessons
from technical-only, contaminated, or invalid evidence. Department or runtime code changes
must be separate bounded system-improvement goals with allowed files and actual
acceptance-test evidence.

The universal company vocabulary is exactly Goal, Department, Workflow, Agent,
Skill, Connection, and Artifact. Do not introduce Engine, Tool, Port, or
ContentPackage as an additional public layer. `ContentPackage` is only an
Artifact manifest. The complete authority, layout, and OpenCode command surface
are documented once in `.agents/company/README.md`; other READMEs link to it
instead of restating the architecture.

## What this site is

This is Shayan Spiel's founder-led buyer and lead-conversion website for SpielOS.
The commercial objective is to turn qualified visitors into implementation leads
and product buyers through the services, Agent Brief, and contact flows.
The former waitlist destination has been replaced by the Features page and
is not part of the site's conversion path.

## Protected scope

The retired showcase implementation remains protected. Do not edit, refactor,
rename, move, or modify any file under `src/components/showcase/*`.
The commercial funnel is Apply-first (owner directive 2026-08-22): every primary
conversion CTA links to `/apply/` — **Apply — Free Review** — with the microcopy
"Free review · No required call · See the scope before you pay". Contextual CTAs:
"Show Us What Keeps Breaking" (DeSlopping contexts: codex/claude-code/opencode
pages) and "Show Us the Work" (AI Workers contexts: software/use-case pages).
Applying comes before payment; pricing supports the decision and never leads.
Cal booking CTAs are retired — do not reintroduce `data-cal-link`, `cal.com`
embed scripts, or a required-call step anywhere in the funnel. The two services
are AI DeSlopping (fix broken AI-built software) and AI Workers (hand repetitive
work to AI), sold at $2,990/month with one active build at a time. The Live page
is proof ("WE RUN ON AI OURSELVES"), framed as credibility, not a conversion
destination. The legacy waitlist route no longer exists.

## Strategy — single source of truth

`.agents/company/strategy/icp.md` is the canonical Ideal Customer Profile (buyer, exclusions,
positioning idea). Every skill, outbound rule, lead score, and piece of site copy
follows it. Never restate or redefine the ICP in another file — reference it.
The Outbound Department implements it via
`.agents/company/departments/outbound/strategy.md` (execution details only); the campaign data
(master xlsx, `.env`) stays local under `.spielos/data/outbound/` and
`.spielos/.env`; both are gitignored.

Company-wide positioning, voice, and measurement rules live beside the ICP in
`.agents/company/strategy/`. Approved reusable facts and proof live in
`.agents/company/assets/`; channel-specific templates live with their Department.
Skills contain methods, never company truth. Generated drafts and run evidence
belong under `.spielos/artifacts/`, not strategy, assets, or skills.

## Routes

| Route | File | Purpose |
|---|---|---|
| `/` | `src/pages/index.astro` | Founder-led homepage (EN) |
| `/founder/` | `src/pages/founder.astro` | Complete founder story (EN) |
| `/notes/` | `src/pages/notes/index.astro` | Notes index (EN) |
| `/notes/[slug]/` | `src/pages/notes/[...slug].astro` | Individual note pages (EN) |
| `/contact/` | `src/pages/contact.astro` | Business contact form (EN) |
| `/services/` | `src/pages/services.astro` | Buyer-facing AI implementation offer (EN) |
| `/services/agent-brief/` | `src/pages/services/agent-brief.astro` | Agent Brief experience (EN) |
| `/pricing/` | `src/pages/pricing.astro` | One monthly rate — value-first pricing page (EN) |
| `/apply/` | `src/pages/apply.astro` | Apply — Free Review 3-step wizard (EN) |
| `/live/` | `src/pages/live.astro` | Plain-language live company record (EN) |
| `/fa/` | `src/pages/fa/index.astro` | Homepage (FA) |
| `/fa/founder/` | `src/pages/fa/founder.astro` | Founder story (FA) |
| `/fa/notes/` | `src/pages/fa/notes/index.astro` | Notes index (FA) |
| `/fa/notes/[slug]/` | `src/pages/fa/notes/[...slug].astro` | Individual note pages (FA) |
| `/fa/contact/` | `src/pages/fa/contact.astro` | Contact form (FA) |
| `/fa/pricing/` | `src/pages/fa/pricing.astro` | Pricing page (FA thin wrapper) |
| `/fa/apply/` | `src/pages/fa/apply.astro` | Apply wizard (FA thin wrapper) |
| `/fa/live/` | `src/pages/fa/live.astro` | Plain-language live company record (FA) |
| `/fa/waitlist/` | `src/pages/fa/waitlist.astro` | 301 redirect to `/fa/features/` |
| `/fa/features/` | `src/pages/fa/features/index.astro` | Buyer-facing features — company lego blocks (FA) |
| `/features/` | `src/pages/features/index.astro` | Buyer-facing features — the one loop and eight real blocks (EN) |
| `/features/director/` | `src/pages/features/director.astro` | Director — the role that owns goals, approvals, evidence, and reports (EN) |
| `/features/departments/` | `src/pages/features/departments.astro` | Departments — reusable business capabilities (EN) |
| `/features/workflows/` | `src/pages/features/workflows.astro` | Workflows — repeatable playbooks inside a Department (EN) |
| `/features/agents/` | `src/pages/features/agents.astro` | Agents — bounded executors for workflow steps (EN) |
| `/features/skills/` | `src/pages/features/skills.astro` | Skills — reusable methods agents follow (EN) |
| `/features/evals/` | `src/pages/features/evals.astro` | Evals — LLM-as-judge quality gates (EN) |
| `/features/connections/` | `src/pages/features/connections.astro` | Connections — approved access to external systems (EN) |
| `/features/artifacts/` | `src/pages/features/artifacts.astro` | Artifacts — output and evidence from every run (EN) |
| `/software/` | `src/pages/software/index.astro` | Software automation solutions hub (EN) |
| `/{slug}-ai-automation/` | `src/pages/{slug}-ai-automation.astro` | 14 software solution pages from `SOFTWARE_SOLUTIONS` (zapier, slack, gmail, google-drive, hubspot, attio, jira, notion, whatsapp, telegram, claude-code, codex, opencode, google-calendar) (EN) |
| `/use-cases/` | `src/pages/use-cases/index.astro` | Use cases hub (EN) |
| `/use-cases/design/` | `src/pages/use-cases/design/index.astro` | Live Design department use case (EN) |
| `/use-cases/analytics/` | `src/pages/use-cases/analytics/index.astro` | Analytics department use case (EN) |
| `/use-cases/seo/` | `src/pages/use-cases/seo/index.astro` | SEO department use case (EN) |
| `/use-cases/marketing/` | `src/pages/use-cases/marketing/index.astro` | Marketing department use case (EN) |
| `/use-cases/content/` | `src/pages/use-cases/content/index.astro` | Content department use case (EN) |
| `/contact/thank-you/` | `src/pages/contact/thank-you.astro` | Contact form success page (`noindex`) (EN) |
| `/use-cases/design/gallery/` | `src/pages/use-cases/design/gallery.astro` | Build-driven Design template gallery (EN) |
| `/fa/use-cases/design/` | `src/pages/fa/use-cases/design/index.astro` | Live Design department use case (FA) |
| `/fa/use-cases/design/gallery/` | `src/pages/fa/use-cases/design/gallery.astro` | Build-driven Design template gallery (FA) |
| `/fa/software/` and `/fa/{slug}-ai-automation/` | FA thin wrappers | Software solutions hub + 14 pages (FA) |
| `/fa/use-cases/{analytics,seo,marketing,content}/` | FA thin wrappers | Department use cases (FA) |
| `/spielos-v1/` | `src/pages/spielos-v1.astro` | Archived legacy product page (`noindex`) |

FA wrappers exist for all routes under `/fa/` following the thin-wrapper pattern.

Do not add: enterprise, marketplace, solutions, consulting, templates, teams,
or unrelated lead magnets. Services and implementation pages are part of
the current buyer-conversion architecture.

## i18n architecture

### Locales

- `en` (default) — English, LTR
- `fa` — Persian, RTL

### URL structure

FA pages use `/fa/[route]` prefix. All FA routes are thin wrappers that pass `locale="fa"` to EN components.

### Centralized helpers

Single source of truth: `src/i18n/index.ts`

- `localizePath(path, locale)` — generates localized URL
- `getLocaleFromPathname(pathname)` — detects locale from URL
- `getSwitchLocaleUrl(pathname, locale)` — generates language switcher URL
- `LOCALE_PREFIX` — maps locale to URL prefix (`{ en: "", fa: "/fa" }`)

### Translations

Single source of truth: `src/i18n/translations.ts`

- `t(locale, key, params?)` — returns translated string
- All UI strings live here. Never hardcode text in components.
- Follow `.agents/skills/translation-fa/SKILL.md` for Persian translation quality.

### Font

IRANSansX variable font with `DOTS` axis set to 7 via `@font-face` descriptor.
`unicode-range` restricted to Arabic/Persian characters (no overlap with Outfit).
Persian headings use heavier font-weight (h1=800, h2=700, h3+=600) via `[dir="rtl"]` rules in `base.css`.

### RTL

- `dir="rtl"` and `lang="fa"` set on `<html>` based on locale
- RTL layout overrides in `base.css` (spacing, borders, flex direction, list markers)
- Tailwind RTL utilities used where possible

### SEO

- hreflang alternate tags for EN/FA pages
- Persian meta descriptions (`SITE.descriptionFa`)
- `og:locale` set to `fa_IR` for FA pages
- Canonical URLs self-reference each locale version

## Navigation

Single source of truth: `src/config.ts` → `NAV_LINKS`.

Default nav: Services → `/services/`, Solutions → `/features/`
(three-category dropdown: By Departments → `/use-cases/` with Design,
Content, Marketing, SEO, Analytics; By Software → `/software/` with the 14
`SOFTWARE_SOLUTIONS` pages; Features → `/features/` with Director,
Departments, Workflows, Agents, Skills, Evals, Connections, Artifacts),
Live → `/live/`, Notes → `/notes/`, Founder → `/founder/`.
The Solutions dropdown is rendered by `src/components/Nav.astro` from the
`NavLink.children` category model in `src/config.ts`: one mega menu with three
labeled categories and no second-level sub-menus or flyouts (desktop
hover-intent with a leave-delay and a transparent trigger-to-panel bridge,
focus/Enter open, Esc close, tap-toggle for coarse pointers, mobile category
accordion, RTL-aware). Every menu item carries its own distinct boxicon from
`NAV_ITEM_ICONS`, defined locally in `src/components/Nav.astro`.
Nav order: Services → Solutions → Pricing → Live → Notes → Founder.
Primary navbar CTA: **Apply — Free Review** → `/apply/` (desktop + mobile).
Clicks fire `apply_cta_clicked` with their `data-cta-location`; the funnel event
for a completed wizard submission is `apply_submitted`. The Agent Brief page
remains informational at `/services/agent-brief/` and linked from the services
page.

The retired showcase navigation is not used by any active route.

## Journey signature

The active website journey surfaces are intentionally isolated: the homepage
hero uses `src/components/HomepageHeroJourney.astro` with its own anchor-timed
draw, and `/services/` uses `src/components/HomepageJourneyRail.astro` for the
fixed viewport rail and scroll progress. The old shared background bars and
generic wrappers were retired; the video gallery keeps its own rendered journey
assets under the Design department and does not share website DOM or CSS.

## Footer

Single source of truth: `src/config.ts` → `FOOTER_LINKS`.

Default footer (`FOOTER_LINKS.default`): Agent Brief, Services, Features, Live,
Notes, Founder, Contact. The "SpielOS" wordmark is rendered from `SITE.name`
as a text label, not a link.
Social icons: X, GitHub.
Copyright: dynamic year, "SpielOS is independently built by Shayan Spiel."

## Icons — CRITICAL

**ONLY use boxicons.** No Lucide, no Heroicons, no inline SVGs, no other icon libraries.

Import: `"boxicons/css/boxicons.min.css"` is loaded globally in `BaseLayout.astro`.

Usage pattern — use icon size utility classes, NOT inline `style="font-size:..."`:
```astro
<i class="bx bx-{name} icon-xl"></i>
```

### Icon size utilities

| Class | Size | Use |
|---|---|---|
| `icon-xs` | 10px | Tiny inline icons, tree indicators |
| `icon-sm` | 12px | Small inline icons |
| `icon-md` | 14px | Medium icons, arrows, chevrons |
| `icon-base` | 16px | Default icon size |
| `icon-lg` | 18px | Standard icons in sidebars |
| `icon-xl` | 20px | Card icons, section icons |
| `icon-2xl` | 22px | Featured icons |
| `icon-3xl` | 24px | Large icons |
| `icon-4xl` | 24px | Hero icons, placeholder icons |

### Available boxicons for common concepts

| Concept | Icon class | Notes |
|---|---|---|
| Error / failure / problem | `bx-error` | Diamond shape, use with `text-destructive` |
| Success / done / correct | `bx-check-square` | Square check, use with `text-success` |
| Warning / time / waiting | `bx-time-five` | Clock face |
| Settings / config / complexity | `bx-slider` | Three slider bars |
| People / team / roles | `bx-group` | Multiple people |
| Link / connection / tools | `bx-link` | Chain link |
| Workflow / pipeline / network | `bx-network-chart` | Network nodes |
| Code / development | `bx-code-alt` | Code brackets |
| Layer / stack / context | `bx-layer` | Layered diamonds |
| Task / evaluation / QA | `bx-task` | Checkbox list |
| Location / based in | `bx-map` | Map pin |
| Education / certification | `bx-certification` | Ribbon badge |
| User / person | `bx-user` | Single person |
| Data / analytics | `bx-data` | Database |
| Trending / growth | `bx-trending-up` | Upward chart |
| Tag / category | `bx-purchase-tag` | Price tag |
| World / global | `bx-globe` | Globe |
| Chevron down | `bx-chevron-down` | |
| Chevron left | `bx-chevron-left` | |
| Chevron right | `bx-chevron-right` | |

### NEVER use

- `bx-check-circle` — circle variant, not square
- `bx-x-circle` — circle variant
- `bx-error-circle` — circle variant
- `bx-info-circle` — circle variant
- Any `*-circle` variant
- Any Lucide, Heroicons, or other icon set
- Inline SVGs for icons (except in the showcase `Icon.astro` registry)

## Design tokens

**Zero hardcoding.** All colors, spacing, radii come from CSS custom properties.

### Source of truth

Tokens mirror `packages/design-system/src/tokens/` in the SpielOS repo
(`~/Desktop/projects/spielos`). When they change upstream, copy the palette
and `semantic-*.css` files into `src/styles/tokens/`, then re-add the
website-only `--panel-deep` extension (the app has no alternating-section
surface). The RTL font override in `index.css` keeps IRANSansX (not Vazirmatn).

### Brand mark

Official mark: diamond glyph on a rounded tile (`src/components/SpielOSLogo.astro`,
mirrors the `BrandMark` primitive). The tile follows the active theme
(`bg-panel-raised`), the glyph inherits `currentColor`
(`text-foreground-strong`). Standalone assets (favicon, OG images) use the
static palette: tile `#282828`, glyph `#ebdbb2`.

### Semantic color tokens

| Token | Use |
|---|---|
| `--background` | Page background |
| `--background-deep` | Recessed edge or shell depth |
| `--panel` | Card/section background |
| `--panel-raised` | Elevated card background |
| `--panel-strong` | Strong panel background |
| `--panel-deep` | Website-only alternating-section surface |
| `--input` | Editable control interior |
| `--hover` | Hover surface |
| `--selected` | Selected surface |
| `--border` | Default borders |
| `--border-strong` | Emphasized borders |
| `--ring` | Theme focus ring color |
| `--foreground` | Body text |
| `--foreground-strong` | Headings, strong text |
| `--foreground-muted` | Subtle text |
| `--muted-foreground` | Secondary text, descriptions |
| `--primary` | Brand/accent color |
| `--primary-soft` | Primary at 20% opacity |
| `--primary-foreground` | Text on primary |
| `--success` | Success states |
| `--success-soft` | Success at 20% |
| `--warning` | Warning states |
| `--warning-soft` | Warning at 20% |
| `--destructive` | Error states |
| `--destructive-soft` | Error at 20% |
| `--accent` | Secondary accent |
| `--accent-soft` | Accent at 20% |
| `--purple` | Tertiary accent |
| `--purple-soft` | Purple at 20% |
| `--info` | Info states |
| `--info-soft` | Info at 20% |
| `--code-block` | Code block background |

### Structural tokens

- Motion: `--duration-fast` (120ms), `--duration` (160ms), `--duration-slow` (240ms), `--ease`
- Direction: `--bidi-sign` (+1 LTR, -1 RTL)
- Interaction: `--focus-border`, `--focus-ring` (derived from `--ring`), `--disabled-surface`, `--disabled-border`, `--disabled-foreground`
- Surfaces: `--skeleton-bg`, `--overlay-bg`, glass tokens (`--glass-bg`, `--glass-bg-strong`, `--glass-border`, `--glass-border-strong`, `--glass-blur`, `--glass-blur-strong`, `--glass-shadow`, `--glass-shadow-hover`)
- Shadows: `--shadow-panel`, `--shadow-popover`
- Provider identity: `--provider-*` (theme-independent brand colors)
- Dark themes use `--code-block: <palette>_bg0_h`; light themes use `<palette>_bg1`

### Border radius tokens

| Token | Value | Use |
|---|---|---|
| `--radius-sm` | 4px | Small elements, tags |
| `--radius-md` | 6px | Cards, buttons, containers |
| `--radius-lg` | 10px | Large cards |
| `--radius-xl` | 14px | Hero containers |
| `--radius-pill` | 999px | Badges, pills |

### Font size tokens

| Token | Value |
|---|---|
| `--font-size-3xs` | 10px |
| `--font-size-2xs` | 11px |
| `--font-size-xs` | 12px |
| `--font-size-sm` | 14px |
| `--font-size-base` | 16px |
| `--font-size-lg` | 18px |
| `--font-size-xl` | 20px |
| `--font-size-2xl` | 24px |
| `--font-size-3xl` | 30px |
| `--font-size-4xl` | 36px |
| `--font-size-5xl` | 48px |
| `--font-size-6xl` | 60px |

### Tailwind mappings

Use Tailwind utilities that map to tokens:
- `bg-background`, `bg-panel`, `bg-panel-raised`, `bg-panel-strong`
- `text-foreground`, `text-foreground-strong`, `text-foreground-muted`, `text-muted-foreground`
- `bg-primary`, `text-primary-foreground`, `bg-primary-soft`
- `border-border`, `border-border-strong`
- `bg-success-soft`, `text-success`, `bg-warning-soft`, `text-warning`, etc.
- `rounded-sm`, `rounded-md`, `rounded-lg`, `rounded-xl`, `rounded-full`
- `text-3xs`, `text-2xs`, `text-xs`, `text-sm`, `text-base`, etc.
- `font-sans` (Outfit), `font-mono` (JetBrains Mono)

## Component patterns

### Section structure

Every landing section follows this pattern:
```astro
<section class="relative py-24 sm:py-32">
  <div class="mx-auto max-w-6xl px-6">
    <!-- SectionHeader component or inline header -->
    <!-- Content grid -->
  </div>
</section>
```

For alternating background:
```astro
<section class="relative py-24 sm:py-32 overflow-hidden">
  <div class="absolute inset-0 bg-panel-deep/50"></div>
  <div class="relative mx-auto max-w-6xl px-6">
```

### SectionHeader component

```astro
<SectionHeader
  label="Optional label"
  title="Headline text"
  description="Optional body text"
/>
```

### Card pattern

```astro
<div class="rounded-md border border-border bg-panel p-5">
  <div class="flex h-9 w-9 items-center justify-center rounded-md bg-{color}-soft mb-3">
    <i class="bx bx-{icon} text-{color} icon-xl"></i>
  </div>
  <h3 class="text-sm font-semibold text-foreground-strong mb-1">Title</h3>
  <p class="text-xs text-muted-foreground leading-relaxed">Description</p>
</div>
```

### Button patterns

Primary:
```astro
<a href="..." class="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground px-6 h-11 text-sm font-semibold hover:brightness-110 active:brightness-95 transition-all">
```

Secondary:
```astro
<a href="..." class="inline-flex items-center justify-center rounded-md border border-border bg-panel px-6 h-11 text-sm font-medium hover:bg-panel-raised hover:border-border-strong transition-all">
```

### AOS animations

All sections use `data-aos="fade-up"` for scroll animations.
AOS is initialized in `BaseLayout.astro` with `duration: 550, once: true, offset: 60`.

## Fonts

- **Outfit** (sans-serif): variable weight 100-900, loaded from `src/assets/fonts/`
- **JetBrains Mono** (monospace): weight 400-600, loaded from `src/assets/fonts/`
- **IRANSansX** (Persian): variable weight 100-1000, DOTS axis 7, loaded from `src/assets/fonts/iransansx/`
- All use `font-display: swap`

## Content collection

Collection name: `notes` (in `src/content/notes/`).

Schema:
```ts
{
  title: string
  description: string
  date: string (transformed to Date)
  permalink: string
  tags: string[]
  image?: string
}
```

## Configuration

Single source of truth: `src/config.ts`.

Exports: `SITE`, `AUTHOR`, `FOUNDER`, `SEO`, `SOCIAL`, `ANALYTICS`, `FORMS`, `WAITLIST_URL`, `NAV_LINKS`, `FOOTER_LINKS`, `THEMES`, `RSS`.

Never hardcode site name, URLs, author info, social links, or metrics in page components.

## SEO

Handled by `src/layouts/BaseLayout.astro`. Each page passes only page-specific values:
- `title`, `description`, `image`, `robots`
- For articles: `ogType`, `publishedTime`, `modifiedTime`, `tags`

hreflang alternate tags are auto-generated for EN/FA pages.
`og:locale` is set to `fa_IR` for FA pages.

## Performance

- Static rendering (SSG)
- No unnecessary client-side JS
- AOS for scroll animations (lightweight)
- Local fonts with `font-display: swap`
- Responsive images with explicit `width`/`height`
- Lazy loading below the fold
- `prefers-reduced-motion` respected by AOS

## Themes

10 themes via `data-theme` attribute on `<html>`.
Default: `gruvbox-dark`.
Theme toggle in footer cycles through all themes.

## Agent skills

The only active skill system is `.agents/skills/`. Do not create a second skill
tree or copy skills into the repository root. Current skills are:

- `analytics` — consent, attribution, GA4, PostHog, and conversion events
- `copywriting-en` / `copywriting-fa` — buyer-focused content creation
- `outbound-email` / `outbound` — lead discovery, qualification, and outreach
- `director` / `department-runner` / `system-improvement` — company operation
- `seo` — crawlability, metadata, schemas, sitemap, and internal linking
- `spielos-ui` — tokens, components, accessibility, and visual contracts
- `translation-fa` — Persian localization and terminology
- `video-creation` — HTML-to-video production

The canonical ICP is `.agents/company/strategy/icp.md`. The website conversion model is
documented in `docs/site-architecture.md`.
