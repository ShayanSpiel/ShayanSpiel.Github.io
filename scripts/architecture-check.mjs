#!/usr/bin/env node
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const failures = [];
const read = (file) => readFileSync(join(root, file), "utf8");
const expect = (condition, message) => {
  if (!condition) failures.push(message);
};

const config = read("src/config.ts");
const agents = read("AGENTS.md");
const baseLayout = read("src/layouts/BaseLayout.astro");

expect(config.includes('SERVICES_PATH = "/services/"'), "navbar CTA path must be /services/");
expect(config.includes('AGENT_BRIEFING_PATH = "/services/#agent-briefing"'), "Agent Briefing CTA must target its services section");
expect(agents.includes("buyer and lead-conversion website"), "AGENTS.md must describe the buyer/lead strategy");
expect(agents.includes("The only active skill system is `.agents/skills/`"), "AGENTS.md must define one active skill system");
expect(!existsSync(join(root, "Skills")), "legacy Skills submodule must not remain beside .agents/skills");
expect(!read("src/components/LanguageSwitcher.astro").includes("<svg"), "LanguageSwitcher must use Boxicons, not an inline SVG icon");
expect(!read("src/components/SocialIcons.astro").includes("set:html"), "SocialIcons must use Boxicons, not injected SVG markup");
expect(read("src/pages/use-cases/index.astro").includes('robots="noindex, follow"'), "placeholder use-cases page must be noindex");
expect(read("src/pages/contact/thank-you.astro").includes('robots="noindex, follow"'), "contact thank-you page must be noindex");
expect(read("src/pages/spielos-v1.astro").includes('robots="noindex, follow"'), "archived v1 page must be noindex");
expect(baseLayout.includes("lead_form_submit"), "BaseLayout must track generic lead form submissions");
expect(!baseLayout.includes("waitlist_form_submit"), "BaseLayout must not use waitlist-specific primary event names");

if (failures.length) {
  console.error(`Architecture checks failed (${failures.length}):`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("Architecture checks passed.");
