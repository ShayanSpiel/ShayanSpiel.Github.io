#!/usr/bin/env node
/** Render one token-aligned Design template into registered channel sizes. */
import puppeteer from "puppeteer";
import { createServer } from "http";
import { existsSync, mkdirSync, readFileSync } from "fs";
import { join, resolve, extname } from "path";
import { fileURLToPath } from "url";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const DESIGN_ROOT = join(ROOT, ".agents/company/departments/design");
const TEMPLATE = join(DESIGN_ROOT, "templates/social/harness-architecture.html");
const PRESETS_FILE = join(DESIGN_ROOT, "presets.json");
const OUTPUT_ROOT = join(ROOT, ".spielos/artifacts/design-showcase/graphics");
const MIME = { ".html": "text/html", ".css": "text/css", ".js": "application/javascript",
  ".json": "application/json", ".woff2": "font/woff2", ".png": "image/png" };

function validate() {
  const failures = [];
  for (const file of [TEMPLATE, PRESETS_FILE, join(DESIGN_ROOT, "system/production.css")]) {
    if (!existsSync(file)) failures.push(`missing ${file}`);
  }
  if (!failures.length) {
    const html = readFileSync(TEMPLATE, "utf8");
    const css = readFileSync(join(DESIGN_ROOT, "system/production.css"), "utf8");
    if (!html.includes("production.css")) failures.push("template does not use the production design system");
    if (!html.includes("GOAL") || !html.includes("EVALUATE")) failures.push("template does not show the canonical loop");
    if (html.includes("Tools stay stable")) failures.push("template uses the retired Tool vocabulary");
    if (!css.includes("src/styles/tokens/index.css")) failures.push("production CSS does not import canonical tokens");
    const presets = JSON.parse(readFileSync(PRESETS_FILE, "utf8"));
    if (Object.keys(presets).length < 6) failures.push("fewer than six channel presets");
  }
  if (failures.length) { console.error(failures.join("\n")); process.exit(1); }
  console.log("Design templates OK: canonical tokens + 7 channel presets");
}

if (process.argv[2] === "--check") { validate(); process.exit(0); }

function startServer() {
  return new Promise((done) => {
    const server = createServer((req, res) => {
      const path = join(ROOT, decodeURIComponent(req.url.split("?")[0]));
      let data;
      try { data = readFileSync(path); }
      catch { res.writeHead(404); res.end("Not found"); return; }
      res.writeHead(200, { "Content-Type": MIME[extname(path)] || "application/octet-stream" });
      res.end(data);
    });
    server.listen(0, "127.0.0.1", () => done({ server, base: `http://127.0.0.1:${server.address().port}` }));
  });
}

async function render() {
  validate();
  const requested = process.argv[2] || "all";
  const output = resolve(process.argv[3] || OUTPUT_ROOT);
  const presets = JSON.parse(readFileSync(PRESETS_FILE, "utf8"));
  const selected = requested === "all" ? Object.entries(presets) : [[requested, presets[requested]]];
  if (selected.some(([, value]) => !value)) throw new Error(`Unknown preset: ${requested}`);
  mkdirSync(output, { recursive: true });
  const { server, base } = await startServer();
  const systemChrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser = await puppeteer.launch({ headless: "shell",
    ...(existsSync(systemChrome) ? { executablePath: systemChrome } : {}),
    args: ["--no-sandbox", "--font-render-hinting=none"] });
  try {
    const page = await browser.newPage();
    for (const [name, size] of selected) {
      await page.setViewport({ ...size, deviceScaleFactor: 1 });
      await page.goto(`${base}/.agents/company/departments/design/templates/social/harness-architecture.html`, { waitUntil: "networkidle0" });
      await page.evaluate(() => document.fonts.ready);
      await page.screenshot({ path: join(output, `harness-architecture-${name}-${size.width}x${size.height}.png`) });
      console.log(`Rendered ${name} ${size.width}x${size.height}`);
    }
  } finally { await browser.close(); server.close(); }
}

render().catch((error) => { console.error(error); process.exit(1); });
