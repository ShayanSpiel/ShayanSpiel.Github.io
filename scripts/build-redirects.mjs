import {readFileSync, writeFileSync, readdirSync, existsSync} from 'node:fs';
import {join} from 'node:path';

// Build-time redirects keep the original reviewed files intact in public/.
const root = 'dist';
const redirects = JSON.parse(readFileSync('scripts/retired-routes.json', 'utf8'));
const origin = 'https://spielos.xyz';
const escapeRegExp = value => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
for (const [source, target] of Object.entries(redirects)) {
  if (!/^\/(?:[^?#]*)\/$/.test(source) || !/^\/(?:[^?#]*)$/.test(target) || source === target || redirects[target]) throw Error(`Invalid redirect: ${source} -> ${target}`);
  if (!existsSync(join(root, source, 'index.html')) || !existsSync(join(root, target, 'index.html'))) throw Error(`Missing redirect endpoint: ${source} -> ${target}`);
}
const walk = dir => readdirSync(dir, {withFileTypes: true}).flatMap(entry => entry.isDirectory() ? walk(join(dir, entry.name)) : [join(dir, entry.name)]);
const entries = Object.entries(redirects).sort((a,b) => b[0].length-a[0].length);
const pattern = new RegExp('(' + entries.map(([source]) => escapeRegExp(source)).join('|') + ')(?=[?#"\'\\s<]|$)', 'g');
for (const file of walk(root).filter(name => name.endsWith('.html'))) {
  const current = readFileSync(file, 'utf8');
  // Direct old inbound aliases and internal links to the final page.
  const updated = current.replace(pattern, source => redirects[source]);
  if (updated !== current) writeFileSync(file, updated);
}
for (const [source, target] of entries) {
  const fa = source.startsWith('/fa/');
  const title = fa ? 'کاروایز' : 'karwise';
  const copy = fa ? 'رفتن به صفحهٔ جدید' : 'Continue to the updated page';
  const html = `<!doctype html><html lang="${fa ? 'fa' : 'en'}" dir="${fa ? 'rtl' : 'ltr'}" data-theme="blue-dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><meta name="color-scheme" content="dark light"><style data-kw-first-paint>:root{--background:#0b0f1a;--foreground:#e2e8f0}html{background:var(--background);color:var(--foreground);color-scheme:dark}html[data-theme=paper-light]{--background:#eee4d4;--foreground:#1e293b;color-scheme:light}body{margin:0;min-height:100svh;display:grid;place-items:center}a{color:inherit}</style><script>try{document.documentElement.dataset.theme=localStorage.getItem("spielos-home-theme")==="paper-light"?"paper-light":"blue-dark"}catch{};location.replace(${JSON.stringify(target)}+location.search+location.hash)</script><meta http-equiv="refresh" content="0;url=${target}"><link rel="canonical" href="${origin}${target}"><title>${title}</title></head><body><noscript><a href="${target}">${copy}</a></noscript></body></html>`;
  writeFileSync(join(root, source, 'index.html'), html);
}
const sitemapPath = join(root, 'sitemap.xml');
let sitemap = readFileSync(sitemapPath, 'utf8');
sitemap = sitemap.replace(/<url>\s*<loc>([^<]+)<\/loc>[\s\S]*?<\/url>/g, (entry, loc) => redirects[loc.startsWith(origin) ? loc.slice(origin.length) : ''] ? '' : entry);
writeFileSync(sitemapPath, sitemap);
console.log(`Prepared ${entries.length} legacy URL redirects`);
