export const SITE = {
  name: "SpielOS",
  tagline: "Notes from the gap",
  url: "https://spielos.xyz",
  description: "I spent ten years building startup systems and more than 20 products. SpielOS is where that work finally became one AI employee and department platform.",
  descriptionFa: "یه دهه سیستم‌های استارتاپ و بیشتر از ۲۰ محصول ساختم. SpielOS جاییه که اون کار بالاخره تبدیل به یه سکوی کارمند و بخش AI شد.",
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
};

export const FORMS = {
  contact: "https://formsubmit.co/66shayan@gmail.com",
};

export const WAITLIST_URL = "/waitlist/";

export const NAV_LINKS = {
  default: [
    { label: "SpielOS", href: "/waitlist/" },
    { label: "Features", href: "/features/" },
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
    { label: "SpielOS", href: "/waitlist/" },
    { label: "Features", href: "/features/" },
    { label: "Notes", href: "/notes/" },
    { label: "Founder", href: "/founder/" },
    { label: "Join waitlist", href: "/waitlist/" },
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
