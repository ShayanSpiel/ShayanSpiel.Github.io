# Design Department

Design owns visual production, not brand strategy. It consumes the canonical
company strategy and SpielOS design system, then produces graphics, banners,
article heroes, posters, and videos with render evidence.

The source of truth is `src/styles/tokens/`; `system/production.css` imports it
instead of copying a palette. Templates are format-agnostic and presets carry
channel dimensions. Workflows: `social-visual`, `rendition-pack`, `video-render`.

## Flat creative signature

The production reference is the existing Gruvbox-dark motion frame: flat grid,
centered Outfit typography, restrained Boxicons, and one wandering line behind
the message. The line is the branded signature across graphics and video: work
already completed is a solid primary stroke; the route ahead is muted and
dashed; the route ends at a simple flat bullseye. Keep it light and quiet.

Do not introduce 3D scenes, device mockups, glassmorphism, decorative card
systems, or spectacle-led gradients. Polish the existing composition through
alignment, spacing, readable hierarchy, the official logo, and a centered
`spielos.xyz` footer. Every design brief must also carry the One Idea Hierarchy
from `.agents/company/strategy/voice.md`: company-promise connection,
topic-specific idea, and one focused asset execution.

The shared flat motion/brand layer lives in
`templates/video/brand-motion.css` (journey line, bullseye goal, safe-area
brand footer); video templates link it and keep only per-scenario overrides.

## Owner creative contract (2026-08-11 review)

The review gates are encoded in `scripts/render-design.js --check` and
`scripts/render-video.js --check` and enforced by the pipeline scripts:

1. **ONE narration voice.** `voice_selection` in `templates/video/narration.json`
   pins the exact prebuilt voice (Charon). `scripts/tts-gemini.js` refuses
   per-call voice overrides, purges stale clips for the scenario before
   generating, and writes the voice into `scene_timing` and
   `public/videos/audio/.voice-manifest.json`; `scripts/mix-audio.js` refuses
   to mix mismatched provenance. Never mix clips from different generations.
2. **Full sentences.** Scene windows come from the MEASURED spoken clip
   durations (`scene_timing` in narration.json, written by tts-gemini.js).
   The video templates fetch narration.json at load and drive their scene
   switches from it — there is no hardcoded window to trim against. Clips get
   silent-edge trim only (never atempo, never mid-sentence cuts); if the
   measured schedule would overrun 14.9s the generator FAILS and the text is
   tightened instead.
3. **No music.** The mix is narration-only. `scripts/mix-audio.js` has no
   music bus, `narration.json` `mix.music` is `"none"`, and `music-ambient.mp3`
   is not referenced anywhere in the pipeline or docs.
4. **Node pulses on the line, once.** Station nodes ride the journey path
   (`path.getPointAtLength` at each scene's measured start fraction — see
   `brand-motion.css`), and each fires a ONE-SHOT subtle ring flash when the
   line reaches it. No infinite ring animations on stations.
5. **Website typography.** Titles are Outfit 800, centered. `production.css`
   declares the website's font families with repo-root-resolvable
   `/public/assets/fonts/...` sources (the site's `src/assets/fonts/fonts.css`
   uses built-only `/assets/...` URLs, so the design system declares the same
   families itself). The gates verify in-render via
   `document.fonts.check("800 16px Outfit")` and computed styles — a
   system-font fallback fails the gate.
6. **Flat canvas social graphics.** `templates/social/harness-architecture.html`
   is a canvas composition: a connected journey line drawn THROUGH the
   department stations (vertices), a central loop symbol with the
   GOAL → OBSERVE → DECIDE → ACT → EVALUATE phases and the goal bullseye at
   its core, and a centered bold Outfit 800 title. No card-with-arrows
   website-screenshot layouts.

## Motion production (executed pipeline)

Video deliverables are produced end-to-end by scripts:

1. `scripts/tts-gemini.js <b|c>` — Gemini 2.5 Flash TTS with the pinned
   master voice (stale clips purged first, silent-edge trim only) and saves
   the MEASURED scene schedule into `templates/video/narration.json` →
   `scene_timing` (+ `.voice-manifest.json` provenance).
2. `scripts/mix-audio.js <b|c>` — narration-only mix from the measured
   schedule, loudnorm −16 LUFS / true peak −1 dBTP, 48kHz stereo AAC. No
   music bed; refuses mismatched voice provenance.
3. `scripts/render-video.js <b|c> <aspect> 30 <out>` — 30fps base render.
   The templates read `scene_timing` from narration.json themselves, so
   scene switches always follow the spoken durations.
4. Merge the mix into the base MP4 (copy video, AAC audio) + poster (0.6s)
   + CTA frame (0.45s after the last scene starts).

Run everything per scenario with `bash scripts/render-all.sh <b|c> [30] [aspects]`.
Review-only deliverables go to `.spielos/artifacts/design-restoration-polish-20260810/`;
the owner-review re-render set goes to `.spielos/artifacts/design-production-upgrade-20260810/`.
