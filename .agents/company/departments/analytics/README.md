# Analytics Department

Analytics owns canonical company metrics, the full funnel, attribution,
data-quality checks, scorecards, diagnostics, and bounded CRO experiments.
Other Departments request evidence from Analytics rather than defining rival
metrics. PostHog is a Connection, so the Department survives provider changes.

Analytics accepts only a delivered shared campaign Artifact. Buffer post IDs,
platform metrics, website events, CTA activity, and leads are joined through
`campaign_id`, `batch_id`, `item_id`, `content_id`, and `creative_signature`.
If any of the ten rendition identities is missing or changed, the report is
incomplete and the campaign cannot teach the next batch.

## Content acquisition reporting contract

The daily content scorecard reports only consented, non-PII evidence:

- qualified visits: `content_landing`, segmented by `source`, `campaign`, and
  `content_id`;
- service intent: `cta_clicked` where `cta_type` is `services` or
  `agent_briefing`;
- lead conversion: `lead_form_success` divided by `content_landing`;
- daily leads: `lead_form_success`, attributed to the last content UTM context
  in the same browser session.

Threads and YouTube Shorts must use `utm_source=threads|youtube`,
`utm_medium=social`, one campaign name, and a unique `utm_content` creative
identifier. Analytics events never include form fields or contact details.

The content scorecard joins each platform package's `creative_signature` with
Buffer's post ID and its later views/engagement metrics, then compares those
records with consented `content_landing`, service CTA, and lead events by UTM.
CTR is defined as tracked website visits divided by the platform's reported
views; the 5% website lead-conversion rate is `lead_form_success / content_landing`.
Missing, delayed, or incomparable platform metrics are labelled incomplete and
never treated as business learning.

## Batch-learning loop

The operating cadence is ten batches of five paired Threads/YouTube ideas per
day. For each completed batch, Analytics records `batch_number`, `batch_item`,
`hook_id`, `narrative_type`, CTA, and creative signature alongside platform
views/engagement and consented website activity. It evaluates only comparable,
complete evidence: view rate, click-through rate, content landings, service
intent, and lead conversion. The next batch changes one documented variable by
default. It may change two or three only when a declared A/B, factorial, or
funnel design has complete control/variant cells and the analysis supports
every independent effect or a specific interaction. Otherwise Analytics
narrows the next test to one variable and marks simultaneous uncategorized
changes contaminated.

The `measured` handoff records the evidence window and canonical funnel math.
The `evaluated` handoff names one to three supported variables, the test type,
scope, evidence window, and next-batch hypothesis. Cross-channel creative and
website CRO remain distinct; website mutation always needs its own approval.
This closes the loop into the next Content strategy Artifact without Analytics
rewriting creative or authorizing delivery.
