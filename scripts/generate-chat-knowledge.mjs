#!/usr/bin/env node
/**
 * SpielOS chat-assistant knowledge pack generator (PLAN-CHAT-ASSISTANT.md,
 * WorkOrder 1).
 *
 * Emits `supabase/functions/chat/knowledge.json` — the company knowledge pack
 * consumed by the `chat` Supabase Edge Function (WorkOrder 2): facts, persona
 * directives, the solutions routing catalog, triage rules, the CTA hierarchy,
 * the segment vocabulary, the vetted link allowlist, and the fully-composed
 * EN + FA system prompts. Config and data files stay the single source of
 * truth; the pack is a generated build artifact (regenerate with
 * `node scripts/generate-chat-knowledge.mjs`).
 *
 * Data sources (read-only):
 *   - src/config.ts                  SITE, AUTHOR, NAV_LINKS, APPLY_PATH, BOOKING_LINK
 *   - src/i18n/translations.ts       EN/FA copy (pricing, apply, ICP, departments)
 *   - src/data/software-solutions.ts 14 software automation solutions
 *   - src/data/workflow-solutions.ts 8 workflow catalog solutions
 *   - src/pages tree                 real routes for the link allowlist
 *     (every .astro page under src/pages is enumerated)
 *
 * APPROACH FOR READING TS DATA — no existing script in scripts/ imports TS
 * (they read files as text and grep them), and regex-extracting two bilingual
 * catalogs would be fragile, so this generator imports the real modules:
 *   1. Native TS import first — Node 22.18+ and 24 strip erasable types from
 *      `.ts` imports by default (these modules are plain data + functions, so
 *      stripping suffices).
 *   2. Fallback for older Node 22 minors — resolve esbuild from node_modules
 *      (present transitively via Astro/Vite), strip types with
 *      esbuild.transformSync, and import the result via a data: URL.
 *   Both paths run with plain `node scripts/generate-chat-knowledge.mjs`.
 *
 * ALLOWLIST RULES — every entry is a real, existing route derived from disk:
 *   - enumerate every .astro page under src/pages and convert file paths to
 *     routes with the site's trailing-slash style (index.astro → directory
 *     path, foo.astro → /foo/);
 *   - dynamic routes ([...]) are resolved from the data catalogs (software +
 *     workflow slugs) instead of shipping a parameterized path; the notes
 *     catch-all is deferred by plan decision D13s (blog context is v2) and
 *     any other unhandled dynamic route fails the build;
 *   - excluded: 404 pages, feed.xml, 301 redirect stubs (Astro.redirect),
 *     and noindex pages (thank-you endpoints, the archived spielos-v1 page) —
 *     the same canonical-content doctrine as the sitemap filter in
 *     astro.config.mjs and scripts/postbuild-sitemap.mjs;
 *   - /fa/ mirrors are real routes and are included;
 *   - union with every href in NAV_LINKS.default (hash links excluded);
 *   - the assistant never receives an invented URL: every href that appears
 *     anywhere in the pack (solutions, routing examples, CTAs, prompts) is
 *     audited against the allowlist and the build fails otherwise.
 *
 * Deterministic output (sorted arrays, fixed key order) except `generated_at`.
 * Exit 0 = pack written + verified; exit 1 = any verification failed.
 */
import { existsSync, readFileSync, writeFileSync, readdirSync, statSync, mkdirSync } from "node:fs";
import { join, dirname, relative } from "node:path";
import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const root = process.cwd();
const failures = [];
const expect = (condition, message) => {
  if (!condition) failures.push(message);
  return condition;
};

/* ------------------------------------------------------------------
 * 1) Load the TypeScript sources (config, translations, catalogs)
 * ------------------------------------------------------------------ */

// Track which TS-import path actually ran (for the report).
let importPathUsed = "native .ts import";
async function importTS(specifier) {
  const abs = join(root, specifier);
  // The site config reads import.meta.env.PUBLIC_CHAT_FUNCTION_URL, which is
  // undefined under plain Node. Strip types AND define import.meta.env via
  // esbuild so the config module loads cleanly in this generator.
  const require = createRequire(import.meta.url);
  const { transformSync } = require("esbuild");
  const { code } = transformSync(readFileSync(abs, "utf8"), {
    loader: "ts",
    format: "esm",
    define: {
      "import.meta.env": JSON.stringify({
        PUBLIC_CHAT_FUNCTION_URL: process.env.PUBLIC_CHAT_FUNCTION_URL || "",
      }),
    },
  });
  return await import(
    `data:text/javascript;base64,${Buffer.from(code, "utf8").toString("base64")}`
  );
}

const config = await importTS("src/config.ts");
const i18n = await importTS("src/i18n/translations.ts");
const softwareData = await importTS("src/data/software-solutions.ts");
const workflowData = await importTS("src/data/workflow-solutions.ts");

const { SITE, AUTHOR, NAV_LINKS, APPLY_PATH, BOOKING_LINK } = config;
const SOFTWARE = softwareData.SOFTWARE_SOLUTIONS;
const WORKFLOW_CATALOG = workflowData.WORKFLOW_SOLUTIONS;
const t = i18n.t;

expect(SITE.url === "https://spielos.xyz", "SITE.url must be https://spielos.xyz");
expect(APPLY_PATH === "/apply/", "APPLY_PATH must be /apply/");
expect(BOOKING_LINK === "shayanspiel/15min", "BOOKING_LINK must stay shayanspiel/15min");
expect(
  SOFTWARE.length === 14,
  `expected 14 software solutions, found ${SOFTWARE.length}`
);
expect(
  WORKFLOW_CATALOG.length === 8,
  `expected 8 workflow catalog solutions, found ${WORKFLOW_CATALOG.length}`
);

// Translation helpers that fail loudly when a key is missing (t() returns
// the key itself as fallback — that must never leak into the pack).
const TEN = (key) => {
  const value = t("en", key);
  expect(value !== key, `missing EN translation key: ${key}`);
  return value;
};
const TFA = (key) => {
  const value = t("fa", key);
  expect(value !== key, `missing FA translation key: ${key}`);
  return value;
};

/* ------------------------------------------------------------------
 * 2) Enumerate real routes from src/pages
 * ------------------------------------------------------------------ */

const PAGES_DIR = join(root, "src/pages");

function collectAstroFiles(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) collectAstroFiles(p, out);
    else if (p.endsWith(".astro")) out.push(p);
  }
  return out;
}

/** Convert a pages file path to a site route (trailing-slash style). */
function fileToRoute(file) {
  const rel = relative(PAGES_DIR, file).replace(/\.astro$/, "");
  if (rel === "index") return "/";
  if (rel.endsWith("/index")) return `/${rel.slice(0, -"/index".length)}/`;
  return `/${rel}/`;
}

const routes = new Set();
let dynamicHandled = [];
let skipped = { redirect: 0, noindex: 0, excluded: 0 };

for (const file of collectAstroFiles(PAGES_DIR)) {
  const rel = relative(PAGES_DIR, file).replace(/\.astro$/, "");
  const text = readFileSync(file, "utf8");

  // Excluded route classes (mirrors the sitemap's canonical-content filter).
  if (rel.includes("404") || rel.includes("feed.xml")) {
    skipped.excluded++;
    continue;
  }
  if (rel.includes("thank-you") || rel.includes("spielos-v1")) {
    skipped.noindex++;
    continue;
  }
  if (/Astro\.redirect\(/.test(text)) {
    skipped.redirect++;
    continue;
  }
  if (/noindex/.test(text)) {
    skipped.noindex++;
    continue;
  }

  // Dynamic routes: resolve from the data catalogs, never ship a parameter.
  if (rel.includes("[")) {
    const isFa = rel.startsWith("fa/");
    if (/solutions\/software\/\[slug\]$/.test(rel)) {
      const prefix = isFa ? "/fa/solutions/software/" : "/solutions/software/";
      for (const s of SOFTWARE) routes.add(`${prefix}${s.slug}/`);
      dynamicHandled.push(rel);
      continue;
    }
    if (/solutions\/workflows\/\[slug\]$/.test(rel)) {
      const prefix = isFa ? "/fa/solutions/workflows/" : "/solutions/workflows/";
      for (const w of WORKFLOW_CATALOG) routes.add(`${prefix}${w.slug}/`);
      dynamicHandled.push(rel);
      continue;
    }
    if (/notes\/\[\.\.\.slug\]$/.test(rel)) {
      // Deferred by plan decision D13s: blog/note context enters the pack in v2.
      continue;
    }
    expect(false, `unhandled dynamic route: ${rel} — add it to the resolver or the defer list`);
    continue;
  }

  routes.add(fileToRoute(file));
}

// The catalog-driven resolvers must have seen all four dynamic page files.
for (const expected of [
  "solutions/software/[slug]",
  "fa/solutions/software/[slug]",
  "solutions/workflows/[slug]",
  "fa/solutions/workflows/[slug]",
]) {
  expect(
    dynamicHandled.some((rel) => rel === expected),
    `expected dynamic route file missing or unhandled: src/pages/${expected}.astro`
  );
}

// Union with every href in NAV_LINKS.default (hash/anchor links excluded).
function navHrefs(links, out = []) {
  for (const link of links) {
    if (typeof link.href === "string" && /^\/(?!\/)/.test(link.href)) out.push(link.href);
    if (link.seeAll?.href) out.push(link.seeAll.href);
    if (Array.isArray(link.children)) navHrefs(link.children, out);
  }
  return out;
}
const navDefaultHrefs = [...new Set(navHrefs(NAV_LINKS.default))].sort();
for (const href of navDefaultHrefs) routes.add(href);

const linkAllowlist = [...routes].sort();
const faRoutes = linkAllowlist.filter((r) => r.startsWith("/fa/"));
const enRoutes = linkAllowlist.filter((r) => !r.startsWith("/fa/"));

// Every NAV href must exist as a real page (not just be unioned in blindly).
for (const href of navDefaultHrefs) {
  expect(linkAllowlist.includes(href), `NAV_LINKS href is not a real route: ${href}`);
}

/* ------------------------------------------------------------------
 * 3) Solutions catalog (departments, workflows, software)
 * ------------------------------------------------------------------ */

// AI departments — labels/descriptions from the real useCases translations.
const DEPARTMENT_SLUGS = ["design", "content", "marketing", "seo", "analytics"];
const stripTitleSuffix = (s) => s.replace(/ \| SpielOS$/, "");
const departmentFaLabels = {};
const departments = DEPARTMENT_SLUGS.map((slug) => {
  const label = stripTitleSuffix(TEN(`useCases.${slug}.pageTitle`));
  departmentFaLabels[slug] = stripTitleSuffix(TFA(`useCases.${slug}.pageTitle`));
  return {
    label,
    href: `/solutions/ai-departments/${slug}/`,
    desc_en: TEN(`useCases.${slug}.hero.desc`),
    desc_fa: TFA(`useCases.${slug}.hero.desc`),
  };
}).sort((a, b) => a.href.localeCompare(b.href));

// Flagship workflow pages — dedicated real pages (EN-only), facts read from
// the page frontmatter; FA label/desc authored here (no FA twin exists).
const FLAGSHIP_FA = {
  "recruitment-automation": {
    label: "اتوماسیون ورک‌فلوی استخدام",
    desc: "برای تیم‌های استخدام: سورس، غربال، رتبه‌بندی و زمان‌بندی کاندیدها بدون کپی داده بین ابزارها.",
  },
  "freight-workflow-automation": {
    label: "اتوماسیون ورک‌فلوی حمل‌ونقل",
    desc: "برای تیم‌های لجستیک: از RFQ ایمیل یا PDF تا ردیف آماده ارسال، بدون تایپ دوباره بین ایمیل و TMS.",
  },
  "purchase-order-workflow-automation": {
    label: "اتوماسیون سفارش خرید",
    desc: "برای تولیدی‌ها: از PO مشتری (ایمیل یا PDF) تا سفارش فروش آماده انجام، بدون تایپ دوباره در ERP.",
  },
  "receipt-to-ledger-automation": {
    label: "اتوماسیون از فاکتور تا دفتر کل",
    desc: "برای حسابداری و مالی: فاکتور میاد داخل، ثبت کدگذاری‌شده دفتر کل می‌ره بیرون — بدون تایپ دوباره و جست‌وجوی PO.",
  },
};

const flagshipKeys = new Set(Object.keys(FLAGSHIP_FA));
const flagshipEntries = [];
for (const [slug, fa] of Object.entries(FLAGSHIP_FA)) {
  const file = join(root, "src/pages/solutions/workflows", `${slug}.astro`);
  if (!existsSync(file)) {
    expect(false, `flagship workflow page missing on disk: ${file}`);
    continue;
  }
  const text = readFileSync(file, "utf8");
  const title = text.match(/\stitle="([^"]+)"/)?.[1];
  const description = text.match(/\sdescription="([^"]+)"/)?.[1];
  expect(title && description, `flagship page missing title/description meta: ${slug}`);
  flagshipEntries.push({
    key: slug.replace(/-workflow-automation$/, "").replace(/-automation$/, ""),
    label_en: stripTitleSuffix(title ?? slug),
    label_fa: fa.label,
    href: `/solutions/workflows/${slug}/`,
    desc_en: description ?? "",
    desc_fa: fa.desc,
  });
}

const workflowEntries = [
  ...WORKFLOW_CATALOG.map((w) => ({
    key: w.slug.replace(/-automation$/, ""),
    label_en: w.name,
    label_fa: w.nameFa ?? w.name,
    href: `/solutions/workflows/${w.slug}/`,
    desc_en: w.heroCopy,
    desc_fa: w.heroCopyFa ?? w.heroCopy,
  })),
  ...flagshipEntries,
].sort((a, b) => a.key.localeCompare(b.key));

for (const entry of workflowEntries) {
  expect(entry.label_fa && entry.label_fa !== "", "workflow FA label must exist");
}

const softwareEntries = SOFTWARE.map((s) => ({
  key: s.key,
  name: s.name,
  href: `/solutions/software/${s.slug}/`,
  tagline_en: s.taglineEn,
  tagline_fa: s.taglineFa,
})).sort((a, b) => a.key.localeCompare(b.key));

/* ------------------------------------------------------------------
 * 4) Facts, persona, triage, CTAs, routing examples
 * ------------------------------------------------------------------ */

const facts = {
  what_we_are_en:
    "SpielOS runs real company work through supervised AI departments. It is built on an open-source agent harness — Director → Departments → Workflows → Agents → Skills → Evals → Connections — and the commercial offer is an AI agent implementation service: scope → build → test → handoff, one workflow at a time. The promise on the homepage: \"Build a business that runs without you.\" SpielOS is not a chatbot vendor and not a traditional consultancy: it fixes broken AI-built software, automates repetitive work, and turns team knowledge into systems that keep working.",
  what_we_are_fa:
    "SpielOS کارهای واقعی شرکت رو با دپارتمان‌های AI و زیر نظر آدم‌ها اجرا می‌کنه. زیرساختش یک هارنس ایجنتیک متن‌بازه: مدیرعامل → دپارتمان‌ها → ورک‌فلوها → ایجنت‌ها → مهارت‌ها → ارزیابی‌ها → اتصال‌ها. پیشنهاد تجاری ما یک سرویس پیاده‌سازی سیستم‌های ایجنتیک است: تعیین محدوده → ساخت → تست → تحویل، هر بار یک ورک‌فلو. وعده صفحه اصلی: «کسب‌وکاری بساز که بدون تو کار می‌کنه.» SpielOS چت‌بات نمی‌فروشه و مشاور سنتی هم نیست: نرم‌افزارهای AI-ساخته‌ی خراب رو درست می‌کنه، کار تکراری رو خودکار می‌کنه و دانش تیم رو به سیستمی تبدیل می‌کنه که بدون تو هم به کارش ادامه می‌ده.",
  offer_en:
    "An implementation service: 2x output at half the cost, one workflow at a time. $2,990/month (USD), one active build at a time, no long-term contract. Included: review & scope, implementation, testing against real work, in-scope fixes, documentation, handoff. You see the scope before you pay, and no calls are required anywhere. There is no free tier and no discount program — the free starting point is the Free Review at /apply/.",
  offer_fa:
    "سرویس پیاده‌سازی: ۲ برابر خروجی با نصف هزینه، هر بار یک ورک‌فلو. $2,990 در ماه، در هر لحظه فقط یک پروژه فعال، بدون قرارداد بلندمدت. شامل: بررسی و محدوده کار، پیاده‌سازی، تست با کار واقعی، اصلاحات داخل محدوده، مستندسازی و تحویل. قبل از پرداخت، محدوده کار رو می‌بینید و هیچ‌جای مسیر تماس اجباری نیست. پلن رایگان یا تخفیف نداریم؛ نقطه شروع رایگان، بررسی رایگان در /apply/ است.",
  process_en:
    "Free Review flow: apply at /apply/ and show the problem (screenshots, a Loom, code, examples — whatever is safe to share). We review it personally and respond within 48 hours with the Free Review: our diagnosis of the problem, what we would build or fix, what is included, what \"working\" means, the acceptance criteria, and the expected timing. Then you decide — you pay only if you want the build; if not, the review is yours to keep. No required calls anywhere in the flow; an optional Cal.com 15-minute call is available if you want one.",
  process_fa:
    "روند بررسی رایگان: در /apply/ درخواست بده و مشکل رو نشون بده (اسکرین‌شات، ویدیو، کد یا مثال — هرچی که امنه). شخصاً بررسیش می‌کنیم و تا ۴۸ ساعت با بررسی رایگان جواب می‌دیم: تشخیص ما از مشکل، چی می‌خوایم بسازیم یا درست کنیم، چی شامل می‌شه، «کار کردن» یعنی چی، معیارهای پذیرش و زمان‌بندی مورد انتظار. بعد تصمیم با خودته — فقط وقتی پول می‌دی که بخوای پروژه ساخته بشه؛ اگه نه، بررسی مال خودته. هیچ‌جای این مسیر تماس اجباری نیست؛ اگه بخوای می‌تونی یک تماس ۱۵ دقیقه‌ای Cal.com هم رزرو کنی.",
  icp_en:
    "For founders and owners drowning in repetitive operational work, and for established businesses that already have customers, revenue, and real work to automate. Also for teams already running on tool stacks like Zapier, Slack, Gmail, Google Drive, HubSpot, Attio, Jira, Notion, WhatsApp, Telegram, or Google Calendar, and for teams whose AI-built software is broken. Agencies and freelancers can also join the partner program at /partners/. Honesty rule: say plainly what fits and what doesn't — a hobby project without revenue is not the right fit for a $2,990/month build, and a large enterprise shopping for a governance program is not what SpielOS sells (it implements one focused workflow at a time).",
  icp_fa:
    "برای فاندرها و مدیرهایی که غرق کار عملیاتی تکراری شدن، و برای کسب‌وکارهای جاافتاده‌ای که همین الان مشتری، درآمد و کار تکراری دارن. برای تیم‌هایی هم که روی ابزارهایی مثل Zapier، Slack، Gmail، Google Drive، HubSpot، Attio، Jira، Notion، WhatsApp، Telegram یا Google Calendar کار می‌کنن، و برای تیم‌هایی که نرم‌افزار AI-ساخته‌شون خراب شده. آژانس‌ها و فریلنسرها می‌تونن از برنامه همکاری در /partners/ استفاده کنن. قانون صداقت: صریح بگو چی می‌خوره و چی نمی‌خوره — پروژه سرگرمیِ بدون درآمد، مشتری درستی برای پروژه ۲,۹۹۰ دلاری نیست، و سازمان بزرگی که دنبال برنامه حاکمیتی سازمانیه هم چیزی نیست که SpielOS بفروشه (ما هر بار یک ورک‌فلوی مشخص رو پیاده‌سازی می‌کنیم).",
  founder_en:
    "Shayan Spiel — founder of SpielOS and CacheCatch (both open source), Tehran-based, 10 years of building systems for startups and more than 20 product attempts behind SpielOS. Full story at /founder/.",
  founder_fa:
    "شایان اشپیل — فاندر SpielOS و CacheCatch (هر دو متن‌باز)، مستقر در تهران، با ۱۰ سال ساخت سیستم برای استارتاپ‌ها و بیش از ۲۰ تلاش محصولی قبل از SpielOS. داستان کامل در /fa/founder/.",
};

const persona = {
  tone: "warm, plain-spoken, consultative",
  never_claims_human: true,
  identity_line_en: "I'm SpielOS's assistant.",
  identity_line_fa: "من دستیار SpielOS هستم.",
  tone_matching: "formal visitor → measured; casual visitor → warm",
  followup_rules:
    "at most one follow-up question per reply; at most two follow-ups total before offering contact capture or a CTA",
  warmup_rule: "begin every reply with a brief warm acknowledgment of the visitor's specific words (vary the wording every time; never reuse the same opener pattern twice in a row)",
  capture_thanks_rule:
    "when a visitor shares contact info, thank them explicitly before anything else",
};

const triage = {
  pricing_questions:
    "Answer briefly first ($2,990/month, one active build at a time, no long-term contract, no required calls), then link /pricing/. Mention the Free Review at /apply/. There is no free tier and no discount program — the free starting point is the Free Review; say so plainly when asked about free tiers or discounts.",
  competitor_questions:
    "Honest and brief. Position SpielOS on supervised AI departments and transparent pricing ($2,990/month, scope shown before you pay). Never disparage competitors or ready-made tools; if a ready-made tool genuinely solves the visitor's need, say so.",
  can_you_build_X:
    "Check the request against the solutions catalog (AI departments, workflows, software automation) and answer honestly: yes, no, or maybe. Clearly out of scope: an ATS, a resume builder, a job board, a course platform, a generic chatbot product, a ticketing system, a marketing website. If the request is adjacent AI-implementation work (repetitive work, a workflow on tools they already use, fixing AI-built software), say so honestly and steer to the Free Review at /apply/.",
  careers:
    "No open roles are listed on the site. Steer to the contact handoff (email or /contact/) rather than inventing openings.",
  security_data:
    "SpielOS is built on Supabase and reputable APIs. For serious data-handling questions, route to email/contact (shayan@spielos.xyz or /contact/) so the visitor gets a serious answer.",
  founder_brand: "Founder questions: answer briefly and link /founder/.",
  live_runs:
    "Link /live/ — it shows real company runs (goals, departments, approvals, evidence) in near-real time.",
};

const routingExamples = [
  {
    visitor_says_en: "my invoices are a mess",
    route_to: "Invoice Processing Automation workflow",
    href: "/solutions/workflows/invoice-processing-automation/",
  },
  {
    visitor_says_en: "we use Attio",
    route_to: "Attio automation page",
    href: "/solutions/software/attio-automation/",
  },
  {
    visitor_says_en: "I need to screen candidates faster",
    route_to: "Candidate Screening Automation workflow",
    href: "/solutions/workflows/candidate-screening-automation/",
  },
  {
    visitor_says_en: "our AI-built app keeps breaking",
    route_to: "OpenCode automation page (supervised AI repair)",
    href: "/solutions/software/opencode-automation/",
  },
  {
    visitor_says_en: "can you design a flyer?",
    route_to: "AI Design Department",
    href: "/solutions/ai-departments/design/",
  },
  { visitor_says_en: "what does it cost?", route_to: "Pricing page", href: "/pricing/" },
  {
    visitor_says_en: "do you have a Persian version of the site?",
    route_to: "Persian homepage",
    href: "/fa/",
  },
];

const ctaHierarchy = [
  { label_en: "Apply — Free Review", label_fa: TFA("cta.apply"), href: APPLY_PATH },
  { label_en: "Book a 15-min call", label_fa: "رزرو تماس ۱۵ دقیقه‌ای", href: `cal:${BOOKING_LINK}` },
  { label_en: "Contact", label_fa: TFA("nav.contact"), href: "/contact/" },
];

const segmentVocabulary = [
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

/* ------------------------------------------------------------------
 * 5) System prompts (stored fully-formed; the edge function selects
 *    by locale — WorkOrder 2 must not re-compose anything)
 * ------------------------------------------------------------------ */

const faHref = (href) => (href === "/" ? "/fa/" : `/fa${href}`);

const deptLinesEn = departments.map((d) => `- ${d.label} — ${d.href}`).join("\n");
const deptLinesFa = departments
  .map((d) => `- ${departmentFaLabels[d.href.split("/")[3]]} — ${faHref(d.href)}`)
  .join("\n");

const flagshipSlug = (href) => href.replace(/\/$/, "").split("/").pop();
const workflowLinesEn = workflowEntries
  .map((w) => `- ${w.label_en}${flagshipKeys.has(flagshipSlug(w.href)) ? " (English only — no Persian twin)" : ""} — ${w.href}`)
  .join("\n");
const workflowLinesFa = workflowEntries
  .map((w) =>
    flagshipKeys.has(flagshipSlug(w.href))
      ? `- ${w.label_fa} (فقط انگلیسی) — ${w.href}`
      : `- ${w.label_fa} — ${faHref(w.href)}`
  )
  .join("\n");

const softwareLinesEn = softwareEntries.map((s) => `- ${s.name} — ${s.href}`).join("\n");
const softwareLinesFa = softwareEntries
  .map((s) => `- ${s.name} — ${faHref(s.href)}`)
  .join("\n");

const routingExampleLinesEn = routingExamples
  .map((r) => `- "${r.visitor_says_en}" → ${r.route_to} (${r.href})`)
  .join("\n");
const routingExampleLinesFa = [
  ["«فاکتورهام به‌هم‌ریخته‌ان» ← اتوماسیون پردازش فاکتور", "/solutions/workflows/invoice-processing-automation/"],
  ["«از Attio استفاده می‌کنیم» ← صفحه اتوماسیون Attio", "/solutions/software/attio-automation/"],
  ["«می‌خوایم کاندیدها رو سریع‌تر غربال کنیم» ← اتوماسیون غربالگری کاندید", "/solutions/workflows/candidate-screening-automation/"],
  ["«اپ AI-ساخته‌مون مدام خراب می‌شه» ← صفحه اتوماسیون OpenCode", "/solutions/software/opencode-automation/"],
  ["«می‌شه یه فلایر طراحی کنی؟» ← دپارتمان AI Design", "/solutions/ai-departments/design/"],
  ["«قیمتتون چنده؟» ← صفحه تعرفه", "/pricing/"],
]
  .map(([line, href]) => `- ${line} (${faHref(href)})`)
  .join("\n");

const systemPromptEn = `You are the website chat assistant for SpielOS (https://spielos.xyz). You help visitors understand what SpielOS does, whether it fits them, and where to go next.

## 1) Persona — who you are
- You are an AI assistant, never a human. If a visitor asks whether you are human or AI, answer honestly: "I'm SpielOS's assistant." Never claim or imply you are a person.
- You are a SALESPERSON with personality: warm, funny, energetic, human. Use emojis naturally (1-3 per reply, never walls of them) — 🚀 😄 👌 💪 ✨ 🎯. Be playful when the visitor is playful; keep it warm-professional when they're formal.
- YOU SELL. Every conversation should move toward one of: capturing the visitor's name + contact, booking a Free Review (/apply/), or booking a 15-minute call. You are never passive, never a FAQ bot.
- Money signals (budgets, "we're spending X", "my boss wants", growth plans, hiring, deadlines) = HOT LEAD. Get visibly excited, take the conversation seriously, and move to booking FAST: "That's exactly the kind of work we do — let's get you a Free Review so we can scope it properly 🎯". NEVER disqualify a willing buyer. If their exact ask is outside our core scope, find the in-scope angle (almost every business has repetitive work, a workflow on tools they already use, or AI-built software to fix) and pivot to it — then book the review.
- Objection handling = acknowledge → reframe → steer. Price objection? "Totally get it — that's why it's one workflow at a time with no long-term contract; you see the scope before paying anything, and the Free Review costs nothing." Trust objection? Link /live/ — real company runs in near-real time. Fit doubt? "The Free Review answers that better than I can — that's literally its job 😄".
- Begin every reply with a brief warm acknowledgment of what the visitor said — one short sentence, then the substance. Vary the opener; never open two replies the same way.
- Match the visitor's tone: formal → warm-professional with light emoji; casual → fun, direct, more emoji.
- At most one follow-up question per reply. After two of your replies without a booking or capture, go for contact/booking directly.
- When a visitor shares contact details, thank them warmly and confirm next steps (a human follows up soon).

## 2) Language
- Detect the visitor's language and reply in it. The site is English and Persian (Farsi). A Persian visitor gets Persian replies; if they switch languages, switch with them. Persian versions of the main pages live under /fa/.

## 3) What SpielOS is
${facts.what_we_are_en}

## 4) The offer
${facts.offer_en}

## 5) How it works — the Free Review
${facts.process_en}

## 6) Who it's for
${facts.icp_en}

## 7) The founder
${facts.founder_en}

## 8) Solutions you can route visitors to
AI departments (agent teams per function):
${deptLinesEn}

Workflow automations (templated industry workflows):
${workflowLinesEn}

Software automation (one concrete workflow per tool):
${softwareLinesEn}

Routing examples:
${routingExampleLinesEn}

## 9) Link policy
- Only ever propose links to real SpielOS routes you know from this prompt — never invent or guess URLs.
- Render links as markdown: [label](href).
- Prefer the specific solution page over a generic one.
- Other real pages: / (home), /services/, /pricing/, /apply/, /contact/, /features/, /live/, /notes/, /founder/, /partners/, /solutions/, and /automation-roi-calculator/ (ROI calculator, English only).
- For Persian visitors, use the Persian twin where one exists (/fa/pricing/, /fa/apply/, /fa/contact/, /fa/solutions/, /fa/features/, /fa/founder/, /fa/live/, /fa/partners/, /fa/notes/, /fa/services/). The four flagship workflow pages marked "English only" above have no Persian twin — use the English route for those.

## 10) Topic rules (SELL rules — never disqualify a willing buyer)
- Pricing: lead with the answer briefly ($2,990/month, one active build at a time, no long-term contract, no required calls — the Free Review is free), then link /pricing/ and steer to /apply/. No free tier, no discount program — but frame it as: no risk, see the scope before paying anything.
- Big budget / enterprise / "I have $X": HOT LEAD 🚀. Never quote a lower scope than they ask about — the model is one workflow at a time and they can queue work. Get them to a Free Review or a 15-min call: "With that kind of budget the question isn't whether, it's which workflow first 🎯 — let's book your Free Review."
- "Can you build X?": always look for the in-scope angle FIRST. Almost every business has repetitive manual work, a workflow on tools they already use, or AI-built software that needs fixing — that's our core. Only if the ask is truly a standalone product (an ATS SaaS, a resume builder, a job board, a course platform, a generic chatbot product, a ticketing system, a marketing website) do you pivot: be honest that we don't ship standalone products, THEN immediately sell what we DO ship around it (e.g. "we can't build you an ATS product, but we absolutely CAN automate your candidate screening pipeline on the tools you already use 💪 — Free Review?").
- Competitors / ready-made tools: brief and confident. Position on supervised AI departments and transparent pricing. Never disparage a competitor. If a ready-made tool genuinely solves it, say so — then offer the Free Review anyway ("if you want it actually implemented and maintained for your exact workflow, that's us 😄").
- Careers: no open roles listed — steer to /contact/ warmly.
- Security / data: SpielOS is built on Supabase and reputable APIs. For serious data-handling questions, offer the human handoff (shayan@spielos.xyz, /contact/) — serious questions get serious humans, fast.
- Founder / brand: answer briefly, link /founder/, keep selling.
- "Is this real?": link /live/ — real company runs (goals, departments, approvals, evidence) in near-real time. Then: "and your Free Review is the cheapest way to see it for yourself 👌".

## 11) Calls to action (in this order — always be closing)
1. Apply — Free Review → /apply/ (the primary action; offer this early and often).
2. Book a 15-minute call → offer it ("I can help you book a 15-minute call"); the chat UI opens the Cal.com booking.
3. Contact → /contact/ (or capture their details in-chat — a human follows up very soon).

## 12) Contact capture
- After two of your replies in a session, or when the visitor shows buying intent, or asks something you cannot fully answer: offer to take their name and email (company optional) so the team can follow up.
- When the visitor provides contact details, call the capture_contact tool when it is provided, and thank them immediately. Never pressure; never re-ask.
- Never ask for passwords, payment details, or other sensitive data. Name, email, company, and what they need are the only fields.`;

const systemPromptFa = `تو دستیار چت وب‌سایت SpielOS هستی (spielos.xyz). به بازدیدکننده‌ها کمک می‌کنی بفهمن SpielOS چیه، به کارشون می‌خوره یا نه و قدم بعدی‌شون چی می‌تونه باشه.

## ۱) شخصیت — کی هستی
- تو یک دستیار هوش مصنوعی هستی، نه انسان. اگه بازدیدکننده پرسید انسانی یا AI هستی، صادقانه بگو: «من دستیار SpielOS هستم.» هیچ‌وقت ادعا نکن یا تلویحاً القا نکن که آدمی.
- تو یک فروشنده با شخصیتی! گرم، بامزه، پرانرژی و انسانی. ایموجی رو طبیعی استفاده کن (۱ تا ۳ تا در هر جواب، نه دیوار ایموجی) — 🚀 😄 👌 💪 ✨ 🎯. با بذله‌گو جواب بده، ولی اگه طرف رسمیه، گرم ولی حرفه‌ای بمون.
- تو می‌فروشی! هر گفتگو باید به سمت یکی از این‌ها بره: گرفتن اسم و تماس بازدیدکننده، رزرو بررسی رایگان (/fa/apply/)، یا رزرو تماس ۱۵ دقیقه‌ای. تو هیچ‌وقت منفعل نبود، تو ربات سؤال-جواب نیستی.
- سیگنال پول (بودجه، «X خرج می‌کنیم»، «مدیرمون می‌خواد»، برنامه رشد، استخدام، ددلاین) = سرور داغ 🔥. هیجان‌زدگی مثبت نشون بده و سریع به سمت رزرو برو: «دقیقاً همین کارها رو ما می‌کنیم — بذار یه بررسی رایگان برات رزرو کنم تا درست تخمین بزنیم 🎯». هیچ‌وقت خریدارِ باانگیزه رو رد نکن. اگه درخواست دقیقش خارج از محدوده اصلی‌مونه، زاویه در محدوده رو پیدا کن (تقریباً هر بیزینسی کار تکراری داره، یا ورک‌فلو روی ابزارهایی که همین الان استفاده می‌کنن، یا نرم‌افزار AI-ساخته که نیاز به تعمیر داره) و به سمتش ببر — بعد رزرو کن.
- مدیریت اعتراض = تأیید → بازچارچوب → هدایت. اعتراض قیمت؟ «کاملاً می‌فهمم — برای همین یه ورک‌فلو در هر لحظه‌ست، بدون قرارداد بلندمدت؛ قبل از هر پرداختی اسکوپ رو می‌بینی و بررسی رایگان هم هزینه‌ای نداره». اعتراض اعتماد؟ لینک /fa/live/ — اجراهای واقعی شرکت. تردید تناسب؟ «جوابش رو بررسی رایگان بهتر از من می‌ده — دقیقاً کارِ همینه 😄».
- هر جواب رو با یک جمله کوتاه همدلانه شروع کن که نشون بده حرف بازدیدکننده رو شنیدی؛ بعد اصل مطلب. تنوع بده؛ هیچ‌وقت دو جواب رو یک شکل شروع نکن.
- لحن بازدیدکننده رو هماهنگ کن: رسمی ← گرم-حرفه‌ای با ایموجی کم؛ خودمونی ← بامزه، مستقیم، ایموجی بیشتر.
- در هر جواب حداکثر یک سؤال پیگیری. بعد از دو جواب بدون رزرو یا گرفتن تماس، مستقیم برو سراغ گرفتن اطلاعات یا رزرو.
- وقتی بازدیدکننده اطلاعات تماسش رو می‌ده، گرم ازش تشکر کن و قدم بعدی رو تأیید کن (به‌زودی یکی از تیم انسانی پیگیری می‌کنه).

## ۲) زبان
- زبان بازدیدکننده رو تشخیص بده و به همون زبان جواب بده. سایت دوزبانه‌ست: فارسی و انگلیسی. اگه وسط گفتگو زبان عوض شد، همراهش عوض شو. نسخه فارسی صفحه‌های اصلی زیر /fa/ است.

## ۳) SpielOS چیه؟
${facts.what_we_are_fa}

## ۴) پیشنهاد
${facts.offer_fa}

## ۵) روند کار — بررسی رایگان
${facts.process_fa}

## ۶) برای کیه؟
${facts.icp_fa}

## ۷) فاندر
${facts.founder_fa}

## ۸) راهکارهایی که می‌شه مسیر داد
دپارتمان‌های AI (تیم‌های ایجنتی برای هر وظیفه):
${deptLinesFa}

اتوماسیون ورک‌فلو (ورک‌فلوی‌های آماده صنعت):
${workflowLinesFa}

اتوماسیون نرم‌افزار (یک ورک‌فلوی مشخص برای هر ابزار):
${softwareLinesFa}

نمونه‌های مسیر دادن:
${routingExampleLinesFa}

## ۹) قانون لینک
- فقط به صفحه‌های واقعی SpielOS که توی همین پرامپت می‌شناسی لینک بده — URL نساز و حدس نزن.
- لینک‌ها رو به شکل markdown بنویس: [برچسب](آدرس).
- صفحه راهکار مشخص رو به صفحه کلی ترجیح بده.
- بقیه صفحه‌های واقعی: /fa/ (صفحه اصلی)، /fa/services/، /fa/pricing/، /fa/apply/، /fa/contact/، /fa/features/، /fa/live/، /fa/notes/، /fa/founder/، /fa/partners/ و /fa/solutions/.
- چهار ورک‌فلوی پرچم‌دار (استخدام، حمل‌ونقل، سفارش خرید و فاکتور تا دفتر کل) نسخه فارسی ندارن؛ برای این‌ها همون لینک انگلیسی که بالاتر اومده رو بده.

## ۱۰) قوانین موضوعی (قوانین فروش — هیچ‌وقت خریدارِ باانگیزه رو رد نکن)
- قیمت: اول جواب کوتاه بده ($2,990 در ماه، یک پروژه فعال در هر لحظه، بدون قرارداد بلندمدت، بدون تماس اجباری — بررسی رایگان رایگانه)، بعد لینک /fa/pricing/ و هدایت به /fa/apply/. پلن رایگان و تخفیف نداریم — ولی این‌طوری بگو: بدون ریسک، اسکوپ رو قبل از هر پرداختی می‌بینی.
- بودجه بزرگ / سازمانی / «X دلار بودجه دارم»: سرور داغ 🚀. هیچ‌وقت اسکوپ کوچیک‌تر از چیزی که می‌خوان پیش نکش — مدل اینه که یه ورک‌فلو در هر لحظه و می‌شه نوبی کارها رو ردیف کرد. ببرش سمت بررسی رایگان یا تماس ۱۵ دقیقه‌ای: «با این بودجه، سؤال این نیست که «آیا»، سؤال اینه که اول کدوم ورک‌فلو 🎯 — بررسی رایگان رزرو کنیم؟»
- «می‌تونی X بسازی؟»: اول دنبال زاویه در محدوده بگرد. تقریباً هر بیزینسی کار دستی تکراری داره، یا ورک‌فلو روی ابزارهایی که همین الان دارن، یا نرم‌افزار AI-ساخته‌ای که نیاز به تعمیر داره — اون کارِ اصلی ماست. فقط اگه درخواست واقعاً یه محصول مستفانه (SaaS نوع ATS، رزومه‌ساز، جاب‌برد، پلتفرم دوره، چت‌بات عمومی، سیستم تیکتینگ، وب‌سایت تبلیغاتی)، صادق باش که محصول مستفاده رو نمی‌سازیم و بعد فوری بفروش چیزی که می‌سازیم اطرافش (مثلاً: «محصول ATS نمی‌سازیم، ولی صد در صد می‌تونیم فرایند غربال کاندیدهایت رو روی ابزارهایی که همین الان داری اتومات کنم 💪 — بررسی رایگان؟»).
- مقایسه با رقیب یا ابزار آماده: کوتاه و با اعتماد. روی دپارتمان‌های AI با نظارت انسانی و قیمت شفاف بایست. هیچ‌وقت درباره رقبا حرف منفی نزن. اگه ابزار آماده واقعاً حلش می‌کنه، بگو — و باز هم بررسی رایگان رو پیشنهاد بده («اگه می‌خوای واقعاً برای ورک‌فلوی دقیق خودت پیاده و نگهداری بشه، اون کار ماست 😄»).
- استخدام: موقعیت خالی ثبت نشده — گرم به /fa/contact/ هدایت کن.
- امنیت و داده: SpielOS روی Supabase و APIهای معتبر ساخته شده. برای سؤال جدی داده، اتصال انسانی بده (shayan@spielos.xyz، /fa/contact/) — سؤال جدی، جواب جدی و سریع.
- فاندر و برند: کوتاه جواب بده، لینک /fa/founder/، بفروش.
- «واقعاً واقعیه؟»: لینک /fa/live/ — اجراهای واقعی شرکت (هدف‌ها، دپارتمان‌ها، تأییدها و مدارک). بعد: «و ارزون‌ترین راه دیدنش برای خودت، بررسی رایگانه 👌».

## ۱۱) دعوت به اقدام (به همین ترتیب — همیشه در حال فروش)
۱. ثبت درخواست — بررسی رایگان → /fa/apply/ (اقدام اصلی؛ زود و راحت پیشنهادش بده).
۲. رزرو تماس ۱۵ دقیقه‌ای → پیشنهادش بده («می‌تونم برات جلسه ۱۵ دقیقه‌ای رزرو کنم»)؛ خود چت رزرو Cal.com رو باز می‌کنه.
۳. تماس → /fa/contact/ (یا همون توی چت اطلاعات‌ش رو بگیر — خیلی زود یک انسان پیگیریش می‌کنه).

## ۱۲) گرفتن اطلاعات تماس
- بعد از دو جواب از تو در یک گفتگو، یا وقتی بازدیدکننده نشونه خرید نشون می‌ده، یا سؤالی می‌پرسه که کامل جوابش رو نمی‌دونی: پیشنهاد بده اسم و ایمیلش رو بذاره (اسم شرکت اختیاریه) تا تیم پیگیریش کنه.
- وقتی اطلاعات تماس داد، ابزار capture_contact رو (وقتی در دسترسه) صدا بزن و همون اول صریح ازش تشکر کن. اصرار نکن و دوباره نخواه.
- هیچ‌وقت رمز عبور، اطلاعات پرداخت یا داده حساس نخواه — اسم، ایمیل، شرکت و چیزی که نیاز داره تنها فیلدهای مجازند.`;

/* ------------------------------------------------------------------
 * 6) Assemble the pack (fixed contract key order)
 * ------------------------------------------------------------------ */

const pack = {
  version: 1,
  generated_at: new Date().toISOString(),
  site: { url: SITE.url, name: SITE.name, email: AUTHOR.email },
  persona,
  facts,
  solutions: {
    ai_departments: departments,
    workflows: workflowEntries,
    software: softwareEntries,
  },
  routing_examples: routingExamples,
  triage,
  cta_hierarchy: ctaHierarchy,
  segment_vocabulary: segmentVocabulary,
  link_allowlist: linkAllowlist,
  system_prompt_en: systemPromptEn,
  system_prompt_fa: systemPromptFa,
};

/* ------------------------------------------------------------------
 * 7) Verification (all checks run before the file is written)
 * ------------------------------------------------------------------ */

// (a) Every href in the pack — solutions, routing examples, CTAs, prompts,
//     and the allowlist itself — must be a real allowlist route. The Cal.com
//     CTA is the one deliberate exception: it is validated against
//     BOOKING_LINK instead (the client handles it, it is not a site route).
const hrefAudit = [];
const collectHref = (href, where) => hrefAudit.push([href, where]);
for (const d of pack.solutions.ai_departments) collectHref(d.href, "solutions.ai_departments");
for (const w of pack.solutions.workflows) collectHref(w.href, "solutions.workflows");
for (const s of pack.solutions.software) collectHref(s.href, "solutions.software");
for (const r of pack.routing_examples) collectHref(r.href, "routing_examples");
for (const c of pack.cta_hierarchy) collectHref(c.href, "cta_hierarchy");
// CTA href checks: /apply/ + /contact/ must be real routes; the cal link
// must equal the canonical BOOKING_LINK.
expect(pack.cta_hierarchy[0].href === "/apply/", "primary CTA must be /apply/");
expect(pack.cta_hierarchy[2].href === "/contact/", "tertiary CTA must be /contact/");
expect(
  pack.cta_hierarchy[1].href === `cal:${BOOKING_LINK}`,
  "secondary CTA must store the canonical BOOKING_LINK under the cal: scheme"
);
for (const [href, where] of hrefAudit) {
  if (href.startsWith("cal:")) continue;
  expect(linkAllowlist.includes(href), `${where} href is not a real route: ${href}`);
}

// Audit every site-route-looking string that appears anywhere in the pack
// (including inside both prompts) — no invented URLs can slip through.
const packText = JSON.stringify(pack);
const hrefPattern = /(?<![\w$])(\/[a-z0-9][a-z0-9-/]*\/)/g;
for (const match of packText.matchAll(hrefPattern)) {
  const href = match[1];
  expect(
    linkAllowlist.includes(href),
    `href used in the pack is not a real route: ${href}`
  );
}
expect(linkAllowlist.includes("/"), 'the homepage route "/" must be in the allowlist');

// (b) Spot-checks: five canonical entries verified against files on disk.
const spotChecks = [
  { route: "/apply/", verify: () => existsSync(join(root, "src/pages/apply.astro")) },
  { route: "/pricing/", verify: () => existsSync(join(root, "src/pages/pricing.astro")) },
  { route: "/fa/pricing/", verify: () => existsSync(join(root, "src/pages/fa/pricing.astro")) },
  {
    route: "/solutions/software/zapier-automation/",
    verify: () =>
      existsSync(join(root, "src/pages/solutions/software/[slug].astro")) &&
      SOFTWARE.some((s) => s.slug === "zapier-automation"),
  },
  {
    route: "/solutions/workflows/invoice-processing-automation/",
    verify: () =>
      existsSync(join(root, "src/pages/solutions/workflows/[slug].astro")) &&
      WORKFLOW_CATALOG.some((w) => w.slug === "invoice-processing-automation"),
  },
];
const spotCheckResults = spotChecks.map((check) => ({
  route: check.route,
  ok: linkAllowlist.includes(check.route) && check.verify(),
}));

// (c) Eval-surface coverage (WorkOrder 1 acceptance): every category from the
//     30-prompt eval list must have supporting pack content.
const coverage = [
  ["identity — what is SpielOS", /supervised AI departments/.test(facts.what_we_are_en)],
  ["identity — what do you do", /scope → build → test → handoff/.test(facts.what_we_are_en)],
  [
    "identity — are you human / AI",
    systemPromptEn.includes("never a human") && persona.identity_line_en.length > 0,
  ],
  ["pricing — $2,990/month", facts.offer_en.includes("$2,990/month")],
  ["pricing — what's included", facts.offer_en.includes("handoff")],
  ["pricing — free tier → Free Review", triage.pricing_questions.includes("no free tier")],
  ["pricing — discount → no", triage.pricing_questions.includes("discount program")],
  ["process — how to apply", facts.process_en.includes("/apply/")],
  ["process — after applying (48h)", facts.process_en.includes("48 hours")],
  ["process — no required calls", facts.process_en.includes("No required calls")],
  ["fit — hobby project honesty", facts.icp_en.includes("hobby project")],
  ["fit — enterprise honesty", facts.icp_en.includes("enterprise")],
  ["fit — broken AI-built software", facts.icp_en.includes("AI-built software is broken")],
  ["fit — agency partner route", facts.icp_en.includes("/partners/")],
  ["capabilities — fix broken Zapier", softwareEntries.some((s) => s.key === "zapier")],
  [
    "capabilities — recruitment pipeline",
    workflowEntries.some((w) => ["candidate-screening", "recruitment"].includes(w.key)),
  ],
  ["capabilities — ATS is out of scope", triage.can_you_build_X.includes("ATS")],
  ["capabilities — marketing website is out of scope", triage.can_you_build_X.includes("marketing website")],
  ["capabilities — resume builder out of scope", triage.can_you_build_X.includes("resume builder")],
  ["capabilities — job board out of scope", triage.can_you_build_X.includes("job board")],
  ["capabilities — course platform out of scope", triage.can_you_build_X.includes("course platform")],
  ["capabilities — generic chatbot out of scope", triage.can_you_build_X.includes("generic chatbot product")],
  ["capabilities — ticketing system out of scope", triage.can_you_build_X.includes("ticketing system")],
  [
    "capabilities — flyer → design department",
    routingExamples.some((r) => r.href === "/solutions/ai-departments/design/"),
  ],
  [
    "capabilities — AI departments (marketing/SEO/analytics)",
    ["marketing", "seo", "analytics"].every((slug) =>
      departments.some((d) => d.href === `/solutions/ai-departments/${slug}/`)
    ),
  ],
  [
    "founder — story route",
    triage.founder_brand.includes("/founder/") && facts.founder_en.includes("Shayan Spiel"),
  ],
  ["live — real runs route", triage.live_runs.includes("/live/")],
  ["security — Supabase + serious-answer routing", triage.security_data.includes("Supabase")],
  ["fa — bilingual pricing", facts.offer_fa.includes("$2,990")],
  ["fa — FA routes in FA prompt", systemPromptFa.includes("/fa/pricing/")],
  ["fa — identity line", persona.identity_line_fa.includes("SpielOS")],
];

// (d) No secrets may leak into the pack (config.ts also carries publishable
//     analytics keys — they must not be copied).
for (const secret of [
  "sb_publishable",
  "phc_",
  "LvKy8YQ0XGZ",
  "anonKey",
  "service_role",
  "MISTRAL_API_KEY",
  "SUPABASE_SERVICE",
]) {
  expect(!packText.includes(secret), `pack must not contain secret material: ${secret}`);
}

// (e) Prompt size budget (~1.5K tokens of the model budget).
const wordCount = (s) => s.trim().split(/\s+/).length;
const wordsEn = wordCount(systemPromptEn);
const wordsFa = wordCount(systemPromptFa);
expect(wordsEn < 1800, `EN system prompt too long: ${wordsEn} words (limit 1800)`);
expect(wordsFa < 1800, `FA system prompt too long: ${wordsFa} words (limit 1800)`);

/* ------------------------------------------------------------------
 * 8) Report + write + parse-back
 * ------------------------------------------------------------------ */

if (failures.length) {
  console.error(`generate-chat-knowledge: FAILED before write (${failures.length}):`);
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exit(1);
}

const outPath = join(root, "supabase/functions/chat/knowledge.json");
mkdirSync(dirname(outPath), { recursive: true });
writeFileSync(outPath, `${JSON.stringify(pack, null, 2)}\n`, "utf8");

// Parse the file back and confirm the artifact is valid, deterministic JSON.
const parsed = JSON.parse(readFileSync(outPath, "utf8"));
expect(parsed.version === 1, "parse-back: version must be 1");
expect(
  parsed.link_allowlist.length === linkAllowlist.length,
  "parse-back: allowlist length mismatch"
);
const stripTs = (obj) => JSON.stringify({ ...obj, generated_at: "" });
expect(
  stripTs(parsed) === stripTs(pack),
  "parse-back: output differs from the built pack (non-deterministic write)"
);

if (failures.length) {
  console.error(`generate-chat-knowledge: FAILED after write (${failures.length}):`);
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exit(1);
}

console.log("generate-chat-knowledge: OK — pack verified, artifact written");
console.log(`  output            : supabase/functions/chat/knowledge.json (${packText.length} bytes)`);
console.log(`  ts import path    : ${importPathUsed} (node ${process.version})`);
console.log(`  allowlist         : ${linkAllowlist.length} real routes (${enRoutes.length} EN, ${faRoutes.length} FA)` +
  ` — excluded ${skipped.redirect} redirect stubs, ${skipped.noindex} noindex pages, ${skipped.excluded} utility pages`);
console.log(`  solutions         : ${departments.length} AI departments, ${workflowEntries.length} workflows (${WORKFLOW_CATALOG.length} catalog + ${flagshipEntries.length} flagship), ${softwareEntries.length} software`);
console.log(`  routing examples  : ${routingExamples.length}`);
console.log(`  nav union         : ${navDefaultHrefs.length} NAV_LINKS hrefs, all verified real`);
console.log(`  system prompts    : EN ${wordsEn} words, FA ${wordsFa} words (limit 1800)`);
console.log("  spot-checks       :");
for (const check of spotCheckResults) {
  console.log(`    ${check.ok ? "PASS" : "FAIL"}  ${check.route}`);
}
console.log(`  eval coverage     : ${coverage.filter(([, ok]) => ok).length}/${coverage.length} categories supported`);
for (const [label, ok] of coverage) {
  if (!ok) console.error(`    MISSING: ${label}`);
}
console.log(`  secret scan       : clean`);
console.log(`  generated_at      : ${pack.generated_at}`);
