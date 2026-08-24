/**
 * Regenerate every favicon raster + the root ICO from the single source of
 * truth: public/assets/favicons/favicon-v2.svg (current brand mark).
 *
 * Usage: node scripts/generate-favicons.mjs
 * Requires: puppeteer (devDependency) + Chrome (executablePath auto-detected).
 */
import puppeteer from "puppeteer";
import { existsSync } from "node:fs";
import { writeFile, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SVG = path.join(ROOT, "public/assets/favicons/favicon-v2.svg");
const OUT = path.join(ROOT, "public/assets/favicons");
const CANDIDATE_CHROMES = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  process.env.CHROME_PATH,
].filter(Boolean);

const SIZES = [16, 32, 180, 192, 512];
const FILES = {
  16: "favicon-16-v2.png",
  32: "favicon-32-v2.png",
  180: "apple-touch-icon-v2.png",
  192: "favicon-192.png",
  512: "favicon-512.png",
};

function packIco(pngBuffers) {
  // ICO container with embedded PNG entries (valid per modern ICO spec).
  const count = pngBuffers.length;
  const header = Buffer.alloc(6);
  header.writeUInt16LE(0, 0); header.writeUInt16LE(1, 2); header.writeUInt16LE(count, 4);
  const entries = Buffer.alloc(16 * count);
  let offset = 6 + 16 * count;
  const blobs = [];
  pngBuffers.forEach(({ size, png }, i) => {
    const e = i * 16;
    entries.writeUInt8(size % 256, e); entries.writeUInt8(size % 256, e + 1);
    entries.writeUInt8(0, e + 2); entries.writeUInt8(0, e + 3);
    entries.writeUInt16LE(1, e + 4); entries.writeUInt16LE(32, e + 6);
    entries.writeUInt32LE(png.length, e + 8); entries.writeUInt32LE(offset, e + 12);
    offset += png.length; blobs.push(png);
  });
  return Buffer.concat([header, entries, ...blobs]);
}

const chrome = CANDIDATE_CHROMES.find((p) => existsSync(p));
if (!chrome) throw new Error("Chrome not found; set CHROME_PATH");
const browser = await puppeteer.launch({ executablePath: chrome });
const page = await browser.newPage();

const SVG_MARK = (await readFile(SVG, "utf8")).replace("<svg ", '<svg width="256" height="256" ');

async function renderPng(size) {
  const scale = size / 256;
  await page.setViewport({ width: 256, height: 256, deviceScaleFactor: scale });
  await page.setContent(
    `<body style="margin:0;background:transparent">${SVG_MARK}</body>`
  );
  await new Promise((r) => setTimeout(r, 80));
  return page.screenshot({ omitBackground: true, clip: { x: 0, y: 0, width: 256, height: 256 } });
}

const rendered = [];
for (const size of SIZES) {
  const png = await renderPng(size);
  await writeFile(path.join(OUT, FILES[size]), png);
  if (size === 16 || size === 32 || size === 48 || size === 256) rendered.push({ size, png });
  console.log(`✓ ${FILES[size]} (${size}x${size})`);
}

// 48px for the ICO's mid-size entry
rendered.push({ size: 48, png: await renderPng(48) });

rendered.sort((a, b) => a.size - b.size);
await writeFile(path.join(ROOT, "public/favicon.ico"), packIco(rendered));
console.log("✓ public/favicon.ico (16/32/48)");
await browser.close();
