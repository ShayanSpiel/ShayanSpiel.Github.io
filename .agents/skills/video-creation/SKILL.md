---
name: video-creation
description: Create promo videos from HTML templates using Puppeteer frame capture, FFmpeg encoding, and Kokoro TTS narration. Use for any video creation task: product videos, social media clips, launch videos, before/after comparisons, explainer videos, or animated demos. Covers scene composition, CSS animation system, virtual clock, multi-aspect-ratio rendering, TTS narration, audio mixing, and batch generation.
---

# Video Creation

## Mission

Create videos from HTML templates by rendering CSS animations frame-by-frame with Puppeteer, encoding them into MP4 with FFmpeg, and adding TTS narration with background music. No video editing software required — just HTML, CSS, JavaScript, and a TTS API.

## Scope

Owns: Video creation, HTML-to-video rendering, scene composition, CSS animation system, virtual clock, multi-aspect-ratio rendering, batch generation, TTS narration, audio mixing, poster generation.

Does NOT own:
- Design tokens → see `../spielos-ui/SKILL.md`
- Analytics tracking → see `../analytics/SKILL.md`
- Content writing → see `../copywriting-en/SKILL.md`

## Reference files

Before creating videos, read:

- `src/video-templates/scenario-b.html` — Before/After template (reference)
- `src/video-templates/scenario-c.html` — Build It template (reference)
- `scripts/render-video.js` — Puppeteer + FFmpeg renderer
- `public/videos/audio/music-ambient.mp3` — Background music

---

## Prerequisites

| Tool | Install | Purpose |
|---|---|---|
| Node.js 18+ | `brew install node` | Runtime |
| Puppeteer | `npm install puppeteer` | Headless Chrome for frame capture |
| FFmpeg | `brew install ffmpeg` | Frame-to-MP4 encoding, audio mixing |
| curl | Built-in | TTS API calls |

### Check prerequisites

```bash
node --version    # Should be 18+
ffmpeg -version   # Should be 5+
```

---

## Pipeline overview

```
Script lines → TTS API → Raw WAVs → Speed compress → Combine with delays → Mix music → Merge into video → Poster
```

1. Write narration script (one line per scene)
2. Generate WAV clips via Kokoro TTS (`am_michael` voice)
3. Apply consistent speed factor to fit 15s
4. Combine clips with scene-timed delays
5. Mix narration + ambient music
6. Render HTML template to base MP4 (Puppeteer + FFmpeg)
7. Merge audio into base MP4
8. Generate poster thumbnail from first frame

---

## TTS voice

**Voice**: `am_michael` (Kokoro male American)

**API**: `https://api.free.ai/v1/tts/`

**Important**: `am_adam` does NOT exist on this API. `am_michael` is the male American Kokoro voice.

### Generate a clip

```bash
curl -s --max-time 60 -X POST https://api.free.ai/v1/tts/ \
  -H "Content-Type: application/json" \
  -d '{"text":"Your narration text here.","voice":"am_michael"}' \
  -o output.json

# Extract audio_url from JSON, then download:
curl -s -o output.wav "$AUDIO_URL"
```

### Rate limiting

- 2 seconds between API calls minimum
- Sequential requests, NOT parallel
- Free tier: ~5000 chars/day/IP

---

## Speed factor

All clips in a scenario must use the SAME speed factor for consistent pacing.

### Formula

```
speed = raw_total_duration / target_duration
```

For 15s videos: `speed = raw_total / 15`

### Known speed factors

| Scenario | Voice | Speed factor |
|---|---|---|
| B (Before/After) | am_michael | 1.425x |
| C (Build It) | am_michael | 1.335x |

### Apply speed

```bash
ffmpeg -y -i input.wav -af "atempo=1.425" -ar 44100 -ac 1 output.mp3
```

**atempo limits**: 0.5x to 2.0x. If you need faster, chain: `atempo=2.0,atempo=1.5` for 3.0x.

---

## Scene timing

Scene timing is derived from compressed clip durations, NOT hardcoded.

### Calculate timing

```bash
# After compressing all clips, measure each duration:
for clip in hook pain promise pillars director cta; do
  dur=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${clip}-final.mp3")
  echo "$clip: ${dur}s"
done

# Add cumulative start times:
# hook: 0 → dur1
# pain: dur1 → dur1+dur2
# promise: dur1+dur2 → dur1+dur2+dur3
# ... etc
```

### Update HTML template

Update the `tick()` function scene boundaries and `stationTimes` array to match calculated timings.

---

## Audio pipeline

### Narration scripts

**Scenario B (Before/After)**:
```
Hook:    "Your AI tools aren't working as a team."
Pain:    "Employees using AI separately. Repeated prompts. Disconnected tools."
Promise: "What if they could work like a real team?"
Pillars: "Roles. Skills. Evals. Workflows."
Director: "Be the director. Or don't."
CTA:     "spielos dot xyz forward slash services"
```

**Scenario C (Build It)**:
```
Hook:    "What if your AI employees could work like a real team?"
Build:   "Hire a role. Give instructions and tools. Set quality standards. Connect into workflows."
Live:    "Your AI department is live."
Director: "Director mode. You choose."
CTA:     "spielos dot xyz forward slash services"
```

### Combine with delays

```bash
ffmpeg -y \
  -i hook-final.mp3 \
  -i pain-final.mp3 \
  -i promise-final.mp3 \
  -i pillars-final.mp3 \
  -i director-final.mp3 \
  -i cta-final.mp3 \
  -filter_complex "
    [0]adelay=0|0[h];
    [1]adelay=2340|2340[pn];
    [2]adelay=6490|6490[pr];
    [3]adelay=8560|8560[pl];
    [4]adelay=10880|10880[dr];
    [5]adelay=12600|12600[ct];
    [h][pn][pr][pl][dr][ct]amix=inputs=6:duration=longest:dropout_transition=0[out]
  " -map "[out]" -t 15 -ar 44100 -ac 2 narration.mp3
```

### Mix with music

```bash
ffmpeg -y -i narration.mp3 -i music-ambient.mp3 \
  -filter_complex "[0]volume=1.0[n];[1]volume=0.2[m];[n][m]amix=inputs=2:duration=longest:dropout_transition=0" \
  -t 15 -ar 44100 -ac 2 final-audio.mp3
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
```

### Merge audio into video

```bash
ffmpeg -y -i base-video.mp4 -i final-audio.mp3 \
  -c:v copy -c:a aac -b:a 128k -shortest output-voiced.mp4
```

---

## Poster generation

```bash
ffmpeg -y -i video-voiced.mp4 -vframes 1 -q:v 2 video-voiced-poster.jpg
```

---

## Full workflow

```bash
# 1. Generate TTS clips (2s between calls)
cd public/videos/audio
for line in "Line 1" "Line 2" "Line 3"; do
  curl -s -X POST https://api.free.ai/v1/tts/ \
    -H "Content-Type: application/json" \
    -d "{\"text\":\"$line\",\"voice\":\"am_michael\"}" > response.json
  url=$(python3 -c "import json; print(json.load(open('response.json'))['audio_url'])")
  curl -s -o clip.wav "$url"
  sleep 2
done

# 2. Apply consistent speed
ffmpeg -y -i clip.wav -af "atempo=1.425" -ar 44100 -ac 1 clip-final.mp3

# 3. Combine with delays (calculate from clip durations)
ffmpeg -y -i clip1-final.mp3 -i clip2-final.mp3 \
  -filter_complex "[0]adelay=0|0[a];[1]adelay=3000|3000[b];[a][b]amix=inputs=2:duration=longest" \
  -t 15 -ar 44100 -ac 2 narration.mp3

# 4. Mix with music
ffmpeg -y -i narration.mp3 -i music-ambient.mp3 \
  -filter_complex "[0]volume=1.0[n];[1]volume=0.2[m];[n][m]amix=inputs=2" \
  -t 15 -ar 44100 -ac 2 final-audio.mp3

# 5. Render base video
cd /path/to/repo
node scripts/render-video.js b landscape 30

# 6. Merge audio
ffmpeg -y -i public/videos/spielos-before-after-16x9.mp4 \
  -i public/videos/audio/final-audio.mp3 \
  -c:v copy -c:a aac -b:a 128k -shortest \
  public/videos/spielos-before-after-16x9-voiced.mp4

# 7. Generate poster
ffmpeg -y -i public/videos/spielos-before-after-16x9-voiced.mp4 \
  -vframes 1 -q:v 2 \
  public/videos/spielos-before-after-16x9-voiced-poster.jpg

# 8. Clean up intermediates
rm -f public/videos/spielos-before-after-16x9.mp4
```

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

  // Scene activation
  if (t < 2.34) { act('s1'); /* reveal elements */ }
  if (t >= 2.34 && t < 6.49) { act('s2'); /* reveal elements */ }
  // ... etc

  requestAnimationFrame(tick);
}
tick();
```

---

## Boxicons in headless Chrome

Boxicons require TWO things to render in Puppeteer:

1. **CSS link** in `<head>`:
```html
<link rel="stylesheet" href="/node_modules/boxicons/css/boxicons.min.css">
```

2. **Local font-face** override:
```css
@font-face {
  font-family: "boxicons";
  font-weight: 400;
  font-style: normal;
  font-display: swap;
  src: url("/public/assets/fonts/boxicons.woff2") format("woff2");
}
```

Without both, icons render as empty squares.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Icons empty squares | Add boxicons CSS link + local @font-face |
| Audio too fast/slow | Check atempo value, should be same for all clips in scenario |
| Scene bleed (old text visible) | Remove CSS `transition` from `.scene` opacity |
| TTS API timeout | Increase `--max-time` to 60, retry |
| TTS API rate limit | Add 2s sleep between requests |
| Frames directory error | Run renders sequentially, not parallel (shared frame dir) |
| atempo out of range | Chain: `atempo=2.0,atempo=1.5` for >2x speed |

---

## Output rules

After creating a video, report:

- Template file path
- Output file path
- Aspect ratios rendered
- Voice used
- Speed factor
- Duration and FPS
- Total frames
- File size
- Any rendering issues
