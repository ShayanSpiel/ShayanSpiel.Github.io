# Videography — humanized demo recording pipeline

Records authentic, human-paced browser demos of delivered workflows and turns
them into showcase MP4s. The design is four isolated modules so new demo types
are new scenario files, never new recorder code:

  1. **resolve**  — pick a delivered order (registry) + provider/flow id
  2. **author**   — write a humanistic scenario JSON (README in `fixtures/`)
  3. **record**   — run the scenario in a real Chromium, capture video
  4. **render**   — ffmpeg webm → polished MP4 (+ future: captions, narration)

## Commands (from repo root)

```bash
# 1. Local proof / fixture demo (no login):
python3 scripts/videography/recorder.py \
  --scenario scripts/videography/scenarios/demo-workflow.json \
  --out .spielos/artifacts/videography/demo-workflow --headful

# 2. Render to MP4:
python3 scripts/videography/render.py \
  .spielos/artifacts/videography/demo-workflow.webm \
  --out .spielos/artifacts/videography/demo-workflow.mp4

# 3. Capture an authenticated ActivePieces session (one-time, human login):
python3 scripts/videography/session.py --url http://localhost:8080 \
  --out .spielos/videography/activepieces-state.json

# 4. Record the real ActivePieces demo:
python3 scripts/videography/recorder.py \
  --scenario scripts/videography/scenarios/activepieces-job-brief-shortlist.json \
  --out .spielos/artifacts/videography/activepieces-demo --headful \
  --storage-state .spielos/videography/activepieces-state.json
```

## Outputs per recording
- `*.webm` — raw browser capture (face of the truth)
- `*.mp4` — rendered showcase video
- `*.steps.json` — full step timeline + logging (audit)

## Evidence
A recording is evidence of `showcase_videos` only when:
- the raw webm + rendered mp4 exist under `.spielos/artifacts/videography/`,
- the steps.json log shows every scenario step ran without failure,
- ffprobe confirms an h264 MP4 at the intended duration,
- the scenario resolved a real delivered order (not a stage).
