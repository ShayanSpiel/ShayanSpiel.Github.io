# AGENTS.md — SpielOS Website

## What this site is

This is Shayan Spiel's personal founder website and the public face of SpielOS.
One commercial objective: send qualified visitors to the SpielOS waitlist.

## Protected scope

The `/waitlist` route and everything exclusively supporting it is protected.
Do not edit, refactor, rename, move, redirect, or modify any file under:
- `src/pages/waitlist.astro`
- `src/components/showcase/*`

Exception: the waitlist is now fully locale-aware like the rest of the site.
All user-facing strings live in `src/i18n/translations.ts` under the `waitlist.*`
key namespace. Never add hardcoded English text to showcase components; always
route through `t(locale, "waitlist.*")`. `src/pages/fa/waitlist.astro` is the
thin FA wrapper (matches all other FA pages).

All homepage CTAs link to `/waitlist/`.

## Routes

| Route | File | Purpose |
|---|---|---|
| `/` | `src/pages/index.astro` | Founder-led homepage (EN) |
| `/founder/` | `src/pages/founder.astro` | Complete founder story (EN) |
| `/notes/` | `src/pages/notes/index.astro` | Notes index (EN) |
| `/notes/[slug]/` | `src/pages/notes/[...slug].astro` | Individual note pages (EN) |
| `/contact/` | `src/pages/contact.astro` | Business contact form (EN) |
| `/waitlist/` | `src/pages/waitlist.astro` | Product landing + waitlist (locale-aware) |
| `/about/` | `src/pages/about.astro` | SpielOS about page (EN) |
| `/fa/` | `src/pages/fa/index.astro` | Homepage (FA) |
| `/fa/about/` | `src/pages/fa/about.astro` | About page (FA) |
| `/fa/founder/` | `src/pages/fa/founder.astro` | Founder story (FA) |
| `/fa/notes/` | `src/pages/fa/notes/index.astro` | Notes index (FA) |
| `/fa/notes/[slug]/` | `src/pages/fa/notes/[...slug].astro` | Individual note pages (FA) |
| `/fa/contact/` | `src/pages/fa/contact.astro` | Contact form (FA) |
| `/fa/waitlist/` | `src/pages/fa/waitlist.astro` | Product landing + waitlist (FA) |
| `/features/` | `src/pages/features/index.astro` | Features hub — four-layer architecture (EN) |
| `/features/chat/` | `src/pages/features/chat/index.astro` | Chat hub — execution modes (EN) |
| `/features/chat/director-mode/` | `src/pages/features/chat/director-mode.astro` | Director Mode — long-running agent sessions (EN) |
| `/features/chat/direct-mode/` | `src/pages/features/chat/direct-mode.astro` | Direct Mode — workflow execution and scheduling (EN) |
| `/features/context/` | `src/pages/features/context/index.astro` | Context hub — files, strategy, memory (EN) |
| `/features/context/files/` | `src/pages/features/context/files.astro` | Files — agent knowledge base (EN) |
| `/features/context/strategy/` | `src/pages/features/context/strategy.astro` | Strategy — prompt and instruction management (EN) |
| `/features/context/memory/` | `src/pages/features/context/memory.astro` | Memory and Dreaming — persistent agent memory (EN) |
| `/features/harness/` | `src/pages/features/harness/index.astro` | Harness hub — agents, skills, workflows, evals (EN) |
| `/features/harness/agents/` | `src/pages/features/harness/agents.astro` | Agents — AI employees and roles (EN) |
| `/features/harness/skills/` | `src/pages/features/harness/skills.astro` | Skills — reusable agent capabilities (EN) |
| `/features/harness/workflows/` | `src/pages/features/harness/workflows.astro` | Workflows — multi-agent pipelines (EN) |
| `/features/harness/evals/` | `src/pages/features/harness/evals.astro` | Evals — agent quality testing (EN) |
| `/features/infrastructure/` | `src/pages/features/infrastructure/index.astro` | Infrastructure hub — providers and connections (EN) |
| `/features/infrastructure/providers/` | `src/pages/features/infrastructure/providers.astro` | Providers — model and LLM selection (EN) |
| `/features/infrastructure/connections/` | `src/pages/features/infrastructure/connections.astro` | Connections — MCP, OAuth, API integrations (EN) |
| `/use-cases/` | `src/pages/use-cases/index.astro` | Use cases hub (EN) |
| `/guides/` | `src/pages/guides/index.astro` | Guides hub (EN) |
| `/shayan/` | `src/pages/shayan.astro` | 301 redirect to `/founder/` |
| `/posts/` | `src/pages/posts/index.astro` | 301 redirect to `/notes/` |

FA wrappers exist for all routes under `/fa/` following the thin-wrapper pattern.

Do not add: pricing, services, enterprise, marketplace, solutions, consulting, templates, teams.

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
- Canonical URLs point to EN versions

## Navigation

Single source of truth: `src/config.ts` → `NAV_LINKS`.

Default nav: SpielOS → `/waitlist/`, Notes → `/notes/`, Founder → `/founder/`, Contact → `/contact/`.
CTA button: "Join waitlist" → `/waitlist/`.

Showcase nav (waitlist page only): anchor links to page sections.

## Footer

Single source of truth: `src/config.ts` → `FOOTER_LINKS`.

Default footer: SpielOS, Notes, Founder, Join waitlist.
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

### Semantic color tokens

| Token | Use |
|---|---|
| `--background` | Page background |
| `--panel` | Card/section background |
| `--panel-raised` | Elevated card background |
| `--panel-strong` | Strong panel background |
| `--foreground` | Body text |
| `--foreground-strong` | Headings, strong text |
| `--foreground-muted` | Subtle text |
| `--muted-foreground` | Secondary text, descriptions |
| `--primary` | Brand/accent color |
| `--primary-soft` | Primary at 20% opacity |
| `--primary-foreground` | Text on primary |
| `--border` | Default borders |
| `--border-strong` | Emphasized borders |
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

Located in `.agents/skills/`:

- `translation-fa/SKILL.md` — Persian translation quality rules, terminology, voice, UX surface guidelines
- `spielos-ui/SKILL.md` — UI polish workflow, token hierarchy, state contracts, verification
