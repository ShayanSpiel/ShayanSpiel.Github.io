"""Recorder CLI: run a humanistic scenario in a real browser and capture video.

Usage (from repo root):
  python3 scripts/videography/recorder.py --scenario SCENARIO.json \
      --out .spielos/artifacts/videography/demo --headful [--seed N]

Outputs: <out>.webm (raw capture), <out>.mp4 (rendered), <out>.steps.json
(timeline/audit), <out>.log (recording notes).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from humanized import Humanized, CURSOR_JS
from scenario import Scenario, ScenarioError

def dom_probe(page) -> dict:
    """Machine-checkable state: cursor present, input driven, result visible."""
    try:
        return page.evaluate("""() => {
          const q = (s) => !!(document.querySelector(s));
          const v = (s) => (document.querySelector(s) || {}).value || '';
          const resultCard = document.querySelector('#resultCard');
          return {
            cursor_installed: !!window.__spielosCursor,
            textarea_value_len: v('textarea#clientBrief').length,
            result_visible: !!(resultCard && !resultCard.classList.contains('hidden')),
            result_rows: document.querySelectorAll('#resultBody tr').length,
            title: (document.title || '').slice(0, 80),
            body_text_len: (document.body ? document.body.innerText.length : 0)
          };
        }""")
    except Exception:
        return {}


REPO = Path(__file__).resolve().parents[2]


def load_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            f"python playwright missing in this interpreter ({sys.executable}): {exc}")


def launch_browser(playwright, *, headful: bool, storage_state: str | None):
    kwargs = {}
    if storage_state and Path(storage_state).exists():
        kwargs["storage_state"] = storage_state
    args = ["--autoplay-policy=no-user-gesture-required",
            "--disable-blink-features=AutomationControlled"]
    attempts = [
        {"executable_path": "/Users/shayan/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"},
        {"executable_path": "/Users/shayan/Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"},
        {"channel": "chrome"},                      # system Chrome (already installed)
        {},
        {"executable_path": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"},
    ]
    last_error = None
    for extra in attempts:
        try:
            return playwright.chromium.launch(headless=not headful, args=args, **extra)
        except Exception as exc:  # pragma: no cover - environment probing
            last_error = exc
    raise last_error


def main() -> int:
    ap = argparse.ArgumentParser(description="Record a humanistic demo scenario to video")
    ap.add_argument("--scenario", required=True, help="path to scenario JSON")
    ap.add_argument("--out", required=True, help="output prefix (no extension)")
    ap.add_argument("--headful", action="store_true", help="show a real browser window")
    ap.add_argument("--headless", action="store_true", help="capture without a window")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--storage-state", default=None, help="playwright storageState JSON")
    args = ap.parse_args()

    try:
        scenario = Scenario.from_file(REPO / args.scenario if not Path(args.scenario).is_absolute()
                                      else args.scenario)
    except ScenarioError as exc:
        print(f"scenario error: {exc}", file=sys.stderr)
        return 2
    if args.seed is not None:
        scenario.seed = args.seed

    out_prefix = Path(args.out)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    log: list[dict] = []
    headful = args.headful and not args.headless
    started = time.time()

    pw = load_playwright()
    with pw() as p:
        browser = launch_browser(p, headful=headful, storage_state=args.storage_state)
        ctx_kwargs = dict(
            viewport={"width": scenario.viewport[0], "height": scenario.viewport[1]},
            record_video_dir=str(out_prefix.parent / f".video-{scenario.name}"),
            record_video_size={"width": scenario.viewport[0], "height": scenario.viewport[1]},
            device_scale_factor=1,
        )
        if args.storage_state and Path(args.storage_state).exists():
            ctx_kwargs["storage_state"] = args.storage_state
        context = browser.new_context(**ctx_kwargs)
        context.add_init_script(script=CURSOR_JS)
        page = context.new_page()
        human = Humanized(page, personality=scenario.personality, seed=scenario.seed)
        human.inject_cursor()
        log.append(human.timeline("cursor_injected", dom=dom_probe(page)))

        step_index = 0
        for step in scenario.steps:
            stype = step["type"]
            log.append(human.timeline("step_start", index=step_index, type=stype, step=step))
            try:
                if stype == "goto":
                    page.goto(step["url"], wait_until="domcontentloaded")
                    human.wait(0.9)
                elif stype == "click":
                    human.click(step["selector"], wait_after=float(step.get("wait_after", 0.6)))
                elif stype == "type":
                    human.type_text(step["selector"], step["text"],
                                    secret=bool(step.get("secret")))
                elif stype == "press":
                    human.press(step["key"], wait_after=float(step.get("wait_after", 0.4)))
                elif stype == "scroll":
                    human.scroll(selector=step.get("selector", "body"),
                                 by=step.get("by"))
                elif stype == "wait":
                    human.wait(float(step.get("seconds", 1)))
                elif stype == "wait_for":
                    human.wait_for_selector(step["selector"],
                                            timeout_ms=int(step.get("timeout_ms", 45000)),
                                            wait_after=float(step.get("wait_after", 1.0)))
                elif stype == "read":
                    human.read(step.get("text", ""), wpm=step.get("wpm"))
                elif stype == "verify_text":
                    loc = page.locator(step.get("selector", "body")).first
                    loc.wait_for(timeout=int(step.get("timeout_ms", 20000)))
                    human.read(step.get("text") or step["selector"])
                elif stype == "open_tab":
                    page2 = context.new_page()
                    page2.goto(step["url"], wait_until="domcontentloaded")
                    page2.bring_to_front()
                    human.wait(1.0)
                elif stype == "shot":
                    name = str(step.get("name") or f"shot-{step_index}")
                    page.screenshot(path=str(out_prefix.parent / (out_prefix.name + f"-{name}.png")))
                    human.wait(float(step.get("wait_after", 0.4)))
            except Exception as exc:
                log.append(human.timeline("step_failed", index=step_index, error=str(exc)))
                print(f"step {step_index} ({stype}) failed: {exc}", file=sys.stderr)
                raise
            log.append(human.timeline("step_done", index=step_index, type=stype,
                                      dom=dom_probe(page)))
            step_index += 1

        # hold a final beat so the last frame is not cut mid-action
        human.wait(1.5)
        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

    raw_video = None
    if video_path and Path(video_path).exists():
        import shutil
        raw_video = out_prefix.with_suffix(".webm")
        shutil.move(video_path, raw_video)
    (out_prefix.parent / (out_prefix.name + ".steps.json")).write_text(
        json.dumps({"scenario": scenario.to_dict(), "log": log,
                    "duration_s": round(time.time() - started, 2)},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"scenario ok: {scenario.name} · {len(scenario.steps)} steps · "
          f"{round(time.time() - started, 1)}s wall · cursor_installed="
          f"{Humanized.visible_cursor_installed(page) if 'page' in dir() else 'n/a'}")
    print(f"raw capture: {raw_video}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
