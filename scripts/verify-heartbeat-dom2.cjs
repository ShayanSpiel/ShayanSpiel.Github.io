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
async function main() {
  const server = await startServer();
  const port = server.address().port;
  const base = `http://localhost:${port}`;
  const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser = await puppeteer.launch({ headless: "new", args: ["--no-sandbox"], executablePath: existsSync(CHROME_PATH) ? CHROME_PATH : undefined });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await page.goto(`${base}/.agents/company/departments/design/templates/video/heartbeat.html`, { waitUntil: "networkidle0", timeout: 15000 });
  await page.evaluate((tm, t) => { window.__timing = tm; window.__t = t; },
    { voice: {}, scenes: [{start:0,end:4},{start:4,end:8},{start:8,end:12},{start:12,end:14}] }, 10);
  await new Promise(r => setTimeout(r, 1200));
  const report = await page.evaluate(() => {
    const r = (id) => { const el = document.getElementById(id); if(!el) return null; const b = el.getBoundingClientRect(); return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)}; };
    return {
      hbeat: r('hbeat'), northstar: r('northstar'), rowRun: r('row-run'), stats: r('hbeat-stats'),
      stat0: r('stat0'), stat1: r('stat1'), stat2: r('stat2'), stat3: r('stat3'),
      runTile: r('run-title'), viewActivity: r('view-activity'),
      w1: r('w1'), w2: r('w2'), cta: r('s4'), journey: r('journey-bg'),
    };
  });
  console.log(JSON.stringify(report, null, 1));
  await browser.close();
  server.close();
}
main().catch(e => { console.error(e); process.exit(1); });
