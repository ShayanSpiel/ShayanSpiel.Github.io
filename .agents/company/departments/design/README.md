# Design Department

Design owns visual production, not brand strategy. It consumes the canonical
company strategy and SpielOS design system, then produces graphics, banners,
article heroes, posters, and videos with render evidence.

The source of truth is `src/styles/tokens/`; `system/production.css` imports it
instead of copying a palette. Templates are format-agnostic and presets carry
channel dimensions. Workflows: `social-visual`, `rendition-pack`, `video-render`.
