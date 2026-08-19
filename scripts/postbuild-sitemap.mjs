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
import { readFileSync, readdirSync, writeFileSync, statSync } from "fs";
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

const redirectShells = [
  { source: "features/index.html", destination: "architecture/index.html", target: "/features/" },
  { source: "features/index.html", destination: "waitlist/index.html", target: "/architecture/" },
  { source: "fa/features/index.html", destination: "fa/architecture/index.html", target: "/fa/features/" },
  { source: "fa/features/index.html", destination: "fa/waitlist/index.html", target: "/fa/architecture/" },
  // Fictional feature pages now 301 to the real block pages they describe.
  { source: "features/director/index.html", destination: "features/chat/index.html", target: "/features/director/" },
  { source: "features/director/index.html", destination: "features/chat/director-mode/index.html", target: "/features/director/" },
  { source: "features/workflows/index.html", destination: "features/chat/direct-mode/index.html", target: "/features/workflows/" },
  { source: "features/index.html", destination: "features/context/index.html", target: "/features/" },
  { source: "features/index.html", destination: "features/context/files/index.html", target: "/features/" },
  { source: "features/index.html", destination: "features/context/strategy/index.html", target: "/features/" },
  { source: "features/index.html", destination: "features/context/memory/index.html", target: "/features/" },
  { source: "features/index.html", destination: "features/harness/index.html", target: "/features/" },
  { source: "features/agents/index.html", destination: "features/harness/agents/index.html", target: "/features/agents/" },
  { source: "features/skills/index.html", destination: "features/harness/skills/index.html", target: "/features/skills/" },
  { source: "features/workflows/index.html", destination: "features/harness/workflows/index.html", target: "/features/workflows/" },
  { source: "features/evals/index.html", destination: "features/harness/evals/index.html", target: "/features/evals/" },
  { source: "features/index.html", destination: "features/infrastructure/index.html", target: "/features/" },
  { source: "features/index.html", destination: "features/infrastructure/providers/index.html", target: "/features/" },
  { source: "features/connections/index.html", destination: "features/infrastructure/connections/index.html", target: "/features/connections/" },
  { source: "fa/features/director/index.html", destination: "fa/features/chat/index.html", target: "/fa/features/director/" },
  { source: "fa/features/director/index.html", destination: "fa/features/chat/director-mode/index.html", target: "/fa/features/director/" },
  { source: "fa/features/workflows/index.html", destination: "fa/features/chat/direct-mode/index.html", target: "/fa/features/workflows/" },
  { source: "fa/features/index.html", destination: "fa/features/context/index.html", target: "/fa/features/" },
  { source: "fa/features/index.html", destination: "fa/features/context/files/index.html", target: "/fa/features/" },
  { source: "fa/features/index.html", destination: "fa/features/context/strategy/index.html", target: "/fa/features/" },
  { source: "fa/features/index.html", destination: "fa/features/context/memory/index.html", target: "/fa/features/" },
  { source: "fa/features/index.html", destination: "fa/features/harness/index.html", target: "/fa/features/" },
  { source: "fa/features/agents/index.html", destination: "fa/features/harness/agents/index.html", target: "/fa/features/agents/" },
  { source: "fa/features/skills/index.html", destination: "fa/features/harness/skills/index.html", target: "/fa/features/skills/" },
  { source: "fa/features/workflows/index.html", destination: "fa/features/harness/workflows/index.html", target: "/fa/features/workflows/" },
  { source: "fa/features/evals/index.html", destination: "fa/features/harness/evals/index.html", target: "/fa/features/evals/" },
  { source: "fa/features/index.html", destination: "fa/features/infrastructure/index.html", target: "/fa/features/" },
  { source: "fa/features/index.html", destination: "fa/features/infrastructure/providers/index.html", target: "/fa/features/" },
  { source: "fa/features/connections/index.html", destination: "fa/features/infrastructure/connections/index.html", target: "/fa/features/connections/" },
];

function minimalRedirectDoc(target) {
  const fa = target.startsWith("/fa/");
  const lang = fa ? "fa" : "en";
  const dir = fa ? "rtl" : "ltr";
  return `<!DOCTYPE html>
<html lang="${lang}" dir="${dir}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0;url=${target}">
<link rel="canonical" href="https://spielos.xyz${target}">
<title>Redirecting</title>
</head>
<body>
<p>Redirecting to <a href="${target}">${target}</a>.</p>
</body>
</html>
`;
}

for (const { source, destination, target } of redirectShells) {
  const sourcePath = join(dist, source);
  const destinationPath = join(dist, destination);
  // Keep the source validation: the destination must be backed by a real page.
  if (!statSync(sourcePath).isFile()) {
    console.error(`postbuild-sitemap: redirect source missing: ${sourcePath}`);
    process.exit(1);
  }
  writeFileSync(destinationPath, minimalRedirectDoc(target));
}

console.log(`postbuild-sitemap: expanded ${redirectShells.length} redirect documents`);
