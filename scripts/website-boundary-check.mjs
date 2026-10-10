#!/usr/bin/env node
import { existsSync, readdirSync, readFileSync, lstatSync } from "node:fs";
import { dirname, extname, join, resolve } from "node:path";

import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const failures = [];
const fail = (message) => failures.push(message);

try {
  const marker = JSON.parse(readFileSync(join(root, ".spielos-boundary.json"), "utf8"));
  if (marker.role !== "website") fail("Repository role must be website.");
} catch {
  fail("A valid website repository role marker is required.");
}
if (!existsSync(join(root, "AGENTS.md"))) fail("Root AGENTS.md instructions are required.");

const prohibitedPaths = [
  ".agents/company",
  ".agents/skills",
  ".spielos",
  ".codex",
  ".opencode",
  ".claude",
  "CLAUDE.md",
  "opencode.json",
  "skills-lock.json",
  "outbound",
  "data",
  "attio-bulk-import-20260901.csv",
  "scripts/sync-live-timeline.py",
  "scripts/promote-campaign-assets.mjs",
  "scripts/html-motion",
  "scripts/videography",
  "test/html-motion",
  "scripts/render-video.js",
  "scripts/render-all.sh",
  "scripts/tts-gemini.js",
  "scripts/mix-audio.js",
  "scripts/verify-video-deliverable.js",
];

for (const path of prohibitedPaths) {
  if (existsSync(join(root, path))) fail(`Harness-owned path remains in the website repository: ${path}`);
}

const sourceRoots = ["AGENTS.md", "agents.md", "README.md", "docs", "scripts", "src", "supabase", "test", "public", "package.json"];
const scannedExtensions = new Set([".astro", ".cjs", ".css", ".html", ".js", ".json", ".md", ".mjs", ".py", ".ts"]);
const forbiddenTokens = [
  ".agents/" + "company/",
  ".agents/" + "skills/",
  ".spielos" + "/",
  "scripts/" + "html-motion/",
  "scripts/" + "videography/",
  "company" + ".sqlite",
];

function inspect(path) {
  const absolute = join(root, path);
  if (!existsSync(absolute)) return;
  const stat = lstatSync(absolute);
  if (stat.isSymbolicLink()) {
    fail(`Website boundary refuses filesystem links: ${path}`);
    return;
  }
  if (stat.isDirectory()) {
    for (const name of readdirSync(absolute)) {
      if (["node_modules", "dist", ".astro", ".git"].includes(name)) continue;
      inspect(join(path, name));
    }
    return;
  }
  if (path === "scripts/website-boundary-check.mjs" || !scannedExtensions.has(extname(path))) return;
  const content = readFileSync(absolute, "utf8");
  for (const token of forbiddenTokens) {
    if (content.includes(token)) fail(`Website source points into the harness: ${path} (${token})`);
  }
}

for (const path of sourceRoots) inspect(path);

if (failures.length) {
  console.error(`Website boundary check failed (${failures.length}):`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("Website and harness ownership boundary is clean.");
