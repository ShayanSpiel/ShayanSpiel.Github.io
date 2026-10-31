#!/usr/bin/env node

/** Generate current Karwise OG artwork from the built public snapshot.
 *
 * The rendered headline and description come from each page's existing
 * og:title and og:description. Page titles and all other copy stay untouched.
 * Redirects, noindex pages, and retired Notes routes are excluded by reading
 * the final `dist/` tree after `build-karwise.mjs` has applied route policy.
 */

import { createHash } from "node:crypto";
import { createServer } from "node:http";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  writeFileSync,
} from "node:fs";
import { execFileSync } from "node:child_process";
import { extname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const PUBLIC = join(ROOT, "public");
const DIST = join(ROOT, "dist");
const TEMPLATE = "/src/og-templates/og-karwise-card.html";
const OUT_DIR = join(PUBLIC, "assets/og/v5");
const MANIFEST_FILE = join(PUBLIC, "assets/og/karwise-cover-manifest.json");
const SITE_ORIGIN = "https://spielos.xyz";
const WIDTH = 1200;
const HEIGHT = 630;
const SYSTEM_BROWSER_CANDIDATES =
  process.platform === "darwin"
    ? [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
      ]
    : [];

const MIME = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".ttf": "font/ttf",
  ".woff2": "font/woff2",
};

function walkHtml(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? walkHtml(path) : path.endsWith(".html") ? [path] : [];
  });
}

function decodeHtml(value) {
  return value
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&nbsp;/g, " ")
    .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)))
    .replace(/&#x([\da-f]+);/gi, (_, code) => String.fromCodePoint(parseInt(code, 16)));
}

function attributes(tag) {
  return Object.fromEntries(
    [...tag.matchAll(/([\w:-]+)\s*=\s*(["'])(.*?)\2/gs)].map((match) => [
      match[1].toLowerCase(),
      decodeHtml(match[3]),
    ]),
  );
}

function tags(html, name) {
  const visibleHtml = html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "");
  return [...visibleHtml.matchAll(new RegExp(`<${name}\\b[^>]*>`, "gi"))].map((match) =>
    attributes(match[0]),
  );
}

function plainText(markup) {
  return decodeHtml(
    markup
      .replace(/<br\s*\/?\s*>/gi, " ")
      .replace(/<[^>]*>/g, " ")
      .replace(/\s+/g, " ")
      .trim(),
  );
}

function routeForFile(file) {
  const local = relative(DIST, file).split(sep).join("/");
  const directory = local.replace(/(?:^|\/)index\.html$/, "");
  return directory ? `/${directory.replace(/^\//, "")}/` : "/";
}

function sourceFileForRoute(route) {
  const path = route.replace(/^\/+|\/+$/g, "");
  return path ? join(PUBLIC, path, "index.html") : join(PUBLIC, "index.html");
}

function artworkTitleSegments(ogTitle, brandName) {
  let segments = ogTitle.split(/\s+\|\s+/).map((segment) => segment.trim()).filter(Boolean);
  if (
    segments.length > 1 &&
    segments.at(-1).toLocaleLowerCase() === brandName.toLocaleLowerCase()
  ) {
    segments.pop();
  }
  if (segments.length > 1) return segments;

  const title = segments[0] || ogTitle;
  const phraseSplit = title.match(/^(.+?[؛;:—–])\s+(.+)$/u);
  if (phraseSplit) return [phraseSplit[1].trim(), phraseSplit[2].trim()];

  const words = title.split(/\s+/).filter(Boolean);
  if (words.length < 2) return [title];
  const splitAt = Math.max(1, Math.floor(words.length / 2));
  return [words.slice(0, splitAt).join(" "), words.slice(splitAt).join(" ")];
}

function getCanonicalPages() {
  if (!existsSync(join(DIST, "sitemap.xml"))) {
    execFileSync(process.execPath, [join(ROOT, "scripts/build-karwise.mjs")], {
      cwd: ROOT,
      stdio: "inherit",
    });
  }

  const pages = [];
  for (const file of walkHtml(DIST)) {
    const html = readFileSync(file, "utf8");
    const metadata = Object.fromEntries(
      tags(html, "meta").map((tag) => [tag.name || tag.property, tag.content]),
    );
    const canonical = tags(html, "link").find((tag) => tag.rel === "canonical")?.href;
    const redirect = tags(html, "meta").some(
      (tag) => tag["http-equiv"]?.toLowerCase() === "refresh",
    );
    const route = routeForFile(file);
    const indexable =
      canonical === `${SITE_ORIGIN}${route}` &&
      !redirect &&
      !metadata.robots?.toLowerCase().includes("noindex");
    if (!indexable) continue;

    const htmlWithoutScripts = html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "");
    const title = plainText(htmlWithoutScripts.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i)?.[1] || "");
    const headingMarkup = htmlWithoutScripts.match(/<h1\b[^>]*>([\s\S]*?)<\/h1>/i)?.[1];
    const locale = attributes(htmlWithoutScripts.match(/<html\b[^>]*>/i)?.[0] || "<html>").lang;
    const ogTitle = metadata["og:title"];
    const description = metadata["og:description"];
    const brandName = metadata["og:site_name"];
    const sourceFile = sourceFileForRoute(route);

    if (!existsSync(sourceFile)) throw new Error(`Canonical page has no public source: ${route}`);
    if (!title || !ogTitle || !description || !brandName || !headingMarkup) {
      throw new Error(`Canonical page is missing title, description, brand, or H1: ${route}`);
    }
    if (locale !== "fa" && locale !== "en") throw new Error(`Unexpected locale on ${route}: ${locale}`);

    const titleSegments = artworkTitleSegments(ogTitle, brandName);

    pages.push({
      route,
      canonical,
      locale,
      sourceFile,
      sourceTitle: title,
      ogTitle,
      description,
      brandName,
      heading: plainText(headingMarkup),
      titleSegments: titleSegments.length ? titleSegments : [ogTitle],
    });
  }

  if (!pages.length) throw new Error("No canonical pages found in dist/. Run the Karwise build first.");
  pages.sort((a, b) => a.canonical.localeCompare(b.canonical));
  return pages;
}

function filenameFor(page) {
  let parts = page.route.split("/").filter(Boolean);
  if (parts[0] === "fa" || parts[0] === "en") parts = parts.slice(1);
  const stem = parts.join("-").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "home";
  return `${stem}-${page.locale}.png`;
}

function startServer() {
  const server = createServer((request, response) => {
    const requestPath = decodeURIComponent(new URL(request.url || "/", "http://127.0.0.1").pathname);
    let file = requestPath.startsWith("/assets/")
      ? join(PUBLIC, requestPath.slice(1))
      : join(ROOT, requestPath.replace(/^\/+/, ""));
    if (file.endsWith(sep)) file = join(file, "index.html");
    file = resolve(file);
    if (!file.startsWith(`${ROOT}${sep}`) || !existsSync(file)) {
      response.writeHead(404).end("Not found");
      return;
    }
    response.writeHead(200, { "Content-Type": MIME[extname(file)] || "application/octet-stream" });
    response.end(readFileSync(file));
  });

  return new Promise((resolveServer, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      resolveServer({ server, origin: `http://127.0.0.1:${address.port}` });
    });
  });
}

function sha256(file) {
  return createHash("sha256").update(readFileSync(file)).digest("hex");
}

function assertPngSize(file) {
  const image = readFileSync(file);
  if (image.length < 24 || image.readUInt32BE(16) !== WIDTH || image.readUInt32BE(20) !== HEIGHT) {
    throw new Error(`Unexpected OG dimensions for ${file}; expected ${WIDTH}x${HEIGHT}`);
  }
}

function updateImageMetadata(html, imageUrl, route) {
  const counts = { og: 0, twitter: 0 };
  const updated = html.replace(
    /<script\b[^>]*>[\s\S]*?<\/script>|<meta\b[^>]*>/gi,
    (tag) => {
      if (/^<script\b/i.test(tag)) return tag;
      const meta = attributes(tag);
      const isOgImage = meta.property?.toLowerCase() === "og:image";
      const isTwitterImage = meta.name?.toLowerCase() === "twitter:image";
      if (!isOgImage && !isTwitterImage) return tag;
      counts[isOgImage ? "og" : "twitter"] += 1;
      return tag.replace(/(\bcontent\s*=\s*)(["'])(.*?)\2/i, (_, prefix, quote) =>
        `${prefix}${quote}${imageUrl}${quote}`,
      );
    },
  );
  if (counts.og !== 1 || counts.twitter !== 1) {
    throw new Error(`${route} must have exactly one OG and one Twitter image tag`);
  }
  return updated;
}

async function main() {
  const pages = getCanonicalPages();
  mkdirSync(OUT_DIR, { recursive: true });
  const { server, origin } = await startServer();
  const executablePath =
    process.env.PUPPETEER_EXECUTABLE_PATH || SYSTEM_BROWSER_CANDIDATES.find(existsSync);
  const browser = await puppeteer.launch({
    headless: true,
    ...(executablePath ? { executablePath } : {}),
  });
  const page = await browser.newPage();
  await page.setViewport({ width: WIDTH, height: HEIGHT, deviceScaleFactor: 1 });
  const records = [];

  try {
    await page.goto(`${origin}${TEMPLATE}`, { waitUntil: "networkidle0", timeout: 30000 });
    for (let index = 0; index < pages.length; index += 1) {
      const item = pages[index];
      const imageName = filenameFor(item);
      const imageFile = join(OUT_DIR, imageName);
      const imagePath = `/assets/og/v5/${imageName}`;
      const data = {
        locale: item.locale,
        eyebrow: item.brandName,
        summary_label: item.locale === "fa" ? "خلاصهٔ صفحه" : "PAGE SUMMARY",
        diagram_heading: item.locale === "fa" ? "نمای کلی" : "AT A GLANCE",
        diagram_note: "",
        diagram_kind: "overview",
        title_lines: item.titleSegments,
        accent_line: item.titleSegments.length > 1 ? 1 : -1,
        supporting_text: item.description,
        canonical: item.canonical,
        url: item.route,
        brand_name: item.brandName,
      };

      await page.evaluate((cover) => window.__applyOg(cover), data);
      await page.waitForFunction(
        () => document.documentElement.dataset.templateReady === "true",
        { timeout: 10000 },
      );
      await page.evaluate(() => document.fonts.ready);
      const fonts = await page.evaluate((locale) => ({
        latin: document.fonts.check('800 76px "Outfit"', "Karwise"),
        persian: locale !== "fa" || document.fonts.check('900 55px "IRANSansX"', "تحول هوش مصنوعی"),
        doran: locale !== "fa" || document.fonts.check('800 56px "Doran"', "آموزش و پیاده‌سازی"),
        logo: Boolean(document.querySelector(".brand-lockup img")?.naturalWidth),
      }), item.locale);
      if (!fonts.latin || !fonts.persian || !fonts.doran || !fonts.logo) {
        throw new Error(`Font or brand asset failed for ${item.route}: ${JSON.stringify(fonts)}`);
      }

      await page.screenshot({ path: imageFile, type: "png" });
      assertPngSize(imageFile);
      const digest = sha256(imageFile);
      const imageUrl = `${SITE_ORIGIN}${imagePath}?v=${digest.slice(0, 12)}`;
      const original = readFileSync(item.sourceFile, "utf8");
      const updated = updateImageMetadata(original, imageUrl, item.route);
      const titleBefore = original.match(/<title\b[^>]*>[\s\S]*?<\/title>/i)?.[0];
      const titleAfter = updated.match(/<title\b[^>]*>[\s\S]*?<\/title>/i)?.[0];
      if (titleBefore !== titleAfter) throw new Error(`Page title changed while updating ${item.route}`);
      writeFileSync(item.sourceFile, updated);

      records.push({
        route: item.route,
        canonical: item.canonical,
        locale: item.locale,
        source_title: item.sourceTitle,
        og_title: item.ogTitle,
        artwork_title: item.titleSegments.join(" | "),
        description: item.description,
        image: imagePath.slice(1),
        image_url: imageUrl,
        sha256: digest,
      });
      process.stdout.write(`\r  [${index + 1}/${pages.length}] ${item.route}               `);
    }
  } finally {
    await browser.close();
    server.close();
  }

  const uniqueImages = new Set(records.map((record) => record.image));
  if (uniqueImages.size !== pages.length) throw new Error("Each canonical page must have its own OG image");

  writeFileSync(
    MANIFEST_FILE,
    `${JSON.stringify(
      {
        version: "karwise-og-v5",
        dimensions: [WIDTH, HEIGHT],
        renderer: "Puppeteer + website design tokens + local production fonts",
        copy_source: "canonical page og:title and og:description; page-title metadata is unchanged",
        pages: records,
      },
      null,
      2,
    )}\n`,
  );
  console.log(`\n  Generated ${records.length} current-page OG images (${WIDTH}x${HEIGHT}).`);
  console.log(`  Retired routes and Notes pages: excluded. Existing assets: preserved.\n`);
}

main().catch((error) => {
  console.error(`\n  OG generation failed: ${error.stack || error.message}`);
  process.exitCode = 1;
});
