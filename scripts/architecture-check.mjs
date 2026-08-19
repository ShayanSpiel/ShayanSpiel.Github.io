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
expect(config.includes('BOOKING_URL = "https://cal.com/shayanspiel/15min?overlayCalendar=true"'), "canonical Cal.com Discovery Call URL stays in config");
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
expect(baseLayout.includes("app.cal.com/embed/embed.js") && baseLayout.includes("rel=\"preconnect\" href=\"https://app.cal.com\""), "BaseLayout must load the Cal embed script site-wide with preconnect for the fastest on-page popup");
expect(!baseLayout.includes("isBookPage") && !baseLayout.includes("booking_page_viewed"), "the /book/ page navigation and its page-view event must be gone");
expect(!baseLayout.includes("Cal('modal'") && !baseLayout.includes("openBookingOverlay"), "BaseLayout must not wrap Cal in a modal overlay");
expect(baseLayout.includes("booking_cta_clicked"), "BaseLayout must fire the PostHog/GA booking CTA event");

expect(baseLayout.includes("booked_call"), "BaseLayout must capture successful bookings from the Cal embed");
expect(!existsSync(join(root, "src/pages/book.astro")) && !existsSync(join(root, "src/pages/fa/book.astro")) && !existsSync(join(root, "src/components/BookingEmbed.astro")), "the /book/ pages and embed component are deleted");
expect(read("src/components/Nav.astro").includes('data-cal-link={BOOKING_LINK}'), "Nav CTAs must be native Cal embed popup triggers");
expect(!read("src/components/LanguageSwitcher.astro").includes("<svg"), "LanguageSwitcher must use Boxicons, not an inline SVG icon");
expect(!read("src/components/SocialIcons.astro").includes("set:html"), "SocialIcons must use Boxicons, not injected SVG markup");
expect(read("src/pages/use-cases/index.astro").includes('robots="noindex, follow"'), "placeholder use-cases page must be noindex");
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
