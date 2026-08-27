---
name: videography
description: Record authentic, human-paced browser demos of delivered Client Delivery workflows and render them into showcase MP4s using the four-module resolve/author/record/render pipeline under scripts/videography. Use when the owner wants a real demo video of a delivered workflow (or a new demo type) rather than a staged/brand-motion video.
---

# Videography

Videography is the Department that turns **real delivered workflows into real
showcase videos**. It records an actual browser session — humanized cursor,
typing, and pacing — of a workflow built by Client Delivery and renders the
capture into a showcase MP4. The recording is evidence, never a creation:
the video shows exactly what the workflow did in that run.

This Department is the **opposite trust model** from Design's brand-motion
`video-creation`: it never stages, scripts visuals, or fabricates results.
It captures what really happened.

## Pipeline (four isolated modules)

1. **resolve** — pick a delivered order from the Client Delivery registry
   (`.agents/company/assets/client-delivery/registry.csv`) and resolve the
   provider + flow id. Provider-agnostic by design; today it is ActivePieces
   (self-hosted at `http://localhost:8080`, MCP at `/mcp`).
2. **author** — write a humanistic scenario JSON under
   `scripts/videography/scenarios/` (see the job-brief demo scenario). A new
   demo type = a new scenario file; the recorder never changes.
3. **record** — `scripts/videography/recorder.py` runs the scenario in a real
   Chromium with a visible humanized cursor, natural typing/scroll/read dwell,
   seeded determinism, and captures video + a per-step DOM-state audit.
4. **render** — `scripts/videography/render.py` encodes the capture to a
   web-optimized MP4 (h264, yuv420p, faststart). Polish (captions, TTS,
   narration, zooms) is a later pass that never alters the raw capture.

## Operating commands (from repo root)

```bash
# Session (one-time, human login) — needed for authenticated ActivePieces flows
python3 scripts/videography/session.py --url http://localhost:8080 \
  --out .spielos/videography/activepieces-state.json

# Record a scenario (local/proof or authenticated ActivePieces demo)
python3 scripts/videography/recorder.py \
  --scenario scripts/videography/scenarios/demo-workflow.json \
  --out .spielos/artifacts/videography/demo-workflow --headful
# + [--storage-state .spielos/videography/activepieces-state.json] for AP flows

# Render MP4
python3 scripts/videography/render.py \
  .spielos/artifacts/videography/demo-workflow.webm \
  --out .spielos/artifacts/videography/demo-workflow.mp4

# Verify a deliverable (streams, duration, h264 MP4)
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height \
  -of default=noprint_wrappers=1 <out>.mp4
```

## Evidence contract

A recording is accepted evidence of `showcase_videos` only when ALL hold:

- the raw `.webm` and rendered `.mp4` exist under
  `.spielos/artifacts/videography/`;
- the `.steps.json` timeline shows every scenario step `step_done` with
  `dom` probes: cursor present, typed value length matches, result visible
  where the scenario declares it;
- ffprobe confirms an h264 MP4 at the scenario viewport and a duration >= the
  intended demo length;
- the scenario resolves a **real delivered order** (id from the registry), not
  a staged stand-in;
- capture authenticity is preserved: never splice, re-run, or blur a failed
  step into success.

## Guards

- Never record anything that requires the owner's credentials without an owner
  session capture (storageState) obtained through `session.py` or equivalent.
- Never publish or upload a recording without owner approval (later
  distribution stages are separate approvals).
- Never relabel a fixture/proof capture as a real workflow demo; the scenario
  name and steps.json must name the resolved order.
- The recorder is the only source of the video; post-production only layers
  presentation (captions/narration/zoom) on top of the real capture.
