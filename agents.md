# Shayan Spiel — Agent Instructions

## Site Overview
- Jekyll 3.10 static site on GitHub Pages
- Custom CSS design system (no framework)
- Components in `_includes/components/`, managed via `_data/components.yml`
- Design tokens in `_data/design-tokens.yml`, synced to `assets/css/tokens.css` via `_tools/sync-tokens.py`
- Build pipeline: `scripts/build.sh` (sync tokens → sync design system → jekyll build)

## Key Conventions
- Use `components/` partials for reusable UI (btn, card, section-head, icon, etc.)
- Use `page-shell` layout for content pages, `post-shell` for blog posts
- Never hardcode styles — add CSS classes to `assets/css/components.css`
- All icons come from `_data/icons.yml`, rendered via `components/icon.html`
- JSON-LD structured data in `_includes/structured-data.html`
- Fonts: self-hosted woff2 in `assets/fonts/`, declared in `assets/css/fonts.css`

## File Organization
- `_layouts/` — page templates
- `_includes/` — partials (nav, footer, head, components/)
- `_data/` — YAML data files
- `_posts/` — blog posts (date-prefixed HTML files)
- `assets/css/` — CSS (tokens, base, components, layout, fonts)
- `clusters/` — topic cluster index pages
- `SpielOS/` — Spiel OS project page
- `_tools/` — build/utility scripts

## Prohibited
- Do not use inline `style=` attributes in templates
- Do not add Google Fonts CDN links (fonts are self-hosted)
- Do not create standalone HTML pages — use Jekyll layouts
- Do not hardcode SVG paths where `components/icon.html` can be used
