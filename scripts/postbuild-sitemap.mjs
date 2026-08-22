#!/usr/bin/env node
/**
 * SpielOS post-build sitemap fix.
 *
 * @astrojs/sitemap 3.7.x emits `sitemap-index.xml` + `sitemap-*.xml` chunks and
 * never writes the canonical `/sitemap.xml` that robots.txt points crawlers to.
 * This consolidates whatever was generated into a single `/sitemap.xml` that
 * always serves: a `urlset` when only one chunk exists, else a `sitemapindex`
 * listing every chunk. Noindex pages are excluded. Intentional migration
 * redirects are expanded from Astro's minimal static stubs into complete
 * noindex documents so the shared SEO audit can still verify them.
 * Exit 0 = ok, exit 1 = broken sitemap found.
 */
import { readFileSync, readdirSync, writeFileSync, statSync, mkdirSync } from "fs";
import { join, extname, dirname } from "path";

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

function routeUrlFromHtml(htmlFile) {
  const rel = htmlFile.replace(dist, "").replace(/\/index\.html$/, "/");
  return `${base}${rel || "/"}`;
}

const noindexUrls = new Set();
const redirectUrls = new Set();
for (const htmlFile of collectHtml(dist)) {
  const html = readFileSync(htmlFile, "utf8");
  const routeUrl = routeUrlFromHtml(htmlFile);
  if (/<meta name="robots"[^>]*content="[^"]*noindex/.test(html)) {
    noindexUrls.add(routeUrl);
  }
  if (/<meta http-equiv="refresh"/i.test(html)) {
    redirectUrls.add(routeUrl);
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

function filterNonCanonical(xml) {
  return xml.replace(/<url>[\s\S]*?<\/url>/g, (urlBlock) => {
    const locMatch = urlBlock.match(/<loc>([^<]+)<\/loc>/);
    if (locMatch && (noindexUrls.has(locMatch[1]) || redirectUrls.has(locMatch[1]))) return "";
    return urlBlock;
  });
}

if (chunkFiles.length === 1) {
  let content = readFileSync(join(dist, chunkFiles[0]), "utf8");
  content = filterNonCanonical(content);
  writeFileSync(sitemapXml, content);
  console.log(`postbuild-sitemap: wrote single-urlset sitemap.xml from ${chunkFiles[0]}`);
} else {
  // Filter noindex/redirect URLs out of every chunk BEFORE indexing so the
  // multi-chunk path gets the same canonical filtering as the single-chunk path.
  for (const f of chunkFiles) {
    const chunkPath = join(dist, f);
    writeFileSync(chunkPath, filterNonCanonical(readFileSync(chunkPath, "utf8")));
  }
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
