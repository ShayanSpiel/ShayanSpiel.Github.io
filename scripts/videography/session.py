"""Capture a Playwright storageState (browser session) for an authenticated demo.

Usage:
  python3 scripts/videography/session.py --url http://localhost:8080 \
      --out .spielos/videography/activepieces-state.json [--wait 45]

Opens a real window; after the login completes press Enter in the terminal
(or wait out --wait), and the session is saved for the recorder.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--wait", type=int, default=45, help="seconds to wait for login")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise SystemExit(f"playwright unavailable: {exc}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(args.url, wait_until="domcontentloaded")
        print(f"Opened {args.url} in a real window. Complete the login in the browser.")
        print(f"Waiting up to {args.wait}s (or press Enter to save now)…")
        deadline = time.time() + args.wait
        saved = False
        while time.time() < deadline:
            try:
                input("Press Enter when logged in…")
                saved = True
                break
            except EOFError:
                time.sleep(1)
        state = context.storage_state()
        out.write_text(json.dumps(state, indent=2), encoding="utf-8")
        print(f"storageState saved: {out} ({len(state.get('cookies', []))} cookies)")
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
