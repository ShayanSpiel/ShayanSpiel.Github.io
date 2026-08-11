---
name: video-creation
description: Create promo videos from HTML templates using Puppeteer frame capture, FFmpeg encoding, and Gemini 2.5 Flash TTS narration. Use for any video creation task: product videos, social media clips, launch videos, before/after comparisons, explainer videos, or animated demos. Covers scene composition, CSS animation system, virtual clock, multi-aspect-ratio rendering, one-voice TTS narration, narration-only mixing, and batch generation.
---

# Video Creation

## Mission

Create flat, production-ready motion pieces from the existing SpielOS templates, encode them with FFmpeg, and deliver them with approved, narration-only audio. Preserve the established composition and branded goal line; the rendering method must never make the result feel like an HTML page recorded as video.

## Scope

Owns: Video creation, HTML-to-video rendering, scene composition, CSS animation system, virtual clock, multi-aspect-ratio rendering, batch generation, one-voice TTS narration, narration-only mixing, poster generation.

Does NOT own:
- Design tokens → see `../spielos-ui/SKILL.md`
- Analytics tracking → see `../analytics/SKILL.md`
- Content writing → see `../copywriting-en/SKILL.md`

## Reference files

Before creating videos, read:

- `.agents/company/departments/design/templates/video/scenario-b.html` — Before/After template
- `.agents/company/departments/design/templates/video/scenario-c.html` — Build It template
- `.agents/company/departments/design/templates/video/brand-motion.css` — shared flat journey-line, bullseye goal, and brand-footer motion layer
- `.agents/company/departments/design/templates/video/narration.json` — TTS voice pin, script, measured scene_timing, and narration-only mix brief
- `.agents/company/strategy/voice.md` — canonical One Idea Hierarchy
- `scripts/render-video.js` — Puppeteer + FFmpeg renderer (and the owner-contract `--check` gate)
- `.agents/company/departments/design/system/production.css` — tokens + website fonts resolved for the render context

---

## Prerequisites

| Tool | Install | Purpose |
|---|---|---|
| Node.js 18+ | `brew install node` | Runtime |
| Puppeteer | `npm install puppeteer` | Headless Chrome for frame capture |
| FFmpeg | `brew install ffmpeg` | Frame-to-MP4 encoding, audio mixing |
| ffprobe | via FFmpeg | Measuring spoken clip durations |

### Check prerequisites

```bash
node --version    # Should be 18+
ffmpeg -version   # Should be 5+
```

---

## Owner creative contract (2026-08-11 review)

The gates below are enforced mechanically by `node scripts/render-video.js --check`
and `node scripts/render-design.js --check` — a deliverable that violates any of
them fails the gate:

1. **ONE narration voice.** `narration.json` `voice_selection` pins the exact
   prebuilt voice (`Charon`). Every clip for every scenario is generated with
   that same voiceName. There is no per-call voice argument, no auditioning,
   no mixing clips from different generations. `tts-gemini.js` refuses voice
   overrides and purges stale clips before generating; `mix-audio.js` refuses
   mismatched provenance (narration.json + `.voice-manifest.json`).
2. **Full sentences — speech first, then scenes.** Scene windows come from the
   MEASURED spoken clip durations written into `narration.json` →
   `scene_timing`. The templates fetch that schedule at load and switch scenes
   from it; a hardcoded window can never cut a sentence. Clips are silent-edge
   trimmed only (no atempo, no mid-sentence trims). If the measured schedule
   would overrun 14.9s the generator fails and the TEXT is tightened.
3. **No music.** The mix is narration-only: no music bed, no duck bus. The
   spec in `narration.json` (`mix.music: "none"`) carries no music fields.
4. **Node pulses on the line, once.** Stations ride the journey path
   (`path.getPointAtLength` at each scene's measured start fraction) and fire
   a one-shot subtle ring flash exactly when the line reaches them. Never an
   infinite ring animation on stations.
5. **Website typography.** Titles are Outfit weight 800 and centered. Fonts
   must resolve in the render context exactly like the site (see Fonts
   section) — a system-font fallback fails the gate.
6. **Flat canvas graphics.** Social templates are canvas compositions
   (connected journey line, loop symbol, centered bold Outfit title), never
   card-with-arrows website-screenshot layouts.

## Pipeline overview

```
Script lines → Gemini TTS (pinned voice, pronunciation-fixed)
→ silent-edge trim + MEASURED scene_timing (speech first)
→ narration-only mix (-16 LUFS / -1 dBTP, 48kHz AAC)
→ base render (templates read scene_timing) → merge audio → poster + CTA frame
```

1. Write narration script (one line per scene) in `templates/video/narration.json`
2. `node scripts/tts-gemini.js <b|c>` — Gemini 2.5 Flash TTS with the pinned
   master voice; purges stale clips for the scenario, measures each spoken
   take, saves `scene_timing` into `narration.json` and provenance into
   `public/videos/audio/.voice-manifest.json`. Fails on overrun (tighten the
   TEXT) and on any voice override.
3. `node scripts/mix-audio.js <b|c>` — narration-only mix from the measured
   schedule, loudnorm -16 LUFS / true peak -1 dBTP, 48kHz AAC. No music bed;
   refuses mismatched voice provenance or a missing measured schedule.
4. `node scripts/render-video.js <scenario> <aspect> 30 <out-base.mp4>` —
   Puppeteer frame capture + FFmpeg encode at 30fps. Templates read
   `scene_timing` from narration.json themselves.
5. Merge mix into base MP4 (copy video, AAC audio)
6. Poster at 0.6s (composed frame, not the dark pre-timing frame); CTA image
   0.45s after the last scene starts.

Run the whole chain per scenario with:
`bash scripts/render-all.sh <b|c> [30] [aspects]`
Deliverables land in `.spielos/artifacts/design-restoration-polish-20260810/`
(review samples) or `.spielos/artifacts/design-production-upgrade-20260810/`
(owner-review re-render set).

## One Idea Hierarchy and visual lock

Before scripting, lock the company-promise connection, one topic-specific idea,
and one asset execution. The title, narration, scenes, signature line, music,
and CTA must support the same topic. A video may explain a different mechanism,
problem, or objection than another video; it must still connect naturally to
the company offer.

The visual authority is the existing flat Gruvbox composition: subtle grid,
centered Outfit typography, restrained Boxicons, and the wandering goal line.
Completed travel is solid primary; future travel is muted dashed; the line ends
in a flat bullseye. Add only alignment, spacing, official logo, centered URL,
and readability polish. Do not introduce 3D, device mockups, glassmorphism,
card-heavy redesigns, or spectacle-led gradients.

> Note: in the narration lines above, "music" is a legacy word in the
> hierarchy rule — the final deliverables are narration-only; the rule's
> intent is that every element of the piece supports the same topic.

---

## TTS voice — one pinned voice, no auditions

### Gemini 2.5 Flash TTS (production)

`scripts/tts-gemini.js` uses `gemini-2.5-flash-preview-tts` with
`GEMINI_API_KEY` loaded only from `.spielos/.env`. The voice is pinned in
`templates/video/narration.json` → `voice_selection` (currently `Charon`, a
natural low-register prebuilt voice) and is read by the generator — there is
no CLI voice argument, so a clip can never be generated with a different
voice. Follow the approved performance direction in `narration.json`:
deep grounded adult male, restrained confidence, warm human cadence. Do not
imitate or claim to reproduce any real person.

Deliberate pronunciation fixes (the legacy Kokoro take failed these):
- `SpielOS` is spoken as "shpeel-oh-es" (never "zyos");
- `spielos.xyz` is spoken as "spielos dot ex why zee";
- the URL CTA always ends fully: "... slash services".

The generator adds these automatically; do not remove them.

Free-tier rate limit is 3 requests/min: the generator spaces calls ~30s apart
and retries 429s with backoff (60s+). Never parallelize TTS calls. If a call
is throttled, WAIT and retry — never switch to a different voice or reuse old
clips to "finish faster".

**No-cut rule:** clips are silent-edge trimmed only. Never atempo-fit a clip
and never trim mid-sentence. If the measured schedule overruns 14.9s, the
narration TEXT in `narration.json` must be tightened and the clip
re-generated. Cutting a sentence mid-word is a rejected deliverable.

### Legacy Kokoro fallback (deprecated — never production)

The robotic `am_michael` Kokoro clips caused rejected deliveries (bad
pronunciation, unnatural pacing, mid-sentence cuts) and mixed ~5 voices into
earlier renders. They are archived under `public/videos/audio/legacy-kokoro/`
and are NOT production assets; they are not referenced by the pipeline and
must never be mixed with Gemini clips.

---

## Scene fit and timing — speech first, then scenes

All clips in a scenario use the SAME pinned voice and a consistent human
pace. Scene timing is derived from MEASURED Gemini clip durations, never from
hardcoded windows:

1. `tts-gemini.js` generates each line (pinned voice), silent-edge trims,
   and measures the take with ffprobe.
2. Starts are scheduled as cumulative measured durations + 0.25s breath gaps;
   the last speech must end by 14.9s (generator fails on overrun).
3. The measured schedule is persisted into `narration.json` → `scene_timing`
   (with the voice) and consumed by `scripts/mix-audio.js` AND the video
   templates (they `fetch()` narration.json at load — no template edit step
   needed, no window to drift).
4. If the schedule overruns 14.9s, tighten the narration text and regenerate —
   never stretch, never cut words, never change voice.

Scene windows in the templates: scene `i` is active from
`scene_timing[i].start` to `scene_timing[i+1].start` (the last scene holds to
15s). Element reveals are small offsets after each scene's start. Station
nodes pop in and flash once when the line's progress reaches their scene
start fraction.

---

## Audio pipeline — narration only

### Narration scripts

**Scenario B (Before/After)**:
```
Hook:    "Your AI tools work alone."
Pain:    "Prompts vanish. Context resets."
Promise: "Give AI work a system."
Pillars: "Roles. Skills. Workflows. Evals."
Director: "Set the goal. The system moves."
CTA:     "Direct the work. spielos dot xyz slash services."
```

**Scenario C (Build It)**:
```
Hook:    "What if your AI employees worked as a team?"
Build:   "Hire roles. Give context. Set standards. Connect workflows."
Live:    "Your AI department is live."
Director: "Choose the goal. Keep the judgment."
CTA:     "Build your system. spielos dot xyz slash services."
```

### Mix (narration-only)

`node scripts/mix-audio.js <b|c>` mixes the measured clips with per-scene
delays and fades, loudnorm −16 LUFS / TP −1 dBTP, 48kHz stereo AAC, 15s.
There is NO music input, no duck bus, and no music file requirement. The mix
refuses to run without a measured schedule (a sentence can never be cut by a
hardcoded window) and refuses mismatched voice provenance.

```bash
node scripts/mix-audio.js b .spielos/artifacts/audio/mix-b.m4a
node scripts/mix-audio.js c .spielos/artifacts/audio/mix-c.m4a
```

### Verify the mix

```bash
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 mix-b.m4a  # ~15s
ffprobe -v error -show_entries stream=codec_type,sample_rate -of json mix-b.m4a  # audio 48000
```

---

## Rendering

### Single video

```bash
node scripts/render-video.js <scenario> <aspect> [fps] [output]
```

**Scenarios**: `b` (Before/After), `c` (Build It)

**Aspects**:
| Name | Resolution | Use |
|---|---|---|
| landscape | 1920x1080 | YouTube, LinkedIn, X |
| portrait | 1080x1920 | Reels, TikTok, Shorts |
| square | 1080x1080 | Instagram feed |
| story | 1080x1350 | Instagram portrait |

### Examples

```bash
node scripts/render-video.js b landscape 30
node scripts/render-video.js b portrait 30
node scripts/render-video.js c landscape 30
node scripts/render-video.js c portrait 30
node scripts/render-video.js --check
```

### Owner-contract gate

```bash
node scripts/render-video.js --check
node scripts/render-design.js --check
```

`--check` launches the real render context (repo root served over localhost)
and fails on: multi-voice narration.json, any music spec remnants in the
spec/pipeline/templates, missing Outfit font in-render
(`document.fonts.check("800 16px Outfit")`), titles not Outfit 800/centered,
stations off the journey line, hardcoded scene windows, and infinite ring
pulses. Run it before every render batch.

### Merge audio into video

```bash
ffmpeg -y -i base-video.mp4 -i mix.m4a -c:v copy -c:a aac -b:a 192k -shortest output-voiced.mp4
```

---

## Poster generation

```bash
ffmpeg -y -ss 0.6 -i video-voiced.mp4 -vframes 1 -q:v 2 video-poster.jpg
ffmpeg -y -i video-voiced.mp4 -ss <lastSceneStart+0.45> -frames:v 1 video-cta.jpg
```

---

## Full workflow

```bash
# 1. Generate + measure narration (ONE pinned voice, stale clips purged)
node scripts/tts-gemini.js b
node scripts/tts-gemini.js c

# 2. Narration-only mixes
node scripts/mix-audio.js b
node scripts/mix-audio.js c

# 3. Render base video (templates time themselves from scene_timing)
node scripts/render-video.js b landscape 30

# 4. Merge narration-only audio
ffmpeg -y -i .spielos/artifacts/design-restoration-polish-20260810/video/spielos-before-after-flat-polish-16x9-base.mp4 \
  -i .spielos/artifacts/audio/mix-b.m4a -c:v copy -c:a aac -b:a 192k -shortest \
  spielos-before-after-16x9-voiced.mp4

# 5. Poster (0.6s) + CTA frame
ffmpeg -y -ss 0.6 -i spielos-before-after-16x9-voiced.mp4 -frames:v 1 spielos-before-after-16x9-voiced-poster.jpg
```

Or run the whole chain per scenario: `bash scripts/render-all.sh <b|c>`.

---

## HTML template anatomy

### Virtual clock

```javascript
window.__t = 0;        // Current time in seconds
window.__fps = 30;     // Frames per second
window.__duration = 15; // Total duration

window.__setFrame = function(frame, fps) {
  window.__fps = fps || 30;
  window.__t = frame / window.__fps;
};
```

### Measured scene schedule (speech first)

Templates fetch the measured schedule at load and gate on it — the frame
stays dark until the schedule arrives, so a render can never start on a
guessed window:

```javascript
window.__timing = null;
fetch('/.agents/company/departments/design/templates/video/narration.json')
  .then(r => r.json())
  .then(d => { window.__timing = d.scene_timing && d.scene_timing.b; });
```

### Scene system

```css
.scene {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  opacity: 0; pointer-events: none; z-index: 10;
}
.scene.active { opacity: 1; pointer-events: auto; }
```

### Text reveal

```css
.r {
  opacity: 0; transform: translateY(24px); filter: blur(4px);
  transition: opacity 0.6s cubic-bezier(0.16,1,0.3,1),
              transform 0.6s cubic-bezier(0.16,1,0.3,1),
              filter 0.4s cubic-bezier(0.16,1,0.3,1);
}
.r.show { opacity: 1; transform: translateY(0); filter: blur(0); }
```

### Tick function pattern

```javascript
function tick() {
  var t = window.__t;
  if (!window.__timing) { requestAnimationFrame(tick); return; }
  var sc = window.__timing.scenes;         // measured windows
  var idx = -1;
  for (var i = 0; i < sc.length; i++) {
    if (t >= sc[i].start && (i === sc.length - 1 || t < sc[i + 1].start)) { idx = i; break; }
  }
  if (idx === 0) { act('s1'); /* reveals relative to sc[0].start */ }
  // ...
  requestAnimationFrame(tick);
}
tick();
```

### Stations on the line (one-shot node hit)

```javascript
// Place each station at its scene-start fraction of the path:
var pt = pathFill.getPointAtLength((sc[sceneIdx].start / lineEnd) * pathLen);
stationEl.setAttribute('transform', 'translate(' + pt.x + ',' + pt.y + ')');
// Fire ONCE when the line reaches it:
if (!fired && progress >= frac) { stationEl.classList.add('show'); ring.classList.add('hit'); }
```

The `.hit` class triggers the one-shot `nodeHit` flash in `brand-motion.css`
(`animation: nodeHit .55s ease-out 1`) — never an infinite ring.

---

## Fonts and tokens in the render context

Templates link `system/production.css`, which:

1. Declares Outfit (variable 100–900), JetBrains Mono (400–600), and boxicons
   `@font-face` blocks with repo-root-resolvable paths
   (`/public/assets/fonts/*.woff2`) — the website's `src/assets/fonts/fonts.css`
   uses built-only `/assets/...` URLs, so the design system declares the same
   families itself for renders.
2. Defines `--font-outfit`/`--font-jetbrains-mono` BEFORE importing the
   canonical tokens (`/src/styles/tokens/index.css`), so the token `--font-sans`
   stack stays valid.
3. Renders must serve the repo ROOT over localhost (both render scripts do) —
   never `file://`, where absolute site-root paths fail.

Titles must be `font-weight: 800` and centered; the gates verify both
in-render.

---

## Boxicons in headless Chrome

Boxicons require TWO things to render in Puppeteer:

1. **CSS link** in `<head>`:
```html
<link rel="stylesheet" href="/node_modules/boxicons/css/boxicons.min.css">
```

2. **A boxicons @font-face** — provided by `production.css`
(`/public/assets/fonts/boxicons.woff2`).

Without both, icons render as empty squares.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Icons empty squares | Confirm the boxicons CSS link + production.css font-face load (repo root served) |
| Gate: Outfit not loaded | Confirm production.css loads; render over localhost, never file:// |
| Gate: station off the line | Templates place stations via `path.getPointAtLength` — don't hand-place coords |
| Gate: scene_timing not applied | Run `tts-gemini.js` first; templates fetch narration.json at load |
| TTS quota / 429 | Wait and retry inside the session; NEVER switch voice or reuse old clips |
| Scene bleed (old text visible) | Remove CSS `transition` from `.scene` opacity |
| Frames directory error | Run renders sequentially, not parallel (shared frame dir) |
| Mix refuses to run | Measured `scene_timing` missing or voice provenance mismatch — regenerate with the pinned voice |

---

## Output rules

After creating a video, report:

- Template file path
- Output file path
- Aspect ratios rendered
- Voice used (must equal `narration.json` `voice_selection` for BOTH scenarios)
- Measured scene windows (speech-first schedule)
- Duration and FPS
- Total frames
- File size
- Any rendering issues
- Audio-stream verification (narration-only, no music) and voice provenance
