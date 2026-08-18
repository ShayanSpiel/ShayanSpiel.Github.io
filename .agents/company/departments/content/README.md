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

## LLM-as-judge quality gate

Mechanical validation never reads copy for clarity, so campaign copy is judged
against a grounded ICP quality standard before it can advance:

- `departments/content/evals.py` defines `content-copy-top10` (suite id
  `content-copy-top10`): ten criteria — `one_reader`, `one_moment`,
  `one_idea`, `understandable_without_spielos`, `buyer_language`,
  `sharp_opening`, `honest_claims`, `platform_native`, `flow_brevity`,
  `fifth_item_reminder` — each grounded in a canonical strategy/skill source.
  Every criterion must pass (`all_pass`, `min_score` 1.0) per item AND per
  batch, judged PER ITEM against the item brief and both platform renditions.
- The `quality_gate` machine step requires an `eval_report` evidence record
  (`kind` eval_report, `source` evals:content-copy-top10, `payload_id` equal
  to the batch_id, `overall` pass) before it can produce `campaign_ready`;
  otherwise it blocks with attention errors naming the failed criteria.
- Evidence validity for this suite is `business`: it gates buyer-facing copy
  against the company's ICP/voice standards before publication.

### Adding an eval suite to ANY department (Lego contract)

1. Create `departments/<name>/evals.py` exporting `EVAL_SUITES` — each suite
   declares ordered `EvalCriterion`s with source-file grounding
   (strategy/skill paths), a `payload_kind`, `thresholds`, an optional
   `item_selector`, and an optional `payload_id_selector`.
2. Declare `eval_suites = ("<suite-id>", ...)` on the Department class.
3. Require a passing `eval_report` evidence in the machine step that gates the
   payload (see `.agents/company/evals/` and `company eval list`).

The evals framework itself (`.agents/company/evals/`) is department-agnostic:
one engine, pluggable judge connectors (`agent:cli` default, `http:provider`
seam), registry auto-discovery from `evals.py` modules, and a `company eval`
CLI (`list`, `run`).

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
