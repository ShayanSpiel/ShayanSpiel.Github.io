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
        // Exclude thin placeholder pages
        if (path === '/guides/' || path === '/fa/guides/') return false;
        if (path === '/use-cases/' || path === '/fa/use-cases/') return false;
        // Exclude /posts/ redirect stubs (301 to /notes/)
        if (path === '/posts/' || path.startsWith('/posts/')) return false;
        // Exclude /shayan/ redirect stub (301 to /founder/)
        if (path === '/shayan/') return false;
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
