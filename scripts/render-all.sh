#!/bin/bash
# render-all.sh — Full SpielOS motion pipeline:
#   narration (TTS PROVIDER CHAIN: Gemini primary → Mistral Voxtral →
#   Cartesia → ElevenLabs, ONE pinned persona, measured scene_timing)
#   → narration-only mix → base render → merge → stable hook thumbnail → QA.
#
# Usage:
#   bash scripts/render-all.sh b          # Scenario B, landscape + portrait, 30fps
#   bash scripts/render-all.sh c 30       # Scenario C, explicit fps
#   bash scripts/render-all.sh b 30 1080x1920,1920x1080  # explicit aspects
#
# Campaign outputs land beside their manifest under the batch's
# youtube-shorts/<item-id>/ directory. Legacy private showcase outputs retain
# the historical production path. Nothing here publishes externally.
#
# Owner contract (2026-08-11 + 2026-08-12): ONE narration persona (pinned in
# narration.json `voice_selection`, enforced by tts-gemini.js and
# mix-audio.js), scene windows derived from MEASURED spoken clip durations plus
# readable visual lead/hold (speech first — templates read narration.json
# scene_timing themselves), a NARRATION-ONLY mix (no music bed, no duck bus), and a
# deterministic multi-provider TTS fallback chain (never switch voice
# mid-scenario, never drop a clip silently).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCENARIO="${1:-b}"
FPS="${2:-30}"
ASPECTS="${3:-landscape portrait}"

# Campaign production receives all strategy, copy, design choices, tracking
# identity, and narration from one shared Artifact. Legacy showcase rendering
# stays available only inside this non-publishing script and is labelled.
if [ -n "$CAMPAIGN_MANIFEST" ] || [ -n "$CAMPAIGN_ITEM_ID" ]; then
  if [ -z "$CAMPAIGN_MANIFEST" ] || [ -z "$CAMPAIGN_ITEM_ID" ]; then
    echo "Set both CAMPAIGN_MANIFEST and CAMPAIGN_ITEM_ID."
    exit 1
  fi
  CAMPAIGN_MODE=1
  MANIFEST_DIR="$(cd "$(dirname "$CAMPAIGN_MANIFEST")" && pwd)"
  MANIFEST_FILE="$(basename "$CAMPAIGN_MANIFEST")"
  BATCH_SLUG="${MANIFEST_FILE%.json}"
  BATCH_SLUG="${BATCH_SLUG%-campaign}"
  ART="$MANIFEST_DIR/$BATCH_SLUG"
  ITEM_ART="$ART/youtube-shorts/$CAMPAIGN_ITEM_ID"
  mkdir -p "$ITEM_ART"
  if [ "$ASPECTS" != "portrait" ]; then
    echo "Campaign YouTube Shorts render requires the portrait aspect only."
    exit 1
  fi
else
  CAMPAIGN_MODE=0
  ART="$ROOT/.spielos/artifacts/design-production-upgrade-20260810"
  mkdir -p "$ART/video" "$ART/graphics"
  export LEGACY_VIDEO_RENDER=1
  export LEGACY_DESIGN_RENDER=1
  echo "Legacy private showcase mode — no campaign delivery or publishing evidence will be created."
fi

echo "╔══════════════════════════════════════════╗"
echo "║   SpielOS Motion Pipeline — $SCENARIO @ ${FPS}fps   ║"
echo "╚══════════════════════════════════════════╝"

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/spielos-video.XXXXXX")"
NARRATION_SPEC="$ROOT/.agents/company/departments/design/templates/video/narration.json"
if [ "$CAMPAIGN_MODE" = "1" ]; then
  cp "$NARRATION_SPEC" "$WORK_DIR/narration-template.json"
fi
cleanup() {
  if [ -f "$WORK_DIR/narration-template.json" ]; then
    cp "$WORK_DIR/narration-template.json" "$NARRATION_SPEC"
  fi
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

# 1) Narration through the TTS provider chain. The generator purges stale
#    clips for the scenario, measures each spoken take, and writes the
#    schedule + provider/voice provenance into narration.json (scene_timing)
#    + .voice-manifest.json. No per-call voice overrides, no atempo, no cuts.
if [ "$SKIP_TTS" != "1" ]; then
  node "$SCRIPT_DIR/tts-gemini.js" "$SCENARIO"
fi

# 2) Narration-only mix (aspect-independent, narration-led duration): no music bed. Refuses to
#    run without measured scene_timing or if the voice provenance mismatches.
node "$SCRIPT_DIR/mix-audio.js" "$SCENARIO" "$WORK_DIR/narration.m4a"

# 3) Thumbnail time: the hook is fully composed and still inside its readable
# window. Never capture the half-revealed 0.6s frame.
THUMB_SEC=$(node -e '
const fs=require("fs");
const d=JSON.parse(fs.readFileSync(process.argv[1],"utf8"));
const s=d.scene_timing[process.argv[2]].scenes[0];
console.log(Math.min(s.end-0.35,s.start+2.2).toFixed(2));
' "$NARRATION_SPEC" "$SCENARIO")

for ASPECT in $ASPECTS; do
  case "$ASPECT" in
    landscape) LABEL=16x9 ;;
    portrait)  LABEL=9x16 ;;
    square)    LABEL=1x1 ;;
    story)     LABEL=4x5 ;;
    *) echo "Unknown aspect $ASPECT"; exit 1 ;;
  esac
  echo ""
  echo "━━━ $ASPECT ($LABEL) ━━━"

  node "$SCRIPT_DIR/render-video.js" "$SCENARIO" "$ASPECT" "$FPS" "$WORK_DIR/base.mp4"

  if [ "$CAMPAIGN_MODE" = "1" ]; then
    ffmpeg -y -v error -i "$WORK_DIR/base.mp4" -i "$WORK_DIR/narration.m4a" \
      -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest "$ITEM_ART/video.mp4"
    ffmpeg -y -v error -ss "$THUMB_SEC" -i "$ITEM_ART/video.mp4" -frames:v 1 -q:v 2 "$ITEM_ART/thumbnail.jpg"
    node "$SCRIPT_DIR/verify-video-deliverable.js" "$ITEM_ART/video.mp4" "$ITEM_ART/qa.json"
    echo "  video + thumbnail + QA → $ITEM_ART"
  else
    NAME="spielos-$( [ "$SCENARIO" = "b" ] && echo before-after || echo build-it )-flat-polish-$LABEL"
    ffmpeg -y -v error -i "$WORK_DIR/base.mp4" -i "$WORK_DIR/narration.m4a" \
      -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest "$ART/video/$NAME-voiced.mp4"
    ffmpeg -y -v error -ss "$THUMB_SEC" -i "$ART/video/$NAME-voiced.mp4" -frames:v 1 -q:v 2 "$ART/video/$NAME-thumbnail.jpg"
    echo "  voiced + thumbnail → $ART/video"
  fi
done

# 4) Campaign image assets have their own Design handoff and are never
# re-rendered as a side effect of one video. Preserve the showcase-only path.
if [ "$CAMPAIGN_MODE" = "0" ]; then
  node "$SCRIPT_DIR/render-design.js" all "$ART/graphics"
  echo "  social graphics → $ART/graphics"
fi

echo ""
echo "  Done. Deliverables in $ART"
