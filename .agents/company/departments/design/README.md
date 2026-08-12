# Design Department

Design owns visual production, not brand strategy. It consumes the canonical
company strategy and SpielOS design system, then produces graphics, banners,
article heroes, posters, and videos with render evidence. The department takes
video orders end-to-end (see "Video order flow" below).

For campaigns, Design accepts only the shared campaign Artifact from Content.
It records the `designed` handoff, validates the template, theme, semantic
tokens, title hierarchy, alignment, and platform preset, then returns one
`render_report` covering every item/platform pair. Templates expose
`__applyCampaignRendition`; renderers inject the rendition selected by
`CAMPAIGN_MANIFEST` and `CAMPAIGN_ITEM_ID`. Templates never fetch a named batch,
own campaign copy, or become a second strategy source.

Rendered evidence preserves `campaign_id`, `batch_id`, `item_id`, `content_id`,
and the derived creative signature. Local paths are not publishable media: the
approval handoff must also record a verified stable HTTPS asset URL.

The source of truth is `src/styles/tokens/`; `system/production.css` imports it
instead of copying a palette. Templates are format-agnostic and presets carry
channel dimensions. `threads-portrait` is 1080×1350 and `youtube-shorts` is
1080×1920; each ContentPackage must use the corresponding rendition rather than
resizing a generic template. Workflows: `social-visual`, `rendition-pack`,
`video-render`, `video-order`.

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

## Owner creative contract (2026-08-11 review + 2026-08-12 owner direction)

The review gates are encoded in `scripts/render-design.js --check` and
`scripts/render-video.js --check` and enforced by the pipeline scripts:

1. **ONE narration persona.** `voice_selection` in `templates/video/narration.json`
   pins the persona voice (Charon, a natural low-register male prebuilt voice).
   `scripts/tts-gemini.js` refuses per-call voice overrides, purges stale clips
   for the scenario before generating, and writes the voice into `scene_timing`
   and `public/videos/audio/.voice-manifest.json`; `scripts/mix-audio.js` refuses
   to mix mismatched provenance. Never mix clips from different generations.
2. **Multi-provider fallback chain (2026-08-12).** Narration is generated through
   a deterministic chain: Gemini 2.5 Flash TTS (primary) → Mistral Voxtral
   (fallback 1, both `MISTRAL_API_KEY` / `MISTRAL_API_KEY_2` with failover) →
   Cartesia (fallback 2) → ElevenLabs (fallback 3). On rate-limit/quota/auth/5xx
   failure the generator logs provider + status, purges the partial scenario,
   and the next provider retries the same clip — a clip is never dropped,
   the voice never changes mid-scenario, and stale clips are never reused.
   All five keys live in `.spielos/.env` (gitignored); `.env.example` carries
   names only. `scripts/tts-providers.js --check` verifies keys, chain order,
   and per-provider masculine voice pins (exit 0/1); `--list` shows
   providers/voices without secrets; `--probe` runs a live diagnostic clip per
   provider (never used for deliverables). Every provider pins a masculine
   low-register voice matching the persona.
3. **Full sentences.** Scene windows come from the MEASURED spoken clip
   durations (`scene_timing` in narration.json, written by tts-gemini.js).
   The video templates fetch narration.json at load and drive their scene
   switches from it — there is no hardcoded window to trim against. Clips get
   silent-edge trim only (never atempo, never mid-sentence cuts); if the
   measured schedule would overrun 14.9s the generator FAILS and the text is
   tightened instead.
4. **No music.** The mix is narration-only. `scripts/mix-audio.js` has no
   music bus, `narration.json` `mix.music` is `"none"`, and no music file is
   referenced anywhere in the pipeline or docs.
5. **Node pulses on the line, once.** Station nodes ride the journey path
   (`path.getPointAtLength` at each scene's measured start fraction — see
   `brand-motion.css`), and each fires a ONE-SHOT subtle ring flash when the
   line reaches it. No infinite ring animations on stations.
6. **Website typography.** Titles are Outfit 800, centered. `production.css`
   declares the website's font families with repo-root-resolvable
   `/public/assets/fonts/...` sources (the site's `src/assets/fonts/fonts.css`
   uses built-only `/assets/...` URLs, so the design system declares the same
   families itself). The gates verify in-render via
   `document.fonts.check("800 16px Outfit")` and computed styles — a
   system-font fallback fails the gate.
7. **Flat canvas social graphics.** `templates/social/harness-architecture.html`
   is a canvas composition: a connected journey line drawn THROUGH the
   department stations (vertices), a central loop symbol with the
   GOAL → OBSERVE → DECIDE → ACT → EVALUATE phases and the goal bullseye at
   its core, and a centered bold Outfit 800 title. No card-with-arrows
   website-screenshot layouts.

## Copywriting contract (per order)

Every video's narration follows the owner contract in `narration.json`
(`tone_contract`): ALWAYS a masculine voice; active, very confident, demanding,
aggressive but friendly, professional AND casual — NOT formal; short punchy
sentences with deliberate pauses; viral-style titles; each line connects to the
scenario's One Idea (strategy/voice.md — reference, never restate) without
mechanically repeating the company headline; the CTA lands the full
"spielos dot xyz slash services" read human-readable. Copy is written SHORT so
the measured schedule fits 14.9s at a slow, confident pace.

## Video order flow (department takes orders)

The `video-order` workflow accepts an order and runs it end-to-end:

1. **Intake** — accept the order (topic, channel aspect, run context).
2. **Idea lock** — One Idea Hierarchy from `.agents/company/strategy/voice.md`:
   company-promise connection + one topic-specific idea + one asset execution.
   The topic must be allowed by the canonical ICP/positioning
   (`.agents/company/strategy/icp.md`, `positioning.md` — reference, never restate).
3. **Scenario script** — narration lines per the copywriting contract
   (masculine persona, short lines, viral title, full CTA), stored in
   `templates/video/narration.json` (scenario lines + `scene_timing`).
4. **TTS via provider chain** — `node scripts/tts-gemini.js <b|c>` (chain in
   `scripts/tts-providers.js`): measured spoken durations, provider + voice
   provenance recorded, 14.9s overrun = tighten text.
5. **Narration-only mix** — `node scripts/mix-audio.js <b|c>` (-16 LUFS /
   -1 dBTP, 48kHz AAC, no music).
6. **Render** — `node scripts/render-video.js <b|c> <aspect> 30 <out>`;
   templates self-time from `scene_timing`; merge mix; posters + CTA frames.
7. **QA gates** — `render-design.js --check`, `render-video.js --check`,
   `tts-providers.js --check`, ffprobe stream/duration checks, frame
   inspection (pulses on line, Outfit 800, no empty renders).
8. **Deliverable** — complete set lands in
   `.spielos/artifacts/design-production-upgrade-20260810/` (video + audio +
   posters + CTA + graphics).

The `video-render` workflow (existing) remains the focused
render-and-verify step used when a script is already settled.

## Motion production (executed pipeline)

Video deliverables are produced end-to-end by scripts:

1. `scripts/tts-gemini.js <b|c>` — TTS through the provider chain with the
   pinned persona voice (stale clips purged first, silent-edge trim only),
   saving the MEASURED scene schedule into `templates/video/narration.json` →
   `scene_timing` (+ provider/voice provenance in `.voice-manifest.json`).
2. `scripts/mix-audio.js <b|c>` — narration-only mix from the measured
   schedule, loudnorm −16 LUFS / true peak −1 dBTP, 48kHz stereo AAC. No
   music bed; refuses mismatched voice provenance.
3. `scripts/render-video.js <b|c> <aspect> 30 <out>` — 30fps base render.
   The templates read `scene_timing` from narration.json themselves, so
   scene switches always follow the spoken durations.
4. Merge the mix into the base MP4 (copy video, AAC audio) + poster (0.6s)
   + CTA frame (0.45s after the last scene starts) + social graphics re-render.

Run everything per scenario with `bash scripts/render-all.sh <b|c> [30] [aspects]`.
The production set goes to `.spielos/artifacts/design-production-upgrade-20260810/`
(replacing any stale set); review samples go to
`.spielos/artifacts/design-restoration-polish-20260810/`.
