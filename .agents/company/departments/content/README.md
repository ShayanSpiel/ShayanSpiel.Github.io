# Content Department

Content carries one customer-relevant idea from strategy to publication in one
versioned campaign Artifact. The Artifact remains cohesive; the writer sees
only the short creative brief, while production metadata is added afterward.

## Creative brief

Each piece locks five short fields:

- `reader`
- `customer_moment`
- `one_idea`
- `desired_result`
- optional `proof`

The piece is written from this brief. Platform renditions may add or subtract a
line, but cannot change the idea. SpielOS and the CTA are optional unless the
piece is the fifth-item reminder.

Every fifth paired idea is `spielos-reminder` and uses the company reminder in
`strategy/voice.md`. It may cite one public proof point. It must not become an
internal run log.

## Platform-native copy

- Threads uses real paragraphs and bullets. A caption link appears on its own
  line after the CTA.
- YouTube Shorts never contains a UTM URL. When relevant, it says `Link in bio.`
- Literal `\n` and `\r` markers are rejected before approval and dispatch.
- A product bridge or CTA is not required on every post.

## Production handoff

After copy is complete, the same Artifact receives design, rendering,
approval, Buffer, and analytics fields. These fields preserve the identity
chain `campaign_id → batch_id → item_id → content_id → creative_signature`, but
they are not writing instructions.

The daily target remains 50 Threads posts and 50 YouTube Shorts in batches of
five paired ideas. Each batch has one approval. Experiments and attribution
remain delivery and measurement metadata; they never expand the creative
prompt.

Campaign phases remain:

`strategy → designed → rendered → approved → delivered → measured → evaluated`

Generated Artifacts belong under `.spielos/artifacts/`.
