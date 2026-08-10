#!/bin/bash
# render-all.sh — Renders the launch video in all social media aspect ratios.
#
# Usage:
#   bash scripts/render-all.sh b        # Scenario B, all ratios, 30fps
#   bash scripts/render-all.sh c 24     # Scenario C, all ratios, 24fps

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCENARIO="${1:-b}"
FPS="${2:-30}"

echo "╔══════════════════════════════════════════╗"
echo "║   SpielOS Launch Video — Batch Render    ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Scenario: $SCENARIO"
echo "  FPS: $FPS"
echo ""

# Ensure output directory exists
mkdir -p "$ROOT/public/videos"

# Landscape — YouTube, LinkedIn, X
echo "━━━ 1/4  Landscape (1920×1080) ━━━"
node "$SCRIPT_DIR/render-video.js" "$SCENARIO" landscape "$FPS"

# Portrait — Instagram Reels, TikTok, Shorts
echo "━━━ 2/4  Portrait (1080×1920) ━━━"
node "$SCRIPT_DIR/render-video.js" "$SCENARIO" portrait "$FPS"

# Square — Instagram feed, X
echo "━━━ 3/4  Square (1080×1080) ━━━"
node "$SCRIPT_DIR/render-video.js" "$SCENARIO" square "$FPS"

# Story — Instagram portrait feed
echo "━━━ 4/4  Story (1080×1350) ━━━"
node "$SCRIPT_DIR/render-video.js" "$SCENARIO" story "$FPS"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║          All videos rendered!            ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Output directory: $ROOT/public/videos"
echo ""
