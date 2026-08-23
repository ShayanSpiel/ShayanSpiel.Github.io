import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const root = process.cwd();
const dist = join(root, "dist");
const read = (route) => readFileSync(join(dist, route, "index.html"), "utf8");

// Owner directive 2026-08-23: icon-only Cal booking triggers are sanctioned
// ONLY as a secondary action on the Contact flow and in the Apply "Not sure?"
// section — everywhere else the funnel stays Apply-first.
const CAL_ALLOWED_ROUTES = new Set(["contact", "fa/contact", "apply", "fa/apply"]);
const calTriggerCount = (html) => (html.match(/<button[^>]*data-cal-link=/g) || []).length;

test("core conversion routes build in English and Persian", () => {
  const enRoutes = ["", "services", "services/agent-brief", "features", "live", "pricing", "apply", "contact", ...["director", "departments", "workflows", "agents", "skills", "evals", "connections", "artifacts"].map((b) => `features/${b}`)];
  const faRoutes = ["fa", "fa/services", "fa/services/agent-brief", "fa/features", "fa/live", "fa/pricing", "fa/apply", "fa/contact", ...["director", "departments", "workflows", "agents", "skills", "evals", "connections", "artifacts"].map((b) => `fa/features/${b}`)];
  for (const route of [...enRoutes, ...faRoutes]) {
    assert.ok(existsSync(join(dist, route, "index.html")), `${route || "/"} must build`);
  }
  for (const route of faRoutes) {
    assert.match(read(route), /<html lang="fa" dir="rtl"/);
  }
});

test("navigation exposes the fixed information architecture and the Apply CTA", () => {
  const en = read("");
  const fa = read("fa");
  for (const href of ["/services/", "/pricing/", "/features/", "/live/", "/notes/", "/founder/", "/apply/"]) assert.match(en, new RegExp(`href="${href}"`));
  for (const href of ["/fa/services/", "/fa/pricing/", "/fa/features/", "/fa/live/", "/fa/notes/", "/fa/founder/", "/fa/apply/"]) assert.match(fa, new RegExp(`href="${href}"`));
  for (const html of [en, fa]) {
    // Owner directive 2026-08-22: Apply-first funnel; the navbar CTA is the
    // tracked Apply link, never a booking trigger or a /book/ navigation.
    assert.match(html, /data-cta-location="nav"/, "the primary navbar CTA must be the tracked Apply funnel link");
    assert.doesNotMatch(html, /<button[^>]*data-cal-link=/, "no booking trigger may appear outside the Contact and Apply flows");
    assert.doesNotMatch(html, /href="\/book\/"/, "no CTA may navigate to /book/");
  }
});

test("home has valid buyer links and the required schema types", () => {
  for (const route of ["", "fa"]) {
    const html = read(route);
    assert.doesNotMatch(html, /href="[^"]*\/notes\/\//);
    for (const type of ["Person", "WebSite", "SoftwareApplication", "BreadcrumbList"]) {
      assert.match(html, new RegExp(`"@type":"${type}"`));
    }
  }
});

test("Features presents the canonical loop and the company tree with Evals", () => {
  const en = read("features");
  const fa = read("fa/features");
  const loopLabels = ["Goal", "Observe", "Decide", "Act", "Evaluate"];
  const mapLabels = ["Department", "Workflow", "Agent", "Skill", "Connection", "Artifact", "Evals"];
  const treeLabels = [["Director", "director"], ["Departments", "departments"], ["Workflows", "workflows"], ["Agents", "agents"], ["Skills", "skills"], ["Evals", "evals"], ["Connections", "connections"], ["Artifacts", "artifacts"]];
  for (const label of [...loopLabels, ...mapLabels]) {
    assert.match(en, new RegExp(`>\s*${label}\s*<`));
  }
  for (const [label, slug] of treeLabels) {
    assert.match(en, new RegExp(`>\s*${label}\s*<`));
    assert.match(en, new RegExp(`href="/features/${slug}/"`));
  }
  assert.match(en, /assets\/og\/features\.png/);
  assert.match(en, /href="\/live\/"/);
  assert.match(en, /href="[^"]*\/apply\//, "Features must route conversion intent to the Apply funnel");
  assert.match(fa, /هدف/);
  assert.match(fa, /دپارتمان/);
  assert.match(fa, /ورک‌فلو/);
  assert.match(fa, /ارزیابی‌ها/);
});

test("sitemap includes localized core pages and excludes redirects and noindex details", () => {
  const sitemap = readFileSync(join(dist, "sitemap.xml"), "utf8");
  const blocks = ["director", "departments", "workflows", "agents", "skills", "evals", "connections", "artifacts"];
  const included = ["/apply/", "/fa/apply/", "/pricing/", "/fa/pricing/", "/contact/", "/fa/contact/", "/features/", "/fa/features/", "/live/", "/fa/live/", "/services/", "/fa/services/", ...blocks.map((b) => `/features/${b}/`), ...blocks.map((b) => `/fa/features/${b}/`)];
  for (const route of included) {
    assert.match(sitemap, new RegExp(`https:\\/\\/spielos\\.xyz${route.replaceAll("/", "\\/")}`), `${route} must be in the sitemap`);
  }
  // Only genuinely archived/noindex surfaces stay out of the sitemap.
  for (const route of ["/spielos-v1/"]) {
    assert.doesNotMatch(sitemap, new RegExp(`https:\\/\\/spielos\\.xyz${route.replaceAll("/", "\\/")}`), `${route} must not be in the sitemap`);
  }
});

test("Agent Brief stays an informational page routed into the Apply funnel", () => {
  for (const route of ["services/agent-brief", "fa/services/agent-brief"]) {
    const page = read(route);
    assert.match(page, /brief-rail/, `${route} must keep the brief framework rail`);
    assert.match(page, /href="[^"]*\/apply\//, `${route} must route conversion intent to the Apply funnel`);
    assert.doesNotMatch(page, /<form[^>]*method="post"/, `${route} must not contain a request form`);
    assert.doesNotMatch(page, /id="request"/, `${route} must not contain the retired #request section`);
    assert.equal(calTriggerCount(page), 0, `${route} must not carry booking triggers`);
  }
  assert.ok(!existsSync(join(root, "src/components/AgentBriefForm.astro")), "AgentBriefForm must be removed");
  assert.ok(!existsSync(join(root, "src/components/ContactModal.astro")), "ContactModal must be removed");
});

test("Live leads with active business work, north star, hierarchy, and visible self-improvement", () => {
  const en = read("live");
  const fa = read("fa/live");
  const snapshot = JSON.parse(readFileSync(join(root, "src/data/live-goals.json"), "utf8"));
  const byId = new Map(snapshot.goals.map((g) => [g.id, g]));
  for (const id of ["live-status-root", "live-northstar", "live-model", "live-stats", "live-howto", "live-timeline", "live-improvement"]) {
    assert.match(en, new RegExp(`id="${id}"`), `${id} must remain part of the Live experience`);
  }
  assert.match(en, /live-hb-ring/);
  assert.match(en, /loop-rail/);
  assert.match(en, /live-business-timeline/);
  assert.match(en, /id="live-company-view"/);
  assert.match(en, /aria-labelledby="business-work-heading"/);
  assert.match(en, /data-live-system-details/);
  // Self-improvement is a full section now, never a collapsed details.
  assert.match(en, /<section[^>]*data-improvement-section/);
  assert.doesNotMatch(en, /<details[^>]*data-improvement-section/);
  // Heartbeat card is ONE clickable card: centered north star, magical
  // heartbeat, View Activity on the right of the same line. No system-details
  // block, no running/resting chip, no last-activity line.
  const cardStart = en.indexOf('id="live-status-root"');
  const cardEnd = en.indexOf('<section id="live-model"');
  const card = en.slice(cardStart, cardEnd);
  assert.ok(cardStart !== -1 && cardEnd !== -1, "heartbeat card region must exist");
  assert.match(card, /data-live-card-link/);
  assert.match(card, /href="#live-timeline"/);
  assert.match(card, /id="live-northstar"[^>]*text-center/);
  assert.match(card, /data-live-view-activity/);
  assert.match(card, /data-live-view-activity[^>]*ms-auto/);
  assert.doesNotMatch(card, /data-live-system-details/, "heartbeat card must not carry collapsed system details");
  assert.doesNotMatch(card, /live-status-state-label-text|data-live-state-label/, "state chip removed from heartbeat card");
  assert.doesNotMatch(card, /live-status-activity/, "last-activity line removed from heartbeat card");
  assert.match(card, /View Activity/);
  // Hierarchy and load-more behavior are part of the timeline surface.
  assert.match(en, /data-live-child/);
  assert.match(en, /data-live-load-more="business"/);
  assert.match(en, /data-live-load-more="improvement"/);
  assert.match(en, /Still being measured/);
  assert.match(fa, /هنوز در حال اندازه‌گیریه/);
  assert.match(fa, /مشاهده فعالیت/);

  // Contract: raw technical metric strings may only live inside the
  // collapsed `<details data-live-system-details>` block -- never in the open
  // page. Strip those details and assert the open page stays clean, so live
  // data can honestly advance to any current run (including system repairs).
  for (const html of [en, fa]) {
    const open = html.replace(/<details\b[^>]*data-live-system-details[\s\S]*?<\/details>/g, "");
    assert.doesNotMatch(open, /acceptance_tests_passed|achieved_children|all_children_achieved/, "technical metric strings only inside collapsed system details");
  }
  // The heartbeat card shows human copy, never the raw canonical goal name or
  // a raw stage chip as the visible heading. Assertions are structural so the
  // live daemon can advance the heartbeat without flaking the test.
  const heartbeat = snapshot.runtime_state && snapshot.runtime_state.heartbeat;
  if (heartbeat) {
    const goal = byId.get(heartbeat.goal_id);
    const visibleTitle = (en.match(/data-heartbeat-goal="([^"]*)"/) || [])[1];
    const allowedTitles = new Set([
      "Working toward the next company goal",
      "Improving how SpielOS works",
    ]);
    for (const g of snapshot.goals) {
      if (g.display_title) allowedTitles.add(g.display_title);
      if (g.display_title_fa) allowedTitles.add(g.display_title_fa);
    }
    assert.ok(allowedTitles.has(visibleTitle), "heartbeat heading must be a human phrase or public copy");
    if (goal) {
      assert.notEqual(visibleTitle, goal.name, "raw canonical goal name must never be the heartbeat heading");
    }
    const visibleMetric = (en.match(/data-heartbeat-metric="([^"]*)"/) || [])[1];
    const userMetricLabels = ["Reply Rate", "Booked calls", "Published items"];
    assert.ok(
      !visibleMetric || userMetricLabels.some((l) => visibleMetric.startsWith(l)) || (goal && (goal.business_value || goal.business_value_fa)),
      "visible heartbeat sub-line must be a user-facing metric or public business value"
    );
  }

  // Recency: the timeline stamps and orders cards by the freshest activity in
  // each goal subtree (children included), never the stale goal-row time.
  // These assertions are deliberately structural (not exact timestamps): the
  // live runner advances cycles, so the built page and the regenerated
  // snapshot can differ by seconds while the invariant still holds.
  // A parent whose children ran today must show a fresher Updated stamp than
  // its own goal-row timestamp, and its subtree must really be freshest.
  const campaign = byId.get("goal-email-campaign-20260810");
  if (campaign) {
    const kidsLatest = snapshot.goals
      .filter((g) => g.parent_id === campaign.id)
      .map((k) => k.latest_activity_at || k.updated_at)
      .filter(Boolean);
    const subtreeFresh = (kidsLatest.length ? [...kidsLatest, campaign.latest_activity_at, campaign.updated_at].filter(Boolean).sort().pop() : campaign.latest_activity_at);
    assert.ok(subtreeFresh && subtreeFresh > campaign.updated_at, "snapshot must propagate freshest subtree activity to parents");
    const cardStart = en.indexOf('data-live-parent-id="goal-email-campaign-20260810"');
    const campaignCard = en.slice(cardStart, en.indexOf("</article>", cardStart));
    // The built card's stamp must NOT be the stale goal-row time; it must be
    // today's subtree activity (the day the children actually ran).
    assert.doesNotMatch(campaignCard, new RegExp(`<time datetime="${campaign.updated_at}"`), "stale goal-row time must not drive the parent Updated stamp");
    assert.match(campaignCard, new RegExp(`<time datetime="${subtreeFresh.slice(0, 10)}T`), "parent Updated stamp must reflect the freshest subtree activity day");
  }

  // Ordering: the freshest-subtree business parent must rank before a goal
  // whose own row is newer but whose subtree has been idle.
  const campaignIdx = en.indexOf('data-live-parent-id="goal-email-campaign-20260810"');
  const contentIdx = en.indexOf('data-live-parent-id="goal-content-batch04-package-v1-20260817"');
  if (campaignIdx !== -1 && contentIdx !== -1) {
    assert.ok(campaignIdx < contentIdx, "freshest-subtree parent must rank above older business goals");
  }
});

test("conversion pages funnel through Apply; Cal is scoped to Contact + Apply secondaries", () => {
  for (const route of ["", "fa", "services", "fa/services", "features", "pricing", "fa/pricing", "services/agent-brief", "contact", "fa/contact", "apply", "fa/apply", "features/director"]) {
    const page = read(route);
    // Owner directive 2026-08-22: every page carries at least one tracked
    // Apply funnel CTA; clicks fire apply_cta_clicked via BaseLayout.
    assert.match(page, /href="[^"]*\/apply\//, `${route} must carry at least one Apply funnel CTA`);
    assert.match(page, /data-cta-location=/, `${route} Apply CTAs must record their location`);
    if (!CAL_ALLOWED_ROUTES.has(route)) {
      assert.equal(calTriggerCount(page), 0, `${route} must not reintroduce Cal booking triggers outside Contact/Apply`);
    } else {
      // Owner directive 2026-08-23: exactly one icon-only secondary call CTA.
      assert.equal(calTriggerCount(page), 1, `${route} may carry exactly one icon-only booking trigger`);
      assert.doesNotMatch(page, /href="\/book\/"/, `${route} must not navigate to /book/`);
    }
    assert.doesNotMatch(page, /data-open-contact-modal/, `${route} must not wire the retired contact modal`);
  }
  // The Apply wizard itself stays the primary action on the Apply page: the
  // free-review form anchor exists beside any optional call trigger.
  for (const route of ["apply", "fa/apply"]) {
    assert.match(read(route), /id="free-review"/, `${route} must keep the free-review wizard`);
  }
});

test("BaseLayout wires apply_cta_clicked from data-cta-location attributes", () => {
  const baseLayout = readFileSync(join(root, "src/layouts/BaseLayout.astro"), "utf8");
  assert.match(baseLayout, /apply_cta_clicked/, "the funnel click event must be implemented");
  assert.match(baseLayout, /data-cta-location/, "CTA locations must be read from the attribute");
  assert.match(baseLayout, /location:\s*link\.getAttribute\('data-cta-location'\)/, "the event payload must carry the CTA location");
});

test("conversion pages preserve the distinctive grid, light, and connected-progress language", () => {
  for (const route of ["", "services", "services/agent-brief", "features", "live"]) {
    const html = read(route);
    assert.match(html, /hero-grid/);
    assert.match(html, /text-primary/);
  }
  assert.match(read(""), /homepage-hero-journey/);
  assert.match(read("services"), /deal-canvas/);
  assert.match(read("services/agent-brief"), /brief-rail/);
  assert.match(read("features"), /department-canvas/);
});

test("features design language: composed canvases, per-block color identity, and step rails render EN+FA", () => {
  const blocks = ["director", "departments", "workflows", "agents", "skills", "evals", "connections", "artifacts"];
  const hub = read("features");
  // Hub lower sections are composed canvases with connector rails, not flat cards
  assert.match(hub, /tree-canvas/);
  assert.match(hub, /tree-rail/);
  assert.match(hub, /control-canvas/);
  assert.match(hub, /control-rail/);
  assert.match(hub, /example-canvas/);
  assert.match(hub, /example-rail/);
  // Per-block color identity on the tree cards (incl. the info color that Tailwind never emits)
  assert.match(hub, /text-info/);
  assert.match(hub, /bg-info-soft/);
  assert.match(hub, /border-info\/30/);
  assert.match(hub, /border-primary\/30/);
  // Block pages: composed canvas + step rail on every real block, EN and FA
  for (const b of blocks) {
    const en = read(`features/${b}`);
    const fa = read(`fa/features/${b}`);
    assert.match(en, /block-canvas/);
    assert.match(en, /block-rail/);
    assert.match(fa, /block-canvas/);
    assert.match(fa, /block-rail/);
  }
  // The tinted border utilities exist in the rendered page styles (Astro inlines
  // page-global styles into the HTML, so assert against the built markup).
  assert.match(hub, /border-primary\\\/30\{border-color:color-mix/);
  assert.match(hub, /border-info\\\/30\{border-color:color-mix/);
  assert.match(hub, /\.text-info\{color:var\(--info\)/);
  assert.match(hub, /\.bg-info-soft\{background-color:var\(--info-soft\)/);
  const firstBlock = read("features/evals");
  assert.match(firstBlock, /border-primary\\\/30\{border-color:color-mix/);
  assert.match(firstBlock, /border-info\\\/30\{border-color:color-mix/);
});

test("new conversion source uses Boxicons, semantic tokens, and no em dash", () => {
  const files = [
    "src/pages/index.astro",
    "src/pages/services.astro",
    "src/pages/services/agent-brief.astro",
    "src/pages/features/index.astro",
    "src/pages/live.astro",
    "src/components/architecture/DepartmentMap.astro",
    "src/components/architecture/OperatingLoop.astro",
    "src/components/features/BlockPage.astro",
    "src/components/features/FeatureNav.astro",
    "src/components/features/FeatureHero.astro",
    "src/components/features/FeatureCTA.astro",
    "src/components/live/LiveTimeline.astro",
    "src/components/live/LiveStatus.astro",
  ];
  const source = files.map((file) => readFileSync(join(root, file), "utf8")).join("\n");
  assert.doesNotMatch(source, /<svg\b/i);
  assert.doesNotMatch(source, /lucide|heroicons/i);
  assert.doesNotMatch(source, /—/);
  assert.doesNotMatch(source, /#[0-9a-f]{3,8}\b/i);
});
