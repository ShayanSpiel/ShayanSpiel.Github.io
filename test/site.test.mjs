import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const root = process.cwd();
const dist = join(root, "dist");
const read = (route) => readFileSync(join(dist, route, "index.html"), "utf8");

test("buyer conversion routes build with lead CTAs", () => {
  const home = read("");
  const services = read("services");
  assert.match(home, /href="\/services\/#agent-briefing/);
  assert.match(services, /agent-briefing/);
});

test("non-indexable utility pages are noindex", () => {
  for (const route of ["use-cases", "contact/thank-you", "spielos-v1"]) {
    assert.match(read(route), /<meta name="robots" content="noindex, follow">/);
  }
});

test("canonical sitemap excludes noindex routes", () => {
  assert.ok(existsSync(join(dist, "sitemap.xml")));
  const sitemap = readFileSync(join(dist, "sitemap.xml"), "utf8");
  for (const route of ["/use-cases/", "/contact/thank-you/", "/spielos-v1/"]) {
    assert.doesNotMatch(sitemap, new RegExp(`https:\\/\\/spielos\\.xyz${route.replaceAll("/", "\\/")}`));
  }
});
