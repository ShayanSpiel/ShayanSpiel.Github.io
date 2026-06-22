#!/usr/bin/env python3
"""
sync-design-system.py
Validates the design system and regenerates /design-system/.

Checks:
  1. Every component in _data/components.yml has a partial in _includes/components/
  2. Every partial has a matching CSS section comment in assets/css/components.css
  3. Every CSS var used in components.css is defined in assets/css/tokens.css

Writes:
  - design-system/index.html (auto-generated catalog page)
  - design-system/components.json (machine-readable component API)

Usage:
    python3 _tools/sync-design-system.py            # validate + write
    python3 _tools/sync-design-system.py --check    # validate only, exit 1 on error
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
COMPONENTS_YML = REPO / "_data" / "components.yml"
PARTIALS_DIR = REPO / "_includes" / "components"
COMPONENTS_CSS = REPO / "assets" / "css" / "components.css"
TOKENS_CSS = REPO / "assets" / "css" / "tokens.css"
OUT_DIR = REPO / "design-system"
OUT_HTML = OUT_DIR / "index.html"
OUT_JSON = OUT_DIR / "components.json"

# CSS section comment pattern. Matches both single-line and multi-line:
#   /* ── card ── */
#   /* ── card ──
#      Description.
#   */
SECTION_RE = re.compile(
    r"/\*\s*─+\s*([^*\n]+?)\s*─+\s*(?:\n.*?)?\*/",
    re.DOTALL,
)
VAR_USED_RE = re.compile(r"var\(\s*(--[\w\-]+)\s*[,)]")
VAR_DEFINED_RE = re.compile(r"(--[\w\-]+)\s*:")


def load_components() -> list[dict]:
    with COMPONENTS_YML.open() as f:
        data = yaml.safe_load(f) or {}
    return data.get("components") or []


def check_partials(components: list[dict]) -> list[str]:
    errs: list[str] = []
    for c in components:
        p = PARTIALS_DIR / f"{c['partial']}.html"
        if not p.exists():
            errs.append(f"missing partial: _includes/components/{c['partial']}.html (component: {c['name']})")
    return errs


def check_css_sections(components: list[dict]) -> list[str]:
    if not COMPONENTS_CSS.exists():
        return [f"missing: {COMPONENTS_CSS.relative_to(REPO)}"]
    css = COMPONENTS_CSS.read_text()
    found: set[str] = set()
    for m in SECTION_RE.finditer(css):
        # First line of comment is the section name; lower + strip
        name = m.group(1).strip().lower()
        # Strip parenthetical descriptions: "post-card (blog list...)" → "post-card"
        name = re.sub(r"\s*\(.*\)\s*$", "", name).strip()
        # Normalize: "section + section-head" → "section"
        name = re.split(r"\s*\+\s*", name)[0].strip()
        found.add(name)
    errs: list[str] = []
    for c in components:
        # Check if any of the css_section entries match a found name
        sections = [s.strip().lower() for s in re.split(r"[+]", c.get("css_section", ""))]
        for s in sections:
            if not s:
                continue
            if s not in found:
                errs.append(f"missing CSS section for component '{c['name']}': expected '/* ── {s} ──' in components.css")
    return errs


def check_tokens() -> list[str]:
    if not TOKENS_CSS.exists():
        return [f"missing: {TOKENS_CSS.relative_to(REPO)} (run sync-tokens.py first)"]
    if not COMPONENTS_CSS.exists():
        return []
    defined = set(VAR_DEFINED_RE.findall(TOKENS_CSS.read_text()))
    used = set(VAR_USED_RE.findall(COMPONENTS_CSS.read_text()))
    self_defined = set(VAR_DEFINED_RE.findall(COMPONENTS_CSS.read_text()))
    defined |= self_defined
    missing = sorted(used - defined)
    if missing:
        return [f"undefined CSS var(s) in components.css: {', '.join(missing)}"]
    return []


def check_icons() -> list[str]:
    """Verify every icon used in posts + includes is defined in icons.yml."""
    icons_yml = REPO / "_data" / "icons.yml"
    if not icons_yml.exists():
        return [f"missing: icons.yml"]
    with icons_yml.open() as f:
        data = yaml.safe_load(f) or {}
    defined = {i["name"] for i in (data.get("icons") or [])}

    used: set[str] = set()
    # Only match icon= and name= inside Liquid component includes
    icon_ref_re = re.compile(
        r'\{%-?\s*include\s+components/[a-z-]+(?:\.html)?[^%]*?-?%\}|'
        r'icon\s*=\s*"([a-z][a-z0-9-]+)"'
    )
    # Also look for `name="X"` in icon.html partial calls (which always follow `include components/icon.html`)
    scan_files = list((REPO / "_posts").glob("*.html")) + list((REPO / "_includes").rglob("*.html")) + list((REPO / "_layouts").glob("*.html"))
    for f in scan_files:
        try:
            text = f.read_text()
        except Exception:
            continue
        # Find every icon="..." occurrence
        for m in re.finditer(r'icon\s*=\s*"([a-z][a-z0-9-]+)"', text):
            used.add(m.group(1))
        # Find every name="..." that follows a components/icon.html include in the same line
        for line in text.splitlines():
            if "components/icon.html" in line:
                m = re.search(r'name\s*=\s*"([a-z][a-z0-9-]+)"', line)
                if m:
                    used.add(m.group(1))

    missing = sorted(used - defined)
    if missing:
        return [f"icon(s) used in posts but not defined in icons.yml: {', '.join(missing)}"]
    return []


def render_html(components: list[dict]) -> str:
    cards: list[str] = []
    for c in components:
        slots = c.get("slots") or []
        slot_rows = "\n".join(
            f"          <li><code>{s['name']}</code>"
            + (f" <span class=\"slot-req\">required</span>" if s.get("required") else f" <span class=\"slot-opt\">optional</span>")
            + (f" &mdash; {s.get('type')}" if s.get("type") else "")
            + (f" &mdash; <em>{s.get('note')}</em>" if s.get("note") else "")
            + "</li>"
            for s in slots
        )
        example = (c.get("example") or "").strip()
        cards.append(
            f"""        <article class="ds-component" id="{c['name']}">
          <header>
            <h2><code>{c['name']}</code></h2>
            <span class="ds-partial">_includes/components/{c['partial']}.html</span>
          </header>
          <p>{c.get('description', '')}</p>
          <h3>Slots</h3>
          <ul class="ds-slots">{slot_rows}
          </ul>
          <h3>Example</h3>
          <pre class="ds-example"><code>{example}</code></pre>
        </article>"""
        )
    body = "\n".join(cards)
    return f"""---
layout: null
permalink: /design-system/
title: Design System
description: Every component, token, and pattern in the Shayan Spiel design system. The single source of truth.
---
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Design System — Shayan Spiel</title>
  <link rel="stylesheet" href="/assets/css/main.css" />
  <style>
    .ds-page {{ max-width: var(--w); margin: 0 auto; padding: var(--s-7) var(--s-5); }}
    .ds-intro {{ margin-bottom: var(--s-7); padding-bottom: var(--s-5); border-bottom: 1px solid var(--bd); }}
    .ds-intro h1 {{ margin-bottom: var(--s-3); }}
    .ds-intro p {{ color: var(--tx-2); max-width: 60ch; }}
    .ds-tokens {{ margin-bottom: var(--s-7); padding-bottom: var(--s-5); border-bottom: 1px solid var(--bd); }}
    .ds-tokens h2 {{ margin-bottom: var(--s-3); }}
    .ds-token-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: var(--s-3); }}
    .ds-token {{ background: var(--bg-1); border: 1px solid var(--bd); border-radius: var(--r-md); padding: var(--s-3); font-family: var(--f-m); font-size: var(--fs-xs); }}
    .ds-token-swatch {{ width: 100%; height: 32px; border-radius: var(--r-sm); margin-bottom: var(--s-2); border: 1px solid var(--bd); }}
    .ds-token-name {{ color: var(--tx); font-weight: 600; }}
    .ds-component {{ background: var(--bg-1); border: 1px solid var(--bd); border-radius: var(--r-xl); padding: var(--s-6); margin-bottom: var(--s-5); }}
    .ds-component header {{ display: flex; align-items: baseline; justify-content: space-between; gap: var(--s-4); flex-wrap: wrap; margin-bottom: var(--s-3); }}
    .ds-component h2 {{ margin: 0; }}
    .ds-component h2 code {{ font-size: var(--fs-xl); }}
    .ds-partial {{ font-family: var(--f-m); font-size: var(--fs-xs); color: var(--tx-3); }}
    .ds-component > p {{ color: var(--tx-2); margin: 0 0 var(--s-4); }}
    .ds-component h3 {{ font-size: var(--fs-sm); text-transform: uppercase; letter-spacing: 0.08em; color: var(--tx-3); margin: var(--s-4) 0 var(--s-2); font-weight: 600; }}
    .ds-slots {{ list-style: none; padding: 0; margin: 0; font-family: var(--f-m); font-size: var(--fs-sm); }}
    .ds-slots li {{ padding: var(--s-2) 0; border-bottom: 1px solid var(--bd); }}
    .ds-slots li:last-child {{ border-bottom: none; }}
    .ds-slots code {{ background: transparent; padding: 0; color: var(--tx); }}
    .slot-req {{ color: #f87171; font-size: var(--fs-xs); margin-left: var(--s-2); }}
    .slot-opt {{ color: var(--tx-3); font-size: var(--fs-xs); margin-left: var(--s-2); }}
    .ds-example {{ background: var(--bg); border: 1px solid var(--bd); border-radius: var(--r-md); padding: var(--s-3) var(--s-4); font-size: var(--fs-xs); line-height: 1.55; overflow-x: auto; margin: 0; }}
    .ds-example code {{ background: transparent; padding: 0; font-size: inherit; }}
  </style>
</head>
<body>
<div class="ds-page">
  <header class="ds-intro">
    <h1>Design System</h1>
    <p>Every component, token, and pattern in the Shayan Spiel design system. The single source of truth. <a href="/_data/components.yml">View manifest</a> · <a href="/_data/design-tokens.yml">View tokens</a></p>
  </header>

  <section class="ds-tokens">
    <h2>Tokens</h2>
    <div class="ds-token-grid">
      <div class="ds-token"><div class="ds-token-swatch" style="background: var(--bg)"></div><div class="ds-token-name">--bg</div></div>
      <div class="ds-token"><div class="ds-token-swatch" style="background: var(--bg-1)"></div><div class="ds-token-name">--bg-1</div></div>
      <div class="ds-token"><div class="ds-token-swatch" style="background: var(--tx)"></div><div class="ds-token-name">--tx</div></div>
      <div class="ds-token"><div class="ds-token-swatch" style="background: var(--tx-2)"></div><div class="ds-token-name">--tx-2</div></div>
      <div class="ds-token"><div class="ds-token-swatch" style="background: var(--tx-3)"></div><div class="ds-token-name">--tx-3</div></div>
      <div class="ds-token"><div class="ds-token-swatch" style="background: var(--bd)"></div><div class="ds-token-name">--bd</div></div>
      <div class="ds-token"><div class="ds-token-swatch" style="background: var(--bd-1)"></div><div class="ds-token-name">--bd-1</div></div>
      <div class="ds-token"><div class="ds-token-swatch" style="background: var(--bd-2)"></div><div class="ds-token-name">--bd-2</div></div>
    </div>
  </section>

  <section>
    <h2 style="margin-bottom: var(--s-5)">Components ({len(components)})</h2>
{body}
  </section>
</div>
</body>
</html>
"""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true", help="validate only, exit 1 on error")
    args = p.parse_args()

    components = load_components()
    if not components:
        print("error: no components in _data/components.yml", file=sys.stderr)
        return 2

    errs: list[str] = []
    errs.extend(check_partials(components))
    errs.extend(check_css_sections(components))
    errs.extend(check_tokens())
    errs.extend(check_icons())

    if errs:
        print("design system validation FAILED:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1

    if args.check:
        print(f"ok ({len(components)} components validated)")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(render_html(components))
    OUT_JSON.write_text(json.dumps({"components": components}, indent=2))
    print(f"ok — {len(components)} components")
    print(f"wrote {OUT_HTML.relative_to(REPO)}")
    print(f"wrote {OUT_JSON.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
