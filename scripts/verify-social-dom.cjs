const puppeteer = require("puppeteer");
const { createServer } = require("http");
const { readFileSync, existsSync } = require("fs");
const { join } = require("path");

const ROOT = __dirname + "/..";
const MIME = { ".html": "text/html", ".css": "text/css", ".js": "application/javascript", ".json": "application/json", ".woff2": "font/woff2", ".png": "image/png", ".svg": "image/svg+xml" };

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

const RENDITION = {
  theme: "gruvbox-dark", layout: "landscape", eyebrow: "SpielOS",
  title_lines: ["AI cannot fix", "a messy process"], accent_line: 1,
  supporting_text: "We map one process, build the system, and show you where the time goes.",
  station_labels: ["Goal", "Inputs", "Outputs", "Interface", "Memory", "Rules", "Success"],
  milestone_labels: ["Mapped workflow", "Build plan", "Connected tools", "Guardrails", "Live URL"],
};

const TEMPLATES = [
  { file: "single-fact.html", w: 1080, h: 1350 },
  { file: "department-map.html", w: 1080, h: 1350 },
  { file: "agent-brief.html", w: 1080, h: 1350 },
  { file: "list-checklist.html", w: 1080, h: 1350 },
  { file: "testimonial-pull-quote.html", w: 1080, h: 1350 },
];

async function main() {
  const server = await startServer();
  const port = server.address().port;
  const base = `http://localhost:${port}`;
  const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser2 = await puppeteer.launch({ headless: "new", args: ["--no-sandbox"], executablePath: existsSync(CHROME_PATH) ? CHROME_PATH : undefined });
  for (const tmpl of TEMPLATES) {
    const page = await browser2.newPage();
    await page.setViewport({ width: tmpl.w, height: tmpl.h, deviceScaleFactor: 1 });
    await page.goto(`${base}/.agents/company/departments/design/templates/social/${tmpl.file}`, { waitUntil: "networkidle0", timeout: 15000 });
    await page.evaluate((r) => {
      window.__applyCampaignRendition({ campaign_id: "vf", batch_id: "vf", item_id: "i", content_id: "c", design: r });
    }, { ...RENDITION });
    await page.waitForFunction(() => document.documentElement.dataset.templateReady === "true", { timeout: 5000 });
    const report = await page.evaluate(() => {
      const rect = (sel) => {
        const el = document.querySelector(sel);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
      };
      const svgLand = document.querySelector(".journey-landscape");
      const svgPort = document.querySelector(".journey-portrait");
      const landDisp = svgLand ? getComputedStyle(svgLand).display : "none";
      const portDisp = svgPort ? getComputedStyle(svgPort).display : "none";
      const nodes = [...document.querySelectorAll(".journey-node")].map(n => {
        const r = n.getBoundingClientRect();
        return { cx: Math.round(r.x + r.width/2), cy: Math.round(r.y + r.height/2) };
      });
      const goal = document.querySelector(".journey-goal");
      const goalRect = goal ? goal.getBoundingClientRect() : null;
      return {
        title: rect("#template-title"),
        hook: rect("#template-hook"),
        checklist: rect("#checklist"),
        checkRows: document.querySelectorAll(".check-row").length,
        footer: rect("footer"),
        journeyLandscapeDisplay: landDisp,
        journeyPortraitDisplay: portDisp,
        journeyPathFill: document.querySelector(".journey-path-fill") ? getComputedStyle(document.querySelector(".journey-path-fill")).stroke : "none",
        nodes: nodes.length,
        goalCenter: goalRect ? { x: Math.round(goalRect.x + goalRect.width/2), y: Math.round(goalRect.y + goalRect.height/2) } : null,
        gridOpacity: getComputedStyle(document.querySelector(".grid")).opacity,
      };
    });
    console.log(`\n=== ${tmpl.file} (${tmpl.w}x${tmpl.h}) ===`);
    console.log(JSON.stringify(report, null, 1));
    await page.close();
  }
  await browser2.close();
  server.close();
}

main().catch(e => { console.error(e); process.exit(1); });
