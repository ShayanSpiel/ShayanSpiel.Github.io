#!/usr/bin/env node
/**
 * tts-gemini.js — Generates scene narration clips with Gemini 2.5 Flash TTS.
 *
 * Owner contract (2026-08-11 review):
 *  - ONE narration voice: MASTER_VOICE is pinned here AND in narration.json
 *    `voice_selection`. There is no per-call voice argument, no auditioning,
 *    no mixed generations. Every clip for every scenario uses the same
 *    voiceName.
 *  - Full sentences: scene timing is derived from the MEASURED spoken clip
 *    durations (speech first, then scenes). Clips are only silent-edge
 *    trimmed — never atempo-fitted and never trimmed mid-sentence. The
 *    script FAILS if the measured schedule overruns 14.9s so narration text
 *    is tightened instead of speech being cut.
 *  - Stale-proofing: before generating a scenario, the previous clips for
 *    that scenario are deleted, and a per-generation manifest
 *    (public/videos/audio/.voice-manifest.json) records the voice + measured
 *    durations. scripts/mix-audio.js refuses to mix clips whose manifest
 *    voice differs from the pinned master voice.
 *
 * Usage:
 *   node scripts/tts-gemini.js <b|c>
 *
 * Writes clips to public/videos/audio/<scenario>-<scene>.wav (44.1kHz mono)
 * and saves the measured scene schedule into narration.json under
 * `scene_timing`, which scripts/mix-audio.js and the templates consume.
 */

import { readFileSync, writeFileSync, existsSync, readdirSync, rmSync } from "fs";
import { execSync } from "child_process";
import { join, resolve } from "path";
import { fileURLToPath } from "url";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const AUDIO = join(ROOT, "public/videos/audio");
const MANIFEST = join(AUDIO, ".voice-manifest.json");
const NARRATION = join(ROOT, ".agents/company/departments/design/templates/video/narration.json");
const config = JSON.parse(readFileSync(NARRATION, "utf8"));

/* ── The single pinned master voice (owner contract №1). ──
   Charon is a natural low-register male prebuilt Gemini voice. It must match
   narration.json `voice_selection`; a mismatch is a hard failure. */
const MASTER_VOICE = config.voice_selection || "Charon";

const scenario = process.argv[2];
if (process.argv[3]) {
  console.error("Voice override is not allowed: EVERY clip must use the pinned master voice.");
  process.exit(1);
}
if (!config.scenarios[scenario]) {
  console.error(`Unknown scenario: ${scenario}. Use b or c.`);
  process.exit(1);
}

const env = existsSync(join(ROOT, ".spielos/.env")) ? readFileSync(join(ROOT, ".spielos/.env"), "utf8") : "";
const key = process.env.GEMINI_API_KEY || env.match(/^GEMINI_API_KEY=(.+)$/m)?.[1]?.trim();
if (!key) { console.error("GEMINI_API_KEY not found in .spielos/.env (or set the GEMINI_API_KEY env var)"); process.exit(1); }

/* Per-scene text-length guidance (not an enforced window): lines are written
   so the natural take lands within ~15s across the scenario. The measured
   schedule below decides; overrun is a hard failure that requires tightening
   the TEXT, never cutting or speeding speech. */
const GAP = 0.2;          /* breath between scenes */
const TARGET_END = 14.9;   /* hard stop; nothing may exceed */

const PRONUNCIATION = [
  [/spielos\.xyz\/services/gi, "spielos dot xyz slash services"],
  [/spielos dot xyz slash services/gi, "spielos dot xyz slash services"],
  [/spielos\.xyz/gi, "spielos dot xyz"],
  [/SpielOS/g, "SpielOS (pronounced shpeel-oh-es)"],
];

const PERFORMANCE = config.voice_direction +
  " Deliver the take like a calm founder talking to a friend: warm, grounded," +
  " flowing. Keep lists moving without long pauses. No robotic spacing, no" +
  " dead air, no rushed endings — finish every word, and complete the final" +
  " line fully.";

function pipe(text) {
  let out = text;
  for (const [bad, good] of PRONUNCIATION) out = out.replace(bad, good);
  return out;
}

function dur(file) {
  return parseFloat(execSync(`ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 ${file}`).toString().trim());
}

async function synth(line, idx) {
  const prompt = `${PERFORMANCE}\nNarrate: "${pipe(line)}"`;
  for (let attempt = 1; attempt <= 6; attempt++) {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key=${key}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: {
            responseModalities: ["AUDIO"],
            speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: MASTER_VOICE } } },
          },
        }),
      }
    );
    if (res.status === 429) {
      const wait = 60 + attempt * 20;
      console.log(`    quota hit — waiting ${wait}s (attempt ${attempt}/6)`);
      await new Promise((r) => setTimeout(r, wait * 1000));
      continue;
    }
    if (!res.ok) { console.error(`TTS API error ${res.status}: ${(await res.text()).slice(0, 300)}`); process.exit(1); }
    const data = await res.json();
    const part = data.candidates?.[0]?.content?.parts?.find((p) => p.inlineData);
    if (!part?.inlineData?.data) { console.error("No audio in Gemini response"); process.exit(1); }
    const mime = part.inlineData.mimeType || "audio/wav";
    const raw = join(AUDIO, `.tmp-${scenario}-${idx}.raw`);
    writeFileSync(raw, Buffer.from(part.inlineData.data, "base64"));
    const wav = join(AUDIO, `.tmp-${scenario}-${idx}.wav`);
    if (mime.includes("L16") || mime.includes("pcm")) {
      const rate = Number(mime.match(/rate=(\d+)/)?.[1] || "24000");
      execSync(`ffmpeg -y -v error -f s16le -ar ${rate} -ac 1 -i ${raw} -ar 44100 -ac 1 -c:a pcm_s16le ${wav}`);
    } else {
      execSync(`ffmpeg -y -v error -i ${raw} -ar 44100 -ac 1 -c:a pcm_s16le ${wav}`);
    }
    rmSync(raw, { force: true });
    return wav;
  }
  console.error("TTS quota exhausted after retries — keep waiting and re-run; never switch voice.");
  process.exit(1);
}

function trimEdges(file) {
  const out = `${file}.t.wav`;
  execSync(`ffmpeg -y -v error -i ${file} -af "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse" -ar 44100 -ac 1 -c:a pcm_s16le ${out}`);
  return out;
}

/* Structural scene order per scenario (matches the templates' scene ids). */
const SCENE_ORDER = {
  b: ["hook", "pain", "promise", "pillars", "director", "cta"],
  c: ["hook", "build", "live", "director", "cta"],
};

async function main() {
  const lines = config.scenarios[scenario];
  const scenes = SCENE_ORDER[scenario];
  console.log(`\n  Generating ${lines.length} Gemini clips (${MASTER_VOICE}) for scenario ${scenario}`);
  console.log(`  Pinned single voice — no overrides, no mixing, no atempo (edge-trim only)\n`);

  /* Stale-proof: remove every previous clip for this scenario so the mix can
     never reuse an old voice or an old generation. */
  for (const f of readdirSync(AUDIO)) {
    if (f.startsWith(`${scenario}-`) && f.endsWith(".wav")) {
      rmSync(join(AUDIO, f), { force: true });
      console.log(`  purged stale clip ${f}`);
    }
  }

  const fitted = [];
  for (let i = 0; i < lines.length; i++) {
    const scene = scenes[i];
    const raw = await synth(lines[i], i);
    const trimmed = trimEdges(raw);
    rmSync(raw, { force: true });
    const final = join(AUDIO, `${scenario}-${scene}.wav`);
    execSync(`ffmpeg -y -v error -i ${trimmed} -ar 44100 -ac 1 -c:a pcm_s16le ${final}`);
    rmSync(trimmed, { force: true });
    const d = dur(final);
    console.log(`  ${scene.padEnd(9)} ${d.toFixed(2)}s (measured, full take)`);
    fitted.push({ scene, duration: d });
    await new Promise((r) => setTimeout(r, 30000));
  }

  /* Schedule: measured durations + breath gaps, must end by TARGET_END. */
  let t = 0.0;
  const timing = [];
  for (const f of fitted) {
    const start = t;
    const end = start + f.duration + 0.05; /* tiny settle after speech */
    timing.push({ scene: f.scene, start: +start.toFixed(2), end: +Math.min(end, TARGET_END).toFixed(2) });
    t = end + GAP;
  }
  const totalEnd = t - GAP;
  console.log(`\n  Schedule (from measured spoken durations):`);
  for (const s of timing) console.log(`    ${s.scene.padEnd(9)} ${s.start.toFixed(2)}s → ${s.end.toFixed(2)}s`);
  console.log(`  Last speech ends: ${totalEnd.toFixed(2)}s / ${TARGET_END}s`);

  if (totalEnd > TARGET_END) {
    console.error(`  OVERRUN ${(totalEnd - TARGET_END).toFixed(2)}s — tighten the narration TEXT in narration.json and regenerate; never cut or speed speech.`);
    process.exit(1);
  }

  /* Persist the schedule + voice provenance for the mix pipeline and templates. */
  config.scene_timing = config.scene_timing || {};
  config.scene_timing[scenario] = { voice: MASTER_VOICE, generated_at: new Date().toISOString(), scenes: timing };
  writeFileSync(NARRATION, JSON.stringify(config, null, 2) + "\n");

  /* Persist the manifest for mix-audio.js stale-proofing. */
  let manifest = {};
  if (existsSync(MANIFEST)) {
    try { manifest = JSON.parse(readFileSync(MANIFEST, "utf8")); } catch { manifest = {}; }
    if (manifest.voice && manifest.voice !== MASTER_VOICE) {
      console.error(`  Stale manifest voice ${manifest.voice} — refusing to mix generations. Regenerate everything with ${MASTER_VOICE}.`);
      process.exit(1);
    }
  }
  manifest = {
    voice: MASTER_VOICE,
    voice_selection: config.voice_selection,
    updated_at: new Date().toISOString(),
    scenarios: { ...(manifest.scenarios || {}), [scenario]: { generated_at: new Date().toISOString(), clips: Object.fromEntries(fitted.map((f) => [f.scene, +f.duration.toFixed(3)])) } },
  };
  writeFileSync(MANIFEST, JSON.stringify(manifest, null, 2) + "\n");
  console.log(`  Saved scene_timing + voice manifest (${MASTER_VOICE}) → narration.json + .voice-manifest.json\n`);
}

main().catch((e) => { console.error(e); process.exit(1); });