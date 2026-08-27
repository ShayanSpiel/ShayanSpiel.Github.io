---
name: workflow-delivery
description: Build-and-verify protocol every Department must follow when building an ActivePieces (or any integration) workflow, so builds are verified end-to-end with a real run before handoff. Use when a Department builds, fixes, or hands off an integration workflow.
---

# Workflow Delivery Protocol: build-and-verify before handoff

A workflow is NOT done because every step is "configured" and the flow is
"valid". That state is how broken builds ship. The ONLY acceptable delivery
state is: a real run with real sample input produced correct end-to-end output,
and the owner received proof. Follow this checklist for every ActivePieces (or
any integration) workflow build.

## Build-and-verify checklist

1. **read piece schemas FIRST.** Before configuring any step, call
   `ap_get_piece_props` (or `ap_research_pieces`) for every piece you will use.
   Record, per step: the exact property NAMES, their TYPES (e.g. `TEXT_AREA`
   vs `text_area`, `TEXT` vs `MARKDOWN`, number vs string), and the OUTPUT
   SHAPE of the action. NEVER guess a property name or type. If a step type is
   unclear, re-read the schema — do not infer it from another flow.
2. **Build the steps** using only the property names and types you just read.
   Keep each reference tied to a real upstream output key (e.g.
   `{{trigger['output'].field}}`, never `{{trigger.field}}`).
3. **Trigger a real run with sample input.** Publish the flow, then execute it
   with realistic sample data (not empty or placeholder). Inspect EVERY step's
   ACTUAL output — not just whether the step is configured or the flow is valid.
   `ap_get_run` must show each step succeeded and returned the expected shape.
4. **verify downstream references against the real output:**
   - HTTP response body is `output.body` (NOT `output`).
   - AI / completion step output is `output` (NOT `output.body` / `output.text`).
   - Form file fields reference the correct trigger output key (the exact field
     name emitted by the form trigger, from its real run).
   If a reference points at a key that the real output does not contain, the
   build is broken — fix the reference and re-run.
5. **Re-run until a real run produces correct end-to-end output.** Do not hand
   off on a green "configured" state. Iterate on the same draft: fix, publish,
   run, inspect, repeat until the full chain is correct.
6. **Hand off ONLY with proof.** Deliver both: (a) the working form/trigger URL
   or webhook, and (b) a sample successful run ID from the real run you
   inspected, where every step shows correct output. No proof, no handoff.

## Fixing an existing working flow

- **Change ONLY the broken step.** Never rebuild a working flow from scratch to
  fix one bug. Locate the failing/broken step, edit just that step, re-run, and
  verify the rest of the chain is unchanged and still correct. A one-line bug
  gets a one-step fix.

## Form-trigger testing constraint

A form trigger cannot be curl-tested — it needs the hosted-form session, not a
raw HTTP call. To verify a form-triggered flow end-to-end, pick ONE:

- **Swap-and-swap-back:** temporarily replace the form trigger with a webhook
  trigger, curl the webhook with sample input, inspect every step's real run
  output, then swap the webhook trigger back to the form trigger (no other
  changes). Re-publish and confirm.
- **Owner test submission:** ask the owner to do ONE real submission through the
  hosted form, then return the resulting run ID. Inspect that run
  per-step and confirm correct end-to-end output before handoff.

Either path still requires the proof from step 6 (working form URL + a sample
successful run ID).

## Non-negotiables

- A "valid" or "configured" flow is not verified. Only a real run is.
- Never guess piece property names or types — read piece schemas every time.
- Never rebuild a working flow to fix a single broken step.
- No handoff without proof.
