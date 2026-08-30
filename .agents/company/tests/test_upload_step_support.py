"""Upload step support in scripts/videography scenario + recorder.

Bounded repair goal-63e11fe96b: restore the `upload` step type that the v5
receipt-ledger capture used at step 18 (selector #receiptImage, fixture
scripts/videography/fixtures/example-invoice.png).

Covers:
- scenario with an `upload` step parses without ScenarioError;
- `upload` without `file` raises ScenarioError ("upload needs file");
- `upload` without `selector` raises ScenarioError (existing step pattern);
- the invoice fixture exists, is a real PNG, has sane dimensions, a
  non-trivial size and visible dark content, and carries the invoice text
  signal (supplier, line items, subtotal, VAT, total) embedded as a PNG
  tEXt chunk so the check is OCR-free and deterministic;
- the recorder `upload` branch resolves the fixture path relative to the
  repo root and dispatches it through Playwright `set_input_files`, then
  records `step_done` (mocked Playwright stack, no real browser).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

REPO = Path(__file__).resolve().parents[3]
VIDEO_DIR = REPO / "scripts" / "videography"
FIXTURE = VIDEO_DIR / "fixtures" / "example-invoice.png"

# scenario.py / recorder.py import each other as sibling modules; put the
# videography dir on sys.path so the tests run without any PYTHONPATH.
sys.path.insert(0, str(VIDEO_DIR))

from scenario import Scenario, ScenarioError  # noqa: E402
import recorder  # noqa: E402

UPLOAD_STEP = {
    "type": "upload",
    "selector": "#receiptImage",
    "file": "scripts/videography/fixtures/example-invoice.png",
    "wait_after": 1.2,
}


# --------------------------------------------------------------------------
# Fakes for the recorder mock (Playwright sync API surface used by main()).
# --------------------------------------------------------------------------
class FakeLocator:
    def __init__(self, page, selector):
        self._page = page
        self._selector = selector

    def set_input_files(self, path):
        self._page.calls.append(("set_input_files", self._selector, path))


class FakePage:
    def __init__(self):
        self.calls = []
        self.wait_ms = 0
        self.video = None

    def add_script_tag(self, **kwargs):
        self.calls.append(("add_script_tag", kwargs))

    def evaluate(self, *args, **kwargs):
        self.calls.append(("evaluate", args))
        return {
            "cursor_installed": True,
            "textarea_value_len": 0,
            "result_visible": False,
            "result_rows": 0,
            "title": "fixture page",
            "body_text_len": 1,
        }

    def wait_for_timeout(self, ms):
        self.wait_ms += ms

    def locator(self, selector):
        self.calls.append(("locator", selector))
        return FakeLocator(self, selector)


class FakeContext:
    def __init__(self, page):
        self.page = page

    def add_init_script(self, **kwargs):
        self.page.calls.append(("add_init_script", kwargs))

    def new_page(self):
        return self.page

    def close(self):
        pass


class FakeBrowser:
    def __init__(self, page):
        self.page = page

    def new_context(self, **kwargs):
        return FakeContext(self.page)

    def close(self):
        pass


class FakePlaywright:
    def __init__(self, page):
        self.chromium = type("FakeChromium", (), {
            "launch": lambda self, **kwargs: FakeBrowser(page),
        })()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class UploadStepScenarioTests(unittest.TestCase):
    def test_upload_step_parses_without_error(self):
        scenario = Scenario.from_dict({"name": "t", "steps": [UPLOAD_STEP]})
        self.assertEqual(scenario.steps[0]["type"], "upload")
        self.assertEqual(scenario.steps[0]["selector"], "#receiptImage")

    def test_upload_step_without_file_raises(self):
        with self.assertRaises(ScenarioError) as ctx:
            Scenario.from_dict({"name": "t", "steps": [
                {"type": "upload", "selector": "#receiptImage"},
            ]})
        self.assertIn("upload needs file", str(ctx.exception))

    def test_upload_step_without_selector_raises(self):
        with self.assertRaises(ScenarioError) as ctx:
            Scenario.from_dict({"name": "t", "steps": [
                {"type": "upload",
                 "file": "scripts/videography/fixtures/example-invoice.png"},
            ]})
        self.assertIn("upload needs selector", str(ctx.exception))


class RecorderUploadBranchTests(unittest.TestCase):
    def test_upload_dispatches_set_input_files_and_records_step_done(self):
        page = FakePage()
        with tempfile.TemporaryDirectory() as tmp:
            scenario_path = Path(tmp) / "upload-scenario.json"
            scenario_path.write_text(
                json.dumps({"name": "upload-test", "steps": [UPLOAD_STEP]}),
                encoding="utf-8")
            out = Path(tmp) / "capture"
            argv = ["recorder.py", "--scenario", str(scenario_path),
                    "--out", str(out)]
            with patch.object(recorder, "load_playwright",
                              return_value=lambda: FakePlaywright(page)):
                with patch.object(sys, "argv", argv):
                    code = recorder.main()
            steps_log = json.loads(
                (Path(tmp) / "capture.steps.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        upload_calls = [c for c in page.calls if c[0] == "set_input_files"]
        self.assertEqual(len(upload_calls), 1, page.calls)
        selector, path = upload_calls[0][1], upload_calls[0][2]
        self.assertEqual(selector, "#receiptImage")
        # File path is resolved relative to repo root, exactly like v5 used.
        self.assertEqual(Path(path), REPO / UPLOAD_STEP["file"])
        done = [e for e in steps_log["log"] if e.get("tag") == "step_done"]
        self.assertEqual(len(done), 1)
        self.assertEqual(done[0]["type"], "upload")
        self.assertEqual(done[0]["index"], 0)
        # wait_after (1.2s) was honoured through Humanized.wait.
        self.assertGreaterEqual(page.wait_ms, 1200)


class InvoiceFixtureTests(unittest.TestCase):
    def test_fixture_is_png_with_invoice_content_signal(self):
        self.assertTrue(FIXTURE.exists(),
                        "fixture scripts/videography/fixtures/example-invoice.png missing")
        size = FIXTURE.stat().st_size
        self.assertGreater(size, 10_000,
                            "fixture is suspiciously small for a rendered invoice")
        self.assertEqual(FIXTURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n",
                         "fixture is not a PNG (bad magic header)")

        with Image.open(FIXTURE) as img:
            w, h = img.size
            self.assertTrue(500 <= w <= 4000, f"width {w} out of sane range")
            self.assertTrue(500 <= h <= 4000, f"height {h} out of sane range")
            # Visible content: threshold dark pixels and require a substantial
            # non-white region (a blank image would have no dark bbox).
            dark_bbox = img.convert("L").point(
                lambda v: 255 if v < 160 else 0).getbbox()
            text_chunks = getattr(img, "text", None) or {}
            rendered = text_chunks.get("InvoiceText", "") if text_chunks else ""

        self.assertIsNotNone(dark_bbox, "invoice image appears blank")
        bw = dark_bbox[2] - dark_bbox[0]
        bh = dark_bbox[3] - dark_bbox[1]
        self.assertGreater(bw, 300, "dark content too narrow")
        self.assertGreater(bh, 300, "dark content too short")

        low = rendered.lower()
        self.assertIn("meridian office supplies", low)      # supplier name
        self.assertIn("bristol", low)                       # supplier address
        self.assertIn("inv-2026-0842", low)                 # invoice number
        self.assertIn("14 august 2026", low)                # invoice date
        self.assertIn("toner cartridge", low)               # line item
        self.assertIn("4.80", low)                          # quantity/unit price
        self.assertIn("550.40", low)                        # subtotal
        self.assertIn("vat", low)                           # VAT line
        self.assertIn("110.08", low)                        # VAT amount
        self.assertIn("660.48", low)                        # total


if __name__ == "__main__":
    unittest.main()