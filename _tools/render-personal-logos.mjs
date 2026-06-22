import puppeteer from 'puppeteer';
import { readFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const logosDir = join(__dirname, '..', 'assets', 'logos', 'personal');
mkdirSync(logosDir, { recursive: true });

const variants = ['primary', 'slogan', 'stacked', 'icon'];
const themes = ['dark', 'light', 'transparent'];
const files = [];
for (const v of variants) for (const t of themes) files.push(`${v}-${t}.svg`);

const browser = await puppeteer.launch({
  headless: true,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  args: ['--no-sandbox', '--disable-setuid-sandbox'],
});

for (const f of files) {
  const svgPath = join(logosDir, f);
  const svgContent = readFileSync(svgPath, 'utf-8');

  const wm = svgContent.match(/width="(\d+)"/);
  const hm = svgContent.match(/height="(\d+)"/);
  const w = wm ? parseInt(wm[1]) : 600;
  const h = hm ? parseInt(hm[1]) : 88;

  const html = `<!DOCTYPE html><html><head><style>body{margin:0;display:flex;background:transparent}</style></head><body>${svgContent}</body></html>`;

  const page = await browser.newPage();
  await page.setViewport({ width: w + 40, height: h + 40, deviceScaleFactor: 2 });
  await page.setContent(html, { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 800));

  const el = await page.$('svg');
  const pngName = f.replace('.svg', '.png');
  await el.screenshot({ path: join(logosDir, pngName), omitBackground: true });
  console.log(`  ${f} -> ${pngName} (${w}x${h})`);
  await page.close();
}

await browser.close();
console.log(`Done - ${files.length} PNGs`);
