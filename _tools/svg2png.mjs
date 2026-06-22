import puppeteer from 'puppeteer';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const logosDir = join(__dirname, '..', 'assets', 'logos');

const files = [
  'primary-dark.svg', 'primary-light.svg', 'primary-transparent.svg',
  'slogan-dark.svg', 'slogan-light.svg', 'slogan-transparent.svg',
  'stacked-dark.svg', 'stacked-light.svg', 'stacked-transparent.svg',
  'icon-dark.svg', 'icon-light.svg', 'icon-transparent.svg',
];

const browser = await puppeteer.launch({
  headless: true,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  args: ['--no-sandbox', '--disable-setuid-sandbox'],
});

for (const f of files) {
  const svgPath = join(logosDir, f);
  const svgContent = readFileSync(svgPath, 'utf-8');
  const match = svgContent.match(/<svg[^>]*\b(width|height)=["'](\d+)["']/g);
  let w = 600, h = 88;
  const wm = svgContent.match(/width="(\d+)"/);
  const hm = svgContent.match(/height="(\d+)"/);
  if (wm) w = parseInt(wm[1]);
  if (hm) h = parseInt(hm[1]);

  const html = `<!DOCTYPE html><html><head><style>body{margin:0;display:flex}</style></head><body>${svgContent}</body></html>`;

  const page = await browser.newPage();
  await page.setViewport({ width: w + 40, height: h + 40, deviceScaleFactor: 2 });
  await page.setContent(html, { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 500));

  const el = await page.$('svg');
  const box = await el.boundingBox();
  const pngName = f.replace('.svg', '.png');
  await el.screenshot({ path: join(logosDir, pngName), omitBackground: true });
  console.log(`  ✓ ${f} → ${pngName} (${w}×${h})`);

  await page.close();
}

await browser.close();
console.log('Done — 12 PNGs generated');
