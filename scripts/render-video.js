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
const durationSec = 15;
const totalFrames = fps * durationSec;

const animFile = join(TEMPLATE_ROOT, scenarioFile);
const framesDir = join(ROOT, `public/videos/frames-${label}`);
const outputFile = customOutput
  ? resolve(customOutput)
  : join(ROOT, `public/videos/spielos-${scenarioName}-${label}.mp4`);

if (checkOnly) {
  const failures = [];
  for (const [key, scenario] of Object.entries(SCENARIOS)) {
    const path = join(TEMPLATE_ROOT, scenario.file);
    if (!existsSync(path)) {
      failures.push(`${key}: missing ${path}`);
      continue;
    }
    const source = readFileSync(path, "utf8");
    for (const required of ["window.__setFrame", "boxicons.min.css", "<html", "</html>"]) {
      if (!source.includes(required)) failures.push(`${key}: template missing ${required}`);
    }
  }
  if (failures.length) {
    console.error(failures.join("\n"));
    process.exit(1);
  }
  console.log(`Video templates OK: ${Object.keys(SCENARIOS).join(", ")}`);
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

render().catch((err) => {
  console.error("Render failed:", err);
  process.exit(1);
});
