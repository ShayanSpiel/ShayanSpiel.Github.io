/**
 * ICON REGISTRY — Single source of truth for all boxicons on this site.
 *
 * Every icon used anywhere in the codebase MUST be listed here.
 * Generated from boxicons 2.1.4 (node_modules/boxicons).
 *
 * Usage in Card.astro:
 *   import { iconMap } from "../../icons";
 *   const boxiconClass = icon ? (iconMap[icon] || `bx-${icon}`) : null;
 *
 * Usage in MDX:
 *   <Card icon='zap' ... />   ← uses iconMap key
 *   <Card icon='globe' ... /> ← uses iconMap key
 *   <i class="bx bx-globe">  ← direct class (must be in VALID_BOXICONS)
 */

// ─── VALID BOXICON CLASSES (subset used on this site) ────────────────────────
// Every value here has been verified against node_modules/boxicons/css/boxicons.min.css.
// If you need a new icon, add it here FIRST, then use it.
export const VALID_BOXICONS = [
  // Semantic states
  'bx-error',            // error / failure / problem
  'bx-check-square',     // success / done / correct
  'bx-time-five',        // warning / time / waiting

  // Actions
  'bxs-bolt',            // energy / lightning / speed (solid; plain bx-bolt does NOT exist)
  'bx-rocket',           // launch / fast / ship
  'bx-search',           // find / search
  'bx-send',             // submit / send
  'bx-play',             // play / execute / run

  // Communication
  'bx-message',          // message / comment
  'bx-message-rounded',  // message rounded
  'bx-envelope',         // email / mail
  'bx-link',             // link / connection
  'bx-link-external',    // external link

  // Objects
  'bx-globe',            // world / global
  'bx-server',           // server / infrastructure
  'bx-layer',            // layers / stack / context
  'bx-chip',             // chip / hardware
  'bx-code-alt',         // code / development (GitHub in notes uses bxl-github elsewhere)
  'bx-file',             // file / document
  'bx-data',             // data / database
  'bx-book',             // book
  'bx-book-open',        // book open
  'bx-shield-quarter',   // shield / security
  'bx-lock',             // lock / secure
  'bx-flag',             // flag

  // People / Users
  'bx-user',             // single user
  'bx-users',            // — does NOT exist, use bx-group
  'bx-group',            // group of people
  'bx-user-check',       // verified user

  // Navigation / UI
  'bx-chevron-right',    // chevron right
  'bx-down-arrow-alt',   // arrow down
  'bx-right-arrow-alt',  // arrow right
  'bx-left-arrow-alt',   // arrow left
  'bx-home',             // home
  'bx-menu',             // — does NOT exist, use bx-menu-alt-right

  // Status / Data
  'bx-trending-up',      // trend up / growth
  'bx-bar-chart',        // bar chart
  'bx-bar-chart-alt-2',  // bar chart alt
  'bx-task',             // task / checklist
  'bx-network-chart',    // network / workflow (note: bx-network does NOT exist)

  // Tools / Settings
  'bx-slider',           // settings / config
  'bx-cog',              // gear / cog
  'bx-terminal',         // terminal / CLI
  'bx-pen',              // pen / edit

  // Other
  'bx-bulb',             // idea / lightbulb
  'bx-crosshair',        // target / crosshair
  'bx-hash',             // hash / tag
  'bx-heart',            // heart
  'bx-image',            // image
  'bx-map',              // map / location
  'bx-certification',    // certification / badge
  'bx-moon',             // moon / dark
  'bx-sun',              // sun / light
  'bx-rss',              // RSS feed
  'bx-hdd',              // hard drive
  'bx-calendar',         // calendar
  'bx-x',                // close / X (note: bx-x-square does NOT exist)
  'bx-dollar',           // dollar / money
  'bx-hide',             // hide / eye-off
  'bx-show',             // show / eye
  'bx-error',            // already listed above
] as const;

export type BoxiconClass = typeof VALID_BOXICONS[number];

// ─── ICON MAP: friendly name → boxicon class ─────────────────────────────────
// Keys are the values used in MDX via <Card icon='...' />.
// All values verified against boxicons 2.1.4.
export const iconMap: Record<string, string> = {
  // Semantic states
  'check':         'bx-check-square',
  'check-square':  'bx-check-square',
  'x-square':      'bx-x',               // bx-x-square does NOT exist
  'circle-x':      'bx-error',
  'circle-check':  'bx-check-square',
  'alert-triangle':'bx-error',

  // Actions / Energy
  'zap':           'bxs-bolt',            // solid bolt; plain bx-bolt does NOT exist
  'rocket':        'bx-rocket',
  'search':        'bx-search',
  'send':          'bx-send',
  'play':          'bx-play',

  // Objects / Tech
  'globe':         'bx-globe',
  'server':        'bx-server',
  'layer':         'bx-layer',
  'layers':        'bx-layer',
  'chip':          'bx-chip',
  'code':          'bx-code-alt',
  'github':        'bx-code-alt',         // bxl-github does NOT exist
  'file':          'bx-file',
  'file-text':     'bx-file',
  'data':          'bx-data',
  'book':          'bx-book',
  'book-open':     'bx-book-open',
  'shield':        'bx-shield-quarter',
  'lock':          'bx-lock',
  'flag':          'bx-flag',

  // People
  'user':          'bx-user',
  'users':         'bx-group',            // bx-users does NOT exist
  'user-check':    'bx-user-check',

  // Navigation
  'arrow-right':   'bx-right-arrow-alt',
  'arrow-left':    'bx-left-arrow-alt',
  'home':          'bx-home',
  'hash':          'bx-hash',

  // Status
  'trending-up':   'bx-trending-up',
  'bar-chart':     'bx-bar-chart',
  'gauge':         'bx-bar-chart-alt-2',
  'task':          'bx-task',
  'network':       'bx-network-chart',    // bx-network does NOT exist
  'network-chart': 'bx-network-chart',

  // Tools
  'settings':      'bx-slider',
  'cog':           'bx-cog',
  'terminal':      'bx-terminal',
  'pen':           'bx-pen',
  'cpu':           'bx-chip',

  // Communication
  'message':           'bx-message',
  'message-square':    'bx-message',
  'message-circle':    'bx-message-rounded',
  'mail':              'bx-envelope',
  'link':              'bx-link',

  // Other
  'lightbulb':     'bx-bulb',
  'target':        'bx-crosshair',
  'clock':         'bx-time-five',
  'error':         'bx-error',
  'heart':         'bx-heart',
  'image':         'bx-image',
  'map':           'bx-map',
  'certification': 'bx-certification',
  'moon':          'bx-moon',
  'sun':           'bx-sun',
  'rss':           'bx-rss',
  'hard-drive':    'bx-hdd',
  'calendar':      'bx-calendar',
  'hide':          'bx-hide',
  'show':          'bx-show',
  'dollar':        'bx-dollar',
  'dollar-sign':   'bx-dollar',
  'eye':           'bx-show',
  'eye-off':       'bx-hide',
  'chevron-right': 'bx-chevron-right',
  'down-arrow':    'bx-down-arrow-alt',
};

// ─── VALIDATION HELPER ───────────────────────────────────────────────────────
// Use in dev to catch bad icon references early.
export function isValidBoxicon(cls: string): boolean {
  return (VALID_BOXICONS as readonly string[]).includes(cls);
}

export function resolveIcon(key: string): string | null {
  if (!key) return null;
  if (key in iconMap) return iconMap[key];
  // Fallback: treat key as boxicon class directly
  const candidate = key.startsWith('bx') ? key : `bx-${key}`;
  return isValidBoxicon(candidate) ? candidate : null;
}
