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
async function main() {
  const server = await startServer();
  const port = server.address().port;
  const base = `http://localhost:${port}`;
  const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser = await puppeteer.launch({ headless: "new", args: ["--no-sandbox"], executablePath: existsSync(CHROME_PATH) ? CHROME_PATH : undefined });
  const page = await browser.newPage();
  await page.setViewport({ width: 1208, height: 628, deviceScaleFactor: 1 });
  await page.goto(`${base}/.agents/company/departments/design/templates/social/agent-brief.html`, { waitUntil: "networkidle0", timeout: 15000 });
  await page.evaluate((r) => {
    window.__applyCampaignRendition({ campaign_id: "probe", batch_id: "probe", item_id: "i", content_id: "c", design: r });
  }, { ...RENDITION });
  await page.waitForFunction(() => document.documentElement.dataset.templateReady === "true", { timeout: 5000 });
  const report = await page.evaluate(() => {
    const info = (sel) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), font: cs.fontFamily, size: cs.fontSize, weight: cs.fontWeight, color: cs.color, display: cs.display };
    };
    return {
      bodyFont: getComputedStyle(document.body).fontFamily,
      eyebrow: info(".eyebrow"),
      title: info("#template-title"),
      hook: info("#template-hook"),
      steps: info("#steps"),
      step1: info("#steps .step:nth-child(1)"),
      step7: info("#steps .step:nth-child(7)"),
      stepNum1: info("#steps .step:nth-child(1) .step-num"),
      stepName1: info("#steps .step:nth-child(1) .step-name"),
      footer: info("footer"),
      canvasOverflow: document.querySelector(".canvas").scrollHeight > document.querySelector(".canvas").clientHeight,
      canvasClientH: document.querySelector(".canvas").clientHeight,
      canvasScrollH: document.querySelector(".canvas").scrollHeight,
    };
  });
  console.log(JSON.stringify(report, null, 1));
  await browser.close();
  server.close();
}
main().catch(e => { console.error(e); process.exit(1); });
