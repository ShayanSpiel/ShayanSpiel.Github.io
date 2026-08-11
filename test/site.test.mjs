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

test("live page builds with hero markers and first-20 entries inline", () => {
  const live = read("live");
  const faLive = read("fa/live");

  // Hero and section markers
  assert.match(live, /id="live-hero"/);
  assert.match(live, /id="live-stats"/);
  assert.match(live, /id="live-timeline"/);
  assert.match(live, /id="live-howto"/);
  assert.match(live, /id="live-cta"/);

  // Structured data: ItemList of recent goals
  assert.match(live, /"@type":"ItemList"/);

  // Timeline entries are inline in the static HTML — first 20 guaranteed,
  // the full snapshot rendered server-side for progressive enhancement.
  const snapshot = JSON.parse(readFileSync(join(root, "src/data/live-goals.json"), "utf8"));
  assert.ok(snapshot.goals.length >= 20, "snapshot must hold at least 20 goals");
  const inlineEntries = (live.match(/data-goal-id="/g) || []).length;
  assert.equal(inlineEntries, snapshot.goals.length);
  for (const goal of snapshot.goals.slice(0, 20)) {
    assert.match(live, new RegExp(goal.name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }

  // Filters render with counts
  assert.match(live, /data-filter-type="business"/);
  assert.match(live, /data-filter-status="abandoned"/);

  // FA wrapper builds as a thin RTL page
  assert.match(faLive, /<html lang="fa" dir="rtl"/);
  assert.match(faLive, /id="live-hero"/);
});

test("sitemap contains the live timeline pages", () => {
  const sitemap = readFileSync(join(dist, "sitemap.xml"), "utf8");
  assert.match(sitemap, /https:\/\/spielos\.xyz\/live\//);
  assert.match(sitemap, /https:\/\/spielos\.xyz\/fa\/live\//);
});
