# SpielOS website architecture

This document is the current operating model for the public website. `AGENTS.md`
contains implementation rules; this file describes the business and ownership
model those rules support.

## Commercial objective

The site converts qualified visitors into two outcomes:

1. Buyers who want an AI workflow implemented.
2. Leads who are not ready to buy but will start a conversation, request an
   Agent Brief, or continue learning through notes and feature pages.

The primary buyer path is `/services/`. The existing Agent Brief experience
remains available at `/services/agent-brief/` and the services page. Do not
replace it with a generic CTA page.
The general fallback is `/contact/`. `/waitlist/` is a protected legacy product
route and must not be used as the default site CTA.

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
Homepage, founder story, notes, features
        ↓
Services implementation offer and Agent Brief assessment
        ↓
Agent Brief or contact form
        ↓
Qualified buyer conversation
```

## Route ownership

| Area | Routes | Owner |
|---|---|---|
| Positioning | `/`, `/founder/`, `/about/` | Page components + `src/config.ts` |
| Buyer conversion | `/services/`, `/services/agent-brief/` | Services pages + `ContactModal` |
| General leads | `/contact/`, `/contact/thank-you/` | Contact page + `FORMS` config |
| Product education | `/features/**`, `/use-cases/` | `FeaturesLayout` + feature components |
| Founder-led content | `/notes/**` | Notes collection + post components |
| Legacy product | `/waitlist/`, `/fa/waitlist/` | Protected showcase components |
| Migration redirects | `/posts/**`, `/shayan/` | Redirect page files |

`/use-cases/`, `/contact/thank-you/`, `/fa/contact/thank-you/`, and archived
product pages are not indexable. They may remain crawlable so search engines
can process their robots directives.

## Shared sources of truth

- Site identity, conversion paths, navigation, footer, analytics IDs:
  `src/config.ts`
- English and Persian UI copy: `src/i18n/translations.ts`
- URL and locale helpers: `src/i18n/index.ts`
- Global metadata, analytics, consent, and organization schema:
  `src/layouts/BaseLayout.astro`
- Standard page shell: `src/layouts/Page.astro`
- Feature shell and breadcrumbs: `src/layouts/FeaturesLayout.astro`
- Canonical ICP: `.agents/company/strategy/icp.md`
- Active skills: `.agents/skills/`

## Conversion analytics

Conversion events use the generic `lead_*` vocabulary. The legacy waitlist form
is tagged with `form_type: waitlist_legacy`; it is not treated as the primary
business funnel.

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

## Validation commands

```bash
npm run typecheck
npm run lint
npm run build
npm run seo:check
npm test
```

The build creates `dist/`; the SEO checker validates the built artifact rather
than source assumptions.
