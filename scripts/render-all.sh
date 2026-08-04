#!/bin/bash
# render-all.sh — Renders the launch video in all social media aspect ratios.
#
# Usage:
#   bash scripts/render-all.sh          # All ratios, 30fps
#   bash scripts/render-all.sh 24       # All ratios, 24fps

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FPS="${1:-30}"

echo "╔══════════════════════════════════════════╗"
echo "║   SpielOS Launch Video — Batch Render    ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  FPS: $FPS"
echo ""

# Ensure output directory exists
mkdir -p "$ROOT/public/videos"

# Landscape — YouTube, LinkedIn, X
echo "━━━ 1/4  Landscape (1920×1080) ━━━"
node "$SCRIPT_DIR/render-video.js" landscape "$FPS"

# Portrait — Instagram Reels, TikTok, Shorts
echo "━━━ 2/4  Portrait (1080×1920) ━━━"
node "$SCRIPT_DIR/render-video.js" portrait "$FPS"

# Square — Instagram feed, X
echo "━━━ 3/4  Square (1080×1080) ━━━"
node "$SCRIPT_DIR/render-video.js" square "$FPS"

# Story — Instagram portrait feed
echo "━━━ 4/4  Story (1080×1350) ━━━"
node "$SCRIPT_DIR/render-video.js" story "$FPS"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║          All videos rendered!            ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Output files:"
ls -lh "$ROOT/public/videos/"*.mp4 2>/dev/null | awk '{print "    " $NF " (" $5 ")"}'
echo ""
