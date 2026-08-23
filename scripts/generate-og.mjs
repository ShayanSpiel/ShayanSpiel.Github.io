#!/usr/bin/env node
/**
 * generate-og.mjs — Renders every site OG image (exact 1200x630) via Puppeteer.
 *
 * Templates (website derivatives of the Design Department's registered social
 * archetypes, gallery research map shortform-template-research-20260817):
 *   - src/og-templates/og-single-fact.html  (default: one bold fact + support)
 *   - src/og-templates/og-pull-quote.html   (quote + attribution)
 *
 * The manifest mirrors each indexable route's real SEO metadata:
 *   - Notes: parsed live from src/content/notes/*.mdx frontmatter
 *   - Software pages: parsed from src/data/software-solutions.ts
 *   - Workflow pages: parsed from src/data/workflow-solutions.ts
 *
 * Usage: node scripts/generate-og.mjs
 */

import puppeteer from "puppeteer";
import { readFileSync, readdirSync, writeFileSync, existsSync, mkdirSync, unlinkSync } from "fs";
import { join, resolve } from "path";
import { fileURLToPath } from "url";
import { createServer } from "http";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const ROOT = resolve(__dirname, "..");
const TEMPLATES = {
  fact: join(ROOT, "src/og-templates/og-single-fact.html"),
  quote: join(ROOT, "src/og-templates/og-pull-quote.html"),
};
const OUT_DIR = join(ROOT, "public/assets/og");
const WIDTH = 1200;
const HEIGHT = 630;

/* ── Helpers ─────────────────────────────────────────────── */
const unquote = (s) => s.replace(/\\/g, "").replace(/"/g, "").trim();
const trunc = (s, n = 150) =>
  s.length <= n ? s : s.slice(0, n).replace(/\s+\S*$/, "").trimEnd() + "…";

/** Parse YAML frontmatter (title/description/permalink) from an .mdx note. */
function parseNote(filePath) {
  const src = readFileSync(filePath, "utf-8");
  const fm = src.match(/^---\n([\s\S]*?)\n---/);
  if (!fm) return null;
  const grab = (key) => {
    const m = fm[1].match(new RegExp(`^${key}:\\s*(.*)$`, "m"));
    return m ? m[1].trim().replace(/^["']|["']$/g, "") : "";
  };
  // description may be a wrapped multi-line scalar — take until next top-level key
  const dm = fm[1].match(/^description:\s*([\s\S]*?)(?=^\w|\n\w+:)/m);
  const description = dm ? dm[1].split("\n").map((l) => l.trim()).join(" ").trim() : "";
  return { title: grab("title"), description, permalink: grab("permalink") };
}

/** Extract slug-keyed string fields from a typed TS data module. */
function parseTsEntries(filePath, fields) {
  const src = readFileSync(filePath, "utf-8");
  // Entries open with "  {" at two-space indent inside the exported array.
  // Anchoring there keeps each segment self-contained, so fields that precede
  // the slug line (key, name) are read from the right entry.
  const entryRe = /\n  \{\s*\n([\s\S]*?)\n  \}(?:,|\s*$)/g;
  const entries = [];
  let m;
  while ((m = entryRe.exec(src))) entries.push(m[1]);
  return entries.map((seg) => {
    const sm = seg.match(/(?:^|\n)\s{4}slug:\s*"([^"]+)"/);
    const out = { slug: sm ? sm[1] : "" };
    for (const f of fields) {
      const fm2 = seg.match(new RegExp(`(?:^|\\n)\\s{4}${f}:\\s*"((?:[^"\\\\]|\\\\.)*)"`));
      out[f] = fm2 ? unquote(fm2[1]) : "";
    }
    return out;
  });
}

/* ── Manifest ─────────────────────────────────────────────── */
function buildManifest() {
  const pages = [];

  /* Core pages */
  pages.push(
    {
      file: "home.png", archetype: "fact", eyebrow: "AI Workflow Automation",
      title_lines: ["AI workflow automation", "that runs without you"], accent_line: 1,
      supporting_text: "We fix broken AI-built software and turn repetitive work into systems that keep working.",
      url: "/",
    },
    {
      file: "founder.png", archetype: "quote", eyebrow: "Founder",
      title_lines: ["Ten years of startup systems.", "One AI company."], accent_line: 1,
      supporting_text: "— Shayan Spiel · Founder & Agent Harness Architect",
      url: "/founder/",
    },
    {
      file: "contact.png", archetype: "fact", eyebrow: "Contact",
      title_lines: ["Show us what keeps breaking"], accent_line: -1,
      supporting_text: "Get in touch about fixing AI-built software or handing repetitive work to AI.",
      url: "/contact/",
    },
    {
      file: "notes-index.png", archetype: "fact", eyebrow: "Notes",
      title_lines: ["Notes from building", "an AI company"], accent_line: 1,
      supporting_text: "Agent systems, context, workflows, evaluations — building in public.",
      url: "/notes/",
    },
    {
      file: "services.png", archetype: "fact", eyebrow: "Services",
      title_lines: ["AI agent implementation,", "measured against your cost"], accent_line: 1,
      supporting_text: "Fix broken AI-built software or hand repetitive work to AI workers. Free review, scope before you pay.",
      url: "/services/",
    },
    {
      file: "agent-brief.png", archetype: "fact", eyebrow: "Agent Brief",
      title_lines: ["Scope before you pay"], accent_line: -1,
      supporting_text: "Map one repetitive workflow into a clear Agent Brief: result, inputs, outputs, controls, success measure.",
      url: "/services/agent-brief/",
    },
    {
      file: "pricing.png", archetype: "fact", eyebrow: "Pricing",
      title_lines: ["$2,990/month.", "One active build at a time."], accent_line: 0,
      supporting_text: "No hourly billing, no lock-in — see the scope before you pay.",
      url: "/pricing/",
    },
    {
      file: "apply.png", archetype: "fact", eyebrow: "Free Review",
      title_lines: ["Apply — Free Review"], accent_line: -1,
      supporting_text: "Hear back within 48 hours — no sales call, no demo. Scope and acceptance criteria before any payment.",
      url: "/apply/",
    },
    {
      file: "live.png", archetype: "fact", eyebrow: "Live",
      title_lines: ["An AI company,", "running in the open"], accent_line: 1,
      supporting_text: "Real goals, departments, approvals, work, and evidence behind the company running on SpielOS.",
      url: "/live/",
    },
    /* Features hub + eight blocks */
    {
      file: "features.png", archetype: "fact", eyebrow: "Features",
      title_lines: ["Inside the SpielOS", "agent harness"], accent_line: 1,
      supporting_text: "Director, Departments, Workflows, Agents, Skills, Evals, Connections, Artifacts — how an AI-run company works.",
      url: "/features/",
    },
    ...["director", "departments", "workflows", "agents", "skills", "evals", "connections", "artifacts"].map(
      (block) => ({
        file: `features-${block}.png`, archetype: "fact", eyebrow: `Features · ${block}`,
        title_lines: [block.charAt(0).toUpperCase() + block.slice(1)],
        accent_line: -1,
        supporting_text: FEATURES_BLOCK_SUPPORT[block],
        url: `/features/${block}/`,
      })
    ),
    /* Solutions hubs + department use cases */
    {
      file: "solutions.png", archetype: "fact", eyebrow: "Solutions",
      title_lines: ["AI automation solutions"], accent_line: -1,
      supporting_text: "Workflows, departments, and software — one concrete automatable loop at a time.",
      url: "/solutions/",
    },
    {
      file: "ai-departments.png", archetype: "fact", eyebrow: "Solutions · Departments",
      title_lines: ["AI departments doing", "real company work"], accent_line: 1,
      supporting_text: "Design, content, marketing, SEO, analytics — on the same loop that runs SpielOS live.",
      url: "/solutions/ai-departments/",
    },
    {
      file: "use-case-design.png", archetype: "fact", eyebrow: "AI Departments",
      title_lines: ["Your AI Design Department"], accent_line: -1,
      supporting_text: "Platform-ready videos and social graphics on the same loop that runs this company.",
      url: "/solutions/ai-departments/design/",
    },
    {
      file: "use-case-content.png", archetype: "fact", eyebrow: "AI Departments",
      title_lines: ["Your AI Content Department"], accent_line: -1,
      supporting_text: "One brief, drafts written for your ideal customer, quality gate and approval before shipping.",
      url: "/solutions/ai-departments/content/",
    },
    {
      file: "use-case-marketing.png", archetype: "fact", eyebrow: "AI Departments",
      title_lines: ["Your AI Marketing Department"], accent_line: -1,
      supporting_text: "Researched leads, personal emails and social DMs, approved sending — recorded back to your CRM.",
      url: "/solutions/ai-departments/marketing/",
    },
    {
      file: "use-case-seo.png", archetype: "fact", eyebrow: "AI Departments",
      title_lines: ["Your AI SEO Department"], accent_line: -1,
      supporting_text: "Continuous keyword research, technical audits, metadata, and Search Console verification — as an operation.",
      url: "/solutions/ai-departments/seo/",
    },
    {
      file: "use-case-analytics.png", archetype: "fact", eyebrow: "AI Departments",
      title_lines: ["Your AI Analytics Department"], accent_line: -1,
      supporting_text: "Event taxonomy, conversion tracking, attribution, and plain-language weekly reports.",
      url: "/solutions/ai-departments/analytics/",
    },
    {
      file: "design-gallery.png", archetype: "fact", eyebrow: "Design Department",
      title_lines: ["Every registered", "design archetype"], accent_line: 1,
      supporting_text: "Flat-motion Shorts and Threads canvases built from research — rebuilt from the live registry every deploy.",
      url: "/solutions/ai-departments/design/gallery/",
    },
    {
      file: "software-hub.png", archetype: "fact", eyebrow: "Solutions · Software",
      title_lines: ["AI automation by software"], accent_line: -1,
      supporting_text: "One concrete workflow we automate on the software you already use: Zapier, Slack, Gmail, HubSpot, Notion…",
      url: "/solutions/software/",
    },
    {
      file: "workflows-hub.png", archetype: "fact", eyebrow: "Solutions · Workflows",
      title_lines: ["Workflow automation", "solutions"], accent_line: 0,
      supporting_text: "Repeatable playbooks for onboarding, intake, follow-up, invoicing, screening — run end to end.",
      url: "/solutions/workflows/",
    },
    {
      file: "lead-researcher.png", archetype: "fact", eyebrow: "Open Source",
      title_lines: ["A free AI lead", "research worker"], accent_line: 1,
      supporting_text: "Finds and verifies leads against your ICP, nonstop. Runs in Claude Code, Codex CLI, or OpenCode.",
      url: "/landing/lead-researcher/",
    },
    /* Utility pages */
    {
      file: "SpielOS.png", archetype: "fact", eyebrow: "Archive",
      title_lines: ["SpielOS v1"], accent_line: -1,
      supporting_text: "Capture. Simulate. Publish. — the original founder distribution infrastructure.",
      url: "/spielos-v1/",
    },
    {
      file: "404.png", archetype: "fact", eyebrow: "404",
      title_lines: ["Page not found"], accent_line: -1,
      supporting_text: "This page does not exist — head back to spielos.xyz.",
      url: "/404.html",
    },
  );

  /* Notes — derived live from the content collection frontmatter */
  const notesDir = join(ROOT, "src/content/notes");
  for (const f of readdirSync(notesDir).filter((f) => f.endsWith(".mdx"))) {
    const note = parseNote(join(notesDir, f));
    if (!note?.permalink || !note?.title) continue;
    const slug = note.permalink.replace(/^\/|\/$/g, "");
    pages.push({
      file: `${slug}.png`,
      archetype: "fact",
      eyebrow: "Notes",
      title_lines: [note.title],
      accent_line: -1,
      supporting_text: trunc(note.description || "", 140),
      url: `/notes${note.permalink}`,
    });
  }

  /* Software solution pages */
  for (const s of parseTsEntries(join(ROOT, "src/data/software-solutions.ts"),
    ["key", "name", "keyword", "taglineEn", "workflowTitleEn"])) {
    pages.push({
      file: `software-${s.key || s.slug}.png`,
      archetype: "fact",
      eyebrow: `Software · ${s.name}`,
      title_lines: [s.taglineEn],
      accent_line: -1,
      supporting_text: s.workflowTitleEn,
      url: `/solutions/software/${s.slug}/`,
    });
  }

  /* Workflow solution pages */
  for (const w of parseTsEntries(join(ROOT, "src/data/workflow-solutions.ts"),
    ["name", "h1", "seoDesc"])) {
    pages.push({
      file: `workflow-${w.slug}.png`,
      archetype: "fact",
      eyebrow: "Workflows",
      title_lines: [w.h1],
      accent_line: -1,
      supporting_text: trunc(w.seoDesc || "", 140),
      url: `/solutions/workflows/${w.slug}/`,
    });
  }

  return pages;
}

const FEATURES_BLOCK_SUPPORT = {
  director: "Owns goals, routes Departments, supervises durable runs, judges evidence, and reports outcomes.",
  departments: "Durable business capabilities with their own strategy, workflows, agents, skills, connections, and evals.",
  workflows: "Repeatable playbooks inside a Department: a typed step graph executed by the shared interpreter.",
  agents: "Bounded executors for workflow steps — they claim work orders, activate skills, execute, complete.",
  skills: "Reusable methods agents activate — the how behind the work.",
  evals: "LLM-as-judge quality gates; a passed eval report is required evidence before work ships.",
  connections: "Approved access to external systems — credentials stay local, actions stay reviewable.",
  artifacts: "Output and evidence from every run — inspectable, evaluable, reusable.",
};

/* ── Static server (serves repo root so template asset paths resolve) ── */
const MIME = {
  ".html": "text/html", ".css": "text/css", ".js": "application/javascript",
  ".json": "application/json", ".png": "image/png", ".svg": "image/svg+xml",
  ".woff2": "font/woff2", ".woff": "font/woff",
};
function startServer() {
  return new Promise((res) => {
    const server = createServer((req, res) => {
      let fp = join(ROOT, decodeURIComponent(req.url.split("?")[0]));
      if (fp.endsWith("/")) fp = join(fp, "index.html");
      const ext = "." + fp.split(".").pop().toLowerCase();
      try {
        const data = readFileSync(fp);
        res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream", "Access-Control-Allow-Origin": "*" });
        res.end(data);
      } catch { res.writeHead(404); res.end("Not found"); }
    });
    server.listen(0, "127.0.0.1", () => {
      const port = server.address().port;
      res({ server, url: `http://127.0.0.1:${port}` });
    });
  });
}

/* ── Main ── */
async function generate() {
  const pages = buildManifest();
  const templateHtml = Object.fromEntries(
    Object.entries(TEMPLATES).map(([k, p]) => [k, readFileSync(p, "utf-8")])
  );
  const { server, url: baseUrl } = await startServer();
  console.log(`  Server: ${baseUrl}`);

  const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser = await puppeteer.launch({
    headless: "shell",
    executablePath: CHROME_PATH,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--font-render-hinting=none"],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: WIDTH, height: HEIGHT, deviceScaleFactor: 1 });

  if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true });

  const rendered = new Set();
  let done = 0;
  let failures = 0;

  for (const meta of pages) {
    done++;
    const html = templateHtml[meta.archetype] ?? templateHtml.fact;
    const tmpName = `og-tmp-${meta.file.replace(/\.png$/, ".html")}`;
    writeFileSync(join(ROOT, tmpName), html);
    const tmpUrl = `${baseUrl}/${tmpName}`;

    try {
      await page.goto(tmpUrl, { waitUntil: "networkidle0", timeout: 20000 });
      await page.evaluate((data) => window.__applyOg(data), {
        eyebrow: meta.eyebrow,
        title_lines: meta.title_lines,
        accent_line: meta.accent_line ?? -1,
        supporting_text: meta.supporting_text || "",
        url: meta.url || "/",
      });
      await page.waitForFunction(
        () => document.documentElement.dataset.templateReady === "true",
        { timeout: 5000 }
      );
      await page.evaluate(() => document.fonts.ready);
      await new Promise((r) => setTimeout(r, 250));
      await page.screenshot({
        path: join(OUT_DIR, meta.file),
        type: "png",
        clip: { x: 0, y: 0, width: WIDTH, height: HEIGHT },
      });
      rendered.add(meta.file);
      process.stdout.write(`\r  [${done}/${pages.length}] ${meta.file}          `);
    } catch (err) {
      failures++;
      process.stdout.write(`\n  FAIL ${meta.file}: ${err.message}\n`);
    } finally {
      try { unlinkSync(join(ROOT, tmpName)); } catch {}
    }
  }

  await browser.close();
  server.close();

  /* Prune rendered OG files no longer in the manifest */
  let pruned = 0;
  for (const f of readdirSync(OUT_DIR)) {
    if (f.endsWith(".png") && !rendered.has(f)) {
      unlinkSync(join(OUT_DIR, f));
      pruned++;
    }
  }

  console.log(`\n  Done: ${rendered.size} OG images (${WIDTH}x${HEIGHT}) -> public/assets/og/`);
  console.log(`  Pruned ${pruned} stale file(s). Failures: ${failures}\n`);
  if (failures > 0 || rendered.size < pages.length) process.exit(1);
}

generate().catch((err) => {
  console.error("OG generation failed:", err);
  process.exit(1);
});
