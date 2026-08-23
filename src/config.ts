import { SOFTWARE_SOLUTIONS } from "./data/software-solutions";

export const SITE = {
  name: "SpielOS",
  tagline: "AI workflow systems for established businesses",
  url: "https://spielos.xyz",
  description: "SpielOS runs real company work through supervised AI departments. Start with one repetitive workflow and a clear Agent Brief.",
  descriptionFa: "SpielOS کارهای واقعی شرکت رو با دپارتمان‌های AI و زیر نظر آدم‌ها اجرا می‌کنه. از یک ورک‌فلوی تکراری و یک Agent Brief روشن شروع کن.",
  locale: "en",
  colorScheme: "dark",
  themeColor: "#282828",
  defaultTheme: "gruvbox-dark",
};

export const AUTHOR = {
  name: "Shayan Spiel",
  email: "66shayan@gmail.com",
  handle: "@ShayanSpiel",
  url: "https://spielos.xyz",
  title: "Founder of SpielOS · Agent Harness Architect",
  jobTitle: "Founder of SpielOS · Agent Harness Architect",
  description: "Founder of SpielOS · Agent Harness Architect",
  sameAs: [
    "https://x.com/ShayanSpiel",
    "https://linkedin.com/in/shayantawabi",
    "https://github.com/ShayanSpiel",
  ],
};

export const FOUNDER = {
  name: "Shayan Spiel",
  role: "Founder of SpielOS · Agent Harness Architect",
  location: "Tehran, Iran",
  education: "MBA in Strategy, University of Tehran, 2017",
  experienceYears: 10,
  productAttempts: 20,
  coreParagraph:
    "I built SpielOS for companies that know AI should become part of how they work, but do not yet have a reliable structure for roles, instructions, knowledge, tools, human decisions, and quality control. It is the product I needed while repeatedly designing these systems myself.",
  proof: [
    { value: "3M", label: "Black Friday visitors" },
    { value: "560K", label: "App installs across two seasons" },
    { value: "50%", label: "Year-over-year revenue growth" },
  ],
  products: [
    {
      name: "SpielOS",
      status: "Active" as const,
      description: "Open-source AI orchestration platform. File-based agent harness with roles, skills, context management, and long-horizon execution.",
      url: "https://github.com/ShayanSpiel/SpielOS",
    },
    {
      name: "CacheCatch",
      status: "Active" as const,
      description: "The first prompt-cache audit and optimization tool for AI agents. Finds context waste, prompt cache misses, and hidden agent cost leaks.",
      url: "https://github.com/ShayanSpiel/CacheCatch",
    },
    {
      name: "Spiel-OS",
      status: "Archive" as const,
      description: "Earlier version of the SpielOS content engine. Markdown-driven marketing team with 8 roles and a 12-state pipeline.",
      url: "https://github.com/ShayanSpiel/Spiel-OS",
    },
    {
      name: "Vibebaba",
      status: "Archive" as const,
      description: "Experimental vibe coding platform. Multi-role agent orchestration on LangGraph with frontend generation and PocketBase backend.",
      url: "https://github.com/ShayanSpiel/vibebaba",
    },
    {
      name: "ShayanWiki",
      status: "Active" as const,
      description: "Markdown-based wiki with content pipeline.",
      url: "https://github.com/ShayanSpiel/ShayanWiki",
    },
  ],
};

export const SEO = {
  ogImageWidth: "1200",
  ogImageHeight: "630",
  robots: "index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1",
  defaultImage: "/assets/og/home.png",
};

export const SOCIAL = {
  x: "https://x.com/ShayanSpiel",
  linkedin: "https://linkedin.com/in/shayantawabi",
  github: "https://github.com/ShayanSpiel",
};

export const ANALYTICS = {
  googleAnalyticsId: "G-P43CBK4EEX",
  googleSearchConsoleVerification: "LvKy8YQ0XGZPYu4bQ9JIhaFmdX3W9Ag7eSPYGTE-ORU",
  posthogApiKey: "phc_1osIFVXYDFr7Z00RN5gRaF4kRfZ1safm9c7NswRfKpm",
  posthogApiHost: "https://t.spielos.xyz",
  debug: false,
  contentSources: ["threads", "youtube"] as const,
  attributionParameters: ["utm_source", "utm_medium", "utm_campaign", "utm_content"] as const,
};

export const FORMS = {
  contact: "https://formsubmit.co/66shayan@gmail.com",
};

// Compatibility alias for older imports. The public waitlist route now redirects here.
export const WAITLIST_URL = "/features/";
export const SERVICES_PATH = "/services/";

// Apply funnel (Phase 1): free-review application page fed by the pricing page.
export const APPLY_PATH = "/apply/";


// The Agent Brief request form was removed; the Agent Brief page is now purely
// informational, so the canonical destination is the page itself (no #request).
export const AGENT_BRIEFING_PATH = "/services/agent-brief/";
export const AGENT_BRIEF_REQUEST_PATH = "/services/agent-brief/";

export interface NavChildLink {
  label: string;
  href: string;
  /** Renders a small liveness ping dot beside the label. */
  live?: boolean;
  /** Category block items. The dropdown renders every child-with-children as
   *  one flat category (header + plain item links). There are NO second-level
   *  sub-menus or flyouts anywhere in the site navigation. */
  children?: NavChildLink[];
  /** Desktop presentation: how many columns the category items render in. */
  columns?: 1 | 2;
  /** Trailing hub link rendered after the item list ("See All"). */
  seeAll?: { label: string; href: string };
}

export interface NavLink {
  label: string;
  href: string;
  /** Dropdown trigger only — renders as a button, never navigates. */
  triggerOnly?: boolean;
  /** Renders a small liveness ping dot beside the label. */
  live?: boolean;
  /** Category blocks rendered as one flat two-column mega menu on desktop
   *  and tidy grouped accordion items on mobile. */
  children?: NavChildLink[];
}

export const NAV_LINKS: { default: NavLink[]; showcase: NavLink[] } = {
  default: [
    { label: "Services", href: "/services/" },
    {
      label: "Solutions",
      href: "/solutions/",
      triggerOnly: true,
      children: [
        {
          label: "AI Departments",
          href: "/solutions/ai-departments/",
          columns: 1,
          children: [
            { label: "AI Design Department", href: "/solutions/ai-departments/design/" },
            { label: "AI Content Department", href: "/solutions/ai-departments/content/" },
            { label: "AI Marketing Department", href: "/solutions/ai-departments/marketing/" },
            { label: "AI SEO Department", href: "/solutions/ai-departments/seo/" },
            { label: "AI Analytics Department", href: "/solutions/ai-departments/analytics/" },
            { label: "Design Template Gallery", href: "/solutions/ai-departments/design/gallery/" },
          ],
          seeAll: { label: "All AI Departments", href: "/solutions/ai-departments/" },
        },
        {
          label: "By Workflow",
          href: "/solutions/workflows/",
          columns: 1,
          children: [
            { label: "Follow-Up Automation", href: "/solutions/workflows/follow-up-automation/" },
            { label: "Data Entry Automation", href: "/solutions/workflows/data-entry-automation/" },
            { label: "Client Onboarding Automation", href: "/solutions/workflows/client-onboarding-automation/" },
            { label: "Client Intake Automation", href: "/solutions/workflows/client-intake-automation/" },
            { label: "Document Collection Automation", href: "/solutions/workflows/document-collection-automation/" },
            { label: "Lead Qualification Automation", href: "/solutions/workflows/lead-qualification-automation/" },
          ],
          seeAll: { label: "All Workflows", href: "/solutions/workflows/" },
        },
        {
          label: "Software Automation",
          href: "/solutions/software/",
          columns: 1,
          children: [
            { label: "Zapier Automation", href: "/solutions/software/zapier-automation/" },
            { label: "Slack Automation", href: "/solutions/software/slack-automation/" },
            { label: "Gmail Automation", href: "/solutions/software/gmail-automation/" },
            { label: "HubSpot Automation", href: "/solutions/software/hubspot-automation/" },
            { label: "Notion Automation", href: "/solutions/software/notion-automation/" },
            { label: "Attio Automation", href: "/solutions/software/attio-automation/" },
          ],
          seeAll: { label: "All Software", href: "/solutions/software/" },
        },
        {
          label: "SpielOS \u2192 AI Company",
          href: "/features/",
          columns: 1,
          children: [
            { label: "Director", href: "/features/director/" },
            { label: "Departments", href: "/features/departments/" },
            { label: "Workflows", href: "/features/workflows/" },
            { label: "Agents", href: "/features/agents/" },
            { label: "Skills", href: "/features/skills/" },
            { label: "Evals", href: "/features/evals/" },
          ],
          seeAll: { label: "See the whole company", href: "/features/" },
        },
      ],
    },
    { label: "Pricing", href: "/pricing/" },
    { label: "Live", href: "/live/", live: true },
    { label: "Notes", href: "/notes/" },
    { label: "Founder", href: "/founder/" },
  ],
  showcase: [
    { label: "How it works", href: "#how-it-works" },
    { label: "Features", href: "#features" },
    { label: "Director", href: "#director" },
  ],
};

export const FOOTER_LINKS = {
  default: [
    { label: "Agent Brief", href: AGENT_BRIEF_REQUEST_PATH },
    { label: "Services", href: "/services/" },
    { label: "Pricing", href: "/pricing/" },
    { label: "Apply", href: APPLY_PATH },
    { label: "Features", href: "/features/" },
    { label: "Live", href: "/live/" },
    { label: "Notes", href: "/notes/" },
    { label: "Founder", href: "/founder/" },
    { label: "Contact", href: "/contact/" },
  ],
  showcase: [
    { label: "Privacy", href: "#" },
    { label: "Terms", href: "#" },
  ],
};

export const THEMES = {
  all: [
    "gruvbox-dark", "gruvbox-light",
    "monochrome-dark", "monochrome-light",
    "blue-dark", "blue-light",
    "discord-dark", "discord-light",
    "black-gold-dark", "black-gold-light",
  ],
  dark: [
    "gruvbox-dark", "monochrome-dark",
    "blue-dark", "discord-dark", "black-gold-dark",
  ],
};

export const RSS = {
  title: "SpielOS — Notes from building SpielOS",
  description: "Writing about agent systems, context, workflows, evaluations, product failures, and the process of building SpielOS.",
  stylesheet: false,
};
export const SUPABASE = {
  url: "https://avyvodinzklyaoketxye.supabase.co",
  anonKey: "sb_publishable_bptu_veUtq7L-qs1ZALYXg_je6vxoh5",
};
