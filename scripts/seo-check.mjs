#!/usr/bin/env node
/**
 * SpielOS SEO check — validates the built site against the SEO invariants
 * defined in .agents/skills/seo/SKILL.md.
 *
 * Usage: npm run seo:check   (runs against dist/)
 * Exit 0 = clean, exit 1 = issues found.
 */
import { readFileSync, readdirSync, statSync } from "fs";
import { join, extname } from "path";

const dist = join(process.cwd(), "dist");
const issues = [];
let okCount = 0;

const check = (cond, label, page = "") => {
  if (cond) okCount++;
  else issues.push(`${page}${label}`);
};

function collectHtml(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) out.push(...collectHtml(p));
    else if (extname(p) === ".html") out.push(p);
  }
  return out;
}

const isRealPage = (path) => {
  const rel = path.replace(dist, "");
  // 301 redirect stubs (posts → notes, shayan → founder)
  if (rel.startsWith("/posts/") || rel === "/posts/index.html") return false;
  if (rel.startsWith("/shayan/")) return false;
  // static assets / legacy noindex pages
  if (rel.startsWith("/assets/")) return false;
  if (rel.startsWith("/SpielOS/")) return false;
  return true;
};

function sentenceLengths(html) {
  const text = html
    .replace(/<script[\s\S]*?<\/script>/g, " ")
    .replace(/<style[\s\S]*?<\/style>/g, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return text
    .split(/[.!?؟]+\s+/)
    .map((s) => s.trim().split(/\s+/).length)
    .filter((n) => n > 0);
}

const pages = collectHtml(dist);
const realPages = pages.filter(isRealPage);

for (const page of realPages) {
  const html = readFileSync(page, "utf8");
  const rel = page.replace(dist, "");
  const isNote = /\/notes\//.test(rel) && !rel.endsWith("/notes/index.html") && !rel.endsWith("/notes/") && rel.endsWith("/index.html") && rel.includes("/notes/") && !rel.startsWith("/fa/notes/");
  const isFa = rel.startsWith("/fa/");

  check(/<title>[^<]{5,120}<\/title>/.test(html), "  missing/invalid <title>", rel);
  check(/<meta name="description"[^>]*content="[^"]{10,}/.test(html), "  missing/invalid description", rel);
  check(/<link rel="canonical"[^>]*href="[^"]+"/.test(html), "  missing canonical", rel);
  check(/<meta name="robots"/.test(html), "  missing robots", rel);
  check(/<meta property="og:title"/.test(html), "  missing og:title", rel);
  check(/<meta property="og:description"/.test(html), "  missing og:description", rel);
  check(/<meta property="og:image"/.test(html), "  missing og:image", rel);
  check(/<meta property="og:type"/.test(html), "  missing og:type", rel);
  check(/<meta name="twitter:card"/.test(html), "  missing twitter:card", rel);
  check(/<link rel="alternate" hreflang="en"/.test(html), "  missing hreflang en", rel);
  check(/<link rel="alternate" hreflang="fa"/.test(html), "  missing hreflang fa", rel);
  check(/<link rel="alternate" hreflang="x-default"/.test(html), "  missing hreflang x-default", rel);

  // Analytics
  check(/google-site-verification/.test(html), "  missing Search Console", rel);
  check(/gtag\('config'/.test(html), "  missing GA4 config", rel);
  check(/googletagmanager\.com\/gtag\/js/.test(html), "  missing gtag.js loader", rel);
  check(/posthog\.init/.test(html), "  missing PostHog init", rel);
  check(/static\/array\.js/.test(html), "  missing PostHog stub", rel);
  check(/requestIdleCallback/.test(html), "  missing deferred loader", rel);

  // Structured data
  const blocks = [...html.matchAll(/<script type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g)];
  check(blocks.length > 0, "  missing JSON-LD", rel);
  blocks.forEach((b, i) => {
    try { JSON.parse(b[1]); }
    catch { check(false, `  invalid JSON-LD block #${i}`, rel); }
  });

  // Readability for note articles (EN + FA)
  if (isNote || (isFa && rel.includes("/notes/") && rel.endsWith("/index.html") && !rel.endsWith("/notes/index.html"))) {
    const lens = sentenceLengths(html);
    const avg = lens.length ? lens.reduce((a, b) => a + b, 0) / lens.length : 0;
    check(avg <= 28, `  avg sentence length ${avg.toFixed(1)} words (>28)`, rel);
  }
}

// Schema coverage expectations per route
const expectSchema = {
  "/index.html": ["Person", "WebSite", "SoftwareApplication", "ItemList", "BreadcrumbList"],
  "/fa/index.html": ["Person", "WebSite", "SoftwareApplication", "ItemList", "BreadcrumbList"],
  "/founder/index.html": ["Person", "BreadcrumbList"],
  "/about/index.html": ["AboutPage", "BreadcrumbList"],
  "/contact/index.html": ["ContactPage", "BreadcrumbList"],
  "/notes/index.html": ["CollectionPage", "BreadcrumbList"],
  "/fa/notes/index.html": ["CollectionPage", "BreadcrumbList"],
};
for (const [route, types] of Object.entries(expectSchema)) {
  const file = join(dist, route);
  if (!exists(file)) { issues.push(`  ${route}: expected page not built`); continue; }
  const html = readFileSync(file, "utf8");
  const blocks = [...html.matchAll(/<script type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g)];
  const present = new Set();
  blocks.forEach((b) => {
    try {
      const data = JSON.parse(b[1]);
      (Array.isArray(data) ? data : [data]).forEach((d) => present.add(d["@type"]));
    } catch {}
  });
  for (const t of types) check(present.has(t), `  missing expected schema ${t}`, route);
}

function exists(p) {
  try { statSync(p); return true; } catch { return false; }
}

console.log(`Checked ${realPages.length} real pages (${pages.length - realPages.length} stubs/assets skipped).`);
console.log(`OK checks: ${okCount}`);
if (issues.length) {
  console.error(`\n${issues.length} SEO issues:\n`);
  for (const i of issues) console.error(" " + i);
  process.exit(1);
}
console.log("All SEO invariants pass.");
