#!/usr/bin/env node
/**
 * render-video.js — Renders an animation to MP4 via Puppeteer + FFmpeg.
 *
 * Usage:
 *   node scripts/render-video.js <scenario> [aspect] [fps] [output]
 *
 * Scenarios:
 *   b  — Before/After (pain → promise → pillars → director → CTA)
 *   c  — Build It (hook → 4 steps → live → director → pillars → CTA)
 *
 * Aspects:
 *   landscape (16:9)  — 1920x1080
 *   portrait  (9:16)  — 1080x1920
 *   square    (1:1)   — 1080x1080
 *   story     (4:5)   — 1080x1350
 *
 * Examples:
 *   node scripts/render-video.js b landscape
 *   node scripts/render-video.js c portrait 24
 */

import puppeteer from "puppeteer";
import { execSync } from "child_process";
import { mkdirSync, rmSync, existsSync, readFileSync, statSync } from "fs";
import { join, resolve } from "path";
import { fileURLToPath } from "url";
import { createServer } from "http";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const ROOT = resolve(__dirname, "..");
const TEMPLATE_ROOT = join(ROOT, ".agents/company/departments/design/templates/video");
const CAMPAIGN_MANIFEST = process.env.CAMPAIGN_MANIFEST
  ? resolve(process.env.CAMPAIGN_MANIFEST) : null;
const CAMPAIGN_ITEM_ID = process.env.CAMPAIGN_ITEM_ID || "";

/* ── Aspect ratios ── */
const ASPECTS = {
  landscape: { width: 1920, height: 1080, label: "16x9" },
  portrait: { width: 1080, height: 1920, label: "9x16" },
  square: { width: 1080, height: 1080, label: "1x1" },
  story: { width: 1080, height: 1350, label: "4x5" },
};

/* ── Scenarios ── */
const SCENARIOS = {
  b: { file: "scenario-b.html", name: "before-after" },
  c: { file: "scenario-c.html", name: "build-it" },
};

/* ── CLI args ── */
const checkOnly = process.argv[2] === "--check";
const scenarioKey = checkOnly ? "b" : (process.argv[2] || "b");
const aspectKey = process.argv[3] || "landscape";
const fps = parseInt(process.argv[4] || "30", 10);
const customOutput = process.argv[5];

if (!SCENARIOS[scenarioKey]) {
  console.error(`Unknown scenario: ${scenarioKey}. Use: ${Object.keys(SCENARIOS).join(", ")}`);
  process.exit(1);
}
if (!ASPECTS[aspectKey]) {
  console.error(`Unknown aspect: ${aspectKey}. Use: ${Object.keys(ASPECTS).join(", ")}`);
  process.exit(1);
}

const { width, height, label } = ASPECTS[aspectKey];
const { file: scenarioFile, name: scenarioName } = SCENARIOS[scenarioKey];
const NARRATION_PATH = join(TEMPLATE_ROOT, "narration.json");

function renderTiming() {
  if (CAMPAIGN_MANIFEST && CAMPAIGN_ITEM_ID) {
    const manifest = JSON.parse(readFileSync(CAMPAIGN_MANIFEST, "utf8"));
    const item = (manifest.items || []).find((entry) => entry.item_id === CAMPAIGN_ITEM_ID);
    const timing = item?.renditions?.youtube?.narration?.scene_timing;
    if (timing?.duration) return timing;
  }
  const narration = JSON.parse(readFileSync(NARRATION_PATH, "utf8"));
  return narration.scene_timing?.[scenarioKey];
}

const activeTiming = renderTiming();
const durationSec = Number(activeTiming?.duration || activeTiming?.scenes?.at(-1)?.end || 0);
if (!checkOnly && (!Number.isFinite(durationSec) || durationSec <= 0 || durationSec >= 60)) {
  console.error(`Invalid narration-led duration ${durationSec}; generate measured timing before rendering.`);
  process.exit(1);
}
const totalFrames = Math.ceil(fps * durationSec);

const animFile = join(TEMPLATE_ROOT, scenarioFile);
const outputFile = customOutput
  ? resolve(customOutput)
  : join(ROOT, `public/videos/spielos-${scenarioName}-${label}.mp4`);
const framesDir = join(resolve(outputFile, ".."), `.frames-${scenarioName}-${label}`);

/* ═══ Owner contract gate (--check) ═══
   Fails on: multi-voice narration, music spec remnants, missing Outfit font
   in-render, off-line stations, hardcoded windows, infinite ring pulses. */
const BRAND_MOTION = join(TEMPLATE_ROOT, "brand-motion.css");
const PRODUCTION_CSS = join(ROOT, ".agents/company/departments/design/system/production.css");

function checkNarrationContract(failures) {
  if (!existsSync(NARRATION_PATH)) { failures.push("narration.json missing"); return; }
  const narration = JSON.parse(readFileSync(NARRATION_PATH, "utf8"));
  const voice = narration.voice_selection;
  if (!voice) failures.push("narration.json: voice_selection empty — no pinned single voice");
  const mix = narration.mix || {};
  if (mix.music !== "none") failures.push(`narration.json: mix.music=${JSON.stringify(mix.music)} — voiced deliverables are narration-only`);
  const raw = JSON.stringify(narration);
  for (const bad of ["music_direction", "music_duck_db", "music-ambient", "voice_audition", "audition_voices", "voice_candidates"]) {
    if (raw.includes(bad)) failures.push(`narration.json: music/audition remnant "${bad}"`);
  }
  const voices = new Set();
  for (const s of ["b", "c"]) {
    const st = narration.scene_timing?.[s];
    if (!st?.generated_at) { failures.push(`narration.json: scenario ${s} has no measured scene_timing — run scripts/tts-gemini.js first (speech first, then scenes)`); continue; }
    if (!st.voice || st.voice !== voice) failures.push(`narration.json: scenario ${s} scene_timing.voice=${st.voice} ≠ voice_selection=${voice} (mixed generations)`);
    voices.add(st.voice);
    const scenes = st.scenes || [];
    if (scenes.length < 4) { failures.push(`narration.json: scenario ${s} has ${scenes.length} scenes`); continue; }
    const narrationLed = st.timing_contract === "narration-led-v2";
    let prev = -0.001;
    for (const sc of scenes) {
      const invalidBase = typeof sc.start !== "number" || typeof sc.end !== "number"
        || sc.start < prev || sc.end <= sc.start;
      const invalidNarrationLed = narrationLed && (typeof sc.speech_start !== "number"
        || typeof sc.speech_end !== "number" || sc.speech_start <= sc.start
        || sc.speech_end <= sc.speech_start || sc.end <= sc.speech_end);
      if (invalidBase || invalidNarrationLed) {
        failures.push(`narration.json: scenario ${s} scene ${sc.scene} window not measured/monotonic (${sc.start}→${sc.end})`);
        break;
      }
      const minimum = sc === scenes[scenes.length - 1] ? 4 : 3;
      if (narrationLed && sc.end - sc.start + 0.001 < minimum) {
        failures.push(`narration.json: scenario ${s} scene ${sc.scene} is shorter than the ${minimum}s readability minimum`);
        break;
      }
      prev = sc.start;
    }
    const last = scenes[scenes.length - 1];
    if (narrationLed && (!Number.isFinite(st.duration) || Math.abs(st.duration - last?.end) > 0.02 || st.duration >= 60)) {
      failures.push(`narration.json: scenario ${s} needs one narration-led duration under 60s matching its final scene`);
    }
  }
  if (voices.size > 1) failures.push(`narration.json: ${voices.size} different voices across scenarios (${[...voices].join(", ")}) — ONE voice required`);
}

function checkStaticFiles(failures) {
  const bm = existsSync(BRAND_MOTION) ? readFileSync(BRAND_MOTION, "utf8") : "";
  if (!bm) failures.push("brand-motion.css missing");
  else {
    if (!bm.includes("nodeHit")) failures.push("brand-motion.css: missing one-shot nodeHit flash");
    if (/station-ring[\s\S]{0,120}?animation[^;]*infinite/.test(bm)) failures.push("brand-motion.css: station ring animation is infinite (owner contract №4: fire ONCE)");
    if (bm.includes("music")) failures.push("brand-motion.css: music reference");
  }
  const pc = existsSync(PRODUCTION_CSS) ? readFileSync(PRODUCTION_CSS, "utf8") : "";
  if (!pc) failures.push("production.css missing");
  else {
    if (!pc.includes("src/styles/tokens/index.css")) failures.push("production.css: missing canonical tokens import");
    if (!pc.includes('url("/public/assets/fonts/outfit-latin.woff2")')) failures.push("production.css: Outfit must load from repo-root-resolvable paths (no system-font fallback)");
    if (!pc.includes('font-weight: 100 900')) failures.push("production.css: Outfit must be the variable 100-900 family (bold 800 titles)");
    if (pc.includes("music")) failures.push("production.css: music reference");
    /* No second display font: every @font-face family must be one of the
       website families (Outfit / JetBrains Mono / boxicons / IRANSansX). */
    const faceFamilies = [...pc.matchAll(/@font-face\s*\{[^}]*font-family\s*:\s*"([^"]+)"\s*;/g)].map((m) => m[1]);
    const ALLOWED_FACES = new Set(["Outfit", "JetBrains Mono", "boxicons", "IRANSansX"]);
    for (const fam of faceFamilies) {
      if (!ALLOWED_FACES.has(fam)) failures.push(`production.css: unexpected display font family "${fam}" (website families only)`);
    }
    if (faceFamilies.length && !faceFamilies.includes("Outfit")) failures.push("production.css: Outfit @font-face missing");
  }
  for (const file of ["scripts/mix-audio.js", "scripts/tts-gemini.js", "scripts/render-all.sh"]) {
    if (!existsSync(join(ROOT, file))) { failures.push(`${file} missing`); continue; }
    const s = readFileSync(join(ROOT, file), "utf8");
    for (const bad of ["music-ambient", "music_direction", "music_duck_db", "am_michael", "atempo=", "Puck"]) {
      if (s.includes(bad)) failures.push(`${file}: stale "${bad}" reference`);
    }
  }
  for (const [key, scenario] of Object.entries(SCENARIOS)) {
    const path = join(TEMPLATE_ROOT, scenario.file);
    if (!existsSync(path)) { failures.push(`${key}: missing ${path}`); continue; }
    const source = readFileSync(path, "utf8");
    for (const required of ["window.__setFrame", "boxicons.min.css", "journey-fill", "goal-ring", "favicons/favicon.svg", "campaign-support", "<html", "</html>", "getPointAtLength", "narration.json"]) {
      if (!source.includes(required)) failures.push(`${key}: template missing ${required}`);
    }
    if (!source.includes("__applyCampaignRendition")) failures.push(`${key}: template lacks the shared campaign rendition handoff`);
    for (const stale of ["Employees using AI separately", "Repeated prompts, copied context", "One assistant doing everything", "Hire a role", "AI directs", "Build your own AI department"]) {
      if (source.includes(stale)) failures.push(`${key}: template retains legacy fixed scene copy: ${stale}`);
    }
    for (const required of ["visual.headline", "visual.supporting_text", "visual.component", "visual.icon", "visual.labels", "Displayed headline must equal spoken text"]) {
      if (!source.includes(required)) failures.push(`${key}: campaign scene control missing ${required}`);
    }
    if (source.includes("batch-01.json")) failures.push(`${key}: template is coupled to a hardcoded campaign batch`);
    for (const bad of ["ringPulse", "music-ambient", "music_direction", "music_duck_db", "am_michael", "atempo=", "stationTimes", "0-3.5s", "0-2.34s"]) {
      if (source.includes(bad)) failures.push(`${key}: template contains stale "${bad}"`);
    }
  }
}

function campaignVideoOrder(manifestPath, itemId) {
  if (!manifestPath || !itemId) return null;
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const item = (manifest.items || []).find((entry) => entry.item_id === itemId);
  if (!item) throw new Error(`Campaign item not found: ${itemId}`);
  const rendition = item.renditions?.youtube;
  if (!rendition?.design || !rendition?.narration) throw new Error(`YouTube Design/narration order missing for ${itemId}`);
  if (rendition.narration.scene_control_version !== "1.0") throw new Error(`YouTube scene control contract missing for ${itemId}`);
  for (const scene of rendition.narration.scenes || []) {
    const spoken = String(scene.text || "").trim().toLowerCase();
    const displayed = String(scene.visual?.headline || "").trim().toLowerCase();
    const urlAligned = scene.visual?.spoken_display_alignment === "url-pronunciation" &&
      scene.visual?.component === "cta" && displayed === "spielos.xyz/services" &&
      spoken === "go to spielos dot xyz slash services.";
    if ((!displayed || displayed !== spoken) && !urlAligned) {
      throw new Error(`Spoken/displayed scene mismatch for ${itemId}/${scene.id}`);
    }
  }
  return { campaign_id: manifest.campaign_id, batch_id: manifest.batch_id, item_id: item.item_id,
    content_id: rendition.content_id, design: rendition.design, narration: rendition.narration };
}

function checkVideoOrder(key) {
  const narration = JSON.parse(readFileSync(NARRATION_PATH, "utf8"));
  const ids = key === "b" ? ["hook", "pain", "promise", "pillars", "director", "cta"] : ["hook", "build", "live", "director", "cta"];
  const texts = key === "b"
    ? ["Context first.", "The work is visible.", "SpielOS connects it.", "Goal. Department. Workflow.", "Evidence stays visible.", "SpielOS dot xyz slash services."]
    : ["Context first.", "The decision is visible.", "SpielOS records the rule.", "Evidence decides next.", "SpielOS dot xyz slash services."];
  return { campaign_id: "contract-check", batch_id: "contract-check-batch", item_id: "contract-check-item",
    content_id: "contract-check-item-youtube", design: {
      template_id: `scenario-${key}`, theme: "gruvbox-dark", surface: "background", color_role: "primary",
      alignment: "center", layout: "journey", size_preset: "youtube-shorts",
      eyebrow: "SpielOS campaign contract", title_lines: ["Context first.", "One clear workflow."],
      supporting_text: "One campaign identity survives every handoff.",
    }, narration: { scene_control_version: "1.0", scenes: texts.map((text, index) => ({ id: ids[index], text, visual: {
      eyebrow: index === 0 ? "SpielOS campaign" : "Current system",
      headline: text, supporting_text: "One controlled scene from one campaign Artifact.",
      component: index === texts.length - 1 ? "cta" : "statement", icon: index === texts.length - 1 ? "bx-link" : "bx-task",
      labels: index === texts.length - 1 ? ["Services"] : ["Goal", "Department", "Workflow"],
    } })),
      scene_timing: narration.scene_timing[key] } };
}

async function applyCampaignOrder(page, order) {
  await page.waitForFunction(() => typeof window.__applyCampaignRendition === "function", { timeout: 8000 });
  await page.evaluate((value) => window.__applyCampaignRendition(value), order);
  await page.waitForFunction(() => document.documentElement.dataset.templateReady === "true", { timeout: 8000 });
}

/* Clip provenance (owner contract №1): the per-generation voice manifest in
   public/videos/audio must exist, must record the pinned master voice, and
   must cover EVERY scene clip of BOTH scenarios — a missing or mismatched
   manifest means clips from another generation could be mixed in. Also fail
   if any stale music file lingers in the narration audio dir. */
const SCENE_ORDER = { b: ["hook", "pain", "promise", "pillars", "director", "cta"], c: ["hook", "build", "live", "director", "cta"] };
const AUDIO_DIR = join(ROOT, "public/videos/audio");
const MANIFEST_PATH = join(AUDIO_DIR, ".voice-manifest.json");

function checkClipProvenance(failures) {
  if (!existsSync(MANIFEST_PATH)) {
    failures.push("public/videos/audio/.voice-manifest.json missing — no clip generation recorded with the pinned voice");
    return;
  }
  const narration = JSON.parse(readFileSync(NARRATION_PATH, "utf8"));
  const voice = narration.voice_selection;
  let manifest;
  try { manifest = JSON.parse(readFileSync(MANIFEST_PATH, "utf8")); }
  catch { failures.push("public/videos/audio/.voice-manifest.json unparseable"); return; }
  if (!manifest.voice || manifest.voice !== voice) {
    failures.push(`voice manifest voice ${JSON.stringify(manifest.voice)} ≠ voice_selection ${voice} — clips from different generations must not mix`);
  }
  for (const s of ["b", "c"]) {
    const clips = manifest.scenarios?.[s]?.clips || {};
    for (const scene of SCENE_ORDER[s]) {
      if (!(scene in clips) || typeof clips[scene] !== "number" || clips[scene] <= 0) {
        failures.push(`voice manifest missing/zero clip ${s}-${scene} — regenerate scenario ${s} with the pinned voice`);
      }
    }
  }
  const musicFile = join(AUDIO_DIR, "music-ambient.mp3");
  if (existsSync(musicFile)) failures.push("stale music-ambient.mp3 still present in public/videos/audio — narration-only pipeline must contain no music file");
}

/* In-render gate per scenario: Outfit 800 must load, the measured schedule
   must be applied, and every station must sit ON the journey line (within
   2.5px of path.getPointAtLength at its scene-start fraction). */
async function videoRenderGate(baseUrl, browser, scenarioKey) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  const templateUrl = `${baseUrl}/.agents/company/departments/design/templates/video/${SCENARIOS[scenarioKey].file}`;
  await page.goto(templateUrl, { waitUntil: "networkidle0", timeout: 30000 });
  await applyCampaignOrder(page, checkVideoOrder(scenarioKey));
  await page.evaluate(() => document.fonts.ready);
  try {
    await page.waitForFunction(
      (key) => {
        const tm = window.__timing;
        const st1 = document.getElementById("st1");
        return tm && st1 && /translate\(/.test(st1.getAttribute("transform") || "");
      },
      { timeout: 8000 },
      scenarioKey
    );
  } catch {
    return [`${scenarioKey}: measured scene_timing never applied in-render (no hardcoded windows allowed)`];
  }
  const errs = await page.evaluate((key) => {
    const out = [];
    if (!document.fonts.check("800 16px Outfit")) out.push("Outfit 800 NOT loaded in render (system-font fallback)");
    const title = document.querySelector(".campaign-headline, .hook-main");
    if (title) {
      const cs = getComputedStyle(title);
      if (!cs.fontFamily.includes("Outfit")) out.push(`title font-family ${cs.fontFamily} (expected Outfit)`);
      if (cs.fontWeight !== "800") out.push(`title font-weight ${cs.fontWeight} (expected 800)`);
      if (cs.textAlign !== "center") out.push(`title text-align ${cs.textAlign} (expected center)`);
    } else out.push("missing .hook-main title");
    const tm = window.__timing;
    const sc = tm.scenes;
    const lineEnd = sc[sc.length - 1].end;
    const pathFill = document.getElementById("journey-fill");
    const len = pathFill.getTotalLength();
    const defs = { b: [
      { land: "st1", scene: 1 }, { land: "st2", scene: 2 }, { land: "st3", scene: 3 },
      { land: "st4", scene: 4 }, { land: "st5", scene: 5 },
    ], c: [
      { land: "st1", scene: 1 }, { land: "st2", scene: 2 }, { land: "st3", scene: 3 }, { land: "st4", scene: 4 },
    ] }[key];
    for (const sd of defs) {
      const el = document.getElementById(sd.land);
      const frac = Math.min(sc[sd.scene].start / lineEnd, 1);
      const pt = pathFill.getPointAtLength(frac * len);
      const t = (el.getAttribute("transform") || "").match(/translate\(([-\d.]+),([-\d.]+)\)/);
      if (!t) { out.push(`${sd.land}: station has no transform`); continue; }
      const d = Math.hypot(parseFloat(t[1]) - pt.x, parseFloat(t[2]) - pt.y);
      if (d > 2.5) out.push(`${sd.land}: OFF the journey line by ${d.toFixed(1)}px`);
    }
    /* Goal bullseye must sit at the line's end point. */
    const goal = document.getElementById(key === "b" ? "st6" : "journey-goal");
    const g = (goal.getAttribute("transform") || "").match(/translate\(([-\d.]+),([-\d.]+)\)/);
    if (g) {
      const endPt = pathFill.getPointAtLength(len);
      const gd = Math.hypot(parseFloat(g[1]) - endPt.x, parseFloat(g[2]) - endPt.y);
      if (gd > 2.5) out.push(`goal OFF the line end by ${gd.toFixed(1)}px`);
    }
    return out;
  }, scenarioKey);
  await page.close();
  return errs;
}

async function runChecks() {
  const failures = [];
  checkNarrationContract(failures);
  checkStaticFiles(failures);
  checkClipProvenance(failures);
  if (failures.length) { console.error(failures.join("\n")); process.exit(1); }
  console.log("Static video contract OK: ONE voice + narration-led readable timing + narration-only + one-shot node pulses");

  const { server, url: baseUrl } = await startServer();
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: "shell",
      executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      args: ["--no-sandbox", "--disable-dev-shm-usage", "--font-render-hinting=none", "--allow-file-access-from-files"],
    });
    for (const key of Object.keys(SCENARIOS)) {
      const errs = await videoRenderGate(baseUrl, browser, key);
      if (errs.length) {
        console.error(`In-render gate failures (${key}):\n` + errs.join("\n"));
        process.exit(1);
      }
      console.log(`In-render gate OK (${key}): Outfit 800 centered title, measured timing applied, stations ON the journey line`);
    }
  } finally {
    if (browser) await browser.close();
    server.close();
  }
  process.exit(0);
}

/* ── Verify FFmpeg ── */
try {
  execSync("ffmpeg -version", { stdio: "ignore" });
} catch {
  console.error("FFmpeg not found. Install: brew install ffmpeg");
  process.exit(1);
}

if (!existsSync(animFile)) {
  console.error(`Animation file not found: ${animFile}`);
  process.exit(1);
}

console.log(`\n  Rendering ${scenarioName} @ ${width}x${height} ${fps}fps (${durationSec}s)`);
console.log(`  Total frames: ${totalFrames}`);
console.log(`  Output: ${outputFile}\n`);

if (existsSync(framesDir)) {
  rmSync(framesDir, { recursive: true });
}
mkdirSync(framesDir, { recursive: true });

/* ── MIME types ── */
const MIME = {
  ".html": "text/html",
  ".css": "text/css",
  ".js": "application/javascript",
  ".json": "application/json",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".ttf": "font/ttf",
};

/* ── Simple static file server ── */
function startServer() {
  return new Promise((resolve) => {
    const server = createServer((req, res) => {
      let filePath = join(ROOT, decodeURIComponent(req.url.split("?")[0]));
      if (filePath.endsWith("/")) filePath = join(filePath, "index.html");

      const ext = "." + filePath.split(".").pop().toLowerCase();
      const mime = MIME[ext] || "application/octet-stream";

      try {
        const data = readFileSync(filePath);
        res.writeHead(200, {
          "Content-Type": mime,
          "Access-Control-Allow-Origin": "*",
          "Cache-Control": "no-cache",
        });
        res.end(data);
      } catch {
        res.writeHead(404);
        res.end("Not found");
      }
    });

    server.listen(0, "127.0.0.1", () => {
      const port = server.address().port;
      resolve({ server, port, url: `http://127.0.0.1:${port}` });
    });
  });
}

/* ── Render ── */
async function render() {
  const { server, url: baseUrl } = await startServer();
  console.log(`  Local server: ${baseUrl}`);

  const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser = await puppeteer.launch({
    headless: "shell",
    executablePath: CHROME_PATH,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--font-render-hinting=none",
      "--allow-file-access-from-files",
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width, height, deviceScaleFactor: 1 });

  const templateUrl = `${baseUrl}/.agents/company/departments/design/templates/video/${scenarioFile}`;
  console.log(`  Loading: ${templateUrl}`);
  await page.goto(templateUrl, { waitUntil: "networkidle0", timeout: 30000 });
  const order = campaignVideoOrder(CAMPAIGN_MANIFEST, CAMPAIGN_ITEM_ID);
  if (!order && process.env.LEGACY_VIDEO_RENDER !== "1") {
    throw new Error("Set CAMPAIGN_MANIFEST and CAMPAIGN_ITEM_ID; campaign video renders cannot use template-owned copy");
  }
  if (order) await applyCampaignOrder(page, order);
  await page.evaluate(() => document.fonts.ready);
  await new Promise((r) => setTimeout(r, 800));

  console.log("  Capturing frames...");

  for (let frame = 0; frame < totalFrames; frame++) {
    await page.evaluate(
      (f, fps) => { window.__setFrame(f, fps); },
      frame,
      fps
    );
    await new Promise((r) => setTimeout(r, 16));
    await new Promise((r) => setTimeout(r, 16));

    const frameNum = String(frame).padStart(5, "0");
    await page.screenshot({
      path: join(framesDir, `frame_${frameNum}.png`),
      type: "png",
    });

    if ((frame + 1) % fps === 0 || frame === totalFrames - 1) {
      const sec = ((frame + 1) / fps).toFixed(1);
      const pct = Math.round(((frame + 1) / totalFrames) * 100);
      process.stdout.write(`\r  Frame ${frame + 1}/${totalFrames} (${sec}s) — ${pct}%`);
    }
  }

  console.log("\n");
  await browser.close();
  server.close();

  /* ── Encode ── */
  console.log("  Encoding MP4...");

  const outputDir = resolve(outputFile, "..");
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  const ffmpegCmd = [
    "ffmpeg", "-y",
    "-framerate", String(fps),
    "-i", join(framesDir, "frame_%05d.png"),
    "-c:v", "libx264",
    "-preset", "slow",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    outputFile,
  ].join(" ");

  try {
    execSync(ffmpegCmd, { stdio: "pipe" });
  } catch (err) {
    console.error("FFmpeg encoding failed:");
    console.error(err.stderr?.toString());
    process.exit(1);
  }

  /* ── Cleanup ── */
  console.log("  Cleaning up frames...");
  rmSync(framesDir, { recursive: true });

  const sizeBytes = statSync(outputFile).size;
  const sizeMB = (sizeBytes / 1024 / 1024).toFixed(1);
  console.log(`\n  Done! ${outputFile} (${sizeMB} MB)\n`);
}

/* Dispatch last: every module-scope const (NARRATION_PATH, MANIFEST_PATH, …)
   must be initialized before runChecks()/render() are invoked, or --check dies
   on a temporal dead zone ReferenceError. */
if (checkOnly) {
  runChecks().catch((err) => { console.error(err); process.exit(1); });
} else {
  render().catch((err) => { console.error("Render failed:", err); process.exit(1); });
}
