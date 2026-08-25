import puppeteer from "puppeteer";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const template = path.join(root, "src/pdf-templates/partner-deal.html");
const outDir = path.join(root, "public/assets/partners");
const outFile = path.join(outDir, "spielos-partner-deal.pdf");

fs.mkdirSync(outDir, { recursive: true });

// Puppeteer's pinned build may be missing from the local cache while an
// older cached Chrome or the system Chrome is available — use what exists.
function resolveChrome() {
  const cacheRoot = path.join(process.env.HOME ?? "", ".cache/puppeteer/chrome");
  try {
    const versions = fs.readdirSync(cacheRoot).filter((d) => d.startsWith("mac_arm-") || d.startsWith("chrome-")).sort().reverse();
    for (const v of versions) {
      const base = path.join(cacheRoot, v);
      for (const candidate of [
        path.join(base, "chrome-mac-arm64", "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"),
        path.join(base, "chrome-mac_arm64", "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"),
      ]) {
        if (fs.existsSync(candidate)) return candidate;
      }
    }
  } catch {}
  return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
}

const browser = await puppeteer.launch({ headless: true, executablePath: resolveChrome() });
try {
  const page = await browser.newPage();
  await page.goto("file://" + template, { waitUntil: "networkidle0" });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({
    path: outFile,
    width: "210mm",
    height: "297mm",
    printBackground: true,
    pageRanges: "1",
    margin: { top: 0, bottom: 0, left: 0, right: 0 },
  });
} finally {
  await browser.close();
}

const bytes = fs.statSync(outFile).size;
console.log(`written ${path.relative(root, outFile)} (${(bytes / 1024).toFixed(1)} KB)`);
