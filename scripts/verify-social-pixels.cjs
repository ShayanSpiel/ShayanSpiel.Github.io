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
  const dibSize = b.readUInt32LE(14);
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
    // BMP stores BGR(A)
    return { b: b[off], g: b[off + 1], r: b[off + 2] };
  };
  return { width, height, px };
}

function near(c, target, tol = 30) {
  if (!c) return false;
  return Math.abs(c.r - target[0]) <= tol && Math.abs(c.g - target[1]) <= tol && Math.abs(c.b - target[2]) <= tol;
}

// gruvbox-dark primary = aqua #458588 (r69 g133 b136); muted foreground #a89984-ish (r168 g153 b132)
const PRIMARY = [69, 133, 136];
const MUTED = [168, 153, 132];

const checks = [
  { file: "single-fact.png", label: "single-fact bottom wave", pts: [[20,1140],[500,1010],[980,970],[1045,930]], color: PRIMARY },
  { file: "department-map.png", label: "department-map left curve", pts: [[60,60],[50,520],[46,1000],[55,1300]], color: PRIMARY },
  { file: "agent-brief.png", label: "agent-brief bottom wave", pts: [[20,1140],[500,1010],[980,970],[1045,930]], color: PRIMARY },
  { file: "list-checklist.png", label: "list-checklist right curve", pts: [[1040,70],[1020,500],[1015,900],[1020,1300]], color: PRIMARY },
  { file: "testimonial-pull-quote.png", label: "testimonial bottom wave", pts: [[20,1140],[500,1010],[980,970],[1045,930]], color: PRIMARY },
];

let fail = 0;
for (const ch of checks) {
  const bmp = join(TMP, ch.file.replace(".png", ".bmp"));
  execSync(`sips -s format bmp "${join(OUT, ch.file)}" --out "${bmp}" >/dev/null 2>&1`);
  const img = readBmp(bmp);
  let hits = 0;
  const misses = [];
  for (const [x, y] of ch.pts) {
    const c = img.px(Math.round(x), Math.round(y));
    if (near(c, ch.color, 45)) hits++; else misses.push(`(${x},${y})=${c ? c.r + "," + c.g + "," + c.b : "null"}`);
  }
  const ok = hits >= Math.max(1, Math.floor(ch.pts.length * 0.6));
  if (!ok) fail++;
  console.log(`${ok ? "PASS" : "FAIL"} ${ch.label}: ${hits}/${ch.pts.length} primary hits${misses.length ? " — misses: " + misses.join(" ") : ""}`);
}

// Verify bullseye goal centers: expect background fill + primary ring + primary core
const goalChecks = [
  { file: "single-fact.png", label: "single-fact goal", c: [1045, 930] },
  { file: "department-map.png", label: "department-map goal", c: [60, 1300] },
  { file: "agent-brief.png", label: "agent-brief goal", c: [1045, 930] },
  { file: "list-checklist.png", label: "list-checklist goal", c: [1020, 1300] },
  { file: "testimonial-pull-quote.png", label: "testimonial goal", c: [1045, 930] },
];
for (const g of goalChecks) {
  const bmp = join(TMP, g.file.replace(".png", ".bmp"));
  const img = readBmp(bmp);
  const core = img.px(g.c[0], g.c[1]);
  const ringL = img.px(g.c[0] - 30, g.c[1]);
  const ringR = img.px(g.c[0] + 30, g.c[1]);
  const innerL = img.px(g.c[0] - 17, g.c[1]);
  const innerR = img.px(g.c[0] + 17, g.c[1]);
  const coreOk = near(core, PRIMARY, 40);
  const ringOk = near(ringL, PRIMARY, 45) || near(ringR, PRIMARY, 45) || near(innerL, PRIMARY, 45) || near(innerR, PRIMARY, 45);
  const ok = coreOk && ringOk;
  if (!ok) fail++;
  console.log(`${ok ? "PASS" : "FAIL"} ${g.label}: core=${core ? core.r + "," + core.g + "," + core.b : "null"} ringL=${ringL ? ringL.r + "," + ringL.g + "," + ringL.b : "null"} ringR=${ringR ? ringR.r + "," + ringR.g + "," + ringR.b : "null"} innerL=${innerL ? innerL.r + "," + innerL.g + "," + innerL.b : "null"}`);
}

console.log(fail === 0 ? "\nALL PIXEL CHECKS PASSED" : `\n${fail} CHECK(S) FAILED`);
process.exit(fail === 0 ? 0 : 1);
