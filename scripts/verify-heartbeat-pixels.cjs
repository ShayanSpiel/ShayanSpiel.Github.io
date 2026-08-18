const { execSync } = require("child_process");
const { readFileSync, mkdirSync } = require("fs");
const { join } = require("path");

const OUT = join(__dirname, "..", ".spielos/artifacts/template-preview-20260817/social");
const TMP = join(__dirname, "..", ".spielos/artifacts/template-preview-20260817/bmp");
mkdirSync(TMP, { recursive: true });

// Read a BMP (24-bit or 32-bit) and return width, height, and a function to sample RGB.
function readBmp(file) {
  const b = readFileSync(file);
  const bfOffBits = b.readUInt32LE(10);
  const width = b.readInt32LE(18);
  const heightRaw = b.readInt32LE(22);
  const height = Math.abs(heightRaw);
  const topDown = heightRaw < 0;
  const bpp = b.readUInt16LE(28);
  const bytesPerPx = bpp / 8;
  const rowSize = Math.ceil((width * bpp) / 32) * 4;
  const px = (x, y) => {
    if (x < 0 || x >= width || y < 0 || y >= height) return null;
    const row = topDown ? y : height - 1 - y;
    const off = bfOffBits + row * rowSize + x * bytesPerPx;
    return { b: b[off], g: b[off + 1], r: b[off + 2] };
  };
  return { width, height, px };
}
function near(c, target, tol = 45) {
  if (!c) return false;
  return Math.abs(c.r - target[0]) <= tol && Math.abs(c.g - target[1]) <= tol && Math.abs(c.b - target[2]) <= tol;
}
function bright(c) { return c && c.r > 200 && c.g > 200 && c.b > 160; }

const file = "heartbeat.png";
const bmp = join(TMP, file.replace(".png", ".bmp"));
execSync(`sips -s format bmp "${join(OUT, file)}" --out "${bmp}" >/dev/null 2>&1`);
const img = readBmp(bmp);
console.log(`heartbeat.png ${img.width}x${img.height}`);

// Probe-driven verification against the rebuilt no-card composition (1920x1080):
// headline band top-left x96-941 y130-385; open lab bands x96-941 y432-915
// (north star row, run row, then the 2x2 record); journey sweeps the right
// side x~1150-1850 and ends at the bullseye (1780,950); footer centered.
function countIn(region, pred, step = 6) {
  let hit = 0, tot = 0;
  for (let x = region[0]; x < region[2]; x += step)
    for (let y = region[1]; y < region[3]; y += step) {
      tot++;
      if (pred(img.px(x, y))) hit++;
    }
  return { hit, tot, pct: (100 * hit / tot).toFixed(1) };
}
const PRIMARY = [69, 133, 136];
const checks = [
  { label: "headline band (bright text + primary accent)", region: [96, 130, 941, 385], pred: c => bright(c) || near(c, PRIMARY) },
  { label: "lab content (open bands + record, no card)", region: [96, 432, 941, 915], pred: c => c && (c.r > 150 || c.g > 150 || near(c, PRIMARY)) },
  { label: "stats row (bright numbers + colored icons)", region: [96, 725, 941, 915], pred: c => bright(c) || (c && c.g > 120 && c.r < 150) },
  { label: "journey line band (primary stroke)", region: [1150, 60, 1850, 1060], pred: c => near(c, PRIMARY) },
];
let fail = 0;
for (const ch of checks) {
  const r = countIn(ch.region, ch.pred);
  const ok = r.hit >= (ch.label.includes("journey") ? 2 : 8);
  if (!ok) fail++;
  console.log(`${ok ? "PASS" : "FAIL"} ${ch.label}: ${r.hit}/${r.tot} (${r.pct}%)`);
}
// direct probes (coordinates scanned from the live DOM / rendered PNG)
const probes = [
  ["stat0 number", 180, 753, bright],
  ["stat1 number", 612, 753, bright],
  ["stat2 number", 184, 865, bright],
  ["stat3 number", 612, 861, bright],
  ["stat0 icon (accent)", 120, 765, c => near(c, PRIMARY)],
  ["stat2 icon (purple)", 120, 881, c => c && c.r > 150 && c.b > 100],
  ["stat3 icon (success green)", 556, 880, c => c && c.r > 120 && c.g > 120 && c.b < 80],
  ["northstar tile (primary)", 133, 495, c => near(c, PRIMARY)],
  ["northstar title (bright)", 344, 501, bright],
  ["run tile (success green)", 133, 625, c => c && c.r > 120 && c.g > 120 && c.b < 80],
  ["view activity chip (primary)", 884, 626, c => near(c, PRIMARY)],
];
for (const [label, x, y, pred] of probes) {
  const c = img.px(x, y);
  const ok = pred(c);
  if (!ok) fail++;
  console.log(`${ok ? "PASS" : "FAIL"} probe ${label} (${x},${y}): ${c ? c.r + "," + c.g + "," + c.b : "null"}`);
}
console.log(fail === 0 ? "\nHEARTBEAT CONTENT VERIFIED" : `\n${fail} CHECK(S) FAILED`);
process.exit(fail === 0 ? 0 : 1);
