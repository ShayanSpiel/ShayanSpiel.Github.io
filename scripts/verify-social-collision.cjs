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
  const browser = await puppeteer.launch({ headless: "new", args: ["--no-sandbox"], executablePath: existsSync(CHROME_PATH) ? CHROME_PATH : undefined });
  for (const tmpl of TEMPLATES) {
    const page = await browser.newPage();
    await page.setViewport({ width: tmpl.w, height: tmpl.h, deviceScaleFactor: 1 });
    await page.goto(`${base}/.agents/company/departments/design/templates/social/${tmpl.file}`, { waitUntil: "networkidle0", timeout: 15000 });
    await page.evaluate((r) => {
      window.__applyCampaignRendition({ campaign_id: "vf", batch_id: "vf", item_id: "i", content_id: "c", design: r });
    }, { ...RENDITION });
    await page.waitForFunction(() => document.documentElement.dataset.templateReady === "true", { timeout: 5000 });
    const report = await page.evaluate(() => {
      const visibleSvg = document.querySelector(".journey-portrait, .journey-landscape");
      const visible = (el) => { const r = el.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; };
      const sel = (s) => { const el = document.querySelector(s); return el ? visible(el) : null; };
      // journey path screen-space bounds (via getScreenCTM on first path)
      const path = visibleSvg ? visibleSvg.querySelector(".journey-path") : null;
      let pathBounds = null;
      if (path) {
        const ctm = path.getScreenCTM();
        const pt = (x,y) => { const p = new DOMPoint(x,y).matrixTransform(ctm); return [Math.round(p.x), Math.round(p.y)]; };
        // sample the path every 2% of the viewBox
        const vb = visibleSvg.viewBox.baseVal;
        let xs = [], ys = [];
        const len = path.getTotalLength();
        for (let t = 0; t <= 1.001; t += 0.02) {
          const p = path.getPointAtLength(len * t);
          const s = pt(p.x, p.y);
          xs.push(s[0]); ys.push(s[1]);
        }
        pathBounds = { minX: Math.min(...xs), maxX: Math.max(...xs), minY: Math.min(...ys), maxY: Math.max(...ys) };
      }
      return {
        header: sel("header"), main: sel("main"), footer: sel("footer"),
        title: sel("#template-title"), hook: sel("#template-hook"),
        factRule: sel(".fact-rule"), quoteGlyph: sel(".quote-glyph"), attribution: sel(".attribution"),
        checklist: sel("#checklist"), mapTiles: sel("#map-tiles"), mapWrap: sel(".map-wrap"), hub: sel(".map-hub"),
        steps: sel(".steps"), stepLast: sel(".steps .step:last-child"),
        pathBounds, goal: sel(".journey-goal"),
      };
    });
    console.log(`\n=== ${tmpl.file} ===`);
    console.log(JSON.stringify(report, null, 1));
    await page.close();
  }
  await browser.close();
  server.close();
}
main().catch(e => { console.error(e); process.exit(1); });
