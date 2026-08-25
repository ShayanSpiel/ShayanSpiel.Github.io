import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const dist = "dist";
const htmlFiles = [];
(function walk(dir) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) walk(p);
    else if (e.name.endsWith(".html")) htmlFiles.push(p);
  }
})(dist);

function routeExists(target) {
  // target like /foo/ or /foo/bar or /file.ext
  if (target.endsWith("/")) return existsSync(join(dist, target, "index.html"));
  if (/\.[a-z0-9]+$/i.test(target)) return existsSync(join(dist, target));
  return existsSync(join(dist, target, "index.html"));
}

const broken = new Map();
for (const file of htmlFiles) {
  const html = readFileSync(file, "utf8");
  const pageUrl = "/" + file.replace(new RegExp(`^${dist}/?`), "").replace(/index\.html$/, "");
  const refs = [];
  for (const m of html.matchAll(/(?:href|src)="([^"]+)"/g)) refs.push(m[1]);
  for (const m of html.matchAll(/srcset="([^"]+)"/g))
    for (const part of m[1].split(",")) refs.push(part.trim().split(/\s+/)[0]);
  for (const raw of refs) {
    let url = raw.trim();
    if (!url || url.startsWith("#") || /^(mailto|tel|data|javascript):/.test(url)) continue;
    url = url.split("#")[0].split("?")[0];
    if (!url) continue;
    if (/^https?:\/\//.test(url)) {
      // external: only flag same-site absolute URLs
      if (!url.includes("spielos.xyz") && !url.includes("localhost")) continue;
      url = new URL(url).pathname;
    }
    if (!url.startsWith("/")) continue; // relative — resolved against page route
    if (url === "/404" || url === "/404/" || url === "/404.html") continue; // error page, served by host
    const clean = url.replace(/\/+/g, "/");
    if (!routeExists(clean)) {
      if (!broken.has(clean)) broken.set(clean, []);
      broken.get(clean).push(pageUrl);
    }
  }
}
if (broken.size === 0) {
  console.log(`link-check: OK — ${htmlFiles.length} pages scanned, no broken internal references`);
} else {
  console.log(`link-check: ${broken.size} broken targets`);
  for (const [target, pages] of [...broken].sort()) {
    console.log(`  MISSING ${target}  (${pages.length} ref${pages.length > 1 ? "s" : ""}: ${[...new Set(pages)].slice(0, 6).join(", ")}${pages.length > 6 ? " …" : ""})`);
  }
  process.exit(1);
}
