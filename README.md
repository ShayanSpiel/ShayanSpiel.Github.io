# Shayan Spiel — spielos.xyz

Personal site and blog of [Shayan Spiel](https://spielos.xyz). Tracks the AI market like a war, builds projects from the gaps.

## Stack

- **Static site:** Jekyll 3.10 on GitHub Pages
- **CSS:** Custom design system (no framework), self-hosted fonts (Inter, Merriweather, JetBrains Mono)
- **Analytics:** GA4 + PostHog (self-hosted proxy via Cloudflare Workers)
- **SEO:** JSON-LD structured data on every page, jekyll-seo-tag, jekyll-sitemap
- **Build:** Python scripts sync design tokens and validate the component system

## Structure

```
_includes/       — Partial templates (head, nav, footer, components)
_layouts/        — Page layouts (default, post-shell, page-shell, blog, archive)
_posts/          — Blog posts (HTML with YAML front matter)
_data/           — YAML data (design tokens, components, icons, clusters, menu)
assets/          — CSS, fonts, images, JS, favicons, OG images
_tools/          — Build scripts (token sync, design system sync, OG gen)
SpielOS/         — Spiel OS project landing page
clusters/        — Topic cluster index pages
design-system/   — Generated design system documentation
```

## Development

```bash
bundle install
bundle exec jekyll serve
```

Full build pipeline (token sync + design system validation + Jekyll build):

```bash
./scripts/build.sh
```

## License

Content and design © Shayan Spiel. Code is MIT unless otherwise noted.

