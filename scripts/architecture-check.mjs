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

expect(config.includes('APPLY_PATH = "/apply/"'), "navbar CTA path must be the Apply funnel (/apply/)");
expect(config.includes('BOOKING_CONFIG = { layout: "month_view", theme: "dark", "ui.color-scheme": "dark" } as const'), "canonical Cal.com Discovery Call embed popup config stays in config");
expect(config.includes('BOOKING_LINK = "shayanspiel/15min"'), "booking CTAs are native Cal embed triggers via BOOKING_LINK");
expect(!config.includes("BOOKING_PAGE_PATH"), "the /book/ navigation route must be gone from config");
expect(config.includes('AGENT_BRIEFING_PATH = "/services/agent-brief/"'), "Agent Brief page stays an informational route");
expect(agents.includes("buyer and lead-conversion website"), "AGENTS.md must describe the buyer/lead strategy");
expect(agents.includes("The only active skill system is `.agents/skills/`"), "AGENTS.md must define one active skill system");
expect(!existsSync(join(root, "Skills")), "legacy Skills submodule must not remain beside .agents/skills");
expect(!existsSync(join(root, "src/components/ContactModal.astro")), "ContactModal must be removed; CTAs open the Cal embed on the page");
expect(!existsSync(join(root, "src/components/AgentBriefForm.astro")), "AgentBriefForm must be removed; the Agent Brief page is informational");
expect(!baseLayout.includes("data-open-contact-modal"), "BaseLayout must not wire the retired contact modal");
expect(baseLayout.includes("book_call"), "BaseLayout must track booking CTA clicks");
expect(baseLayout.includes("bookingEnabled") && baseLayout.includes("app.cal.com/embed/embed.js") && baseLayout.includes("bookingEnabled && <link rel=\"preconnect\""), "BaseLayout must load Cal resources only on Apply and Contact");
expect(!baseLayout.includes("isBookPage") && !baseLayout.includes("booking_page_viewed"), "the /book/ page navigation and its page-view event must be gone");
expect(!baseLayout.includes("Cal('modal'") && !baseLayout.includes("openBookingOverlay"), "BaseLayout must not wrap Cal in a modal overlay");
expect(baseLayout.includes("booking_cta_clicked"), "BaseLayout must fire the PostHog/GA booking CTA event");

expect(baseLayout.includes("booked_call"), "BaseLayout must capture successful bookings from the Cal embed");
expect(!existsSync(join(root, "src/pages/book.astro")) && !existsSync(join(root, "src/pages/fa/book.astro")) && !existsSync(join(root, "src/components/BookingEmbed.astro")), "the /book/ pages and embed component are deleted");
const nav = read("src/components/Nav.astro");
expect(nav.includes("APPLY_PATH") && nav.includes('data-cta-location="nav"') && nav.includes('data-cta-location="nav_mobile"'), "Nav primary CTA must be the Apply funnel link on desktop and mobile");
expect(!read("src/components/LanguageSwitcher.astro").includes("<svg"), "LanguageSwitcher must use Boxicons, not an inline SVG icon");
expect(!read("src/components/SocialIcons.astro").includes("<svg") && !read("src/components/SocialIcons.astro").includes("set:html"), "SocialIcons must use Boxicons only");
expect(read("src/pages/use-cases/index.astro").includes("Astro.redirect") && read("src/pages/use-cases/index.astro").includes('"/solutions/"'), "legacy use-cases hub must remain a 301 redirect to Solutions");
expect(baseLayout.includes('boxicons-subset.css') && !baseLayout.includes('boxicons/css/boxicons.min.css'), "the site must ship the generated Boxicons subset, not the full icon library");
expect(!read("src/pages/apply.astro").includes("66shayan@gmail.com"), "Apply must not hardcode a legacy email address");
// Owner directive 2026-08-26: real brand marks are live on Nav + ToolGrid via
// the single source of truth (src/data/brand-logos.ts). Boxicons remain the
// icon system for every non-brand UI icon.
expect(read("src/components/Nav.astro").includes("brandLogo") && read("src/components/home/ToolGrid.astro").includes("brandLogo"), "active navigation and tool surfaces must use the real brand-logo system (brandLogo from src/data/brand-logos.ts)");
expect(read("src/pages/contact/thank-you.astro").includes('robots="noindex, follow"'), "contact thank-you page must be noindex");
expect(read("src/pages/spielos-v1.astro").includes('robots="noindex, follow"'), "archived v1 page must be noindex");
expect(baseLayout.includes("cta_clicked") && baseLayout.includes("book_call"), "BaseLayout must track booking CTA clicks as book_call");
expect(baseLayout.includes("data-cal-cta"), "BaseLayout must recognize direct booking CTA anchors");
expect(!baseLayout.includes("waitlist_form_submit"), "BaseLayout must not use waitlist-specific primary event names");

if (failures.length) {
  console.error(`Architecture checks failed (${failures.length}):`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("Architecture checks passed.");
