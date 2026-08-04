#!/usr/bin/env node
/**
 * generate-og.mjs — Renders OG images from the SpielOS design system via Puppeteer.
 *
 * Usage: node scripts/generate-og.mjs
 */

import puppeteer from "puppeteer";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join, resolve } from "path";
import { fileURLToPath } from "url";
import { createServer } from "http";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const ROOT = resolve(__dirname, "..");
const TEMPLATE = join(ROOT, "src/og-templates/og-base.html");
const OUT_DIR = join(ROOT, "public/assets/og");
const FONT_PATH = join(ROOT, "src/assets/fonts/outfit-latin.woff2");

/* ── Design system tokens (Gruvbox Dark) ── */
const T = {
  bg: "#1d2021",
  panel: "#282828",
  panelRaised: "#32302f",
  fg: "#ebdbb2",
  fgStrong: "#fbf1c7",
  fgMuted: "#bdae93",
  muted: "#a89984",
  primary: "#458588",
  accent: "#689d6a",
  purple: "#b16286",
  success: "#98971a",
  warning: "#d79921",
  destructive: "#cc241d",
  border: "#504945",
};

/* ── Page manifest: filename → { title, desc, accent, tag? } ── */
const PAGES = {
  /* ── Core pages ── */
  "home.png": {
    title: "SpielOS",
    desc: "AI employee and department platform. Build roles, skills, workflows, and evaluations — then direct your AI team from one place.",
    accent: T.primary,
  },
  "about.png": {
    title: "About SpielOS",
    desc: "The platform for building and directing AI employees and departments.",
    accent: T.primary,
  },
  "contact.png": {
    title: "Contact",
    desc: "Get in touch about SpielOS, partnerships, or working together.",
    accent: T.accent,
  },
  "blog.png": {
    title: "Notes",
    desc: "Writing about agent systems, context, workflows, evaluations, and building in public.",
    accent: T.purple,
  },
  "guides.png": {
    title: "Guides",
    desc: "Step-by-step guides for building AI departments with SpielOS.",
    accent: T.accent,
  },
  "use-cases.png": {
    title: "Use Cases",
    desc: "How companies use SpielOS to build AI departments for real work.",
    accent: T.warning,
  },
  "waitlist.png": {
    title: "Join the Waitlist",
    desc: "Get early access to SpielOS and start building your first AI department.",
    accent: T.primary,
  },
  "SpielOS.png": {
    title: "SpielOS v1",
    desc: "The open-source AI orchestration platform for roles, skills, context, and workflows.",
    accent: T.primary,
  },
  "404.png": {
    title: "Page Not Found",
    desc: "The page you are looking for does not exist.",
    accent: T.destructive,
  },

  /* ── Features hub ── */
  "features.png": {
    title: "Features",
    desc: "The four-layer architecture behind SpielOS: chat, context, harness, and infrastructure.",
    accent: T.primary,
  },
  "features-chat.png": {
    title: "Chat",
    desc: "Director Mode and Direct Mode for interacting with your AI department.",
    accent: T.primary,
    tag: "Chat",
  },
  "features-chat-director-mode.png": {
    title: "Director Mode",
    desc: "Long-running agent sessions with human approval, branching, and multi-step execution.",
    accent: T.purple,
    tag: "Director Mode",
  },
  "features-chat-direct-mode.png": {
    title: "Direct Mode",
    desc: "Instant workflow execution and scheduling from chat.",
    accent: T.accent,
    tag: "Direct Mode",
  },
  "features-context.png": {
    title: "Context",
    desc: "Files, strategy, and memory — the knowledge layer for your AI employees.",
    accent: T.accent,
    tag: "Context",
  },
  "features-context-files.png": {
    title: "Files",
    desc: "Agent knowledge base — structured file access for roles and skills.",
    accent: T.accent,
    tag: "Files",
  },
  "features-context-strategy.png": {
    title: "Strategy",
    desc: "Prompt and instruction management for consistent AI behavior.",
    accent: T.warning,
    tag: "Strategy",
  },
  "features-context-memory.png": {
    title: "Memory & Dreaming",
    desc: "Persistent agent memory with background reflection and learning.",
    accent: T.purple,
    tag: "Memory",
  },
  "features-harness.png": {
    title: "Harness",
    desc: "Agents, skills, workflows, and evaluations — the execution layer.",
    accent: T.warning,
    tag: "Harness",
  },
  "features-harness-agents.png": {
    title: "Agents",
    desc: "Define AI employees with roles, guardrails, and responsibilities.",
    accent: T.primary,
    tag: "Agents",
  },
  "features-harness-skills.png": {
    title: "Skills",
    desc: "Reusable agent capabilities — composable building blocks for your AI team.",
    accent: T.accent,
    tag: "Skills",
  },
  "features-harness-workflows.png": {
    title: "Workflows",
    desc: "Multi-agent pipelines with visual builder and approval gates.",
    accent: T.purple,
    tag: "Workflows",
  },
  "features-harness-evals.png": {
    title: "Evals",
    desc: "Agent quality testing — evaluate output against defined criteria.",
    accent: T.warning,
    tag: "Evals",
  },
  "features-infrastructure.png": {
    title: "Infrastructure",
    desc: "Providers and connections — the integration layer for your AI department.",
    accent: T.destructive,
    tag: "Infrastructure",
  },
  "features-infrastructure-providers.png": {
    title: "Providers",
    desc: "Choose and configure LLM providers for your AI employees.",
    accent: T.primary,
    tag: "Providers",
  },
  "features-infrastructure-connections.png": {
    title: "Connections",
    desc: "MCP, OAuth, and API integrations for your AI workflows.",
    accent: T.accent,
    tag: "Connections",
  },

  /* ── Notes (reuse blog.png style with different titles) ── */
  "72-hour-sprint.png": { title: "72-Hour Content Sprint", desc: "How I built and shipped a full content system in three days.", accent: T.purple },
  "agentic-loops.png": { title: "From Declarative Rules to Agentic Loops", desc: "Why static prompts break and how to build adaptive agent systems.", accent: T.primary },
  "ai-war-price-intelligence.png": { title: "AI War: Price Intelligence", desc: "Building competitive price intelligence with AI agents.", accent: T.warning },
  "blog-rebuild-4h.png": { title: "Rebuilt My Blog in 4 Hours", desc: "How I migrated and shipped two posts the same night.", accent: T.accent },
  "content-pipeline.png": { title: "Content Pipeline", desc: "Building a systematic content creation pipeline with AI.", accent: T.primary },
  "decisions-are-content.png": { title: "Decisions Are Content", desc: "Why every business decision should be treated as durable content.", accent: T.purple },
  "deepseek-v4-official-launch.png": { title: "DeepSeek V4 Launch", desc: "Analysis of the DeepSeek V4 official launch and what it means.", accent: T.accent },
  "deepseek-v4-price-war.png": { title: "DeepSeek V4 Price War", desc: "How DeepSeek V4 changed the AI pricing landscape.", accent: T.warning },
  "gates-not-models.png": { title: "Gates, Not Models", desc: "Why the bottleneck in AI is quality gates, not model capability.", accent: T.destructive },
  "GLM5.2-Cost-Breakdown.png": { title: "GLM 5.2 Cost Breakdown", desc: "Detailed cost analysis of GLM 5.2 for production workloads.", accent: T.warning },
  "migration-audits.png": { title: "Migration Audits", desc: "How to audit and migrate AI systems without breaking production.", accent: T.accent },
  "pipeline-not-strategy.png": { title: "Pipeline, Not Strategy", desc: "Why AI success depends on execution pipelines, not strategy documents.", accent: T.primary },
  "positioning-state.png": { title: "Positioning State", desc: "The current state of AI positioning and market dynamics.", accent: T.purple },
  "rtl-design-system.png": { title: "RTL Design System", desc: "Building a bidirectional design system for Persian and English.", accent: T.accent },
  "second-brain.png": { title: "Second Brain", desc: "How I automated my content with a second brain system.", accent: T.primary },
  "seo-from-architecture.png": { title: "SEO from Architecture", desc: "Why technical SEO starts with information architecture.", accent: T.warning },
  "session-as-content.png": { title: "Session as Content", desc: "How building sessions become the content itself.", accent: T.purple },
  "sessions-to-posts.png": { title: "Sessions to Posts", desc: "Turning work sessions into published content automatically.", accent: T.accent },
  "spielos-open-source.png": { title: "SpielOS Open Source", desc: "Why I made SpielOS open source and what it means for the platform.", accent: T.primary },
  "spielos-update.png": { title: "SpielOS Update", desc: "Latest updates, features, and improvements to SpielOS.", accent: T.accent },
  "tokens-per-sheep.png": { title: "Tokens Per Sheep", desc: "Token economics and cost optimization for AI workloads.", accent: T.warning },
  "translation-glossary.png": { title: "Translation Glossary", desc: "Building and maintaining a translation glossary for AI systems.", accent: T.purple },
  "skills-repo.png": { title: "Turn Your Website Into a Content Engine With These 10 Agent Skills", desc: "Video creation from HTML, content writing, Persian translation, SEO, analytics, design systems. Full repo, full scripts, full templates.", accent: T.accent },
  "waitlist-supabase.png": { title: "Waitlist + Supabase", desc: "How I built the SpielOS waitlist with Supabase.", accent: T.accent },
};

/* ── MIME types ── */
const MIME = {
  ".html": "text/html", ".css": "text/css", ".js": "application/javascript",
  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg",
  ".svg": "image/svg+xml", ".woff2": "font/woff2", ".woff": "font/woff",
};

/* ── Static server ── */
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
      res({ server, port, url: `http://127.0.0.1:${port}` });
    });
  });
}

/* ── Main ── */
async function generate() {
  const templateHtml = readFileSync(TEMPLATE, "utf-8");
  const { server, port, url: baseUrl } = await startServer();
  console.log(`  Server: ${baseUrl}`);

  const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser = await puppeteer.launch({
    headless: "shell",
    executablePath: CHROME_PATH,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--font-render-hinting=none", "--allow-file-access-from-files"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 630, deviceScaleFactor: 1 });

  if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true });

  const entries = Object.entries(PAGES);
  let done = 0;

  for (const [filename, meta] of entries) {
    done++;
    const tagColor = meta.accent;
    const tagBg = meta.accent + "22";

    const html = templateHtml
      .replace('id="title"', `id="title"`)
      .replace('id="desc"', `id="desc"`)
      .replace(`id="glow"`, `id="glow" style="background:${meta.accent};"`)
      .replace(`id="accentBar"`, `id="accentBar" style="background:${meta.accent};"`)
      .replace(`id="tag"`, `id="tag"`)
      .replace("</body>", `
        <script>
          document.getElementById("title").textContent = ${JSON.stringify(meta.title)};
          document.getElementById("desc").textContent = ${JSON.stringify(meta.desc)};
          ${meta.tag ? `const tag = document.getElementById("tag"); tag.textContent = ${JSON.stringify(meta.tag)}; tag.style.background = ${JSON.stringify(tagBg)}; tag.style.color = ${JSON.stringify(tagColor)}; tag.style.display = "inline-flex";` : `document.getElementById("tag").style.display = "none";`}
        </script>
      </body>`);

    const tmpFile = join(ROOT, `og-tmp-${filename}.html`);
    writeFileSync(tmpFile, html);

    const pageUrl = `${baseUrl}/og-tmp-${filename}.html`;
    await page.goto(pageUrl, { waitUntil: "networkidle0", timeout: 15000 });
    await page.evaluate(() => document.fonts.ready);
    await new Promise((r) => setTimeout(r, 300));

    await page.screenshot({
      path: join(OUT_DIR, filename),
      type: "png",
      clip: { x: 0, y: 0, width: 1200, height: 630 },
    });

    process.stdout.write(`\r  [${done}/${entries.length}] ${filename}`);
  }

  console.log("\n");
  await browser.close();
  server.close();

  /* cleanup tmp files */
  for (const filename of Object.keys(PAGES)) {
    const tmp = join(ROOT, `og-tmp-${filename}.html`);
    if (existsSync(tmp)) {
      const { unlinkSync } = await import("fs");
      unlinkSync(tmp);
    }
  }

  console.log(`  Done! ${Object.keys(PAGES).length} OG images → public/assets/og/\n`);
}

generate().catch((err) => {
  console.error("OG generation failed:", err);
  process.exit(1);
});
