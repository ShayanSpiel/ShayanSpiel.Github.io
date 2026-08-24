import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwind from "@astrojs/tailwind";

export default defineConfig({
  site: "https://spielos.xyz",
  base: "/",
  // "ignore" accepts both /path and /path/. With "always", the dev/preview
  // server hard-404s no-slash URLs before the custom 404.astro is considered,
  // so the 404 page would not show for every 404 scenario. "ignore" routes
  // every URL form through the same pipeline, so the custom 404 renders
  // everywhere. Output stays directory-based (build.format default), so all
  // generated and canonical URLs keep their trailing slashes.
  trailingSlash: "ignore",
  integrations: [
    mdx(),
    sitemap({
      filter: (page) => {
        // Exclude 404 pages
        if (page.includes('/404')) return false;
        const path = new URL(page).pathname;
        // 301 redirect stubs — kept on disk only for backward-compatible
        // redirects; they hold no canonical content and must not appear in
        // the sitemap.
        // Legacy software pages: /[software]-ai-automation/ → /solutions/software/{slug}/
        if (/^\/[a-z0-9-]+-ai-automation\/$/.test(path)) return false;
        // Software hub stubs: /software/ and /fa/software/ → /solutions/
        if (path === '/software/' || path === '/fa/software/') return false;
        // Use-case tree stubs: every /use-cases/** and /fa/use-cases/** path
        // (hub, department pages, design gallery) → /solutions/ or
        // /solutions/ai-departments/**
        if (/^\/(fa\/)?use-cases(\/|$)/.test(path)) return false;
        return true;
      },
    }),
    tailwind(),
  ],
  i18n: {
    defaultLocale: "en",
    locales: ["en", "fa"],
    routing: {
      prefixDefaultLocale: false,
    },
  },
});
