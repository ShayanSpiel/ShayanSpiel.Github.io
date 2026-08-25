# SpielOS Website

The bilingual buyer and lead-conversion website for [SpielOS](https://spielos.xyz), built with Astro and deployed as static HTML on GitHub Pages.

## Stack

- Astro 5 with MDX content collections
- Tailwind CSS backed by semantic design tokens
- English and Persian thin-wrapper routes, including RTL support
- Local Outfit, JetBrains Mono, IRANSansX, and subset Boxicons fonts
- GA4 and PostHog full-capture analytics
- AOS scroll animation with reduced-motion support

## Conversion architecture

The primary journey is Homepage → Services/Solutions/Pricing → Apply. The current route inventory and ownership rules live in [docs/site-architecture.md](docs/site-architecture.md). Repository constraints, i18n rules, tokens, and protected scope live in [agents.md](agents.md).

Main route families:

- `/`, `/founder/`, `/notes/`, `/contact/`, `/live/`
- `/services/`, `/services/agent-brief/`, `/pricing/`, `/apply/`
- `/solutions/ai-departments/`, `/solutions/workflows/`, `/solutions/software/`
- `/features/` and its eight feature detail pages
- `/partners/` and `/landing/lead-researcher/`
- `/fa/**` thin wrappers for every live route

Legacy software and use-case paths are retained only as 301 redirect stubs. Transactional success pages, the archive, and the 404 page are `noindex`.

## Commands

```bash
npm install
npm run dev
npm run lint
npm run build
npm run seo:check
npm test
```

`npm run icons:generate` rebuilds the committed Boxicons glyph subset from icon names used outside the protected showcase.

## Source layout

```text
src/
  components/       Shared UI; showcase/ is protected legacy scope
  content/          English and Persian MDX notes
  data/             Typed solution and live-state data
  i18n/             Locale helpers and the translation source of truth
  layouts/          Shared document, SEO, analytics, navigation, and footer shell
  pages/            English routes plus Persian thin wrappers
  styles/           Semantic tokens, base rules, utilities, and icon subset
scripts/            Build, architecture, link, analytics, SEO, and asset checks
test/               Built-site contract tests
docs/               Current website architecture
.agents/            Company and website operating skills
```

## Design and performance rules

- Use semantic color, spacing, radius, and motion tokens; do not hardcode visual values.
- Use Boxicons only for interface icons. The subset CSS is generated; the full library is not shipped.
- Maximum component radius is `rounded-md`.
- Keep content static by default. Client scripts must support a real interaction or measurement requirement.
- Images require dimensions, useful alt text, and lazy loading below the fold.
- UI strings belong in `src/i18n/translations.ts`.

## SEO

`BaseLayout.astro` owns canonical metadata, hreflang, social metadata, and stable Organization, Person, and WebSite entities. Page schemas describe only visible page content. The sitemap excludes redirects and `noindex` pages.

Pushes to `main` run the GitHub Pages deployment workflow for `spielos.xyz`.
