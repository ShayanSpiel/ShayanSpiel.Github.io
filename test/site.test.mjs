import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const root = process.cwd();
const dist = join(root, "dist");
const read = (route) => readFileSync(join(dist, route, "index.html"), "utf8");

const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const BUSINESS_OWNERS = ["director", "email", "outbound"];
const isBusiness = (g) => BUSINESS_OWNERS.includes(g.owner_id);

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

test("live page builds with hero markers, merged status, split timeline, and live status", () => {
  const live = read("live");
  const faLive = read("fa/live");

  // Hero and section markers
  assert.match(live, /id="live-hero"/);
  assert.match(live, /id="live-status-root"/);
  assert.match(live, /id="live-stats"/);
  assert.match(live, /id="live-timeline"/);
  assert.match(live, /id="live-howto"/);
  assert.match(live, /id="live-cta"/);

  // Structured data: ItemList of recent goals
  assert.match(live, /"@type":"ItemList"/);

  // Brand logo tile renders inside the h1 next to the running headline
  const h1 = (live.match(/<h1[^>]*>[\s\S]*?<\/h1>/) || [""])[0];
  assert.match(h1, /bg-panel-raised/);
  assert.match(h1, /<svg/);
  assert.match(h1, /SpielOS is now running SpielOS!/);

  // Hero description: this page is the LIVE operations log (EN page)
  assert.match(live, /LIVE operations log/);

  // The loop box is full-width and carries its marker
  assert.match(live, /data-live-loop/);

  const snapshot = JSON.parse(readFileSync(join(root, "src/data/live-goals.json"), "utf8"));
  assert.ok(snapshot.goals.length >= 15, "snapshot must hold at least 15 goals");

  // Merged status card: state + heartbeat markers, clickable to the timeline
  assert.match(live, /data-live-state="(running|resting)"/);
  assert.match(live, /data-live-state-label/);
  assert.match(live, /id="live-status-root"[^>]*href="#live-timeline"/);
  assert.match(live, /bx-bullseye/);
  assert.match(live, /data-heartbeat-state="(running|resting)"/);
  assert.match(live, /data-heartbeat-goal/);
  assert.match(live, /data-heartbeat-metric/);
  assert.match(live, /data-heartbeat-stage/);
  const heartbeat = snapshot.heartbeat || (snapshot.runtime_state && snapshot.runtime_state.heartbeat) || null;
  if (heartbeat) {
    assert.match(
      live,
      new RegExp(`data-heartbeat-goal="${escapeRegExp(heartbeat.goal_name)}"`),
      "status card must show the active business goal name"
    );
    assert.match(live, new RegExp(`data-heartbeat-stage="${escapeRegExp(heartbeat.stage || "")}"`));
    assert.match(live, /data-heartbeat-state="running"/);
    assert.match(live, /live-hb-icon/, "running status card keeps the heartbeat icon");
  } else {
    assert.match(live, /data-heartbeat-state="resting"/);
    assert.match(live, /live-status-resting/);
  }

  // Two timeline sections: business + improvement, each with its own limit
  const businessAll = snapshot.goals.filter(isBusiness);
  const improvementAll = snapshot.goals.filter((g) => !isBusiness(g));
  assert.ok(businessAll.length > 0, "snapshot must hold business goals");
  assert.ok(improvementAll.length > 0, "snapshot must hold improvement goals");
  assert.match(live, /data-live-section="business"/);
  assert.match(live, /data-live-section="improvement"/);

  const businessInline = Math.min(10, businessAll.length);
  const improvementInline = Math.min(5, improvementAll.length);

  // Inline/hidden split: business entries render first (top of the DOM),
  // then improvement entries; newest-first within each section.
  const inlineIds = [];
  const hiddenIds = [];
  for (const m of live.matchAll(/class="live-entry([^"]*)"[^>]*data-goal-id="([^"]+)"/g)) {
    (m[1].includes("live-entry--hidden") ? hiddenIds : inlineIds).push(m[2]);
  }
  assert.equal(inlineIds.length, businessInline + improvementInline, "business + improvement inline counts");
  assert.equal(hiddenIds.length, snapshot.goals.length - inlineIds.length, "all older entries stay hidden in the DOM");
  assert.equal(inlineIds.length + hiddenIds.length, snapshot.goals.length, "every goal renders exactly once");

  const businessNewest = [...businessAll].sort((a, b) => b.created_at.localeCompare(a.created_at));
  const improvementNewest = [...improvementAll].sort((a, b) => b.created_at.localeCompare(a.created_at));
  assert.deepEqual(
    inlineIds.slice(0, businessInline),
    businessNewest.slice(0, businessInline).map((g) => g.id),
    "business inline entries must be the newest business goals in order"
  );
  assert.deepEqual(
    inlineIds.slice(businessInline),
    improvementNewest.slice(0, improvementInline).map((g) => g.id),
    "improvement inline entries must be the newest improvement goals in order"
  );

  // Each section gets its own centered Show more button when it has hidden entries
  assert.equal(
    (live.match(/id="live-show-more-business"/g) || []).length,
    businessAll.length > 10 ? 1 : 0,
    "business Show more renders only when business goals exceed the inline limit"
  );
  assert.equal(
    (live.match(/id="live-show-more-improvement"/g) || []).length,
    improvementAll.length > 5 ? 1 : 0,
    "improvement Show more renders only when improvement sessions exceed the inline limit"
  );

  // Status-only filter row: no type group, counts and aria-pressed kept
  assert.equal((live.match(/id="live-filters"/g) || []).length, 1);
  assert.doesNotMatch(live, /data-filter-type/, "type filter group must be removed");
  assert.match(live, /data-filter-status="abandoned"/);
  assert.match(live, /aria-pressed="true"/);
  assert.match(live, /aria-pressed="false"/);

  // Roundness contract: no rounded-full pills, no circle node wrappers
  assert.doesNotMatch(live, /rounded-full/);
  assert.doesNotMatch(live, /h-5 w-5 items-center justify-center rounded-full/);

  // Live status chip + client state source
  assert.match(live, /data-live-state="(running|resting)"/);
  assert.match(live, /data-live-state-label/);
  assert.match(live, /id="live-state-i18n"/);

  // dist/live-state.json is copied from public/ with valid state + heartbeat
  const liveStatePath = join(dist, "live-state.json");
  assert.ok(existsSync(liveStatePath), "dist/live-state.json must exist after build");
  const liveState = JSON.parse(readFileSync(liveStatePath, "utf8"));
  assert.ok(liveState.state === "running" || liveState.state === "resting", "state field must be running or resting");
  assert.equal(typeof liveState.last_sync_at, "string");
  assert.ok(liveState.totals && typeof liveState.totals.goals_total === "number");
  assert.ok("heartbeat" in liveState, "live-state.json must carry a heartbeat field");
  if (liveState.heartbeat) {
    assert.equal(typeof liveState.heartbeat.goal_id, "string");
    assert.equal(typeof liveState.heartbeat.goal_name, "string");
    assert.equal(typeof liveState.heartbeat.metric, "string");
    assert.equal(typeof liveState.heartbeat.updated_at, "string");
  }

  // FA wrapper builds as a thin RTL page
  assert.match(faLive, /<html lang="fa" dir="rtl"/);
  assert.match(faLive, /id="live-hero"/);
});

test("sitemap contains the live timeline pages", () => {
  const sitemap = readFileSync(join(dist, "sitemap.xml"), "utf8");
  assert.match(sitemap, /https:\/\/spielos\.xyz\/live\//);
  assert.match(sitemap, /https:\/\/spielos\.xyz\/fa\/live\//);
});
