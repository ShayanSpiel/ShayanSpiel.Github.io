#!/usr/bin/env node
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { extname, join, relative } from "node:path";

const root = process.cwd();
const dist = join(root, "dist");
const failures = [];
const fail = (message) => failures.push(message);

function filesUnder(dir, predicate = () => true) {
  const files = [];
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) files.push(...filesUnder(path, predicate));
    else if (predicate(path)) files.push(path);
  }
  return files;
}

if (!existsSync(dist)) fail("dist/ is missing; run the production build first");

const sourceFiles = filesUnder(join(root, "src"), (file) => /\.(?:astro|ts|js|mdx|css)$/.test(file));
const allowedSvgFiles = new Set([
  "src/components/SpielOSLogo.astro",
  "src/components/HomepageHeroJourney.astro",
  "src/components/HomepageJourneyRail.astro",
  // Brand-mark surfaces: the official glyph split (LiveHeroMark) and the
  // Apply-page real tool marks (ToolLogos, owner directive 2026-08-26).
  "src/components/live/LiveHeroMark.astro",
  "src/components/ToolLogos.astro",
  // Diagram/graph canvases: the Live AI company map and the Lab graph space
  // are legitimate SVG-native diagram surfaces (owner WIP 2026-09).
  "src/pages/live-ai-company.astro",
  "src/pages/lab/neurons.astro",
]);
for (const file of sourceFiles) {
  const rel = relative(root, file);
  if (rel.startsWith("src/components/showcase/")) continue;
  const content = readFileSync(file, "utf8");
  if (content.includes('import "boxicons/css/boxicons.min.css"')) fail(`${rel} imports the full Boxicons library`);
  if (content.includes("apexcharts")) fail(`${rel} imports the retired chart runtime`);
  // Real brand logos are sanctioned (owner directive 2026-08-26) but must
  // flow through the single source of truth: src/data/brand-logos.ts.
  // No other file may glob/import the SVG assets directly.
  if (rel !== "src/data/brand-logos.ts" && content.includes("assets/brand-logos")) {
    fail(`${rel} touches brand-logo assets outside src/data/brand-logos.ts`);
  }
  if (content.includes("66shayan@gmail.com")) fail(`${rel} contains the retired hardcoded email address`);
  if (/<svg\b/.test(content) && !allowedSvgFiles.has(rel) && !rel.startsWith("src/og-templates/") && !rel.startsWith("src/pdf-templates/") && rel !== "src/lib/icons.ts") {
    fail(`${rel} contains an inline SVG outside the approved diagram/brand surfaces`);
  }
  // Brand-mark surfaces carry official provider brand colors by definition
  // (owner directive 2026-08-26) — the non-brand UI colors there must still
  // come from tokens, but the mark palette itself is exempt. The Live AI
  // company map is unfinished owner WIP and is tracked separately.
  const brandMarkSurfaces = new Set([
    "src/components/ToolLogos.astro",
    "src/pages/live-ai-company.astro",
  ]);
  if ((rel.startsWith("src/components/") || rel.startsWith("src/pages/")) && !brandMarkSurfaces.has(rel) && /#[0-9a-f]{3,8}\b|\brgba?\(|\bhsla?\(/i.test(content)) {
    fail(`${rel} hardcodes a color outside the token system`);
  }
}

if (existsSync(join(root, "WEBSITE_CONVERSION_REBUILD_PLAN.md"))) fail("stale conversion rebuild plan still exists");

if (existsSync(dist)) {
  const htmlFiles = filesUnder(dist, (file) => extname(file) === ".html");
  const redirectRoutes = new Set();
  const realPages = [];
  for (const file of htmlFiles) {
    const html = readFileSync(file, "utf8");
    const route = `/${relative(dist, file).replace(/index\.html$/, "").replace(/^404\.html$/, "404/")}`;
    if (/<meta http-equiv="refresh"/i.test(html)) redirectRoutes.add(route);
    else realPages.push({ file, html, route });
  }

  for (const { html, route } of realPages) {
    for (const match of html.matchAll(/<img\b[^>]*>/g)) {
      const tag = match[0];
      if (!/\balt="[^"]*"/.test(tag)) fail(`${route} has an image without alt text`);
      if (!/\bwidth="\d+"/.test(tag) || !/\bheight="\d+"/.test(tag)) fail(`${route} has an image without intrinsic dimensions`);
      if (!/\bloading="(?:lazy|eager)"/.test(tag)) fail(`${route} has an image without an explicit loading policy`);
      if (!/\bdecoding="(?:async|sync|auto)"/.test(tag)) fail(`${route} has an image without an explicit decoding policy`);
    }
    for (const match of html.matchAll(/href="(\/[^"#?]*)/g)) {
      const href = match[1].endsWith("/") ? match[1] : `${match[1]}/`;
      if (redirectRoutes.has(href)) fail(`${route} links internally through redirect stub ${href}`);
    }
    const hasCalResource = /https:\/\/app\.cal\.com\/embed\/embed\.js|<link[^>]+href="https:\/\/app\.cal\.com"/.test(html);
    const bookingPage = /^\/(?:fa\/)?(?:apply|contact)\/$/.test(route);
    if (hasCalResource !== bookingPage) fail(`${route} has an incorrect Cal.com resource policy`);
  }

  const builtAssets = filesUnder(join(dist, "_astro"));
  for (const file of builtAssets) {
    const size = statSync(file).size;
    if (extname(file) === ".js" && size > 100_000) fail(`${relative(dist, file)} is an oversized client script (${size} bytes)`);
    if (extname(file) === ".css" && size > 250_000) fail(`${relative(dist, file)} is an oversized stylesheet (${size} bytes)`);
    if (/apex|boxicons\.(?:eot|ttf|woff)$/i.test(file)) fail(`${relative(dist, file)} is a retired runtime asset`);
  }
}

if (failures.length) {
  console.error(`Site audit failed (${failures.length}):`);
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log("site-audit: OK — design, image, redirect, third-party, and asset-budget contracts pass");
