// WO2 knowledge-pack evals — deterministic unit assertions derived from the
// plan's 30-prompt eval surface (identity, pricing, process, fit, capability
// questions answered by pack content). Model-graded evals need network access
// to Mistral, which this WorkOrder forbids; instead we assert that the pack's
// system prompt contains every fact the 30 canonical prompts require, that the
// routing map is complete, and that persona/capture directives are present.
//
// Loaded from test-run.mjs: runEvals(knowledge, core) -> { passed, failed, failures }

export function runEvals(knowledge, core) {
  const en = knowledge.system_prompt_en ?? "";
  const fa = knowledge.system_prompt_fa ?? "";
  const both = en + fa;
  const addendumEn = core.CAPTURE_ADDENDUM_EN;
  const addendumFa = core.CAPTURE_ADDENDUM_FA;

  const checks = [];
  const check = (name, cond) => checks.push({ name, ok: !!cond });
  const includes = (name, hay, needle) => check(name, hay.includes(needle));

  // --- identity (5 prompts) -------------------------------------------------
  includes("identity: SpielOS described as supervised AI departments", en, "supervised AI departments");
  includes("identity: harness chain Director -> Departments -> Workflows -> Agents -> Skills -> Evals -> Connections", en, "Director → Departments → Workflows → Agents → Skills → Evals → Connections");
  includes("identity: homepage promise quoted", en, "Build a business that runs without you.");
  includes("identity: assistant never claims human, identity line present", en, "I'm SpielOS's assistant.");
  includes("identity: FA pack has the Persian identity line", fa, "من دستیار SpielOS هستم.");

  // --- pricing (4 prompts) --------------------------------------------------
  includes("pricing: $2,990/month present", both, "$2,990/month");
  includes("pricing: FA pack has the price", fa, "$2,990");
  includes("pricing: no free tier / no discount program stated", en, "no free tier");
  includes("pricing: free starting point is the Free Review at /apply/", en, "Free Review at /apply/");

  // --- process (4 prompts) --------------------------------------------------
  includes("process: apply at /apply/", both, "/apply/");
  includes("process: 48-hour review response window", en, "48 hours");
  includes("process: no required calls anywhere", en.toLowerCase(), "no calls are required");
  includes("process: optional Cal.com 15-minute call", en, "Cal.com 15-minute call");

  // --- fit / ICP (4 prompts) ------------------------------------------------
  includes("fit: hobby project honesty rule", en, "hobby project");
  includes("fit: enterprise governance honesty rule", en, "governance program");
  includes("fit: broken AI-built software is in scope", en, "AI-built software");
  includes("fit: agency/freelancer partner program at /partners/", en, "/partners/");

  // --- capabilities (10 prompts) --------------------------------------------
  includes("capability: broken Zapier routes to zapier page", en, "/solutions/software/zapier-automation/");
  includes("capability: recruitment pipeline route exists", en, "/solutions/workflows/recruitment-automation/");
  includes("capability: design flyer routes to design department", en, "/solutions/ai-departments/design/");
  includes("capability: AI dept marketing route exists", en, "/solutions/ai-departments/marketing/");
  includes("capability: AI dept SEO route exists", en, "/solutions/ai-departments/seo/");
  includes("capability: AI dept analytics route exists", en, "/solutions/ai-departments/analytics/");
  includes("capability: ATS honest pivot (no standalone product, sell the workflow)", both, "ATS");
  includes("capability: resume builder honest pivot", en, "resume builder");
  includes("capability: job board honest pivot", en, "job board");
  includes("capability: ticketing system honest pivot", en, "ticketing system");

  // --- ATS edge honesty (3 prompts) -----------------------------------------
  includes("ats-edge: course platform honest pivot", en, "course platform");
  includes("ats-edge: generic chatbot honest pivot", en, "chatbot product");
  includes("ats-edge: marketing website honest pivot", en, "marketing website");

  // --- sales personality (owner directive 2026-09-06: sales agent, not FAQ) --
  includes("sales: never disqualify a willing buyer", en, "NEVER disqualify");
  includes("sales: money signals are hot leads", en, "HOT LEAD");
  includes("sales: big budget rule present", en, "Big budget");
  includes("sales: objection handling pattern", en, "acknowledge → reframe → steer");
  includes("sales: always-be-closing CTAs", en, "always be closing");
  includes("sales: emoji directive", en, "emojis naturally");
  includes("sales: personality — funny", en, "funny");
  includes("sales: FA money-signal rule", fa, "سرور داغ");
  includes("sales: FA never-reject rule", fa, "خریدارِ باانگیزه رو رد نکن");
  includes("sales: FA objection pattern", fa, "تأیید → بازچارچوب → هدایت");

  // --- persona directives (checked per transcript in the plan) --------------
  includes("persona: warm acknowledgment at reply start", en, "Begin every reply with a brief warm acknowledgment");
  includes("persona: thanks on capture with next steps", en, "thank them warmly");
  includes("persona: at most one follow-up per reply", en, "At most one follow-up question per reply");
  includes("persona: tone matching rule", en, "formal → warm-professional");
  includes("persona: FA tone matching rule", fa, "رسمی ← گرم-حرفه‌ای");

  // --- language / locale ----------------------------------------------------
  includes("locale: language detection + switch rule", en, "reply in it");
  includes("locale: FA twin routes documented", en, "/fa/");
  includes("locale: FA pack self-describes as the chat assistant", fa, "دستیار چت");

  // --- routing map completeness (link allowlist matches real routes) --------
  const allow = knowledge.link_allowlist ?? [];
  check("routing: link allowlist is non-empty", allow.length > 50);
  check("routing: primary CTA /apply/ in allowlist", allow.includes("/apply/"));
  check("routing: pricing in allowlist", allow.includes("/pricing/"));
  check("routing: contact in allowlist", allow.includes("/contact/"));
  check("routing: FA apply twin in allowlist", allow.includes("/fa/apply/"));
  check("routing: all allowlist entries are site-relative paths", allow.every((h) => h.startsWith("/") && !h.includes("://")));
  check("routing: solutions hub in allowlist", allow.includes("/solutions/"));
  check("routing: founder page in allowlist", allow.includes("/founder/"));
  check("routing: live page in allowlist", allow.includes("/live/"));

  // --- segment vocabulary (D4b fixed enum) -----------------------------------
  const segs = knowledge.segment_vocabulary ?? [];
  const expectedSegs = [
    "founders/owners",
    "marketing",
    "ops",
    "recruitment",
    "finance",
    "design/content",
    "software/product",
    "agency/freelance",
    "other",
  ];
  check("segments: fixed vocabulary complete (9 values)", expectedSegs.every((s) => segs.includes(s)));
  check("segments: vocabulary has no extras", segs.length === expectedSegs.length);

  // --- security routing (triage) ---------------------------------------------
  includes("security: serious data questions routed to email/contact", en, "human handoff (shayan@spielos.xyz");
  includes("security: built on Supabase + reputable APIs", en, "Supabase and reputable APIs");
  includes("security: never asks for passwords or payment details", both, "password");

  // --- CTA hierarchy ---------------------------------------------------------
  const ctas = knowledge.cta_hierarchy ?? [];
  check("cta: primary is Apply Free Review", ctas[0]?.href === "/apply/");
  check("cta: secondary is the Cal.com booking", String(ctas[1]?.href ?? "").startsWith("cal:"));
  check("cta: tertiary is contact", ctas[2]?.href === "/contact/");

  // --- capture addendum (runtime marker protocol) ----------------------------
  includes("capture: addendum teaches the exact marker format (en)", addendumEn, "<<CAPTURE:name=John Doe|email=john@example.com|phone=+15551234567|company=Acme|needs=automate invoicing|segment=software/product>>");
  includes("capture: addendum lists the fixed segment vocabulary", addendumEn, "agency/freelance");
  includes("capture: addendum forbids echoing the marker", addendumEn, "never rendered");
  includes("capture: FA addendum teaches the same marker", addendumFa, "<<CAPTURE:name=");
  includes("capture: addendum replaces tool-call instruction (en)", addendumEn, "replaces any tool-call instruction");
  includes("capture: addendum says empty fields allowed except name/one channel", addendumEn, "except name and one contact channel");
  includes("capture: addendum forbids repeat capture in one session", addendumEn, "do not emit the marker again");

  // --- founder facts ---------------------------------------------------------
  includes("founder: Shayan Spiel named", en, "Shayan Spiel");
  includes("founder: Tehran-based", en, "Tehran");
  includes("founder: open-source projects listed", both, "CacheCatch");
  includes("founder: /founder/ page linked", en, "/founder/");

  // --- ICP facts -------------------------------------------------------------
  includes("icp: 2-50 style team framing via established businesses", en, "established businesses");
  includes("icp: tool stack examples listed", en, "Zapier");
  check("icp: FA pack covers the ICP too", fa.includes("فاندر") || fa.includes("مدیر"));

  let passed = 0;
  let failed = 0;
  const failures = [];
  for (const c of checks) {
    if (c.ok) {
      passed += 1;
      console.log(`  ok  eval ${passed}/${checks.length}  ${c.name}`);
    } else {
      failed += 1;
      failures.push({ name: c.name, error: "assertion failed" });
      console.log(`FAIL  eval  ${c.name}`);
    }
  }
  return { passed, failed, failures, total: checks.length };
}
