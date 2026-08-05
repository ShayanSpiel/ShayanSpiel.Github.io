#!/usr/bin/env node
/**
 * SpielOS post-build sitemap fix.
 *
 * @astrojs/sitemap 3.7.x emits `sitemap-index.xml` + `sitemap-*.xml` chunks and
 * never writes the canonical `/sitemap.xml` that robots.txt points crawlers to.
 * This consolidates whatever was generated into a single `/sitemap.xml` that
 * always serves: a `urlset` when only one chunk exists, else a `sitemapindex`
 * listing every chunk. Noindex pages are excluded. Exit 0 = ok, exit 1 = broken sitemap found.
 */
import { readFileSync, readdirSync, copyFileSync, writeFileSync, statSync } from "fs";
import { join, extname } from "path";

const dist = join(process.cwd(), "dist");
const base = "https://spielos.xyz";
const SITE = new URL(base);

function collectHtml(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) out.push(...collectHtml(p));
    else if (extname(p) === ".html") out.push(p);
  }
  return out;
}

const noindexUrls = new Set();
for (const htmlFile of collectHtml(dist)) {
  const html = readFileSync(htmlFile, "utf8");
  if (/<meta name="robots"[^>]*content="[^"]*noindex/.test(html)) {
    const rel = htmlFile.replace(dist, "");
    noindexUrls.add(`${base}${rel}`);
  }
}

const chunkFiles = readdirSync(dist)
  .filter((f) => /^sitemap-\d+\.xml$/.test(f))
  .sort((a, b) => {
    const na = Number(a.match(/^sitemap-(\d+)\.xml$/)[1]);
    const nb = Number(b.match(/^sitemap-(\d+)\.xml$/)[1]);
    return na - nb;
  });

if (chunkFiles.length === 0) {
  console.error("postbuild-sitemap: no sitemap chunks found in dist/");
  process.exit(1);
}

const sitemapXml = join(dist, "sitemap.xml");

function filterNoindex(xml) {
  return xml.replace(/<url>[\s\S]*?<\/url>/g, (urlBlock) => {
    const locMatch = urlBlock.match(/<loc>([^<]+)<\/loc>/);
    if (locMatch && noindexUrls.has(locMatch[1])) return "";
    return urlBlock;
  });
}

if (chunkFiles.length === 1) {
  let content = readFileSync(join(dist, chunkFiles[0]), "utf8");
  content = filterNoindex(content);
  writeFileSync(sitemapXml, content);
  console.log(`postbuild-sitemap: wrote single-urlset sitemap.xml from ${chunkFiles[0]}`);
} else {
  const entries = chunkFiles
    .map((f) => `    <sitemap><loc>${new URL(f, SITE).href}</loc></sitemap>`)
    .join("\n");
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${entries}\n</sitemapindex>\n`;
  writeFileSync(sitemapXml, xml);
  console.log(`postbuild-sitemap: wrote sitemapindex sitemap.xml (${chunkFiles.length} chunks)`);
}

const raw = readFileSync(sitemapXml, "utf8");
if (!/<loc>https:\/\/spielos\.xyz/.test(raw)) {
  console.error("postbuild-sitemap: sitemap.xml missing expected host URLs");
  process.exit(1);
}
console.log("postbuild-sitemap: dist/sitemap.xml OK");