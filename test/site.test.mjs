import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const root = process.cwd();
const dist = join(root, "dist");
const read = (route) => readFileSync(join(dist, route, "index.html"), "utf8");

test("core conversion routes build in English and Persian", () => {
  const enRoutes = ["", "services", "services/agent-brief", "features", "architecture", "live", ...["director", "departments", "workflows", "agents", "skills", "evals", "connections", "artifacts"].map((b) => `features/${b}`)];
  const faRoutes = ["fa", "fa/services", "fa/services/agent-brief", "fa/features", "fa/architecture", "fa/live", ...["director", "departments", "workflows", "agents", "skills", "evals", "connections", "artifacts"].map((b) => `fa/features/${b}`)];
  for (const route of [...enRoutes, ...faRoutes]) {
    assert.ok(existsSync(join(dist, route, "index.html")), `${route || "/"} must build`);
  }
  for (const route of faRoutes) {
    assert.match(read(route), /<html lang="fa" dir="rtl"/);
  }
});

test("navigation exposes the fixed information architecture and one-click form", () => {
  const en = read("");
  const fa = read("fa");
  for (const href of ["/services/", "/features/", "/live/", "/notes/", "/founder/"]) assert.match(en, new RegExp(`href="${href}"`));
  for (const href of ["/fa/services/", "/fa/features/", "/fa/live/", "/fa/notes/", "/fa/founder/"]) assert.match(fa, new RegExp(`href="${href}"`));
  assert.match(en, /href="\/services\/agent-brief\/#request"/);
  assert.match(fa, /href="\/fa\/services\/agent-brief\/#request"/);
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
  assert.match(en, /href="\/services\/agent-brief\/#request"/);
  assert.match(fa, /هدف/);
  assert.match(fa, /دپارتمان/);
  assert.match(fa, /ورک‌فلو/);
  assert.match(fa, /ارزیابی‌ها/);
});

test("retired hubs redirect directly to localized Architecture", () => {
  for (const [route, target] of [
    ["waitlist", "/architecture/"],
    ["architecture", "/features/"],
    ["fa/waitlist", "/fa/architecture/"],
    ["fa/architecture", "/fa/features/"],
  ]) {
    const html = read(route);
    assert.match(html, new RegExp(`http-equiv="refresh" content="0;url=${target}"`));
    assert.match(html, /<meta name="robots" content="noindex">/);
    assert.match(html, new RegExp(`<link rel="canonical" href="https://spielos.xyz${target}"`));
  }
});

test("fictional feature pages redirect 301 to the real blocks and stay noindex", () => {
  const redirects = [
    ["features/chat", "/features/director/"],
    ["features/chat/director-mode", "/features/director/"],
    ["features/chat/direct-mode", "/features/workflows/"],
    ["features/context", "/features/"],
    ["features/harness/agents", "/features/agents/"],
    ["features/harness/skills", "/features/skills/"],
    ["features/harness/workflows", "/features/workflows/"],
    ["features/harness/evals", "/features/evals/"],
    ["features/infrastructure/connections", "/features/connections/"],
    ["features/infrastructure/providers", "/features/"],
    ["fa/features/chat", "/fa/features/director/"],
    ["fa/features/context", "/fa/features/"],
    ["fa/features/harness/evals", "/fa/features/evals/"],
    ["fa/features/infrastructure/providers", "/fa/features/"],
  ];
  for (const [route, target] of redirects) {
    const html = read(route);
    assert.match(html, new RegExp(`http-equiv="refresh" content="0;url=${target}"`));
    assert.match(html, /<meta name="robots" content="noindex">/);
    assert.match(html, new RegExp(`<link rel="canonical" href="https://spielos.xyz${target}"`));
  }
});

test("sitemap includes localized core pages and excludes redirects and noindex details", () => {
  const sitemap = readFileSync(join(dist, "sitemap.xml"), "utf8");
  const blocks = ["director", "departments", "workflows", "agents", "skills", "evals", "connections", "artifacts"];
  const included = ["/features/", "/fa/features/", "/live/", "/fa/live/", "/services/", "/fa/services/", ...blocks.map((b) => `/features/${b}/`), ...blocks.map((b) => `/fa/features/${b}/`)];
  for (const route of included) {
    assert.match(sitemap, new RegExp(`https:\\/\\/spielos\\.xyz${route.replaceAll("/", "\\/")}`), `${route} must be in the sitemap`);
  }
  const excluded = ["/waitlist/", "/fa/waitlist/", "/architecture/", "/fa/architecture/", "/features/chat/", "/features/context/", "/features/harness/evals/", "/features/infrastructure/providers/", "/fa/features/chat/", "/fa/features/harness/"];
  for (const route of excluded) {
    assert.doesNotMatch(sitemap, new RegExp(`https:\\/\\/spielos\\.xyz${route.replaceAll("/", "\\/")}`), `${route} must not be in the sitemap`);
  }
});

test("Agent Brief uses one shared native three-field form with safe analytics", () => {
  for (const route of ["services/agent-brief", "fa/services/agent-brief"]) {
    const page = read(route);
    const section = (page.match(/<section id="request"[\s\S]*?<\/section>/) || [""])[0];
    assert.ok(section, `${route} must contain #request`);
    assert.match(section, /<form[^>]*method="post"/);
    assert.equal((section.match(/<(?:input|textarea)[^>]*name="(?:name|email|workflow)"/g) || []).length, 3);
    assert.match(section, /name="page_path"/);
    assert.match(section, /name="locale"/);
  }
  const source = readFileSync(join(root, "src/components/AgentBriefForm.astro"), "utf8");
  for (const event of ["lead_form_view", "lead_form_start", "lead_form_submit", "lead_form_success", "lead_form_error"]) assert.match(source, new RegExp(event));
  assert.match(source, /window\.spielosTrack\(name, \{ form_type: 'agent_brief', page: page, locale: locale, location: formLocation \}\)/);
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
  assert.match(en, /href="\/services\/agent-brief\/#request"/);
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

test("conversion pages preserve the distinctive grid, light, and connected-progress language", () => {
  for (const route of ["", "services", "services/agent-brief", "features", "live"]) {
    const html = read(route);
    assert.match(html, /hero-grid/);
    assert.match(html, /text-primary/);
  }
  assert.match(read(""), /jl-wrap/);
  assert.match(read("services"), /service-rail/);
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
    "src/components/AgentBriefForm.astro",
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
