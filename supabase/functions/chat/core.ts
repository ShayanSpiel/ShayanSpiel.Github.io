// SpielOS website chat assistant - edge function core (platform-neutral).
// Goal goal-3220ae01c4f7 | Run run-1f2927f6eb0d | WorkOrder work-e1c5f052f619 (WO2).
//
// The request/response handling lives here so it can be unit-tested in plain
// Node (test/*.mjs) with an injected env getter and injected fetch. The Deno
// entrypoint (index.ts) wires this to Deno.serve and the esm.sh supabase-js
// client factory. No Deno/Node-specific APIs are referenced below.
//
// Contract (locked; WO3 builds the client against this):
//   POST /functions/v1/chat
//   { messages: [{role:"user"|"assistant", content}...], locale:"en"|"fa",
//     session_id:"uuid-ish string" }
//   Response: text/event-stream
//     data: {"delta":"text chunk"}\n\n
//     ... data: {"capture":true,"thanks_line":"..."}\n\n  (once, on capture)
//     ... data: {"done":true,"reply_id":"..."}\n\n
//   Errors: JSON {"error":"..."} + status 429/400/405/403/500.

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequestBody {
  messages: ChatMessage[];
  locale: string;
  session_id: string;
  /** Optional client cookie context: { name?, email?, phone? } for returning visitors. */
  returning_visitor?: { name?: string; email?: string; phone?: string };
}

export interface CapturedLead {
  name: string;
  email: string;
  phone: string;
  company: string;
  needs: string;
  segment: string | null;
}

export interface SupabaseLike {
  from: (table: string) => {
    select: (cols: string) => {
      eq: (col: string, val: string) => { maybeSingle: () => Promise<{ data: unknown; error: unknown }> };
    };
    update: (patch: Record<string, unknown>) => {
      eq: (col: string, val: string) => Promise<{ error: unknown }>;
    };
    insert: (rows: Record<string, unknown>[]) => Promise<{ error: unknown }>;
  };
}

export type EnvGetter = (key: string) => string | undefined;
export type FetchLike = typeof fetch;
export type CreateClientLike = (url: string, key: string) => SupabaseLike;

// --- constants ---------------------------------------------------------------

const CORS_ALLOWLIST = [
  "https://spielos.xyz",
  "https://shayanspiel.github.io",
  "http://localhost:4321",
  "http://127.0.0.1:4321",
];

const MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions";
const MISTRAL_MODEL = "mistral-small-latest";
// Provider failover (owner incident 2026-09-05: Mistral free-tier
// completions quota can read 0 req/min even with valid keys — the
// narration pipeline already carries the same Mistral->Gemini chain).
// Gemini exposes an OpenAI-compatible endpoint, so the SSE parsing stays
// identical; only URL + auth header differ.
const GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions";
const GEMINI_MODEL = "gemini-2.5-flash";
// Third fallback: open-mistral-nemo rides a separate Mistral quota bucket
// (owner incident 2026-09-05: small-latest monthly + gemini daily both
// exhausted under test load; nemo still answered 200).
const NEMO_MODEL = "open-mistral-nemo";
// Mistral key pool (owner supplied keys 3+4 on 2026-09-05; big quota — guard it).
// Tried in order for the primary attempt; the first usable key wins.
const MISTRAL_KEY_ENVS = ["MISTRAL_API_KEY", "MISTRAL_API_KEY_2", "MISTRAL_API_KEY_3", "MISTRAL_API_KEY_4"];
const MAX_HISTORY = 16;
const MAX_CHARS = 2000;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const FORMSUBMIT_URL = "https://formsubmit.co/ajax/shayan@spielos.xyz";

// Rate limit design note: this Map is per-isolate and best-effort - Supabase
// edge functions may run on multiple isolates, so a determined visitor can
// exceed these caps by (isolate count x limit). v2 moves the counters to a
// durable store (Supabase KV / rate-limit table) keyed by session_id+IP.
const RATE_MINUTE = 10;
const RATE_HOUR = 30;

// SSE framing helper: platform-neutral at build type level. In Deno and in the
// Node test harness (where TextEncoder exists) this returns the encoded bytes;
// the caller guards both shapes for total platform independence.
export function sseFrame(obj: Record<string, unknown>): Uint8Array | string {
  const line = `data: ${JSON.stringify(obj)}\n\n`;
  const TE = (globalThis as { TextEncoder?: typeof TextEncoder }).TextEncoder;
  if (typeof TE === "function") return new TE().encode(line);
  return line;
}

// SSE lines longer than the marker prefix are checked against a partial-match
// guard so a marker split across stream chunks is never leaked mid-word.
const MARKER_START = "<<CAPTURE:";
const MARKER_END = ">>";

const RATE_LIMIT_MSG = "Too many messages. Take a breath and come back in a bit.";
const UPSTREAM_MSG = "The assistant is briefly unavailable — try again in a moment.";

// Marker-only appendage for the Mistral system prompt. The knowledge pack's
// own S12 capture rules apply; this replaces the tool-call instruction with
// the v1 streaming marker protocol (no Mistral tools in v1 - deliberate).
const CAPTURE_ADDENDUM_EN = `

## 13) Contact capture protocol (streaming marker - replaces any tool-call instruction above)
- Ask for contact exactly ONCE, right after your FIRST substantive answer: end that first reply with one short, warm question like: "Before I go on - who am I talking to? A name and an email or phone number, so a human on our side can get back to you fast." Then drop it; never ask again in the session.
- When the visitor shares contact details (name plus email OR phone), emit one line in EXACTLY this format anywhere in your reply, after your thank-you sentence:
  <<CAPTURE:name=John Doe|email=john@example.com|phone=+15551234567|company=Acme|needs=automate invoicing|segment=software/product>>
- Phone accepts digits, +, spaces, dashes. Email OR phone - at least one is required alongside the name.
- "segment" must be your best guess from this fixed list: founders/owners, marketing, ops, recruitment, finance, design/content, software/product, agency/freelance, other. Use "other" when unsure.
- All fields except name and one contact channel may be empty (e.g. company=|needs=|segment=other) - still emit the marker as long as you have name + (email or phone).
- The marker is consumed by the system, never rendered to the visitor. Do not mention it, do not wrap it in code fences, and never place it inside markdown.
- If the visitor has already been captured in this session, do not emit the marker again.`;

const CAPTURE_ADDENDUM_FA = `

## ۱۳) پروتکل گرفتن اطلاعات تماس (مارکر استریم — جایگزین هر دستور ابزار در بالا)
- درخواست اطلاعات تماس رو فقط یک‌بار بکن، درست بعد از اولین جواب کاملت: آخر همون جواب اول با یک سؤال کوتاه و صمیمی بپرس: «راستی، با کی صحبت می‌کنم؟ اسم و ایمیل یا شماره تلفنت رو بده تا یکی از تیم انسانی ما سریع بهت جواب بده.» بعد دیگه تکرارش نکن.
- وقتی بازدیدکننده اطلاعات تماسش رو می‌ده (اسم به‌علاوه ایمیل یا شماره تلفن)، در جوابت و بعد از جمله تشکر، یک خط دقیقاً به این شکل بنویس:
  <<CAPTURE:name=John Doe|email=john@example.com|phone=+15551234567|company=Acme|needs=اتوماسیون فاکتور|segment=software/product>>
- شماره تلفن می‌تونه رقم، +، فاصله و خط تیره داشته باشه. ایمیل یا شماره تلفن — حداقل یکی به‌همراه اسم لازمه.
- «segment» بهترین حدس تو از این لیست ثابته: founders/owners, marketing, ops, recruitment, finance, design/content, software/product, agency/freelance, other. اگه مطمئن نیستی «other» بذار.
- همه فیلدها به‌جز name و یک کانال تماس می‌تونن خالی باشن (مثلاً company=|needs=|segment=other) — تا وقتی اسم و ایمیل یا شماره داری مارکر رو بفرست.
- مارکر رو سیستم پردازش می‌کنه و بازدیدکننده هیچ‌وقت نمی‌بینتش. به خود مارکر اشاره نکن، داخل کد ننویسش و هرگز داخل markdown نذارش.
- اگه در همین گفتگو قبلاً اطلاعات تماس گرفته شده، مارکر رو دوباره نفرست.`;

// --- pure helpers (exported for direct unit testing) ------------------------

export function corsHeaders(origin: string | null): Record<string, string> {
  if (origin && CORS_ALLOWLIST.includes(origin)) {
    return {
      "Access-Control-Allow-Origin": origin,
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Api-Key, Authorization, apikey, x-client-info",
      "Access-Control-Max-Age": "86400",
      Vary: "Origin",
    };
  }
  return { Vary: "Origin" };
}

export function validateBody(body: unknown): { ok: true; value: ChatRequestBody } | { ok: false; reason: string } {
  if (typeof body !== "object" || body === null) return { ok: false, reason: "Invalid request body." };
  const b = body as Record<string, unknown>;
  const messages = b.messages;
  if (!Array.isArray(messages) || messages.length === 0) return { ok: false, reason: "messages must be a non-empty array." };
  if (messages.length > MAX_HISTORY) return { ok: false, reason: `messages must be at most ${MAX_HISTORY} entries.` };
  for (let i = 0; i < messages.length; i++) {
    const m = messages[i];
    if (typeof m !== "object" || m === null) return { ok: false, reason: `messages[${i}] must be an object.` };
    const role = (m as Record<string, unknown>).role;
    if (role !== "user" && role !== "assistant") return { ok: false, reason: `messages[${i}].role must be "user" or "assistant".` };
    const content = (m as Record<string, unknown>).content;
    if (typeof content !== "string") return { ok: false, reason: `messages[${i}].content must be a string.` };
    if (content.length > MAX_CHARS) return { ok: false, reason: `messages[${i}].content exceeds ${MAX_CHARS} characters.` };
  }
  const last = messages[messages.length - 1] as Record<string, unknown>;
  if (last.role !== "user") return { ok: false, reason: "The last message must have role \"user\"." };
  const locale = b.locale;
  if (locale !== "en" && locale !== "fa") return { ok: false, reason: "locale must be \"en\" or \"fa\"." };
  const sid = b.session_id;
  if (typeof sid !== "string" || sid.length < 8 || sid.length > 64) return { ok: false, reason: "session_id must be a string of 8-64 characters." };
  const rv = b.returning_visitor;
  const returning_visitor = (typeof rv === "object" && rv !== null)
    ? {
        name: typeof (rv as Record<string, unknown>).name === "string" ? String((rv as Record<string, unknown>).name).slice(0, 80) : undefined,
        email: typeof (rv as Record<string, unknown>).email === "string" ? String((rv as Record<string, unknown>).email).slice(0, 254).toLowerCase() : undefined,
        phone: typeof (rv as Record<string, unknown>).phone === "string" ? String((rv as Record<string, unknown>).phone).slice(0, 32) : undefined,
      }
    : undefined;
  return {
    ok: true,
    value: { messages: messages as ChatMessage[], locale, session_id: sid, returning_visitor },
  };
}

// Best-effort per-isolate rate limiter. Buckets are pruned lazily; the Map
// holds at most a few hundred session entries in normal traffic. See the
// rate-limit design note above the constants for the multi-isolate caveat.
export class RateLimiter {
  private hits = new Map<string, number[]>();

  check(key: string, now = Date.now()): { allowed: boolean; remainingMinute: number } {
    const minuteWindow = 60_000;
    const hourWindow = 3_600_000;
    const all = (this.hits.get(key) ?? []).filter((t) => now - t < hourWindow);
    const perMinute = all.filter((t) => now - t < minuteWindow);
    if (perMinute.length >= RATE_MINUTE) return { allowed: false, remainingMinute: 0 };
    if (all.length >= RATE_HOUR) return { allowed: false, remainingMinute: RATE_MINUTE - perMinute.length };
    all.push(now);
    this.hits.set(key, all);
    return { allowed: true, remainingMinute: RATE_MINUTE - perMinute.length - 1 };
  }
}

export interface MarkerParseResult {
  captured: CapturedLead | null;
  visibleText: string; // marker stripped
}

/**
 * Scans text for a complete `<<CAPTURE:...>>` marker. Returns the validated
 * lead + the visible text with the marker removed. A complete-but-INVALID
 * marker (bad email / short name) is still stripped - it must never leak to
 * the visitor - but yields captured=null so no CRM write happens.
 */
export function parseCaptureMarker(text: string, segments: string[]): MarkerParseResult {
  const start = text.indexOf(MARKER_START);
  if (start < 0) return { captured: null, visibleText: text };
  const end = text.indexOf(MARKER_END, start);
  if (end < 0) return { captured: null, visibleText: text };
  const inner = text.slice(start + MARKER_START.length, end);
  const fields = new Map<string, string>();
  for (const part of inner.split("|")) {
    const eq = part.indexOf("=");
    if (eq <= 0) continue;
    fields.set(part.slice(0, eq).trim().toLowerCase(), part.slice(eq + 1).trim());
  }
  const name = (fields.get("name") ?? "").trim();
  const email = (fields.get("email") ?? "").trim().toLowerCase();
  const phoneRaw = (fields.get("phone") ?? "").trim();
  const phoneDigits = phoneRaw.replace(/[^\d+]/g, "");
  const phoneOk = phoneDigits.length >= 7 && phoneDigits.length <= 16;
  const emailOk = EMAIL_RE.test(email);
  const company = (fields.get("company") ?? "").trim();
  const needs = (fields.get("needs") ?? "").trim();
  const rawSegment = (fields.get("segment") ?? "").trim().toLowerCase();
  // Contact requires a name AND at least one usable channel (email or phone).
  const captured: CapturedLead | null =
    name.length >= 2 && name.length <= 80 && (emailOk || phoneOk)
      ? {
          name,
          email: emailOk ? email : "",
          phone: phoneOk ? phoneDigits.slice(0, 32) : "",
          company: company.slice(0, 120),
          needs: needs.slice(0, 600),
          segment: segments.includes(rawSegment) ? rawSegment : null,
        }
      : null;
  const cleaned = (text.slice(0, start) + text.slice(end + MARKER_END.length)).replace(/ +\n/g, "\n").trimEnd();
  return { captured, visibleText: cleaned };
}

/**
 * Streaming-safe incremental scan: given the text visible-so-far minus any
 * held-back tail, decide what can be flushed to the client now and what must
 * be held back because it might be the beginning (or inside) a capture
 * marker. `alreadyCaptured` stops re-emission after the first valid capture.
 */
export function scanChunk(
  text: string,
  segments: string[],
  alreadyCaptured: boolean,
): { flush: string; hold: string; captured: CapturedLead | null } {
  const complete = parseCaptureMarker(text, segments);
  if (complete.captured && !alreadyCaptured) {
    return { flush: complete.visibleText, hold: "", captured: complete.captured };
  }
  // Either no complete marker, or a complete marker that is invalid (bad
  // email/name) or already consumed: strip invalid/duplicate markers now and
  // hold back any suffix that could grow into (or already be) a marker so its
  // text never leaks to the visitor.
  let work = text;
  let guard = 0;
  while (work.includes(MARKER_START) && guard++ < 8) {
    const r = parseCaptureMarker(work, segments);
    work = r.visibleText;
    if (r.captured && !alreadyCaptured) break; // caller re-checks this case
  }
  const holdLen = maxMarkerPrefixLen(work);
  if (holdLen > 0) {
    return { flush: work.slice(0, work.length - holdLen), hold: work.slice(work.length - holdLen), captured: null };
  }
  return { flush: work, hold: "", captured: null };
}

/** Longest suffix of `text` that must be held back: either a strict prefix of
 * `<<CAPTURE:` (a marker could still be forming) or everything from a complete
 * start marker onward (body still streaming, terminator not yet arrived). */
function maxMarkerPrefixLen(text: string): number {
  const idx = text.indexOf(MARKER_START);
  if (idx >= 0) return text.length - idx; // full start present, end pending
  const n = Math.min(text.length, MARKER_START.length - 1);
  for (let len = n; len > 0; len--) {
    if (MARKER_START.startsWith(text.slice(text.length - len))) return len;
  }
  return 0;
}

// --- lead write path ---------------------------------------------------------

export function deriveBestMatchWorkflow(lead: CapturedLead): string | null {
  const n = lead.needs.toLowerCase();
  if (!n) return null;
  const rules: Array<[RegExp, string]> = [
    [/invoice|receipt|ledger|فاکتور|حسابدار/, "invoice-processing-automation"],
    [/recruit|candidate|cv|hiring|استخدام|کاندید/, "recruitment-automation"],
    [/onboard/, "client-onboarding-automation"],
    [/intake/, "client-intake-automation"],
    [/document|سند/, "document-collection-automation"],
    [/data.?entry|ورود داده/, "data-entry-automation"],
    [/follow.?up|پیگیری/, "follow-up-automation"],
    [/lead|qualif|صلاحیت/, "lead-qualification-automation"],
    [/freight|حمل|logistics|لجستیک/, "freight-workflow-automation"],
    [/purchase|order|po\b|خرید/, "purchase-order-workflow-automation"],
    [/marketing|مارکتینگ|outbound|بیرون‌زنی/, "marketing"],
    [/seo|جستجو|keyword/, "seo"],
    [/content|محتوا|مقاله|article|blog/, "content"],
    [/design|طراح|flyer|banner/, "design"],
    [/analytic|analytics|داده|dashboard|گزارش/, "analytics"],
  ];
  for (const [re, wf] of rules) {
    if (re.test(n)) return wf;
  }
  return null;
}

export async function persistLead(
  sb: SupabaseLike,
  lead: CapturedLead,
  ctx: { session_id: string; locale: string },
  now = new Date(),
): Promise<{ ok: boolean; error?: string }> {
  const email = lead.email;                 // empty when phone-only contact
  const phone = lead.phone;
  const nowIso = now.toISOString();
  const segment = lead.segment ?? "other";
  const bestMatch = deriveBestMatchWorkflow(lead);
  // Dedupe: email match first; phone-only contacts match on the stored
  // personalization-hook channel (we park the phone there for v1 until the
  // CRM grows a phone column) via lead_key "phone:<digits>".
  const leadKey = email ? email : "phone:" + phone;
  let existing: unknown = null;
  if (email) {
    const r = await sb.from("leads").select("id,lead_key,email,contact_name,segment,sources").eq("email", email).maybeSingle();
    if (r.error) return { ok: false, error: String(r.error) };
    existing = r.data;
  }
  if (!existing && phone) {
    const r = await sb.from("leads").select("id,lead_key,email,contact_name,segment,sources").eq("lead_key", leadKey).maybeSingle();
    if (r.error) return { ok: false, error: String(r.error) };
    existing = r.data;
  }
  const readErr = null;
  if (existing) {
    const ex = existing as Record<string, unknown>;
    const prevSources = Array.isArray(ex.sources) ? (ex.sources as unknown[]) : [];
    const sources = prevSources.includes("website_chat") ? prevSources : [...prevSources, "website_chat"];
    const patch: Record<string, unknown> = { sources, updated_at: nowIso };
    if (typeof ex.contact_name !== "string" || ex.contact_name.trim() === "") patch.contact_name = lead.name;
    if (bestMatch) patch.best_match_workflow = bestMatch;
    // Remember the latest channel; v1 parks phone in personalization_hook.
    if (phone) patch.personalization_hook = "phone: " + phone;
    const { error: updErr } = await sb.from("leads").update(patch).eq("id", String(ex.id));
    if (updErr) return { ok: false, error: String(updErr) };
    return { ok: true };
  }
  {
    const { error: insErr } = await sb.from("leads").insert([
      {
        lead_key: leadKey,
        email: email || null,
        contact_name: lead.name,
        segment,
        sources: ["website_chat"],
        best_match_workflow: bestMatch,
        personalization_hook: phone ? "phone: " + phone : null,
        country: null,
        icp_score: null,
        created_at: nowIso,
        updated_at: nowIso,
      },
    ]);
    if (insErr) return { ok: false, error: String(insErr) };
    return { ok: true };
  }
}

export async function appendEmailEvent(
  sb: SupabaseLike,
  lead: CapturedLead,
  ctx: { session_id: string; locale: string; needs?: string },
  now = new Date(),
): Promise<{ ok: boolean; error?: string }> {
  const { error } = await sb.from("email_events").insert([
    {
      lead_key: lead.email,
      email: lead.email,
      event: "captured",
      at: now.toISOString(),
      subject: "Website chat lead captured",
      provider: "mistral-chat",
      campaign: "chat-assistant",
      batch: null,
      detail: JSON.stringify({ session_id: ctx.session_id, needs: ctx.needs ?? lead.needs, locale: ctx.locale, phone: lead.phone || undefined }),
    },
  ]);
  return error ? { ok: false, error: String(error) } : { ok: true };
}

/** Fire-and-forget FormSubmit email; failure must never block the CRM write. */
export async function notifyFormSubmit(lead: CapturedLead, fetchImpl: FetchLike): Promise<void> {
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 3000);
    const res = await fetchImpl(FORMSUBMIT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: lead.name,
        email: lead.email,
        phone: lead.phone,
        company: lead.company,
        needs: lead.needs,
        segment: lead.segment ?? "other",
        _subject: "New chat lead — spielos.xyz",
      }),
      signal: ctrl.signal,
    });
    clearTimeout(timer);
    if (!res.ok) console.error(`[chat] formsubmit ${res.status}`);
  } catch (e) {
    console.error(`[chat] formsubmit failed: ${String(e)}`);
  }
}

/** Strip every complete capture marker from text (used for held-back tails). */
function core_stripMarker(text: string, segments: string[]): string {
  let out = text;
  let guard = 0;
  while (out.includes(MARKER_START) && guard++ < 8) {
    const r = parseCaptureMarker(out, segments);
    out = r.visibleText;
    if (r.captured) break;
  }
  return out;
}

// --- Mistral stream ---------------------------------------------------------

interface MistralDeltaEvent {
  choices?: Array<{ delta?: { content?: string } }>;
}

function extractDelta(line: string): string | null {
  // line arrives without the "data: " prefix and with trailing \r removed.
  if (line === "[DONE]") return null;
  try {
    const parsed = JSON.parse(line) as MistralDeltaEvent;
    return parsed.choices?.[0]?.delta?.content ?? null;
  } catch {
    return null;
  }
}

async function* mistralSseDeltas(res: { body: ReadableStream<Uint8Array> }, fetchImpl?: FetchLike): AsyncGenerator<string> {
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let nl: number;
    while ((nl = buf.indexOf("\n")) >= 0) {
      let line = buf.slice(0, nl);
      buf = buf.slice(nl + 1);
      if (line.endsWith("\r")) line = line.slice(0, -1);
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trimStart();
      if (!payload) continue;
      const delta = extractDelta(payload);
      if (delta !== null && delta !== "") yield delta;
    }
  }
}

// --- handler ----------------------------------------------------------------

export interface HandlerDeps {
  getEnv: EnvGetter;
  fetchImpl: FetchLike;
  knowledge: {
    system_prompt_en: string;
    system_prompt_fa: string;
    segment_vocabulary: string[];
  };
  createClient: CreateClientLike;
  now?: () => Date;
  rateLimiter?: RateLimiter;
}

export interface MinimalRequest {
  method: string;
  url: string;
  headers: { get(name: string): string | null };
  json: () => Promise<unknown>;
}

export interface MinimalResponse {
  status: number;
  headers: Record<string, string>;
  body: string | ReadableStream<Uint8Array>;
}

const rateLimiter = new RateLimiter();
const replyCounter = { n: 0 };

export function jsonResponse(body: Record<string, unknown>, status: number, extra: Record<string, string> = {}): MinimalResponse {
  return {
    status,
    headers: { "Content-Type": "application/json", ...extra },
    body: JSON.stringify(body),
  };
}

export async function handleChat(req: MinimalRequest, deps: HandlerDeps): Promise<MinimalResponse> {
  const { getEnv, fetchImpl, knowledge } = deps;
  const origin = req.headers.get("origin") ?? null;
  const cors = corsHeaders(origin);
  const ip = req.headers.get("x-forwarded-for") ?? req.headers.get("cf-connecting-ip") ?? "unknown";

  // 405: non-POST/OPTIONS
  if (req.method === "OPTIONS") {
    return { status: 204, headers: { ...cors }, body: "" };
  }
  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed. Use POST." }, 405, cors);
  }

  // 403: disallowed origin (only when an Origin header is present at all)
  if (origin && !CORS_ALLOWLIST.includes(origin)) {
    return jsonResponse({ error: "Origin not allowed." }, 403, cors);
  }

  // Rate limit per session_id + IP (per-isolate, best-effort - see note above).
  // Runs AFTER body validation so malformed requests (400) do not consume a
  // visitor's message quota; only turns that would reach Mistral are counted.
  // The key's session half comes from the validated body; the URL fallback
  // only feeds the limiter when a body never parses, which is unbillable anyway.
  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return jsonResponse({ error: "Request body must be valid JSON." }, 400, cors);
  }
  const parsed = validateBody(raw);
  if (!parsed.ok) return jsonResponse({ error: parsed.reason }, 400, cors);
  const validated = parsed.value;
  const { messages, locale, session_id } = validated;

  const rlKey = `${ip}|${session_id}`;
  const { allowed, remainingMinute } = rateLimiter.check(rlKey);
  if (!allowed) {
    return jsonResponse({ error: RATE_LIMIT_MSG }, 429, {
      ...cors,
      "X-RateLimit-Remaining-Minute": "0",
      "Retry-After": "60",
    });
  }
  const rateHeaders: Record<string, string> = { "X-RateLimit-Remaining-Minute": String(Math.max(0, remainingMinute)) };

  // System prompt from the knowledge pack, selected by locale, plus the
  // marker-protocol addendum (supersedes the pack's tool-call S12 wording).
  const basePrompt = locale === "fa" ? knowledge.system_prompt_fa : knowledge.system_prompt_en;
  // Brevity directive (owner 2026-09-05): compact, skimmable answers.
  const brevity = locale === "fa"
    ? "\n\n## ۱۴) پاسخ‌های کوتاه\n- جواب‌ها جمع‌وجور باشه: حداکثر ۴-۶ جمله یا ۶-۸ خط. اول مستقیم جواب بده، بعد در صورت نیاز یک لینک. هیچ‌وقت متن بلند و دیواری ننویس. سؤال اضافه فقط یکی."
    : "\n\n## 14) Answer brevity\n- Keep answers compact: at most 4-6 sentences or 6-8 short lines. Lead with the direct answer, add one link only when it helps. Never write walls of text. At most one question per reply.";
  // Returning-visitor context (client cookie): greet warmly by name if known,
  // never re-ask for contact from someone already captured.
  const returning = (validated.returning_visitor)
    ? ("\n\n## 15) Returning visitor\nThis visitor talked with you before: "
        + JSON.stringify(validated.returning_visitor)
        + "\n- If a name is present, greet them naturally by name in your first reply.\n- They already shared contact details previously: NEVER ask for their name/email/phone again and never emit the capture marker again.")
    : "";
  const systemPrompt = basePrompt + (locale === "fa" ? CAPTURE_ADDENDUM_FA : CAPTURE_ADDENDUM_EN) + brevity + returning;

  const replyId = `r-${Date.now().toString(36)}-${(replyCounter.n++).toString(36)}`;

  // Upstream call with streaming + provider failover: try Mistral first,
  // fall back to Gemini when Mistral is rate-limited (429) or unavailable.
  // Both expose OpenAI-compatible SSE, so parsing is shared.
  let upstream: Response | null = null;
  let provider = "mistral";

  for (const envName of MISTRAL_KEY_ENVS) {
    const mistralKey = getEnv(envName);
    if (!mistralKey) continue;
    try {
      const res = await fetchImpl(MISTRAL_URL, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${mistralKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: MISTRAL_MODEL,
          messages: [{ role: "system", content: systemPrompt }, ...messages],
          stream: true,
          temperature: 0.5,
          max_tokens: 1200,
        }),
      }) as Response;
      if (res.ok && res.body) {
        upstream = res;
        break;
      }
      console.error(`[chat] ${session_id}: mistral(${envName}) status ${res.status}`);
    } catch (e) {
      console.error(`[chat] ${session_id}: mistral(${envName}) fetch failed: ${String(e)}`);
    }
  }
  if (!upstream) console.error(`[chat] ${session_id}: mistral pool exhausted — trying gemini`);

  if (!upstream) {
    provider = "gemini";
    const geminiKey = getEnv("GEMINI_API_KEY");
    if (geminiKey) {
      try {
        const res = await fetchImpl(GEMINI_URL, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${geminiKey}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            model: GEMINI_MODEL,
            messages: [{ role: "system", content: systemPrompt }, ...messages],
            stream: true,
            temperature: 0.5,
            max_tokens: 1200,
          }),
        }) as Response;
        if (res.ok && res.body) {
          upstream = res;
        } else {
          console.error(`[chat] ${session_id}: gemini status ${res.status} — trying nemo`);
        }
      } catch (e) {
        console.error(`[chat] ${session_id}: gemini fetch failed: ${String(e)} — trying nemo`);
      }
    } else {
      console.error(`[chat] ${session_id}: missing GEMINI_API_KEY — trying nemo`);
    }
  }

  if (!upstream) {
    provider = "nemo";
    const mistralKey2 = getEnv("MISTRAL_API_KEY_2") || getEnv("MISTRAL_API_KEY");
    if (!mistralKey2) {
      console.error(`[chat] ${session_id}: no keys left in fallback chain`);
      return jsonResponse({ error: UPSTREAM_MSG }, 500, { ...cors, ...rateHeaders });
    }
    try {
      const res = await fetchImpl(MISTRAL_URL, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${mistralKey2}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: NEMO_MODEL,
          messages: [{ role: "system", content: systemPrompt }, ...messages],
          stream: true,
          temperature: 0.5,
          max_tokens: 1200,
        }),
      }) as Response;
      if (!res.ok || !res.body) {
        console.error(`[chat] ${session_id}: nemo status ${res.status}`);
        return jsonResponse({ error: UPSTREAM_MSG }, 500, { ...cors, ...rateHeaders });
      }
      upstream = res;
    } catch (e) {
      console.error(`[chat] ${session_id}: nemo fetch failed: ${String(e)}`);
      return jsonResponse({ error: UPSTREAM_MSG }, 500, { ...cors, ...rateHeaders });
    }
  }

  // SSE response stream to the browser
  const segments = knowledge.segment_vocabulary;
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      let visible = ""; // confirmed marker-free text flushed or pending flush
      let hold = ""; // tail that might be a partial marker
      let alreadyCaptured = false;
      try {
        for await (const delta of mistralSseDeltas(upstream)) {
          const candidate = hold + delta;
          const { flush, hold: newHold, captured } = scanChunk(candidate, segments, alreadyCaptured);
          hold = newHold;
          if (flush) {
            visible += flush;
            const chunk = sseFrame({ delta: flush });
            controller.enqueue(typeof chunk === "string" ? encoder.encode(chunk) : chunk);
          }
          if (captured && !alreadyCaptured) {
            alreadyCaptured = true;
            // CRM write happens before the client is told the capture landed.
            const leadOk = await writeLead(deps, captured, { session_id, locale, now: deps.now?.() });
            if (leadOk) {
              const ev = sseFrame({ capture: true, thanks_line: thanksLine(locale) });
              controller.enqueue(typeof ev === "string" ? encoder.encode(ev) : ev);
            } else {
              // Capture failed server-side; keep the visible reply flowing so
              // the visitor never sees an error caused by the CRM write.
              console.error(`[chat] ${session_id}: lead persist failed; capture event suppressed`);
            }
          }
        }
        // Flush any held-back tail. If a valid capture already happened, any
        // remaining hold is marker-body text (or a duplicate marker) and is
        // dropped; parse it first so duplicate markers never leak either.
        if (hold) {
          if (alreadyCaptured) {
            const tail = core_stripMarker(hold, segments);
            if (tail) {
              visible += tail;
              const chunk = sseFrame({ delta: tail });
              controller.enqueue(typeof chunk === "string" ? encoder.encode(chunk) : chunk);
            }
            hold = "";
          } else {
            const tail = hold;
            hold = "";
            visible += tail;
            const chunk = sseFrame({ delta: tail });
            controller.enqueue(typeof chunk === "string" ? encoder.encode(chunk) : chunk);
          }
        }
        const d1 = sseFrame({ done: true, reply_id: replyId });
        controller.enqueue(typeof d1 === "string" ? encoder.encode(d1) : d1);
        controller.close();
      } catch (e) {
        console.error(`[chat] ${session_id}: stream error: ${String(e)}`);
        try {
          const d2 = sseFrame({ done: true, reply_id: replyId, error: UPSTREAM_MSG });
          controller.enqueue(typeof d2 === "string" ? encoder.encode(d2) : d2);
          controller.close();
        } catch {
          // ignore secondary close failure
        }
      }
    },
  });

  return {
    status: 200,
    headers: {
      ...cors,
      ...rateHeaders,
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-store",
      "X-Accel-Buffering": "no",
      Connection: "keep-alive",
    },
    body: stream,
  };
}

// Kept for potential future query-param use; the rate-limit key now uses the
// validated body's session_id instead.
function extractSessionId(url: string): string {
  try {
    const u = new URL(url);
    return u.searchParams.get("session_id") ?? "unknown";
  } catch {
    return "unknown";
  }
}

function thanksLine(locale: string): string {
  return locale === "fa"
    ? "ممنون که اطلاعات تماسش رو گذاشتی — تیم SpielOS به‌زودی پیگیر می‌شه."
    : "Thanks for sharing that — the SpielOS team will follow up soon.";
}

async function writeLead(
  deps: HandlerDeps,
  lead: CapturedLead,
  ctx: { session_id: string; locale: string; now?: Date },
): Promise<boolean> {
  const { getEnv, createClient, fetchImpl } = deps;
  const url = getEnv("SUPABASE_URL");
  const key = getEnv("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) {
    console.error(`[chat] ${ctx.session_id}: missing SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY; capture dropped`);
    return false;
  }
  let sb: SupabaseLike;
  try {
    sb = createClient(url, key);
  } catch (e) {
    console.error(`[chat] ${ctx.session_id}: supabase client create failed: ${String(e)}`);
    return false;
  }
  const leadOk = await persistLead(sb, lead, ctx, ctx.now);
  if (!leadOk.ok) {
    console.error(`[chat] ${ctx.session_id}: persistLead failed: ${leadOk.error}`);
    return false;
  }
  const evOk = await appendEmailEvent(sb, lead, ctx, ctx.now);
  if (!evOk.ok) console.error(`[chat] ${ctx.session_id}: email_events insert failed: ${evOk.error}`);
  // FormSubmit is a bonus channel - never blocks the capture event.
  await notifyFormSubmit(lead, fetchImpl);
  return true;
}

// Exported for tests: mistral SSE line parser and helpers.
export { extractDelta, extractSessionId, thanksLine };
export { MARKER_START, MARKER_END, MAX_HISTORY, MAX_CHARS, RATE_MINUTE, RATE_HOUR };
export { CORS_ALLOWLIST };
export { MISTRAL_URL, MISTRAL_MODEL, GEMINI_URL, GEMINI_MODEL, FORMSUBMIT_URL };
export { CAPTURE_ADDENDUM_EN, CAPTURE_ADDENDUM_FA };
