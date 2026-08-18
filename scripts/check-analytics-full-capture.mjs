#!/usr/bin/env node
/**
 * SpielOS analytics full-capture acceptance check
 * (goal-analytics-full-capture-v1-20260818).
 *
 * Asserts:
 *  (a) no consent-gate tokens remain anywhere under src/;
 *  (b) the BaseLayout loader is full capture: gtag('config', ...) +
 *      posthog.init(...) with `person_profiles: 'always'` and
 *      `mask_all_inputs: true`, and NO `disable_session_recording`;
 *  (c) funnel.json (3.1.0) stages reference only real loader events, the
 *      website_lead_gen block carries the goal events, required properties,
 *      objectives (existing values kept), and formulas, and the campaign
 *      join keys / required properties are intact;
 *  (d) posthog.py taxonomy matches the loader: `lead_form_view` and
 *      `lead_form_success` are in REAL_LOADER_EVENTS,
 *      `agent_briefing_form_start` is NOT, and
 *      LEAD_SUCCESS_EVENTS == ('lead_form_success',) (checked through the
 *      company package with PYTHONPATH=.agents).
 *
 * Usage: node scripts/check-analytics-full-capture.mjs
 * Exit 0 = clean, exit 1 = failure with a clear message.
 */
import { readFileSync, readdirSync, statSync } from "fs";
import { execFileSync } from "child_process";
import { join, relative } from "path";

const root = process.cwd();
const issues = [];

function collectFiles(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) collectFiles(p, out);
    else out.push(p);
  }
  return out;
}

// ---- (a) no consent-gate tokens in src/ ----
const consentTokens = [
  "spielos.analytics-consent",
  "__spielosAnalyticsConsent",
  "analytics-consent",
  "gtag('consent'",
  "spielos:analytics-consent",
];
for (const file of collectFiles(join(root, "src"))) {
  const text = readFileSync(file, "utf8");
  for (const token of consentTokens) {
    if (text.includes(token)) {
      issues.push(`(a) consent-gate token ${JSON.stringify(token)} still present in ${relative(root, file)}`);
    }
  }
}

// ---- (b) loader is full capture ----
const loader = readFileSync(join(root, "src/layouts/BaseLayout.astro"), "utf8");
for (const token of ["gtag('config',", "posthog.init(", "person_profiles: 'always'", "mask_all_inputs: true"]) {
  if (!loader.includes(token)) issues.push(`(b) loader missing ${JSON.stringify(token)}`);
}
if (loader.includes("disable_session_recording")) {
  issues.push("(b) loader must not set disable_session_recording (session replay stays ON)");
}

// ---- (c) funnel.json stages / website_lead_gen / join keys ----
const funnelPath = join(root, ".agents/company/departments/analytics/funnel.json");
const funnel = JSON.parse(readFileSync(funnelPath, "utf8"));
if (funnel.version !== "3.1.0") {
  issues.push(`(c) funnel.json version must be 3.1.0, got ${JSON.stringify(funnel.version)}`);
}
const expectedStages = {
  attention: ["$pageview", "content_landing"],
  engagement: ["cta_clicked"],
  intent: ["lead_form_view", "lead_form_start"],
  lead: ["lead_form_submit", "lead_form_success"],
  qualified: ["qualified_lead"],
  conversation: ["booked_call"],
  revenue: ["sale"],
};
for (const [stageId, events] of Object.entries(expectedStages)) {
  const stage = (funnel.stages || []).find((s) => s.id === stageId);
  if (!stage) {
    issues.push(`(c) funnel.json missing stage ${JSON.stringify(stageId)}`);
    continue;
  }
  const actual = [...(stage.events || [])].sort();
  const expected = [...events].sort();
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    issues.push(`(c) funnel.json stage ${JSON.stringify(stageId)} events ${JSON.stringify(actual)} != expected ${JSON.stringify(expected)}`);
  }
}
const wlg = funnel.website_lead_gen;
if (!wlg) {
  issues.push("(c) funnel.json missing website_lead_gen block");
} else {
  for (const prop of ["locale", "page_path", "landing_path", "source", "medium", "campaign", "content_id", "form_type"]) {
    if (!Array.isArray(wlg.required_properties) || !wlg.required_properties.includes(prop)) {
      issues.push(`(c) website_lead_gen missing required property ${JSON.stringify(prop)}`);
    }
  }
  const objectives = wlg.objectives || {};
  for (const [key, value] of Object.entries({ qualified_visits_per_day: 200, leads_per_day: 10, lead_conversion_rate: 0.05 })) {
    if (objectives[key] !== value) {
      issues.push(`(c) website_lead_gen objective ${JSON.stringify(key)} must stay ${value}, got ${JSON.stringify(objectives[key])}`);
    }
  }
  if (!wlg.formulas || Object.keys(wlg.formulas).length === 0) {
    issues.push("(c) website_lead_gen missing formulas");
  }
}
const joinKeys = ["campaign_id", "batch_id", "item_id", "content_id", "creative_signature"];
if (JSON.stringify(funnel.campaign_join_keys || []) !== JSON.stringify(joinKeys)) {
  issues.push("(c) funnel.json campaign_join_keys must stay intact");
}
const requiredProperties = [
  "locale", "page_path", "landing_path", "source", "medium", "campaign",
  "campaign_id", "batch_id", "item_id", "content_id", "platform",
  "creative_signature", "batch_number", "batch_item", "hook_id", "narrative_type",
];
if (JSON.stringify(funnel.required_properties || []) !== JSON.stringify(requiredProperties)) {
  issues.push("(c) funnel.json required_properties must stay intact");
}

// ---- (d) posthog.py taxonomy matches the loader ----
const taxonomyChecks = [
  "import company.departments.analytics.posthog as ph",
  "assert 'lead_form_view' in ph.REAL_LOADER_EVENTS, 'lead_form_view missing from REAL_LOADER_EVENTS'",
  "assert 'lead_form_success' in ph.REAL_LOADER_EVENTS, 'lead_form_success missing from REAL_LOADER_EVENTS'",
  "assert 'agent_briefing_form_start' not in ph.REAL_LOADER_EVENTS, 'agent_briefing_form_start must be retired from REAL_LOADER_EVENTS'",
  "assert ph.LEAD_SUCCESS_EVENTS == ('lead_form_success',), 'LEAD_SUCCESS_EVENTS must be (lead_form_success,)'",
].join("; ");
try {
  execFileSync("python3", ["-B", "-c", taxonomyChecks], {
    cwd: root,
    env: { ...process.env, PYTHONPATH: join(root, ".agents"), PYTHONDONTWRITEBYTECODE: "1" },
    stdio: "pipe",
  });
} catch (error) {
  const detail = (error.stderr || error.stdout || error.message || "").toString().trim();
  issues.push(`(d) posthog.py taxonomy check failed: ${detail}`);
}

if (issues.length > 0) {
  console.error("check-analytics-full-capture: FAILED");
  for (const issue of issues) console.error(`  - ${issue}`);
  process.exit(1);
}
console.log("check-analytics-full-capture: OK");
console.log("  (a) no consent-gate tokens in src/");
console.log("  (b) loader is full capture (gtag config + posthog.init, person_profiles always, mask_all_inputs true, no disable_session_recording)");
console.log("  (c) funnel.json 3.1.0 stages reference only real loader events; website_lead_gen contract intact");
console.log("  (d) posthog.py REAL_LOADER_EVENTS / LEAD_SUCCESS_EVENTS match the loader");
process.exit(0);