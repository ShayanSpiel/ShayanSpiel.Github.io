/**
 * Centralized i18n module.
 *
 * Single source of truth for locale detection, URL generation, and
 * locale-aware navigation. No hardcoded /fa/ in components.
 */
import { type Locale } from "./translations";

export type { Locale };

export const DEFAULT_LOCALE: Locale = "en";
export const LOCALES: Locale[] = ["en", "fa"];
export const LOCALE_PREFIX: Record<Locale, string> = { en: "", fa: "/fa" };

/**
 * Detect locale from an Astro URL pathname.
 */
export function getLocaleFromPathname(pathname: string): Locale {
  if (pathname.startsWith("/fa/")) return "fa";
  if (pathname === "/fa") return "fa";
  return DEFAULT_LOCALE;
}

/**
 * Generate a localized URL for a given path.
 * EN: /notes/ → /notes/
 * FA: /notes/ → /fa/notes/
 * Waitlist stays English-only (no FA version).
 */
export function localizePath(path: string, locale: Locale = DEFAULT_LOCALE): string {
  const prefix = LOCALE_PREFIX[locale];
  if (!prefix) return path;
  if (path.startsWith("/fa/")) return path;
  return `${prefix}${path}`;
}

/**
 * Build the language switcher URL.
 * Toggles between EN and FA for the same page.
 */
export function getSwitchLocaleUrl(currentPathname: string, currentLocale: Locale): string {
  const targetLocale = currentLocale === "en" ? "fa" : "en";
  const prefix = LOCALE_PREFIX[targetLocale];

  if (currentLocale === "en") {
    // EN → FA: prepend /fa/
    return `${prefix}${currentPathname}`;
  }

  // FA → EN: strip /fa/ prefix
  return currentPathname.replace(/^\/fa(\/|$)/, "/") || "/";
}
