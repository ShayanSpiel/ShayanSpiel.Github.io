"""Humanized Playwright driver for authentic demo capture.

Makes a real browser session look and feel human: visible cursor with Bezier
trajectories, natural typing rhythm, eased scrolling, and reading dwell time.
All timing is seeded so a scenario is reproducible in intent.

Core contract:
  - Every input action dispatches real browser input events (CDP).
  - The visible cursor is injected DOM that tracks the real pointer, so the
    recorded video always shows where the operator is "pointing".
  - Sync Playwright only; pure capture-side library (no runtime access).
"""
from __future__ import annotations

import math
import random
import time

CURSOR_JS = r"""
(() => {
  if (window.__spielosCursor) return;
  function boot() {
    if (window.__spielosCursor) return;
    const el = document.createElement('div');
    el.id = '__spielosCursor';
    el.style.cssText = [
      'position:fixed', 'left:0px', 'top:0px', 'z-index:2147483647',
      'pointer-events:none', 'will-change:transform',
      'filter:drop-shadow(0 1px 2px rgba(0,0,0,.45))'
    ].join(';');
    el.innerHTML = '<svg width="26" height="26" viewBox="0 0 26 26" xmlns="http://www.w3.org/2000/svg">'
      + '<path d="M4 3 L4 20 L9.2 15.6 L12.6 22.6 L15.4 21.2 L12 14.4 L17.8 14.2 Z" '
      + 'fill="#ebdbb2" stroke="#282828" stroke-width="1.4" stroke-linejoin="round"/></svg>';
    document.documentElement.appendChild(el);
    let x = -100, y = -100;
    document.addEventListener('mousemove', (e) => { x = e.clientX; y = e.clientY; late(); }, true);
    function late() { el.style.left = (x - 2) + 'px'; el.style.top = (y - 2) + 'px'; }
    window.__spielosCursor = el;
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
  // Also try immediately in case documentElement already exists.
  if (document.documentElement) boot();
})();
"""


class Personality:
    """Timing profiles. careful = deliberate demo pacing (default)."""

    def __init__(self, name: str = "careful"):
        self.name = name
        if name == "fast":
            self.key_min, self.key_max = 0.025, 0.075
            self.move_base = 0.55
            self.read_wpm = 320.0
        elif name == "precise":
            self.key_min, self.key_max = 0.05, 0.14
            self.move_base = 0.85
            self.read_wpm = 200.0
        else:  # careful
            self.key_min, self.key_max = 0.06, 0.19
            self.move_base = 1.0
            self.read_wpm = 170.0


class Humanized:
    """Wrap a sync Playwright page with human-like interaction primitives."""

    def __init__(self, page, personality: str = "careful", seed: int = 7):
        self.page = page
        self.p = Personality(personality)
        self.rng = random.Random(seed)
        self._last = {"x": 40.0, "y": 40.0}

    # -- cursor ------------------------------------------------------------
    def inject_cursor(self) -> None:
        try:
            self.page.add_script_tag(content=CURSOR_JS)
        except Exception:
            self.page.evaluate(CURSOR_JS)

    # -- helpers -----------------------------------------------------------
    def _bezier(self, x0, y0, x1, y1, steps):
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy) or 1.0
        px, py = -dy / dist, dx / dist
        amp = dist * self.rng.uniform(0.08, 0.22) * (1 if self.rng.random() < 0.5 else -1)
        c0 = (x0 + dx * 0.2 + px * amp, y0 + dy * 0.2 + py * amp)
        c1 = (x0 + dx * 0.8 + px * amp * 0.6, y0 + dy * 0.8 + py * amp * 0.6)
        pts = []
        for i in range(steps + 1):
            t = i / steps
            mt = 1 - t
            a, b, c, d = mt ** 3, 3 * mt * mt * t, 3 * mt * t * t, t ** 3
            pts.append((a * x0 + b * c0[0] + c * c1[0] + d * x1,
                        a * y0 + b * c0[1] + c * c1[1] + d * y1))
        return pts

    def _ms(self, base) -> int:
        return int(base * 1000 * self.p.move_base)

    def move(self, x, y, overshoot: bool = True) -> None:
        sx, sy = self._last["x"], self._last["y"]
        dist = math.hypot(x - sx, y - sy)
        steps = max(18, min(70, int(dist / 3.2)))
        pts = self._bezier(sx, sy, x, y, steps)
        base = 0.004 * self.p.move_base
        for (px, py) in pts:
            self.page.mouse.move(px, py)
            self.page.wait_for_timeout(int(base * self.rng.uniform(0.6, 1.7) * 1000))
        if overshoot and dist > 80 and self.rng.random() < 0.35:
            ox = x + self.rng.uniform(-14, 14)
            oy = y + self.rng.uniform(-6, 10)
            self.page.mouse.move(ox, oy)
            self.page.wait_for_timeout(self._ms(0.06))
        for _ in range(self.rng.randint(1, 3)):
            self.page.mouse.move(x + self.rng.uniform(-1.2, 1.2),
                                 y + self.rng.uniform(-1.2, 1.2))
            self.page.wait_for_timeout(int(self.rng.uniform(30, 90) * self.p.move_base))
        self._last.update(x=x, y=y)

    def _element_point(self, locator):
        box = locator.bounding_box()
        if not box:
            raise RuntimeError(f"element not visible: {locator}")
        return (box["x"] + box["width"] * self.rng.uniform(0.42, 0.58),
                box["y"] + box["height"] * self.rng.uniform(0.42, 0.58))

    def _scroll_into_view(self, locator) -> None:
        try:
            locator.scroll_into_view_if_needed()
            self.page.wait_for_timeout(int(self.rng.uniform(250, 550) * self.p.move_base))
        except Exception:
            pass

    def click(self, selector: str, wait_after: float = 0.6) -> None:
        loc = self.page.locator(selector).first
        self._scroll_into_view(loc)
        x, y = self._element_point(loc)
        self.move(x, y)
        self.page.wait_for_timeout(int(self.rng.uniform(120, 320) * self.p.move_base))
        self.page.mouse.down()
        self.page.wait_for_timeout(int(self.rng.uniform(45, 110) * self.p.move_base))
        self.page.mouse.up()
        self.page.wait_for_timeout(int(wait_after * 1000 * self.p.move_base))

    def type_text(self, selector: str, text: str, secret: bool = False) -> None:
        self.click(selector, wait_after=0.25)
        for ch in text:
            self.page.keyboard.type(ch)
            self.page.wait_for_timeout(
                int(self.rng.uniform(self.p.key_min, self.p.key_max) * 1000))
            if ch in " .,\n" and self.rng.random() < 0.18:
                self.page.wait_for_timeout(
                    int(self.rng.uniform(250, 750) * self.p.move_base))
        if not secret:
            self.page.wait_for_timeout(int(self.rng.uniform(200, 500) * self.p.move_base))

    def press(self, key: str, wait_after: float = 0.4) -> None:
        self.page.keyboard.press(key)
        self.page.wait_for_timeout(int(wait_after * 1000 * self.p.move_base))

    def scroll(self, selector: str = "body", by: int | None = None) -> None:
        loc = self.page.locator(selector).first
        try:
            loc.hover()
        except Exception:
            pass
        if by is None:
            self.page.mouse.wheel(0, self.rng.randint(300, 520))
        else:
            steps = max(3, min(12, abs(by) // 60))
            step = by / steps
            for _ in range(steps):
                self.page.mouse.wheel(0, step)
                self.page.wait_for_timeout(int(self.rng.uniform(60, 140) * self.p.move_base))

    def read(self, text: str, wpm: float | None = None) -> None:
        words = max(1, len(str(text).split()))
        seconds = (words / (wpm or self.p.read_wpm)) * 60 * self.rng.uniform(0.85, 1.3)
        self.page.wait_for_timeout(int(seconds * 1000))

    def wait(self, seconds: float) -> None:
        self.page.wait_for_timeout(int(seconds * 1000))

    def wait_for_selector(self, selector: str, timeout_ms: int = 30000,
                          wait_after: float = 1.0) -> None:
        self.page.wait_for_selector(selector, timeout=timeout_ms)
        self.page.wait_for_timeout(int(wait_after * 1000 * self.p.move_base))

    @staticmethod
    def timeline(tag: str, **fields) -> dict:
        return {"t": round(time.time(), 3), "tag": tag, **fields}

    @staticmethod
    def visible_cursor_installed(page) -> bool:
        try:
            return bool(page.evaluate("!!window.__spielosCursor"))
        except Exception:
            return False
