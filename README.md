# SpielOS Website

Founder-led pre-launch website for [SpielOS](https://spielos.xyz). English + Persian (RTL) with full i18n.

## What it does

Connects Shayan Spiel's experience and product history to why SpielOS exists, with the waitlist as the single conversion destination.

## Tech stack

- **Framework:** Astro 5 (static site generation)
- **Styling:** Tailwind CSS + CSS custom properties (design tokens)
- **Content:** MDX notes collection
- **Fonts:** Outfit (sans), JetBrains Mono (mono), IRANSansX (Persian) — local woff2
- **Icons:** Boxicons CSS font
- **Animations:** AOS (Animate on Scroll)
- **Analytics:** Google Analytics + PostHog
- **Deploy:** GitHub Pages via GitHub Actions
- **Domain:** spielos.xyz

## Routes

| Route | Description |
|---|---|
| `/` | Founder-led homepage (EN) |
| `/founder/` | Complete founder story (EN) |
| `/notes/` | Notes index (EN) |
| `/notes/[slug]/` | Individual note pages (EN) |
| `/contact/` | Business contact form (EN) |
| `/waitlist/` | Product landing + waitlist (EN, protected) |
| `/about/` | SpielOS about page (EN) |
| `/features/` | Features hub — four-layer architecture (EN) |
| `/features/chat/` | Chat hub — execution modes (EN) |
| `/features/chat/director-mode/` | Director Mode — long-running agent sessions (EN) |
| `/features/chat/direct-mode/` | Direct Mode — workflow execution and scheduling (EN) |
| `/features/context/` | Context hub — files, strategy, memory (EN) |
| `/features/context/files/` | Files — agent knowledge base (EN) |
| `/features/context/strategy/` | Strategy — prompt and instruction management (EN) |
| `/features/context/memory/` | Memory and Dreaming — persistent agent memory (EN) |
| `/features/harness/` | Harness hub — agents, skills, workflows, evals (EN) |
| `/features/harness/agents/` | Agents — AI employees and roles (EN) |
| `/features/harness/skills/` | Skills — reusable agent capabilities (EN) |
| `/features/harness/workflows/` | Workflows — multi-agent pipelines (EN) |
| `/features/harness/evals/` | Evals — agent quality testing (EN) |
| `/features/infrastructure/` | Infrastructure hub — providers and connections (EN) |
| `/features/infrastructure/providers/` | Providers — model and LLM selection (EN) |
| `/features/infrastructure/connections/` | Connections — MCP, OAuth, API integrations (EN) |
| `/use-cases/` | Use cases hub (noindex, placeholder) |
| `/guides/` | Guides hub (noindex, placeholder) |
| `/fa/*` | All FA wrappers (thin wrappers passing `locale="fa"`) |
| `/shayan/` | 301 redirect to `/founder/` |
| `/posts/` | 301 redirect to `/notes/` |

## i18n architecture

- **Locales:** `en` (default), `fa` (Persian, RTL)
- **URL structure:** `/fa/[route]` prefix for Persian pages
- **Centralized helpers:** `src/i18n/index.ts` — `localizePath()`, `getLocaleFromPathname()`, `getSwitchLocaleUrl()`
- **Translations:** `src/i18n/translations.ts` — all UI strings, `t(locale, key)` function
- **FA pages:** Thin wrappers at `src/pages/fa/*.astro` that pass `locale="fa"` to EN components
- **Font:** IRANSansX variable font with `DOTS` axis set to 7 via `@font-face` descriptor
- **RTL:** Automatic `dir="rtl"` and `lang="fa"` on `<html>` based on locale
- **SEO:** hreflang alternate tags, Persian meta descriptions, `og:locale` set to `fa_IR`

## Getting started

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

Output goes to `dist/`.

## Project structure

```
src/
  config.ts              # Single source of truth for all site data
  i18n/
    index.ts             # Locale helpers (localizePath, getSwitchLocaleUrl)
    translations.ts      # All EN/FA translation strings
  content/
    config.ts            # Content collection schema
    notes/               # MDX note files (EN)
    notesFa/             # MDX note files (FA)
  components/
    Nav.astro            # Global navigation
    Footer.astro         # Global footer
    LanguageSwitcher.astro # EN/FA toggle
    SpielOSLogo.astro    # Logo component
    SocialIcons.astro    # Social link icons
    sections/            # Reusable landing page sections
      SectionHeader.astro
      ProofMetrics.astro
      ProductCard.astro
    posts/               # MDX post helper components
      Card.astro
      PostCta.astro
      DataChart.astro
      Pullquote.astro
      Source.astro
      Takeaway.astro
      ProseCenter.astro
      SectionHead.astro
    features/            # Feature page components
      FeatureNav.astro   # Sidebar navigation
      FeatureHero.astro
      FeatureCTA.astro
      FeatureLayer.astro
      Breadcrumbs.astro
    showcase/            # Waitlist page components (protected)
  layouts/
    BaseLayout.astro     # Root HTML layout (SEO, fonts, analytics)
    Page.astro           # Standard page wrapper
    FeaturesLayout.astro # Feature pages with sidebar nav
  pages/                 # Route files
    fa/                  # Persian page wrappers (thin)
  styles/
    tokens/              # Design token CSS files (10 themes)
    global.css           # Global styles + component classes
    base.css             # Reset + RTL overrides
  assets/
    fonts/               # Local font files (Outfit, JetBrains Mono, IRANSansX)
  icons.ts               # Icon registry (boxicons map + validation)
.agents/
  skills/
    translation-fa/      # Persian translation skill
    spielos-ui/          # UI polish skill
```

## Design system

All styling uses semantic CSS custom properties. No hardcoded colors. Token files in `src/styles/tokens/` mirror the SpielOS design system (`packages/design-system/src/tokens/` in `~/Desktop/projects/spielos`) plus the website-only `--panel-deep` extension.

Key tokens: `--background`, `--background-deep`, `--panel`, `--panel-raised`, `--panel-strong`, `--panel-deep`, `--input`, `--hover`, `--selected`, `--foreground`, `--primary`, `--border`, `--ring`, `--success`, `--warning`, `--destructive`, `--accent`, `--purple`, `--code-block`, plus focus/disabled/glass/provider structural tokens.

Border radius: `--radius-sm` (4px) → `--radius-md` (6px) → `--radius-lg` (10px) → `--radius-xl` (14px) → `--radius-pill` (999px).

Brand mark: diamond glyph on a rounded tile (`src/components/SpielOSLogo.astro`). The tile follows the active theme (`bg-panel-raised`), the glyph inherits `currentColor`. Standalone assets (favicon, OG images) use the static palette: tile `#282828`, glyph `#ebdbb2`.

Icon size utilities (in `global.css`): `icon-xs` (10px), `icon-sm` (12px), `icon-md` (14px), `icon-base` (16px), `icon-lg` (18px), `icon-xl` (20px), `icon-2xl` (22px), `icon-3xl` (24px).

See `AGENTS.md` for full token reference and component patterns.

## Icons

Boxicons only. No other icon libraries. No inline SVGs for icons (except in the showcase `Icon.astro` registry).

```astro
<i class="bx bx-{name} icon-xl"></i>
```

See `AGENTS.md` for available icon mapping and the icon registry in `src/icons.ts`.

## Content

Notes live in `src/content/notes/` (EN) and `src/content/notesFa/` (FA) as MDX files. Each note has:
- `title`, `description`, `date`, `permalink`, `tags`, `image` (optional)

## SEO

- Static rendering (SSG) — all pages are pre-rendered HTML
- Canonical URLs on every page
- hreflang alternate tags for EN/FA
- Open Graph and Twitter Card metadata
- JSON-LD structured data on homepage (Person, WebSite, SoftwareApplication)
- RSS feed at `/feed.xml`
- XML sitemap at `/sitemap.xml`
- `robots.txt` with AI crawler policies
- `noindex` on placeholder pages (guides, use-cases, 404)

## Performance

- Static HTML by default, no client-side rendering for content
- Local fonts with `font-display: swap`
- AOS for scroll animations (lightweight)
- ApexCharts loaded dynamically only on pages that use DataChart
- Responsive images with explicit `width`/`height`
- `prefers-reduced-motion` respected

## Deployment

Push to `main` triggers GitHub Actions build → deploys to GitHub Pages.
Custom domain: `spielos.xyz` (via `public/CNAME`).

## License

MIT
