#!/usr/bin/env bash
# build.sh — full build pipeline for the Shayan Spiel site.
#
# 1. Sync design tokens (YAML → tokens.css)
# 2. Sync design system (validate components, regenerate /design-system/)
# 3. Build the Jekyll site
#
# Exits non-zero on any failure.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

echo "→ sync-tokens"
python3 _tools/sync-tokens.py

echo "→ sync-design-system"
python3 _tools/sync-design-system.py

echo "→ jekyll build"
export PATH="/usr/local/opt/ruby/bin:$PATH"
bundle exec jekyll build

echo "✓ build complete"
