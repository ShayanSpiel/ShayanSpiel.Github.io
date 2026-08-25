// BRAND LOGOS — real tool logos as raw SVG strings, keyed by SOFTWARE_SOLUTIONS key.
// Single source of truth for every surface that shows a tool brand mark
// (nav mega menu, homepage tool grid, solutions hub, software hub,
// workflow pages, software solution pages). Each SVG is colored through
// its own brand palette and sized by the consuming container via
// `[&>svg]:h-* [&>svg]:w-*` utilities.

const files = import.meta.glob("../assets/brand-logos/*.svg", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

/** Raw brand-logo SVG for a software key (e.g. "zapier"), or "" when absent. */
export function brandLogo(key: string): string {
  return files[`../assets/brand-logos/${key}.svg`] ?? "";
}

/** True when a real logo exists for the given software key. */
export function hasBrandLogo(key: string): boolean {
  return brandLogo(key) !== "";
}
