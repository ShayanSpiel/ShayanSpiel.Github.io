---
name: analytics
description: Implement, review, and preserve SpielOS analytics: GA4, PostHog, Search Console, consent architecture, event taxonomy, attribution, privacy, loader implementation, and analytics verification. Use for any analytics implementation, tag change, event tracking, consent configuration, or analytics debugging. Do NOT use for SEO metadata or structured data — use the seo skill instead.
---

# SpielOS Analytics

SpielOS is a static Astro site (SSG) served at `https://spielos.xyz` with a Persian (`fa`, RTL) mirror under `/fa/`. Analytics must respect user consent, never block rendering, and produce accurate buyer and lead-conversion data across both locales.

## Scope

This skill owns:

- GA4 (Google Analytics 4) implementation and configuration
- PostHog implementation and configuration
- Search Console verification meta tag (presence check; SEO owns the implementation)
- Consent-state architecture
- Event taxonomy and naming
- Attribution (UTM, referrer)
- Privacy-sensitive configuration
- Loader implementation (gtag.js, PostHog JS SDK)
- Analytics verification (DebugView, live events, production checks)

This skill does NOT own:

- SEO metadata, structured data, canonicalization, hreflang, sitemap, robots, redirects, or internal linking (see `.agents/skills/seo/SKILL.md`)
- Editorial voice or copy style (see copywriting skills)

## Before editing analytics

Read these files:

1. `AGENTS.md` — routes, protected scope, i18n rules
2. `src/config.ts` — `SITE`, `ANALYTICS`, `SOCIAL`
3. `src/layouts/BaseLayout.astro` — global head: analytics loaders, event taxonomy
4. `.agents/skills/seo/SKILL.md` — SEO invariants (analytics presence check, not implementation)

### Authoritative files

Treat `src/config.ts` and `BaseLayout.astro` as authoritative. Never hardcode analytics IDs, keys, or hosts in page components.

## Configuration

Single source of truth: `src/config.ts` → `ANALYTICS`:

- `googleAnalyticsId` — GA4 property (current: `G-P43CBK4EEX`)
- `googleSearchConsoleVerification` — Search Console meta token
- `posthogApiKey`, `posthogApiHost` — PostHog instance on `https://t.spielos.xyz`

Never duplicate analytics IDs in page components. All analytics lives in BaseLayout (global) or the analytics skill's shared utilities.

## Loading model

BaseLayout loads analytics in this order:

1. PostHog stub loads the library from `api_host + "/static/array.js"` inline in `<head>`.
2. GA4 commands are queued inline (`window.dataLayer` + `gtag`) with `send_page_view: true`, `cookie_flags: 'SameSite=None;Secure'`, `debug_mode` from config.
3. gtag.js and `posthog.init` run on `requestIdleCallback` (fallback `setTimeout`) so analytics never blocks render.

### Configuration rules

- `debug_mode` must be `false` in production. Only enable for local development or explicit debugging sessions.
- `person_profiles` defaults to `'identified_only'`. Use `'always'` only when a documented requirement justifies anonymous person profiles (e.g., funnel analysis on unauthenticated traffic).
- Session recording is enabled (do not set `disable_session_recording`). Do not set `autocapture` or `capture_pageview` to false — pageviews, autocapture, and session replay must stay on.
- Do not initialize analytics in a way that violates the configured consent state.

### Loader integrity

- Do not add a second loader for GA4 or PostHog.
- If a GTM container is ever added, keep `gtmId` in config and load the GTM snippet instead of the direct gtag loader — never run both.
- Document whether direct gtag or GTM owns Google tracking. Never load both.
- No duplicate GA4, GTM, or PostHog loaders.

## Consent architecture

### Consent states

Analytics behavior must respect consent:

- **Denied**: No GA4 cookies, no PostHog person identification, no event tracking beyond strictly necessary.
- **Accepted**: Full analytics, GA4 cookies set, PostHog initialized with person profiles.
- **Preference changed**: Re-evaluate all analytics based on new consent state.

### Consent implementation

- Consent acceptance, rejection, and preference-change events must be captured and tested.
- GA4's `gtag('consent', ...)` must be called before any `gtag('config', ...)` to set default consent state.
- PostHog initialization must check consent state before calling `posthog.init` or must use PostHog's consent mode.
- Do not send events to GA4 or PostHog before consent is granted (except strictly necessary events if legally required).

### Consent verification

- Test consent acceptance flow: verify GA4 and PostHog start receiving events.
- Test consent rejection flow: verify no analytics events fire.
- Test consent preference change: verify analytics state updates correctly.
- Check that consent state persists across page loads.

## Event taxonomy

Events fire to both gtag and PostHog via a single `track()` helper defined in BaseLayout. Do not add a second event system.

### Defined events

| Event | Parameters | Description |
|---|---|---|
| `lead_form_start` | `form_type` | Lead form opened |
| `lead_form_submit` | `form_type` | Lead form submitted |
| `lead_form_success` | `form_type` | Lead form submission succeeded |
| `lead_form_error` | `form_type` | Lead form submission failed |
| `cta_clicked` | `cta_type`: service_assessment \| primary | CTA button clicked |
| `social_clicked` | `platform` | Social link clicked |
| `outbound_link` | `url`, `link_text` | Outbound link clicked |
| `scroll_depth` | `depth`: 25 \| 50 \| 75 \| 100 | Scroll milestone reached |
| `theme_toggled` | `theme` | Theme changed |

### Event rules

- Event names must be snake_case.
- Parameters must be lowercase.
- Do not send personally identifiable information (PII) in events: no email, name, phone, IP, or address.
- Event deduplication: do not fire the same event twice for a single user action.
- UTM and referrer data must be preserved across navigation where applicable.

## Privacy

- No PII in events, properties, or custom dimensions.
- No tracking pixels or fingerprinting beyond standard analytics.
- PostHog must not capture inputs from form fields.
- IP anonymization is the default for GA4; do not override.
- Privacy-page consistency: analytics behavior must match what the privacy page describes.

## Production versus development

- `debug_mode` must be `false` in production GA4 config.
- PostHog `debug` option must be `false` in production.
- Development environments may enable debug features but must not send production events.
- Environment validation: verify analytics config matches the deployment environment.

## Failed-network behavior

Analytics loaders must degrade gracefully:

- If GA4 script fails to load, queued `gtag` commands silently fail.
- If PostHog script fails to load, PostHog calls silently fail.
- No user-visible errors from analytics failures.
- Analytics failures must not block page rendering or interactivity.

## Verification

### Automated

After analytics changes, run:

```bash
npm run typecheck
npm run build
npm run seo:check
```

`seo:check` validates that analytics loaders are present. For analytics-specific verification, use manual checks.

### Manual

- GA4 DebugView: enable debug mode locally, verify events appear in real-time in GA4 DebugView.
- PostHog live events: verify events appear in PostHog's live events panel.
- Production check: after deploy, verify GA4 Realtime report shows pageviews, PostHog shows events.
- Consent test: in production, verify consent banner behavior matches analytics state.
- Browser DevTools: verify no duplicate GA4 or PostHog network requests.
- Cookie audit: verify GA4 cookies are set only after consent.

### Search Console

- Verify `google-site-verification` meta tag is present in page source (presence only — SEO owns the implementation).
- Verify Search Console property is verified and receiving data.

## Protected scope

Do not edit `src/pages/waitlist.astro` or `src/components/showcase/*`. Their analytics comes from BaseLayout (global) — do not add inline analytics or page-specific tracking inside showcase components.

## Report

After analytics work, report:

- Files changed
- Loader changes (if any)
- Event taxonomy changes (if any)
- Consent behavior changes (if any)
- Configuration changes
- Verification results (automated and manual)
- Any warnings or issues discovered
