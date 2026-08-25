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
]);
for (const file of sourceFiles) {
  const rel = relative(root, file);
  if (rel.startsWith("src/components/showcase/")) continue;
  const content = readFileSync(file, "utf8");
  if (content.includes('import "boxicons/css/boxicons.min.css"')) fail(`${rel} imports the full Boxicons library`);
  if (content.includes("apexcharts")) fail(`${rel} imports the retired chart runtime`);
  if (content.includes("assets/brand-logos")) fail(`${rel} references retired inline brand-logo assets`);
  if (content.includes("66shayan@gmail.com")) fail(`${rel} contains the retired hardcoded email address`);
  if (/<svg\b/.test(content) && !allowedSvgFiles.has(rel) && !rel.startsWith("src/og-templates/") && !rel.startsWith("src/pdf-templates/") && rel !== "src/lib/icons.ts") {
    fail(`${rel} contains an inline SVG outside the approved diagram/brand surfaces`);
  }
  if ((rel.startsWith("src/components/") || rel.startsWith("src/pages/")) && /#[0-9a-f]{3,8}\b|\brgba?\(|\bhsla?\(/i.test(content)) {
    fail(`${rel} hardcodes a color outside the token system`);
  }
}

if (existsSync(join(root, "src/assets/brand-logos")) && readdirSync(join(root, "src/assets/brand-logos")).length) {
  fail("src/assets/brand-logos still contains orphaned assets");
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
