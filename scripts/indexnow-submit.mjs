#!/usr/bin/env node
/**
 * IndexNow bulk submission for SpielOS.
 *
 * Sends every canonical URL from the live sitemap to https://api.indexnow.org/indexnow
 * using the site's IndexNow key. The key file (public/<KEY>.txt) is served at the site
 * root and proves ownership; this script only notifies Bing/IndexNow of URLs.
 *
 * Run AFTER deploy so both the URLs and the key file are live.
 *   node scripts/indexnow-submit.mjs            # live submission
 *   node scripts/indexnow-submit.mjs --dry-run  # collect + print URLs, no POST
 *
 * IndexNow API status codes:
 *   200 / 202 -> accepted
 *   400 -> invalid request (bad key/keyLocation)
 *   403 -> key/file forbidden or host mismatch
 *   422 -> some URLs invalid
 *   429 -> rate limited
 */
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const KEY = "7fa891bc6d8d4e46a848710ea8f65b96";
const HOST = "spielos.xyz";
const KEY_LOCATION = `https://${HOST}/${KEY}.txt`;
const SITEMAP_URL = "https://spielos.xyz/sitemap.xml";
const ENDPOINT = "https://api.indexnow.org/indexnow";
const CHUNK = 5000; // IndexNow allows up to 10,000 URLs per request
const DRY_RUN = process.argv.includes("--dry-run");

async function fetchText(url, retries = 4) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, { redirect: "follow" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.text();
    } catch (err) {
      if (attempt === retries) throw new Error(`GET ${url} failed: ${err.message}`);
      await new Promise((r) => setTimeout(r, attempt * 2000));
    }
  }
}

async function collectUrls() {
  const local = join(process.cwd(), "dist", "sitemap.xml");
  const root = existsSync(local) ? readFileSync(local, "utf8") : await fetchText(SITEMAP_URL);
  const urls = new Set();
  const docs = [root];
  if (/<sitemapindex[\s>]/.test(root)) {
    for (const m of root.matchAll(/<loc>([^<]+)<\/loc>/g)) docs.push(await fetchText(m[1]));
  }
  for (const doc of docs) {
    for (const m of doc.matchAll(/<loc>([^<]+)<\/loc>/g)) urls.add(m[1]);
  }
  return [...urls];
}

async function submitChunk(urlList) {
  const body = JSON.stringify({ host: HOST, key: KEY, keyLocation: KEY_LOCATION, urlList });
  const res = await fetch(ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json; charset=utf-8" },
    body,
  });
  const text = await res.text();
  return { status: res.status, text };
}

async function main() {
  const urls = await collectUrls();
  if (urls.length === 0) {
    console.error("indexnow: no URLs found in sitemap");
    process.exit(1);
  }
  console.log(`indexnow: ${urls.length} URL(s) from ${KEY_LOCATION}`);
  if (DRY_RUN) {
    for (const u of urls) console.log(`  ${u}`);
    console.log("indexnow: dry-run complete (no submission)");
    return;
  }
  let failed = 0;
  for (let i = 0; i < urls.length; i += CHUNK) {
    const chunk = urls.slice(i, i + CHUNK);
    const { status, text } = await submitChunk(chunk);
    if (status === 200 || status === 202) {
      console.log(`indexnow: chunk ${i / CHUNK + 1} accepted (${status}) — ${chunk.length} urls`);
    } else {
      failed++;
      console.error(`indexnow: chunk ${i / CHUNK + 1} rejected (${status}) — ${text}`);
    }
  }
  if (failed > 0) {
    console.error("indexnow: one or more chunks failed");
    process.exit(1);
  }
  console.log("indexnow: all URLs submitted");
}

main().catch((err) => {
  console.error("indexnow:", err.message);
  process.exit(1);
});
