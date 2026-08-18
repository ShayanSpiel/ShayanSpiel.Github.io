const puppeteer = require("puppeteer");
const { createServer } = require("http");
const { readFileSync, mkdirSync, existsSync } = require("fs");
const { join } = require("path");

const ROOT = "/Users/shayan/ShayanSpiel.Github.io";
const OUT_DIR = join(ROOT, ".spielos/artifacts/template-preview-20260817/video/frames");
const TEMPLATE = join(ROOT, ".agents/company/departments/design/templates/video/heartbeat.html");

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

  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });

  const url = `${base}/.agents/company/departments/design/templates/video/heartbeat.html`;
  console.log("Loading heartbeat...");
  await page.goto(url, { waitUntil: "networkidle0", timeout: 15000 });

  // Render frame 0 (0s) and frame 10 (0.33s at 30fps)
  for (const sec of [0, 0.33]) {
    await page.evaluate((s) => {
      // Seek the heartbeat animation
      if (window.__seek) window.__seek(s);
      else {
        // Force animation time
        document.querySelectorAll(".scene").forEach(el => {
          el.style.animationPlayState = "paused";
        });
      }
    }, sec);
    await new Promise(r => setTimeout(r, 500));

    const frameNum = String(Math.round(sec * 30)).padStart(3, "0");
    const outPath = join(OUT_DIR, `heartbeat-${frameNum}.jpg`);
    await page.screenshot({ path: outPath, type: "jpeg", quality: 90 });
    console.log(`  ✓ frame ${frameNum} (${sec}s) → ${outPath}`);
  }

  await browser.close();
  server.close();
  console.log("\nHeartbeat frames rendered.");
}

main().catch(e => { console.error(e); process.exit(1); });
