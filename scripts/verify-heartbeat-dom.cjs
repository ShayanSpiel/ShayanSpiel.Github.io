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

  // inject preview timing like render-social.cjs does
  await page.evaluate((tm, t) => { window.__timing = tm; window.__t = t; },
    { voice: {}, scenes: [{start:0,end:4},{start:4,end:8},{start:8,end:12},{start:12,end:14}] }, 10);
  await new Promise(r => setTimeout(r, 1200));

  const report = await page.evaluate(() => {
    const rect = (el) => { if(!el) return null; const r = el.getBoundingClientRect(); return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}; };
    const state = (id) => { const el = document.getElementById(id); if(!el) return null; const cs = getComputedStyle(el); return { opacity: cs.opacity, display: cs.display, show: el.classList.contains('show'), active: el.classList.contains('active') }; };
    const hbeat = document.getElementById('hbeat');
    const cs = hbeat ? getComputedStyle(hbeat) : null;
    return {
      timing: !!window.__timing,
      timingError: window.__timingError,
      t: window.__t,
      activeScene: document.querySelector('.scene.active') ? document.querySelector('.scene.active').id : null,
      hbeat: { rect: rect(hbeat), opacity: cs ? cs.opacity : null, display: cs ? cs.display : null, z: cs ? cs.zIndex : null },
      northstar: state('northstar'),
      div1: state('div1'),
      rowRun: state('row-run'),
      div2: state('div2'),
      stat0: state('stat0'), stat1: state('stat1'), stat2: state('stat2'), stat3: state('stat3'),
      bandMain: state('h1'),
      bgGrid: state('bg-grid'),
      journeyBg: state('journey-bg'),
      journeyFill: state('journey-fill'),
      goalShow: document.getElementById('journey-goal') ? document.getElementById('journey-goal').classList.contains('show') : null,
    };
  });
  console.log(JSON.stringify(report, null, 1));
  await browser.close();
  server.close();
}
main().catch(e => { console.error(e); process.exit(1); });
