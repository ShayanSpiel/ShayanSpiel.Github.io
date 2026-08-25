#!/usr/bin/env node
import puppeteer from "puppeteer";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const baseUrl = process.env.SPIELOS_AUDIT_URL || "http://127.0.0.1:4321";
const outputDir = process.env.SPIELOS_AUDIT_SCREENSHOTS || "/tmp/spielos-visual-audit";
mkdirSync(outputDir, { recursive: true });

const routes = [
  "/",
  "/fa/",
  "/services/",
  "/solutions/",
  "/solutions/workflows/follow-up-automation/",
  "/solutions/software/codex-automation/",
  "/pricing/",
  "/apply/",
  "/founder/",
  "/notes/ai-war-price-intelligence/",
  "/solutions/ai-departments/design/gallery/",
  "/landing/lead-researcher/",
];
const viewports = [
  { name: "desktop", width: 1440, height: 1000 },
  { name: "mobile", width: 390, height: 844 },
];
const failures = [];
const executablePath = process.env.SPIELOS_AUDIT_CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const browser = await puppeteer.launch({ headless: true, executablePath, args: ["--no-sandbox"] });

try {
  for (const viewport of viewports) {
    for (const route of routes) {
      const page = await browser.newPage();
      await page.setViewport(viewport);
      page.on("pageerror", (error) => failures.push(`${viewport.name} ${route}: ${error.message}`));
      page.on("requestfailed", (request) => {
        if (request.url().startsWith(baseUrl)) failures.push(`${viewport.name} ${route}: failed ${request.url()}`);
      });
      const response = await page.goto(`${baseUrl}${route}`, { waitUntil: "domcontentloaded", timeout: 30_000 });
      const status = response?.status() ?? 0;
      if (status < 200 || status >= 400) failures.push(`${viewport.name} ${route}: HTTP ${status || "unknown"}`);
      await page.evaluate(async () => { await document.fonts.ready; });
      await new Promise((resolve) => setTimeout(resolve, 150));
      const result = await page.evaluate(() => {
        const doc = document.documentElement;
        const missingIcons = [...document.querySelectorAll("i.bx")]
          .filter((icon) => {
            const content = getComputedStyle(icon, "::before").content;
            return content === "none" || content === '""';
          })
          .map((icon) => icon.className);
        return {
          h1: document.querySelectorAll("h1").length,
          main: Boolean(document.querySelector("main")),
          nav: Boolean(document.querySelector("nav")),
          overflow: doc.scrollWidth - doc.clientWidth,
          overflowNodes: [...document.querySelectorAll("body *")]
            .filter((element) => {
              const rect = element.getBoundingClientRect();
              return rect.right > doc.clientWidth + 2 || rect.left < -2;
            })
            .slice(0, 5)
            .map((element) => `${element.tagName.toLowerCase()}.${[...element.classList].slice(0, 3).join(".")}`),
          missingIcons,
          lang: doc.lang,
          dir: doc.dir,
        };
      });
      if (!result.h1 || !result.main || !result.nav) failures.push(`${viewport.name} ${route}: missing primary page structure`);
      if (result.overflow > 2) failures.push(`${viewport.name} ${route}: horizontal overflow ${result.overflow}px (${result.overflowNodes.join(", ")})`);
      if (result.missingIcons.length) failures.push(`${viewport.name} ${route}: missing icon glyphs ${result.missingIcons.join(", ")}`);
      if (route.startsWith("/fa/") && (result.lang !== "fa" || result.dir !== "rtl")) failures.push(`${viewport.name} ${route}: invalid Persian document direction`);
      if (!route.startsWith("/fa/") && (result.lang !== "en" || result.dir !== "ltr")) failures.push(`${viewport.name} ${route}: invalid English document direction`);
      if (["/", "/fa/", "/services/", "/solutions/", "/apply/", "/notes/ai-war-price-intelligence/"].includes(route)) {
        const name = route === "/" ? "home" : route.replace(/^\/|\/$/g, "").replaceAll("/", "-");
        await page.screenshot({ path: join(outputDir, `${name}-${viewport.name}.png`), fullPage: true });
      }
      await page.close();
    }
  }
} finally {
  await browser.close();
}

if (failures.length) {
  console.error(`Visual audit failed (${failures.length}):`);
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}
console.log(`visual-audit: OK — ${routes.length * viewports.length} page/viewport combinations; screenshots in ${outputDir}`);
