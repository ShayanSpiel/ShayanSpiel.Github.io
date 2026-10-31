# Current OG image workflow

`public/` is the released Karwise website snapshot. OG page inventory comes
from the final `dist/` build after `scripts/retired-routes.json` has applied
redirect policy. This excludes redirect stubs and retired Notes routes; the
legacy Astro manifest in `scripts/generate-og.mjs` is not the active inventory.

## Update or add a page

1. Set the page's real title, `og:title`, description, canonical URL and locale
   in its public HTML. Do not write a new headline for the image.
2. Run `npm run og:generate`. It builds the final route set, renders one
   1200×630 image per canonical page, and updates only `og:image` and
   `twitter:image` URLs. Artwork uses the page's current `og:title` and
   `og:description`; page titles and copy remain unchanged.
3. Run `npm run build`, `npm test`, `npm run lint` and `npm run seo:check`.

Generated covers live under `public/assets/og/v5/`. The versioned manifest
`public/assets/og/karwise-cover-manifest.json` records each canonical route,
its source title and description, image path and content hash. Existing OG
files are preserved; generation does not prune old assets.

The website build fails if a canonical page lacks a manifest entry, has a
stale title or description, reuses another page's image, points at a missing
cover, has a stale image hash, or has mismatched OG and Twitter image URLs.
Add the page and its cover before publishing.
