# Content Department

Content is a production Department in the one company runtime. It turns
approved company evidence into briefs, posts, articles, and coordinated
ContentPackages, then routes approved outputs through publishing Connections.
Visual production belongs to Design.

## Shared campaign Artifact

Campaign facts are written once and move through Departments as one versioned
Artifact defined in `../campaign_contract.py`. Content owns the strategy,
context-first hook, platform copy, CTA, measurement hypothesis, and requested
design variables. It does not write copy inside Design templates, invent asset
URLs, create Buffer-shaped dictionaries, or redefine Analytics joins.

Each campaign also declares an experiment: `single-variable`, `a/b`,
`factorial`, or `funnel`; one to three supported variables; one control and at
least one variant cell; assignment method and unit; primary metric, guardrails,
minimum evidence per cell, and analysis method. Sparse evidence defaults the
next batch to one variable. Two or three changes require supported independent
effects or one supported interaction effect.

The immutable identity chain is `campaign_id → batch_id → item_id → content_id
→ creative_signature`. Design, Buffer, and Analytics must return those same
values in their evidence. A campaign advances only through `strategy → designed
→ rendered → approved → delivered → measured → evaluated`; no Department may
skip a phase.

## One Idea Hierarchy

Every brief must reference `.agents/company/strategy/voice.md` and lock three
fields before drafting: the company-promise connection, one topic-specific
idea, and the asset execution (title, supporting argument, evidence, and CTA).
The topic may change across funnels, articles, posts, emails, graphics, and
videos. Each asset still communicates one dominant idea, and every supporting
element must serve it. Reject briefs with competing headlines, unrelated
benefits, or a topic that cannot connect naturally to the company offer.

## Workflows

- `content-package` — evidence, idea lock, brief, produce, review, package.
- `social-post` — topic-specific idea, platform-native draft, and approval.
- `article` — one evidence-backed, search-aware argument in long form.
- `publish` — validate, approve, dispatch, and verify.
- `content-campaign` — package one idea into distinct Threads and YouTube
  Shorts renditions, render the appropriate design-system asset, run the
  duplicate/attribution quality gate, obtain a package-specific approval, then
  dispatch through Buffer.

## Campaign quality and measurement contract

Every `content-campaign` Artifact has five buyer-relevant ideas and a
separate platform package for Threads and YouTube Shorts. Each platform package
must include its own native copy, public rendered image/video, tracked
`https://spielos.xyz/services/` or `/contact/` destination, and end its
description with: `This is SpielOS, An AI company running itself.`

The shared campaign Artifact names the template, layout, website theme, semantic surface
token, semantic color role, and alignment. Raw colors and a repeat of the same
idea/platform/variation signature are rejected. Design uses the registered
`threads-portrait` (1080×1350) and `youtube-shorts` (1080×1920) renditions;
the site token and font rules remain the source of visual truth.

Buffer capacity is read from its live `dailyPostingLimits` response for the
specified channels. The publisher may fill available capacity only with
quality-gated, distinct, individually approved packages; it never guesses a
quota or substitutes a duplicate. Every destination uses `utm_source`,
`utm_medium=social`, one campaign, and a unique `utm_content`, so Analytics can
join platform views and engagement with website visits, CTA clicks, and leads.
The Buffer package is derived only from the approved Artifact and preserves
the exact approval ID and creative signature for every rendition.

## Daily batch cadence

The daily operating target is 50 Threads posts and 50 YouTube Shorts. Content
is prepared as ten reviewable batches of five *paired ideas*, never as one
unexamined queue. Every batch contains five distinct Threads/Shorts pairs and
stops at its own explicit publishing approval; a rejected batch does not allow
the next batch to advance.

Every asset begins with context: the operator's real situation, the operating
problem, and what SpielOS does before it gives advice. Each batch's fifth idea
is a real build-SpielOS-live story: trigger, tension, decision, tradeoff,
harness rule, and next measurable step. It links to `/live/` as proof and keeps
the tracked services CTA as the commercial path. The quality gate stores hook,
context, CTA, narrative type, and creative signatures so Analytics can compare
future views, engagement, CTR, website visits, and lead conversion without
inventing a lesson before evidence exists.

Creative experiments use `scope=cross-channel-creative`; landing-page or form
experiments use `scope=website-cro` and always retain a separate website-change
approval. An experiment plan never authorizes publishing or site mutation.

Generated intermediates and packages belong under `.spielos/artifacts/`.
