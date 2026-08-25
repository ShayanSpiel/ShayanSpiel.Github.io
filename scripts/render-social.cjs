const puppeteer = require("puppeteer");
const { createServer } = require("http");
const { readFileSync, mkdirSync, existsSync } = require("fs");
const { join } = require("path");

const ROOT = "/Users/shayan/ShayanSpiel.Github.io";
const OUT_DIR = join(ROOT, ".spielos/artifacts/template-preview-20260817/social");

const TEMPLATES = [
  { file: "single-fact.html", out: "single-fact.png", w: 1080, h: 1350 },
  { file: "department-map.html", out: "department-map.png", w: 1080, h: 1350 },
  { file: "agent-brief.html", out: "agent-brief.png", w: 1080, h: 1350 },
  { file: "list-checklist.html", out: "list-checklist.png", w: 1080, h: 1350 },
  { file: "testimonial-pull-quote.html", out: "testimonial-pull-quote.png", w: 1080, h: 1350 },
  {
    file: "heartbeat.html", out: "heartbeat.png", w: 1920, h: 1080, video: true, dir: "video",
    // The template intentionally stays dark until narration.json has
    // scene_timing.i (a measured schedule). For static previews we inject a
    // deterministic preview schedule so the template's own tick() drives the
    // state: scene 2 active (headline + full card: north star, run row,
    // 2x2 stats), journey traveled to the last station, bullseye ahead.
    previewTiming: { voice: {}, scenes: [
      { start: 0, end: 4 }, { start: 4, end: 8 }, { start: 8, end: 12 }, { start: 12, end: 14 }
    ] },
    previewT: 10,
  },
];

const RENDITION = {
  theme: "gruvbox-dark",
  layout: "landscape",
  eyebrow: "SpielOS",
  title_lines: ["AI cannot fix", "a messy process"],
  accent_line: 1,
  supporting_text: "We map one process, build the system, and show you where the time goes.",
  station_labels: ["Goal", "Inputs", "Outputs", "Interface", "Memory", "Rules", "Success"],
  milestone_labels: ["Mapped workflow", "Build plan", "Connected tools", "Guardrails", "Live URL"],
};

const MIME = { ".html": "text/html", ".css": "text/css", ".js": "application/javascript",
  ".json": "application/json", ".woff2": "font/woff2", ".png": "image/png", ".svg": "image/svg+xml" };

function startServer() {
  return new Promise((res) => {
    const server = createServer((req, rsp) => {
      let fp = join(ROOT, decodeURIComponent(req.url.split("?")[0]));
      if (fp.endsWith("/")) fp = join(fp, "index.html");
      if (!existsSync(fp)) { rsp.writeHead(404); rsp.end(); return; }
      const ext = fp.split(".").pop().toLowerCase();
      rsp.writeHead(200, { "Content-Type": MIME["." + ext] || "application/octet-stream" });
      rsp.end(readFileSync(fp));
    });
    server.listen(0, () => res(server));
  });
}

async function main() {
  mkdirSync(OUT_DIR, { recursive: true });
  const server = await startServer();
  const port = server.address().port;
  const base = `http://localhost:${port}`;

  const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox"],
    executablePath: existsSync(CHROME_PATH) ? CHROME_PATH : undefined,
  });

  for (const tmpl of TEMPLATES) {
    const page = await browser.newPage();
    await page.setViewport({ width: tmpl.w, height: tmpl.h, deviceScaleFactor: 1 });
    const subdir = tmpl.dir || "social";
    const url = `${base}/.agents/company/departments/design/templates/${subdir}/${tmpl.file}`;
    console.log(`Rendering ${tmpl.file} → ${tmpl.out} (${tmpl.w}x${tmpl.h}) from ${subdir}/`);
    await page.goto(url, { waitUntil: "networkidle0", timeout: 15000 });

    if (tmpl.video) {
      // The template waits for narration.json scene_timing.i (absent) and stays
      // dark. Inject the preview schedule + time so the template's own tick()
      // drives scenes, card bands, journey fill, and station flashes.
      if (tmpl.previewTiming) {
        await page.evaluate((tm, t) => {
          window.__timing = tm;
          window.__t = t;
        }, tmpl.previewTiming, tmpl.previewT);
      }
      // Safety net: force inner content visible WITHOUT stacking scenes —
      // .scene stays opacity-gated by the template's .active class; only the
      // reveal/band elements that may not have hit their .show delay yet are
      // forced to their final state.
      await page.addStyleTag({ content: `
        /* Reveal + band elements: final state (template toggles .show for the
           active scene; this catches any that haven't reached their delay). */
        .r, .d1, .d2, .d3, .band, .hbeat-northstar, .hbeat-row, .hbeat-divider,
        .hbeat-stat, .hbeat-action, .cta, .cta-badge, .cta-title, .cta-url {
          opacity: 1 !important;
          transform: none !important;
          filter: none !important;
          visibility: visible !important;
        }
        .hbeat { opacity: 1 !important; }
        /* Keep the journey exactly as the template animates it — do not force. */
        .journey-svg { opacity: 1 !important; }
      ` });
    } else {
      await page.evaluate((r) => {
        window.__applyCampaignRendition({
          campaign_id: "social-fix", batch_id: "batch-fix",
          item_id: "item", content_id: "content-fix", design: r,
        });
      }, { ...RENDITION });
    }

    if (!tmpl.video) {
      await page.waitForFunction(() => document.documentElement.dataset.templateReady === "true", { timeout: 5000 });
    }
    await new Promise(r => setTimeout(r, 800));

    const outPath = join(OUT_DIR, tmpl.out);
    await page.screenshot({ path: outPath, type: "png" });
    console.log(`  ✓ ${outPath}`);
    await page.close();
  }

  await browser.close();
  server.close();
  console.log("\nAll social PNGs rendered.");
}

main().catch(e => { console.error(e); process.exit(1); });
