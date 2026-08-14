import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const root = process.cwd();
const dist = join(root, "dist");
const read = (route) => readFileSync(join(dist, route, "index.html"), "utf8");

test("core conversion routes build in English and Persian", () => {
  for (const route of ["", "services", "services/agent-brief", "architecture", "live", "fa", "fa/services", "fa/services/agent-brief", "fa/architecture", "fa/live"]) {
    assert.ok(existsSync(join(dist, route, "index.html")), `${route || "/"} must build`);
  }
  for (const route of ["fa", "fa/services", "fa/services/agent-brief", "fa/architecture", "fa/live"]) {
    assert.match(read(route), /<html lang="fa" dir="rtl"/);
  }
});

test("navigation exposes the fixed information architecture and one-click form", () => {
  const en = read("");
  const fa = read("fa");
  for (const href of ["/services/", "/architecture/", "/live/", "/notes/", "/founder/"]) assert.match(en, new RegExp(`href="${href}"`));
  for (const href of ["/fa/services/", "/fa/architecture/", "/fa/live/", "/fa/notes/", "/fa/founder/"]) assert.match(fa, new RegExp(`href="${href}"`));
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

test("Architecture presents the canonical loop and seven company parts", () => {
  const en = read("architecture");
  const fa = read("fa/architecture");
  for (const label of ["Goal", "Observe", "Decide", "Act", "Evaluate", "Department", "Workflow", "Agent", "Skill", "Connection", "Artifact"]) {
    assert.match(en, new RegExp(`>${label}<`));
  }
  assert.match(en, /harness-architecture-og-1200x630\.png/);
  assert.match(en, /href="\/live\/"/);
  assert.match(en, /href="\/services\/agent-brief\/#request"/);
  assert.match(fa, /هدف/);
  assert.match(fa, /دپارتمان/);
  assert.match(fa, /ورک‌فلو/);
});

test("retired hubs redirect directly to localized Architecture", () => {
  for (const [route, target] of [
    ["waitlist", "/architecture/"],
    ["features", "/architecture/"],
    ["fa/waitlist", "/fa/architecture/"],
    ["fa/features", "/fa/architecture/"],
  ]) {
    const html = read(route);
    assert.match(html, new RegExp(`http-equiv="refresh" content="0;url=${target}"`));
    assert.match(html, /<meta name="robots" content="noindex">/);
    assert.match(html, new RegExp(`<link rel="canonical" href="https://spielos.xyz${target}"`));
  }
});

test("legacy feature detail pages remain available but noindex", () => {
  for (const route of ["features/chat", "features/context", "features/harness", "features/infrastructure/providers", "fa/features/chat", "fa/features/context", "fa/features/harness", "fa/features/infrastructure/providers"]) {
    assert.match(read(route), /<meta name="robots" content="noindex, follow">/);
  }
});

test("sitemap includes localized core pages and excludes redirects and noindex details", () => {
  const sitemap = readFileSync(join(dist, "sitemap.xml"), "utf8");
  for (const route of ["/architecture/", "/fa/architecture/", "/live/", "/fa/live/", "/services/", "/fa/services/"]) {
    assert.match(sitemap, new RegExp(`https:\\/\\/spielos\\.xyz${route.replaceAll("/", "\\/")}`));
  }
  for (const route of ["/waitlist/", "/fa/waitlist/", "/features/", "/fa/features/", "/features/chat/"]) {
    assert.doesNotMatch(sitemap, new RegExp(`https:\\/\\/spielos\\.xyz${route.replaceAll("/", "\\/")}`));
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

test("Live leads with active business work and hides technical records by default", () => {
  const en = read("live");
  const fa = read("fa/live");
  for (const id of ["live-status-root", "live-model", "live-stats", "live-howto", "live-timeline"]) {
    assert.match(en, new RegExp(`id="${id}"`), `${id} must remain part of the Live experience`);
  }
  assert.match(en, /live-hb-ring/);
  assert.match(en, /loop-rail/);
  assert.match(en, /live-business-timeline/);
  assert.match(en, /id="live-company-view"/);
  assert.match(en, /aria-labelledby="business-work-heading"/);
  assert.match(en, /data-live-system-details/);
  assert.match(en, /data-improvement-section/);
  assert.doesNotMatch(en, /<details[^>]*data-improvement-section[^>]*open/);
  assert.match(en, /Still being measured/);
  assert.match(en, /href="\/services\/agent-brief\/#request"/);
  assert.match(fa, /هنوز در حال اندازه‌گیریه/);
});

test("conversion pages preserve the distinctive grid, light, and connected-progress language", () => {
  for (const route of ["", "services", "services/agent-brief", "architecture", "live"]) {
    const html = read(route);
    assert.match(html, /hero-grid/);
    assert.match(html, /text-primary/);
  }
  assert.match(read(""), /jl-wrap/);
  assert.match(read("services"), /service-rail/);
  assert.match(read("services/agent-brief"), /brief-rail/);
  assert.match(read("architecture"), /department-canvas/);
});

test("new conversion source uses Boxicons, semantic tokens, and no em dash", () => {
  const files = [
    "src/pages/index.astro",
    "src/pages/services.astro",
    "src/pages/services/agent-brief.astro",
    "src/pages/architecture.astro",
    "src/pages/live.astro",
    "src/components/AgentBriefForm.astro",
    "src/components/architecture/DepartmentMap.astro",
    "src/components/architecture/OperatingLoop.astro",
    "src/components/live/LiveTimeline.astro",
  ];
  const source = files.map((file) => readFileSync(join(root, file), "utf8")).join("\n");
  assert.doesNotMatch(source, /<svg\b/i);
  assert.doesNotMatch(source, /lucide|heroicons/i);
  assert.doesNotMatch(source, /—/);
  assert.doesNotMatch(source, /#[0-9a-f]{3,8}\b/i);
});
