const { execSync } = require("child_process");
const { readFileSync, mkdirSync } = require("fs");
const { join } = require("path");
const OUT = join(__dirname, "..", ".spielos/artifacts/template-preview-20260817/social");
const TMP = join(__dirname, "..", ".spielos/artifacts/template-preview-20260817/bmp");
mkdirSync(TMP, { recursive: true });
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
const file = "heartbeat.png";
const bmp = join(TMP, file.replace(".png", ".bmp"));
execSync(`sips -s format bmp "${join(OUT, file)}" --out "${bmp}" >/dev/null 2>&1`);
const img = readBmp(bmp);
const probes = [
  ["stat0 number area (424,760)", 424, 760],
  ["stat0 icon area (190,750)", 190, 750],
  ["stat1 number (997,760)", 997, 760],
  ["northstar title (710,500)", 710, 500],
  ["northstar bullseye tile (640,445)", 640, 445],
  ["run title text (470,625)", 470, 625],
  ["view activity chip (1200,623)", 1200, 623],
  ["card interior empty (130,940)", 130, 940],
  ["card border top (77,368)", 77, 368],
  ["background outside card (30,300)", 30, 300],
];
for (const [label, x, y] of probes) {
  const c = img.px(x, y);
  console.log(`${label}: ${c ? c.r + "," + c.g + "," + c.b : "null"}`);
}
// scan a vertical strip inside stat0 for any non-background pixels
let found = [];
for (let y = 710; y <= 835 && found.length < 12; y += 2) {
  for (let x = 160; x <= 690 && found.length < 12; x += 4) {
    const c = img.px(x, y);
    if (c && (c.r > 120 || c.g > 120)) { found.push(`(${x},${y})=${c.r},${c.g},${c.b}`); }
  }
}
console.log("stat0 area bright pixels:", found.length ? found.join(" ") : "NONE");
