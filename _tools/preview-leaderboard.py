#!/usr/bin/env python3
"""
Build a self-contained standalone HTML preview of the LLM Cost Leaderboard page.

- Embeds the real site CSS (fonts + main) inline so it looks identical to the
  deployed site when opened directly via file:// (no server needed).
- Includes the real site nav and footer (footer.html content inlined).
- Loads tweets via the Twitter oEmbed API with theme=dark for seamless dark-mode
  integration (same approach as /SpielOS).

Usage:
    python3 _tools/preview-leaderboard.py
    open _tools/preview.html
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "llm-cost-leaderboard.html"
OUT = ROOT / "_tools" / "preview.html"
FONTS_CSS = (ROOT / "assets" / "css" / "fonts.css").read_text(encoding="utf-8")
MAIN_CSS = (ROOT / "assets" / "css" / "main.css").read_text(encoding="utf-8")


def rewrite_css_paths(css: str) -> str:
    css = re.sub(r"url\((['\"]?)/assets/fonts/([^'\")]+)\1\)",
                 r"url(\1../assets/fonts/\2\1)", css)
    css = re.sub(r"url\((['\"]?)/assets/([^'\")]+)\1\)",
                 r"url(\1../assets/\2\1)", css)
    return css


src = SRC.read_text(encoding="utf-8")

fm_match = re.match(r"^---([\s\S]*?)---", src)
title = description = ""
if fm_match:
    for line in fm_match.group(1).splitlines():
        if line.startswith("title:"):
            title = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            description = line.split(":", 1)[1].strip().strip('"').strip("'")

body = src[fm_match.end():] if fm_match else src

style_match = re.search(r"<style>([\s\S]*?)</style>", src)
page_style = style_match.group(1) if style_match else ""

fonts_inline = rewrite_css_paths(FONTS_CSS)
main_inline = rewrite_css_paths(MAIN_CSS)

# Real site footer with email signup (footer.html content, Liquid tags stripped)
footer = """<footer role="contentinfo">
  <div class="footer-inner">
    <nav class="footer-social" role="list" aria-label="Social links">
      <a href="https://x.com/ShayanSpiel" target="_blank" rel="noopener" aria-label="X / Twitter" role="listitem">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
      </a>
      <a href="https://www.linkedin.com/in/shayantawabi" target="_blank" rel="noopener" aria-label="LinkedIn" role="listitem">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.5 2h-17A1.5 1.5 0 0 0 2 3.5v17A1.5 1.5 0 0 0 3.5 22h17a1.5 1.5 0 0 0 1.5-1.5v-17A1.5 1.5 0 0 0 20.5 2zM8 19H5v-9h3zM6.5 8.25A1.75 1.75 0 1 1 8.3 6.5a1.78 1.78 0 0 1-1.8 1.75zM19 19h-3v-4.74c0-1.42-.6-1.93-1.38-1.93A1.74 1.74 0 0 0 13 14.19a.66.66 0 0 0 0 .14V19h-3v-9h2.9v1.3a3.11 3.11 0 0 1 2.7-1.4c1.55 0 3.36.86 3.36 3.66z"/></svg>
      </a>
      <a href="https://github.com/ShayanSpiel" target="_blank" rel="noopener" aria-label="GitHub" role="listitem">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
      </a>
      <a href="/feed.xml" aria-label="RSS Feed" role="listitem">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M6.18 15.64a2.18 2.18 0 0 1 2.18 2.18C8.36 19 7.38 20 6.18 20A2.18 2.18 0 0 1 4 17.82a2.18 2.18 0 0 1 2.18-2.18M4 4.44A15.56 15.56 0 0 1 19.56 20h-2.83A12.73 12.73 0 0 0 4 7.27V4.44m0 5.66a9.9 9.9 0 0 1 9.9 9.9h-2.83A7.07 7.07 0 0 0 4 12.93V10.1Z"/></svg>
      </a>
      <a href="mailto:66shayan@gmail.com" aria-label="Email" role="listitem">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
      </a>
    </nav>

    <form class="footer-newsletter" id="subscribe" action="https://docs.google.com/forms/d/e/1FAIpQLScSAISdLXFTAex_cHMmdMCXQdaMGlwLouLRmptFo_5VcdV_GA/formResponse" method="POST" target="hidden_iframe" aria-label="Newsletter signup">
      <label for="footer-email" class="sr-only">Email address</label>
      <input id="footer-email" type="email" name="entry.754901073" placeholder="Your email" required autocomplete="email" aria-required="true" />
      <input type="hidden" name="entry.2021940811" value="Newsletter" />
      <button type="submit">Subscribe</button>
    </form>
    <div class="footer-newsletter-status" id="newsletter-status" role="status" aria-live="polite"></div>

    <div class="footer-copy">&copy; 2026 Shayan Spiel &middot; <a href="/branding/">Branding</a></div>
  </div>

  <iframe name="hidden_iframe" id="hidden_iframe" title="newsletter-submit" hidden></iframe>
  <script>
  (function () {
    var form = document.getElementById("subscribe");
    var iframe = document.getElementById("hidden_iframe");
    var status = document.getElementById("newsletter-status");
    if (!form || !iframe) return;
    var btn = form.querySelector("button");
    var input = form.querySelector('input[type="email"]');
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var email = (input && input.value || "").trim();
      if (!email) { if (input) input.focus(); return; }
      if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)) {
        if (status) status.textContent = "Please enter a valid email.";
        if (status) status.className = "footer-newsletter-status err";
        if (input) input.focus();
        return;
      }
      btn.textContent = "Sending...";
      btn.disabled = true;
      if (status) { status.textContent = ""; status.className = "footer-newsletter-status"; }
      form.submit();
      setTimeout(function () {
        btn.textContent = "Subscribed";
        if (input) input.value = "";
        if (status) { status.textContent = "You're in. Check your inbox."; status.className = "footer-newsletter-status ok"; }
      }, 1500);
    });
  })();
  </script>
</footer>"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="robots" content="noindex,nofollow">
<meta name="color-scheme" content="dark">

<!-- Site fonts -->
<style>
{fonts_inline}
</style>

<!-- Site main styles -->
<style>
{main_inline}
</style>

<!-- Page-specific styles -->
<style>
{page_style}
</style>
</head>
<body class="page">
<a href="#main-content" class="skip-link">Skip to content</a>

<nav class="nav" aria-label="Main navigation">
  <div class="nav-inner">
    <a class="nav-brand" href="/" aria-label="Shayan Spiel — Home">
      <svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M16 7l-12 12 6 6 3-3 3 3 3-3 3 3 6-6-12-12zM16 19l-3-3 3-3 3 3-3 3z"/></svg>
    </a>
    <span class="nav-links">
      <a href="/about/">About</a>
      <a href="/posts/">Blog</a>
      <a href="/contact/">Contact</a>
    </span>
    <a href="/SpielOS/" class="nav-cta">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M13 5l7 7-7 7M5 12h15"/></svg>
      Get Spiel
    </a>
  </div>
</nav>

<main id="main-content">
{body}
</main>

{footer}
</body>
</html>
"""

OUT.write_text(html, encoding="utf-8")
print(f"OK — wrote {OUT}")
print(f"     open file://{OUT}")
