# SpielOS website architecture

This document is the current operating model for the public website. `AGENTS.md`
contains implementation rules; this file describes the business and ownership
model those rules support.

## Commercial objective

The site converts qualified visitors into two outcomes:

1. Buyers who want an AI workflow implemented.
2. Leads who are not ready to buy but will start a conversation (Discovery
   Call), or continue learning through notes and feature pages.

The primary buyer path is the **Apply — Free Review funnel** at `/apply/`
(fed by `/services/` and `/pricing/`). The navbar CTA on desktop and mobile
points at `/apply/`; clicks fire `apply_cta_clicked` (with their
`data-cta-location`) and a completed wizard submission fires
`apply_submitted`. Cal booking is an optional secondary action only: a small
icon CTA on the Contact and Apply pages ("Not sure?" sections) opens Cal's
native booking embed (popup) right on the page via
`<button data-cal-link="shayanspiel/15min" data-cal-config='{"layout":"month_view","theme":"dark","ui.color-scheme":"dark"}'>`.
`app.cal.com` embed.js loads site-wide with preconnect so that popup opens as
fast as possible. The Agent Brief page remains available as an informational
experience at `/services/agent-brief/` and on the services page; it has no
request form. Do not replace it with a generic CTA page and do not
reintroduce `/book/` navigation or direct cal.com links on conversion CTAs.
The general fallback is `/contact/`, and `/partners/` covers partnership
inquiries. The former `/waitlist/` route is gone entirely; legacy software,
software-hub, and use-case URLs survive only as 301 redirect stubs to the
`/solutions/**` tree and are excluded from the sitemap. The former showcase
implementation remains recoverable in Git history and is not part of the
active funnel.

## One Idea Hierarchy

The website follows the company-wide hierarchy in
`.agents/company/strategy/voice.md`:

1. The company promise anchors the funnel: pursue 2× output at half the
   operating cost, one workflow at a time.
2. Each route or funnel step chooses one topic-specific idea appropriate to its
   job: a problem, mechanism, objection, proof point, lesson, or outcome.
3. Each page executes that topic with one clear title and one argument. Sections
   may expand, explain, and prove it, but they must not compete with it.

Feature pages, notes, and videos do not repeat the services headline by rote.
They explain different parts of the same commercial story and lead naturally
to the next relevant step.

## Audience path

```text
Founder / operator with repetitive work
        ↓
Homepage, founder story, notes, solutions tree, Live
        ↓
Services and pricing, then the Apply — Free Review wizard (primary CTA)
        ↓
Free review application (optional Cal Discovery Call icon CTA or contact form)
        ↓
Qualified buyer conversation
```

## Route inventory

Live routes: `/`, `/founder/`, `/notes/**`, `/contact/` (+ thank-you),
`/services/`, `/services/agent-brief/`, `/pricing/`, `/apply/` (+ thank-you),
`/live/`, `/partners/` (EN + FA twin), `/landing/lead-researcher/`
(EN + FA twin), the full `/solutions/**` tree — hub `/solutions/`,
`/solutions/ai-departments/{index,design,content,marketing,seo,analytics}`
plus `/solutions/ai-departments/design/gallery/`,
`/solutions/workflows/{index,[slug]}` with the 8 `WORKFLOW_SOLUTIONS` slugs,
`/solutions/software/{index,[slug]}` with the 14 `SOFTWARE_SOLUTIONS` keys —
and `/features/**`. FA thin wrappers exist under `/fa/**` for all of them.
Legacy `/{key}-ai-automation/`, `/software/`, and `/use-cases/**` URLs
(EN + FA) remain only as 301 redirect stubs into `/solutions/**`.

## Route ownership

| Area | Routes | Owner |
|---|---|---|
| Positioning | `/`, `/founder/` | Page components + `src/config.ts` |
| Buyer conversion | `/apply/` (+ thank-you), `/services/`, `/services/agent-brief/`, `/pricing/` | Services, pricing, and Apply wizard pages; navbar Apply CTA (`APPLY_PATH`) |
| Solutions IA | `/solutions/**` (departments, workflows, software) | Solutions pages + `SOFTWARE_SOLUTIONS` / `WORKFLOW_SOLUTIONS` data |
| Partnerships | `/partners/` | Partners page + translations |
| Landing pages | `/landing/lead-researcher/` | Landing page component |
| Product education | `/features/**`, `/live/` | Feature layouts and Live page components |
| General leads | `/contact/`, `/contact/thank-you/` | Contact page + `FORMS` config |
| Founder-led content | `/notes/**` | Notes collection + post components |

Thank-you pages (`/contact/thank-you/`, `/apply/thank-you/`, and their FA
twins) are not indexable. The 301 redirect stubs listed above carry no
canonical content and are excluded from `sitemap.xml` in `astro.config.mjs`.
Archived product pages (`/spielos-v1/`) are `noindex, follow`.

## Design department page and the build-driven gallery

The AI Design department lives on two routes:

- `/solutions/ai-departments/design/` - the department case: how it works,
  workflows, agents, skills, connections, artifacts, and the Changes-live
  registry panel. Indexable, with EN/FA canonical and hreflang pairs and
  breadcrumb JSON-LD. The old `/use-cases/design/` URL 301-redirects here.
- `/solutions/ai-departments/design/gallery/` - a categorized template
  gallery that is rebuilt from the live registry at every deploy, showing
  every registered Design archetype: motion (kind `shorts`) and stills
  (kind `social`), plus the legacy core set and badges for New (v3.4
  additions via `content_relevance`) and Preview (unconfirmed,
  `confirmed: false`). The old `/use-cases/design/gallery/` URL
  301-redirects here.

Persian thin wrappers at `/fa/solutions/ai-departments/design/` and
`/fa/solutions/ai-departments/design/gallery/` pass `locale="fa"` to the
same components.

Build data flow for the gallery:

1. Archive list is read from
   `.agents/company/departments/design/templates/registry.json` at build time
   (`readFileSync` in `gallery.astro`) - it is never hardcoded on the page,
   and the registry itself is read-only for the site.
2. Committed renders under `public/design-gallery/` are matched by archetype
   `id`: MP4 + JPEG poster for motion, PNG for stills. Entries without a
   render fall back to a polished icon card.
3. Rebuilding the site after a registry change updates the public gallery
   automatically. Badges and composition-source lines come from the registry
   entry plus `useCases.design.gallery.*` translations.

Navigation: the default nav renders the Solutions dropdown as one flat
four-category mega menu (AI Departments column: Design, Content, Marketing,
SEO, Analytics, Design Template Gallery; By Workflow column: the 8
`WORKFLOW_SOLUTIONS` pages; Software Automation column: 14 of the
`SOFTWARE_SOLUTIONS` pages; SpielOS → AI Company column: Director,
Departments, Workflows, Agents, Skills, Evals, Connections, Artifacts) from
the `NavLink.children` category model in `src/config.ts`;
`src/components/Nav.astro` renders it (desktop hover-intent with a leave
delay and a transparent trigger-to-panel bridge, focus/Enter open, Esc close,
tap-toggle for coarse pointers, mobile category accordion, RTL-aware). There
are no second-level sub-menus or flyouts. Every menu item carries its own
distinct boxicon. The Live dot is preserved and the primary navbar CTA is
the Apply funnel link (`apply_cta_clicked`).

The active website journey surfaces are isolated. The homepage hero uses
`src/components/HomepageHeroJourney.astro` with its own anchor-timed draw;
`src/components/HomepageJourneyRail.astro` owns the fixed viewport rail on
`/services/`. Background journey bars were retired from the rest of the site.
The Design video gallery remains independent and uses its own rendered journey
assets under `.agents/company/departments/design/templates/`.

## Shared sources of truth

- Site identity, conversion paths, navigation, footer, analytics IDs:
  `src/config.ts`
- English and Persian UI copy: `src/i18n/translations.ts`
- URL and locale helpers: `src/i18n/index.ts`
- Global metadata, full-capture analytics, and stable Organization, Person, and WebSite schemas:
  `src/layouts/BaseLayout.astro`
- Standard page shell: `src/layouts/Page.astro`
- Feature shell and breadcrumbs: `src/layouts/FeaturesLayout.astro`
- Canonical ICP: `.agents/company/strategy/icp.md`
- Active skills: `.agents/skills/`

## Conversion analytics

Apply funnel events (PostHog + GA4) are primary: `apply_cta_clicked` fires
(with `data-cta-location`) when a visitor clicks any Apply CTA, and
`apply_submitted` fires on a completed wizard submission. Cal booking events
remain for the optional icon CTA: `booking_cta_clicked` (with
`cta_type: book_call`) when a visitor clicks a booking CTA; `booked_call`
when the Cal embed (popup) reports a successful booking. The
Cal.com-to-Attio sync captures the booked call separately for the
`booked_calls` metric. `cta_clicked` still covers `/services/` and
primary-action clicks. Contact submissions use the generic `lead_*`
vocabulary; analytics never include form contents or visitor identity.

No event may contain email addresses, names, messages, business descriptions,
or other form contents.

## Indexation policy

Index pages that are complete, useful, unique, and connected to real search
intent. Noindex:

- Placeholder pages
- Form confirmation pages
- Archived pages
- Duplicate migration routes
- Internal utility pages

Every indexable page must have unique title and description, a self-canonical,
valid reciprocal hreflang links, valid structured data where appropriate, and a
direct crawlable internal path from the site navigation or related content.

All former migration-redirect routes (`/architecture/`, `/waitlist/`, `/about/`,
`/fa/about/`, `/shayan/`, `/posts/**`, `/features/chat/**`, `/features/context/**`,
`/features/harness/**`, `/features/infrastructure/**`) were removed as page files.
They no longer exist at any URL.

## Validation commands

```bash
npm run typecheck
npm run lint
npm run build
npm run seo:check
npm run audit:site
npm test
```

The build creates `dist/`; the SEO checker validates the built artifact rather
than source assumptions.
