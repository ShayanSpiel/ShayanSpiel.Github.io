# Website implementation guidance

Restored website guidance from the earlier operating document. Ownership is
governed by root `AGENTS.md`; current routes and funnel architecture are
documented in `docs/site-architecture.md`. Source files are authoritative
when an older example here names a route or component that has changed.
Company Skills and workflow execution stay in the local company home.

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
- Keep Persian copy natural and consistent with the centralized translation helpers.

### Font

Use the font families and RTL rules declared in `src/assets/fonts/fonts.css`
and `src/styles/base.css`. Preserve Persian glyph coverage, legibility, and
locale-specific heading weights when changing typography.

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

Default nav: Services → `/services/`, Solutions → `/solutions/`
(one mega menu with four labeled categories: AI Departments →
`/solutions/ai-departments/` with Design, Content, Marketing, SEO,
Analytics and the Design Template Gallery; By Workflow →
`/solutions/workflows/` with the 8 `WORKFLOW_SOLUTIONS` pages; Software
Automation → `/solutions/software/` with 14 of the `SOFTWARE_SOLUTIONS`
pages; SpielOS → AI Company → `/features/` with Director, Departments,
Workflows, Agents, Skills, Evals, Connections, Artifacts),
Pricing → `/pricing/`, Live → `/live/`, Notes → `/notes/`, Founder → `/founder/`.
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

Default footer (`FOOTER_LINKS.default`): Agent Brief, Services, Pricing,
Apply, Partners, Features, Live, Notes, Founder, Contact. The "SpielOS"
wordmark is rendered from `SITE.name` as a text label, not a link.
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

Tokens mirror `packages/design-system/src/tokens/` in the companion SpielOS
product repo (path is environment-specific; resolve it from your local
checkout, e.g. via a `SPIELOS_PRODUCT_REPO` environment variable). When they
change upstream, copy the palette and `semantic-*.css` files into
`src/styles/tokens/`, then re-add the website-only `--panel-deep` extension
(the app has no alternating-section surface). The RTL font override in
`index.css` keeps IRANSansX (not Vazirmatn).

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

The design language uses slightly-rounded squares only — **no pills, no
circles**. Maximum roundness is `--radius-md`.

| Token | Value | Use |
|---|---|---|
| `--radius-sm` | 4px | Small elements, tags |
| `--radius-md` | 6px | Everything else — cards, buttons, containers, badges |

The former `--radius-lg`, `--radius-xl`, and `--radius-pill` tokens (and the
`rounded-lg`/`rounded-xl`/`rounded-pill`/`rounded-full` utilities) are removed.
Do not reintroduce them; use `rounded-md`.

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
- `rounded-sm`, `rounded-md` (maximum — the scale has no pill, circle, or large radii)
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

Font declarations in `src/assets/fonts/fonts.css` are authoritative. Use
Outfit for body/UI and DM Serif Display sparingly where declared by the
public design system; preserve Persian font coverage for RTL routes.
Use local font files and `font-display: swap`.

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

Exports: `SITE`, `AUTHOR`, `FOUNDER`, `SEO`, `SOCIAL`, `ANALYTICS`, `FORMS`,
`APPLY_PATH`, `BOOKING_LINK`, `BOOKING_CONFIG`, `AGENT_BRIEFING_PATH`,
`AGENT_BRIEF_REQUEST_PATH`, `NAV_LINKS`, `FOOTER_LINKS`, `THEMES`, `RSS`,
`SUPABASE`. The former `WAITLIST_URL`, `SERVICES_PATH`, and `BOOKING_URL`
aliases have been removed — do not reintroduce them.

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
