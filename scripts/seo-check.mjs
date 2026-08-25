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
const SITE = "https://spielos.xyz";

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

function routeFromFile(file) {
  const rel = file.replace(dist, "").replace(/\/index\.html$/, "/");
  if (rel === "/404.html") return "/404/";
  return rel || "/";
}

function meta(html, pattern) {
  return html.match(pattern)?.[1]?.trim() || "";
}

const isRealPage = (path) => {
  const rel = path.replace(dist, "");
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
const redirectPages = new Set(pages.filter((page) => /<meta http-equiv="refresh"/i.test(readFileSync(page, "utf8"))));
const realPages = pages.filter((page) => isRealPage(page) && !redirectPages.has(page));
const routeSet = new Set(realPages.map(routeFromFile));
const pageMeta = new Map();
const noindexRoutes = new Set();

for (const page of realPages) {
  const html = readFileSync(page, "utf8");
  const rel = page.replace(dist, "");
  const isNote = /\/notes\//.test(rel) && !rel.endsWith("/notes/index.html") && !rel.endsWith("/notes/") && rel.endsWith("/index.html");

  check(/<title>[^<]{5,120}<\/title>/.test(html), "  missing/invalid <title>", rel);
  check(/<meta name="description"[^>]*content="[^"]{10,}/.test(html), "  missing/invalid description", rel);
  check(/<link rel="canonical"[^>]*href="[^"]+"/.test(html), "  missing canonical", rel);
  check(/<meta name="robots"/.test(html), "  missing robots", rel);
  check(/<meta property="og:title"/.test(html), "  missing og:title", rel);
  check(/<meta property="og:description"/.test(html), "  missing og:description", rel);
  check(/<meta property="og:image"/.test(html), "  missing og:image", rel);
  check(/<meta property="og:type"/.test(html), "  missing og:type", rel);
  check(/<meta name="twitter:card"/.test(html), "  missing twitter:card", rel);
  const pageIsNoindex = /<meta name="robots"[^>]*content="[^"]*noindex/i.test(html);
  if (!pageIsNoindex) {
    check(/<link rel="alternate" hreflang="en"/.test(html), "  missing hreflang en", rel);
    check(/<link rel="alternate" hreflang="fa"/.test(html), "  missing hreflang fa", rel);
    check(/<link rel="alternate" hreflang="x-default"/.test(html), "  missing hreflang x-default", rel);
  }

  const route = routeFromFile(page);
  const title = meta(html, /<title>([^<]+)<\/title>/i);
  const description = meta(html, /<meta name="description"[^>]*content="([^"]*)"/i);
  const canonical = meta(html, /<link rel="canonical"[^>]*href="([^"]+)"/i);
  const robots = meta(html, /<meta name="robots"[^>]*content="([^"]*)"/i);
  pageMeta.set(route, { html, title, description, canonical, robots });
  if (robots.includes("noindex")) noindexRoutes.add(route);

  check(canonical.startsWith(SITE), "  canonical is not an absolute site URL", rel);
  if (canonical.startsWith(SITE) && !robots.includes("noindex")) {
    const canonicalPath = new URL(canonical).pathname;
    check(routeSet.has(canonicalPath), `  canonical target is not a built page: ${canonicalPath}`, rel);
  }

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
  const schemaNodes = [];
  blocks.forEach((b, i) => {
    try { schemaNodes.push(JSON.parse(b[1])); }
    catch { check(false, `  invalid JSON-LD block #${i}`, rel); }
  });
  const ids = new Set();
  const refs = new Set();
  const walkSchema = (value) => {
    if (!value || typeof value !== "object") return;
    if (typeof value["@id"] === "string") {
      if (Object.keys(value).length === 1) refs.add(value["@id"]);
      else ids.add(value["@id"]);
    }
    Object.values(value).forEach(walkSchema);
  };
  schemaNodes.forEach(walkSchema);
  for (const ref of refs) {
    if (ref.startsWith(`${SITE}/#`) && !ids.has(ref)) issues.push(`${rel}  unresolved JSON-LD @id reference: ${ref}`);
  }

  // Readability for note articles (EN + FA)
  if (isNote) {
    const lens = sentenceLengths(html);
    const avg = lens.length ? lens.reduce((a, b) => a + b, 0) / lens.length : 0;
    check(avg <= 28, `  avg sentence length ${avg.toFixed(1)} words (>28)`, rel);
  }
}

function checkUnique(field, label) {
  const seen = new Map();
  for (const [route, values] of pageMeta) {
    if (!values[field] || values.robots.includes("noindex")) continue;
    const routes = seen.get(values[field]) || [];
    routes.push(route);
    seen.set(values[field], routes);
  }
  for (const [value, routes] of seen) {
    if (routes.length > 1) issues.push(`  duplicate ${label} (${JSON.stringify(value)}): ${routes.join(", ")}`);
  }
}

checkUnique("title", "title");
checkUnique("description", "description");

for (const [route, values] of pageMeta) {
  if (values.robots.includes("noindex")) continue;
  const alternateMap = new Map();
  for (const match of values.html.matchAll(/<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"/g)) {
    alternateMap.set(match[1], match[2]);
  }
  for (const [lang, href] of alternateMap) {
    if (!href.startsWith(SITE)) {
      issues.push(`  ${route} hreflang ${lang} is not an absolute site URL`);
      continue;
    }
    const targetRoute = new URL(href).pathname;
    const target = pageMeta.get(targetRoute);
    if (!target) {
      issues.push(`  ${route} hreflang ${lang} target is not a built page: ${targetRoute}`);
      continue;
    }
    if (target.robots.includes("noindex")) issues.push(`  ${route} hreflang ${lang} points to noindex page: ${targetRoute}`);
    const reciprocal = [...target.html.matchAll(/<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"/g)]
      .some((match) => new URL(match[2]).pathname === route);
    if (!reciprocal) issues.push(`  ${route} hreflang ${lang} is not reciprocal with ${targetRoute}`);
  }
}

const sitemap = exists(join(dist, "sitemap.xml")) ? readFileSync(join(dist, "sitemap.xml"), "utf8") : "";
check(Boolean(sitemap), "  missing sitemap.xml");
for (const match of sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)) {
  const url = match[1];
  if (!url.startsWith(SITE)) {
    issues.push(`  sitemap URL has wrong host: ${url}`);
    continue;
  }
  const route = new URL(url).pathname;
  check(!noindexRoutes.has(route), `  sitemap contains noindex route: ${route}`);
  check(routeSet.has(route), `  sitemap contains route that is not a built page: ${route}`);
}

for (const [route, values] of pageMeta) {
  if (values.robots.includes("noindex")) continue;
  check(sitemap.includes(`<loc>${SITE}${route}</loc>`), `  indexable route missing from sitemap: ${route}`);
  for (const match of values.html.matchAll(/href="(\/[^"#?]*)[^" ]*"/g)) {
    const href = match[1];
    if (href.startsWith("/assets/") || href.startsWith("/_astro/") || href === "/feed.xml" || href === "/robots.txt" || href === "/humans.txt" || href === "/site.webmanifest" || href.endsWith(".xml")) continue;
    const targetRoute = href.endsWith("/") ? href : `${href}/`;
    if (!routeSet.has(targetRoute)) issues.push(`  ${route} links to missing internal route: ${href}`);
  }
}

// Schema coverage expectations per route
const expectSchema = {
  "/index.html": ["Organization", "Person", "WebSite", "SoftwareApplication", "BreadcrumbList"],
  "/fa/index.html": ["Organization", "Person", "WebSite", "SoftwareApplication", "BreadcrumbList"],
  "/founder/index.html": ["Person", "BreadcrumbList"],
  "/contact/index.html": ["BreadcrumbList"],
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
      const collectTypes = (value) => {
        if (!value || typeof value !== "object") return;
        if (typeof value["@type"] === "string") present.add(value["@type"]);
        if (Array.isArray(value["@type"])) value["@type"].forEach((type) => present.add(type));
        Object.values(value).forEach(collectTypes);
      };
      collectTypes(data);
    } catch {}
  });
  for (const t of types) check(present.has(t), `  missing expected schema ${t}`, route);
}

function exists(p) {
  try { statSync(p); return true; } catch { return false; }
}

console.log(`Checked ${realPages.length} indexable/noindex pages (${redirectPages.size} redirect stubs skipped).`);
console.log(`OK checks: ${okCount}`);
if (issues.length) {
  console.error(`\n${issues.length} SEO issues:\n`);
  for (const i of issues) console.error(" " + i);
  process.exit(1);
}
console.log("All SEO invariants pass.");
