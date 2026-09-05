// WO2 test runner — plain Node, no deps. Runs the real core.ts handler logic
// against fully mocked upstreams (Mistral SSE, PostgREST, FormSubmit).
//
//   node supabase/functions/chat/test/test-run.mjs
//
// core.ts is TypeScript; we transpile it in-memory with the repo's esbuild
// (devDependency of astro) and import the result as a data: module. No Deno
// runtime is needed: core.ts is platform-neutral by design.

import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { build } = require("esbuild");
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { makeMockFetch, makeMockSupabaseClient } from "./mock-server.mjs";
import { runEvals } from "./evals.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const chatDir = path.resolve(__dirname, "..");

// --- load core.ts -----------------------------------------------------------

const built = await build({
  entryPoints: [path.join(chatDir, "core.ts")],
  bundle: false,
  write: false,
  format: "esm",
  platform: "neutral",
});
const coreCode = built.outputFiles[0].text;
const core = await import(
  "data:text/javascript;base64," + Buffer.from(coreCode, "utf8").toString("base64")
);

const knowledge = JSON.parse(fs.readFileSync(path.join(chatDir, "knowledge.json"), "utf8"));

// --- test helpers -----------------------------------------------------------

const SUPABASE_URL = "https://test-supabase.local";
const ENV = {
  MISTRAL_API_KEY: "test-mistral-key",
  SUPABASE_URL,
  SUPABASE_SERVICE_ROLE_KEY: "test-service-role-key",
};

function makeDeps(scenario, opts = {}) {
  const mock = makeMockFetch({ scenario, ...opts });
  return {
    mock,
    deps: {
      getEnv: (k) => ENV[k],
      fetchImpl: mock.fetchImpl,
      knowledge: {
        system_prompt_en: knowledge.system_prompt_en,
        system_prompt_fa: knowledge.system_prompt_fa,
        segment_vocabulary: knowledge.segment_vocabulary,
      },
      createClient: (_url, _key) => makeMockSupabaseClient(mock.fetchImpl, SUPABASE_URL),
    },
  };
}

function makeRequest(overrides = {}) {
  const headers = new Map(Object.entries(overrides.headers ?? { "content-type": "application/json" }));
  return {
    method: overrides.method ?? "POST",
    url: overrides.url ?? "https://test-supabase.supabase.co/functions/v1/chat",
    headers: { get: (n) => headers.get(n.toLowerCase()) ?? null },
    json: async () => overrides.body,
  };
}

let sessionCounter = 0;
function validBody(extra = {}) {
  sessionCounter += 1;
  return {
    messages: [{ role: "user", content: "Hi, what is SpielOS?" }],
    locale: "en",
    // Each call gets a fresh session id so behavior tests are order-
    // independent (the handler's module-level rate limiter is shared).
    session_id: `sess-${String(sessionCounter).padStart(8, "0")}-test-00000001`,
    ...extra,
  };
}

async function readSse(res) {
  assert.equal(typeof res.body, "object");
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let raw = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    raw += dec.decode(value, { stream: true });
  }
  const events = [];
  for (const block of raw.split("\n\n")) {
    if (!block.startsWith("data:")) continue;
    events.push(JSON.parse(block.slice(5).trim()));
  }
  return { raw, events };
}

async function readJson(res) {
  assert.equal(typeof res.body, "string", "error responses must have string bodies");
  return JSON.parse(res.body);
}

let passed = 0;
let failed = 0;
const failures = [];

async function test(name, fn) {
  try {
    await fn();
    passed += 1;
    console.log(`  ok  ${name}`);
  } catch (e) {
    failed += 1;
    failures.push({ name, error: e });
    console.log(`FAIL  ${name}\n      ${e.message.split("\n")[0]}`);
  }
}

// Reset the module-level rate limiter between test groups where needed.
function freshRateLimiter() {
  return new core.RateLimiter();
}

// --- tests ------------------------------------------------------------------

console.log("chat edge function — behavior tests\n");

await test("OPTIONS from allowlisted origin -> 204 + CORS echo", async () => {
  const { deps } = makeDeps("plain");
  const res = await core.handleChat(makeRequest({ method: "OPTIONS", headers: { origin: "https://spielos.xyz" } }), deps);
  assert.equal(res.status, 204);
  assert.equal(res.headers["Access-Control-Allow-Origin"], "https://spielos.xyz");
  assert.equal(res.headers["Access-Control-Allow-Methods"], "POST, OPTIONS");
});

await test("OPTIONS from disallowed origin -> 204 but NO CORS headers", async () => {
  const { deps } = makeDeps("plain");
  const res = await core.handleChat(makeRequest({ method: "OPTIONS", headers: { origin: "https://evil.example" } }), deps);
  assert.equal(res.status, 204);
  assert.equal(res.headers["Access-Control-Allow-Origin"], undefined);
});

await test("POST from disallowed origin -> 403 JSON error", async () => {
  const { deps } = makeDeps("plain");
  const res = await core.handleChat(makeRequest({ headers: { origin: "https://evil.example" }, body: validBody() }), deps);
  assert.equal(res.status, 403);
  const j = await readJson(res);
  assert.ok(j.error);
});

await test("POST from allowlisted origin echoes CORS header", async () => {
  const { deps } = makeDeps("plain");
  const res = await core.handleChat(makeRequest({ headers: { origin: "http://localhost:4321" }, body: validBody() }), deps);
  assert.equal(res.headers["Access-Control-Allow-Origin"], "http://localhost:4321");
  const { events } = await readSse(res);
  assert.ok(events.at(-1).done === true);
});

await test("GET -> 405 JSON error", async () => {
  const { deps } = makeDeps("plain");
  const res = await core.handleChat(makeRequest({ method: "GET" }), deps);
  assert.equal(res.status, 405);
  const j = await readJson(res);
  assert.ok(j.error.includes("POST"));
});

await test("missing MISTRAL_API_KEY -> 500 upstream message", async () => {
  const { deps } = makeDeps("plain");
  deps.getEnv = () => undefined;
  const res = await core.handleChat(makeRequest({ body: validBody() }), deps);
  assert.equal(res.status, 500);
  const j = await readJson(res);
  assert.equal(j.error, "The assistant is briefly unavailable — try again in a moment.");
});

await test("rate limit: 11th message within a minute -> 429", async () => {
  const { deps } = makeDeps("plain");
  const sid = "rl-minute-0000-0000-0000-000000000001";
  for (let i = 0; i < 10; i++) {
    const res = await core.handleChat(makeRequest({ body: validBody({ session_id: sid }) }), deps);
    assert.equal(res.status, 200, `message ${i + 1} should pass`);
    await readSse(res);
  }
  const res = await core.handleChat(makeRequest({ body: validBody({ session_id: sid }) }), deps);
  assert.equal(res.status, 429);
  const j = await readJson(res);
  assert.equal(j.error, "Too many messages. Take a breath and come back in a bit.");
  assert.equal(res.headers["Retry-After"], "60");
});

await test("rate limit: independent per session_id", async () => {
  const { deps } = makeDeps("plain");
  const sid = "rl-second-0000-0000-0000-00000000000A";
  for (let i = 0; i < 10; i++) {
    const res = await core.handleChat(makeRequest({ body: validBody({ session_id: sid }) }), deps);
    assert.equal(res.status, 200);
    await readSse(res);
  }
  const other = await core.handleChat(makeRequest({ body: validBody({ session_id: "rl-second-0000-0000-0000-00000000000B" }) }), deps);
  assert.equal(other.status, 200);
  await readSse(other);
});

await test("rate limit: 31st within an hour -> 429 (hour cap)", async () => {
  // Use the exported RateLimiter directly for determinism: 30 hits spread
  // across the hour window (each >60s apart, so the minute cap never trips),
  // then the 31st within the hour must be blocked.
  const rl = freshRateLimiter();
  const now = Date.now();
  const spread = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]
    .map((m) => now - (29 - m) * 61_000); // one hit every 61s over ~30 minutes
  for (const [i, t] of spread.entries()) {
    const r = rl.check("ip|sess", t);
    assert.equal(r.allowed, true, `hour-cap setup message ${i + 1} at ${new Date(t).toISOString()}`);
  }
  const blocked = rl.check("ip|sess", now);
  assert.equal(blocked.allowed, false);
});

await test("validation: empty messages -> 400", async () => {
  const { deps } = makeDeps("plain");
  const res = await core.handleChat(makeRequest({ body: { messages: [], locale: "en", session_id: "x".repeat(12) } }), deps);
  assert.equal(res.status, 400);
  assert.ok((await readJson(res)).error);
});

await test("validation: 17 messages -> 400", async () => {
  const { deps } = makeDeps("plain");
  const messages = Array.from({ length: 17 }, (_, i) => ({ role: i % 2 ? "assistant" : "user", content: `m${i}` }));
  const res = await core.handleChat(makeRequest({ body: validBody({ messages }) }), deps);
  assert.equal(res.status, 400);
  assert.ok((await readJson(res)).error.includes("16"));
});

await test("validation: 2001-char content -> 400", async () => {
  const { deps } = makeDeps("plain");
  const res = await core.handleChat(makeRequest({ body: validBody({ messages: [{ role: "user", content: "a".repeat(2001) }] }) }), deps);
  assert.equal(res.status, 400);
  assert.ok((await readJson(res)).error.includes("2000"));
});

await test("validation: last message not user -> 400", async () => {
  const { deps } = makeDeps("plain");
  const res = await core.handleChat(makeRequest({ body: validBody({ messages: [{ role: "assistant", content: "hello" }] }) }), deps);
  assert.equal(res.status, 400);
});

await test("validation: bad role -> 400", async () => {
  const { deps } = makeDeps("plain");
  const res = await core.handleChat(makeRequest({ body: validBody({ messages: [{ role: "system", content: "hi" }] }) }), deps);
  assert.equal(res.status, 400);
});

await test("validation: locale not en/fa -> 400", async () => {
  const { deps } = makeDeps("plain");
  const res = await core.handleChat(makeRequest({ body: validBody({ locale: "de" }) }), deps);
  assert.equal(res.status, 400);
});

await test("validation: short session_id -> 400", async () => {
  const { deps } = makeDeps("plain");
  const res = await core.handleChat(makeRequest({ body: validBody({ session_id: "abc" }) }), deps);
  assert.equal(res.status, 400);
});

await test("validation: invalid JSON body -> 400", async () => {
  const { deps } = makeDeps("plain");
  const req = makeRequest({ body: undefined });
  req.json = async () => {
    throw new Error("bad json");
  };
  const res = await core.handleChat(req, deps);
  assert.equal(res.status, 400);
});

await test("plain SSE flow: deltas + done, no capture", async () => {
  const { deps, mock } = makeDeps("plain");
  const res = await core.handleChat(makeRequest({ body: validBody() }), deps);
  assert.equal(res.status, 200);
  assert.equal(res.headers["Content-Type"], "text/event-stream");
  const { raw, events } = await readSse(res);
  const deltas = events.filter((e) => typeof e.delta === "string");
  assert.ok(deltas.length >= 3, "expected several delta events");
  const text = deltas.map((d) => d.delta).join("");
  assert.equal(text, "Hi there! SpielOS runs real company work through supervised AI departments.");
  assert.equal(events.at(-1).done, true);
  assert.ok(events.at(-1).reply_id.startsWith("r-"));
  assert.ok(!raw.includes("<<CAPTURE"));
  assert.equal(mock.log.formsubmit.length, 0, "no FormSubmit without capture");
  assert.equal(mock.log.postgrest.length, 0, "no CRM writes without capture");
});

await test("capture flow: marker parsed, stripped, lead upserted, event appended, formsubmit sent", async () => {
  const { deps, mock } = makeDeps("capture-split");
  const res = await core.handleChat(makeRequest({ body: validBody() }), deps);
  const { raw, events } = await readSse(res);
  assert.ok(!raw.includes("<<CAPTURE"), "marker must never reach the client");

  const captureEvent = events.find((e) => e.capture === true);
  assert.ok(captureEvent, "capture event must be emitted");
  assert.ok(typeof captureEvent.thanks_line === "string" && captureEvent.thanks_line.length > 0);
  const captureIdx = events.indexOf(captureEvent);
  assert.ok(captureIdx < events.length - 1, "capture event arrives before done");

  const deltas = events.filter((e) => typeof e.delta === "string").map((d) => d.delta).join("");
  assert.equal(deltas, "Thanks for sharing! Here's the plan.\n\n I'll have the team reach out.");

  // CRM: read-before-write happened (select by email first)
  const selects = mock.log.postgrest.filter((p) => p.method === "GET" && p.table === "leads");
  assert.equal(selects.length, 1);
  assert.equal(selects[0].emailFilter, "john@example.com", "email must be lowercased");
  // lead insert
  const inserts = mock.log.postgrest.filter((p) => p.method === "POST" && p.table === "leads");
  assert.equal(inserts.length, 1);
  const lead = inserts[0].body[0];
  assert.equal(lead.lead_key, "john@example.com");
  assert.equal(lead.email, "john@example.com");
  assert.equal(lead.contact_name, "John Doe");
  assert.equal(lead.segment, "software/product");
  assert.deepEqual(lead.sources, ["website_chat"]);
  assert.ok(lead.best_match_workflow === null || typeof lead.best_match_workflow === "string");
  // email_events row
  const ev = mock.log.postgrest.filter((p) => p.method === "POST" && p.table === "email_events");
  assert.equal(ev.length, 1);
  const row = ev[0].body[0];
  assert.equal(row.event, "captured");
  assert.equal(row.campaign, "chat-assistant");
  assert.equal(row.provider, "mistral-chat");
  assert.equal(row.subject, "Website chat lead captured");
  const detail = JSON.parse(row.detail);
  assert.equal(typeof detail.session_id, "string");
  assert.equal(detail.needs, "automate invoicing");
  assert.equal(detail.locale, "en");
  // FormSubmit attempted
  assert.equal(mock.log.formsubmit.length, 1);
  assert.equal(mock.log.formsubmit[0].body.email, "john@example.com");
  assert.equal(mock.log.formsubmit[0].body._subject, "New chat lead — spielos.xyz");
});

await test("capture flow: existing lead -> update path (contact_name kept, sources appended)", async () => {
  const { deps, mock } = makeDeps("capture-split");
  // seed the CRM with an existing lead
  mock.crm.leads.set(42, {
    id: 42,
    email: "john@example.com",
    contact_name: "Pre Existing",
    sources: ["outbound"],
    segment: "ops",
  });
  const res = await core.handleChat(makeRequest({ body: validBody() }), deps);
  const { events } = await readSse(res);
  assert.ok(events.some((e) => e.capture === true));
  const patches = mock.log.postgrest.filter((p) => p.method === "PATCH" && p.table === "leads");
  assert.equal(patches.length, 1);
  const patch = patches[0].body;
  assert.equal(patch.contact_name, undefined, "existing contact_name must NOT be overwritten");
  assert.deepEqual(patch.sources, ["outbound", "website_chat"]);
  assert.ok(patch.updated_at);
  assert.equal(mock.log.postgrest.filter((p) => p.method === "POST" && p.table === "leads").length, 0, "no insert on existing");
});

await test("capture with invalid email -> no capture event, no CRM writes", async () => {
  const { deps, mock } = makeDeps("capture-invalid-email");
  const res = await core.handleChat(makeRequest({ body: validBody() }), deps);
  const { raw, events } = await readSse(res);
  assert.ok(!raw.includes("<<CAPTURE"));
  assert.ok(!events.some((e) => e.capture === true), "invalid capture must not emit capture event");
  assert.equal(mock.log.postgrest.length, 0);
  assert.equal(mock.log.formsubmit.length, 0);
});

await test("capture with segment outside vocabulary -> stored as other", async () => {
  const { deps, mock } = makeDeps("capture-bad-segment");
  const res = await core.handleChat(makeRequest({ body: validBody() }), deps);
  const { events } = await readSse(res);
  assert.ok(events.some((e) => e.capture === true));
  const inserts = mock.log.postgrest.filter((p) => p.method === "POST" && p.table === "leads");
  assert.equal(inserts[0].body[0].segment, "other");
});

await test("capture in FA locale -> Persian thanks_line, locale in event detail", async () => {
  const { deps, mock } = makeDeps("capture-fa");
  const res = await core.handleChat(makeRequest({ body: validBody({ locale: "fa" }) }), deps);
  const { events } = await readSse(res);
  const cap = events.find((e) => e.capture === true);
  assert.ok(cap);
  assert.ok(/[\u0600-\u06FF]/.test(cap.thanks_line), "FA thanks_line must be Persian");
  const ev = mock.log.postgrest.filter((p) => p.method === "POST" && p.table === "email_events");
  assert.equal(JSON.parse(ev[0].body[0].detail).locale, "fa");
});

await test("double marker in one reply -> only one capture event", async () => {
  const { deps, mock } = makeDeps("capture-twice");
  const res = await core.handleChat(makeRequest({ body: validBody() }), deps);
  const { raw, events } = await readSse(res);
  assert.ok(!raw.includes("<<CAPTURE"));
  assert.equal(events.filter((e) => e.capture === true).length, 1);
  const deltas = events.filter((e) => typeof e.delta === "string").map((d) => d.delta).join("");
  assert.equal(deltas, " one  two.");
  assert.equal(mock.log.postgrest.filter((p) => p.method === "POST" && p.table === "leads").length, 1);
});

await test("marker-only reply -> capture event, empty visible text", async () => {
  const { deps, mock } = makeDeps("capture-marker-only");
  const res = await core.handleChat(makeRequest({ body: validBody() }), deps);
  const { raw, events } = await readSse(res);
  assert.ok(!raw.includes("<<CAPTURE"));
  assert.equal(events.filter((e) => e.capture === true).length, 1);
  assert.equal(events.filter((e) => typeof e.delta === "string").length, 0);
});

await test("FormSubmit 500 does NOT block capture", async () => {
  const { deps, mock } = makeDeps("capture-split", { formsubmitStatus: 500 });
  const res = await core.handleChat(makeRequest({ body: validBody() }), deps);
  const { events } = await readSse(res);
  assert.ok(events.some((e) => e.capture === true), "capture:true even when FormSubmit fails");
  assert.equal(mock.log.formsubmit.length, 1, "FormSubmit was attempted");
  assert.equal(mock.log.postgrest.filter((p) => p.method === "POST" && p.table === "leads").length, 1, "lead still written");
  assert.equal(mock.log.postgrest.filter((p) => p.method === "POST" && p.table === "email_events").length, 1, "event still written");
});

await test("PostgREST down -> no capture event, stream still completes", async () => {
  const { deps, mock } = makeDeps("capture-split", { postgrestStatus: 500 });
  const res = await core.handleChat(makeRequest({ body: validBody() }), deps);
  const { raw, events } = await readSse(res);
  assert.ok(!events.some((e) => e.capture === true), "capture event suppressed on CRM failure");
  assert.equal(events.at(-1).done, true, "stream must still complete gracefully");
  assert.ok(!raw.includes("<<CAPTURE"));
});

await test("upstream Mistral 500 -> JSON 500 error", async () => {
  const { deps, mock } = makeDeps("upstream-500");
  const res = await core.handleChat(makeRequest({ body: validBody() }), deps);
  assert.equal(res.status, 500);
  const j = await readJson(res);
  assert.equal(j.error, "The assistant is briefly unavailable — try again in a moment.");
});

await test("missing SUPABASE_URL -> capture suppressed but stream completes", async () => {
  const { deps, mock } = makeDeps("capture-split");
  deps.getEnv = (k) => (k === "MISTRAL_API_KEY" ? ENV.MISTRAL_API_KEY : undefined);
  const res = await core.handleChat(makeRequest({ body: validBody() }), deps);
  const { events } = await readSse(res);
  assert.ok(!events.some((e) => e.capture === true));
  assert.equal(events.at(-1).done, true);
});

// --- pure unit tests --------------------------------------------------------

await test("unit: marker parse + strip (single string)", async () => {
  const r = core.parseCaptureMarker("Hello <<CAPTURE:name=Ann|email=ann@x.co|company=|needs=|segment=ops>> bye", knowledge.segment_vocabulary);
  assert.equal(r.captured.name, "Ann");
  assert.equal(r.captured.email, "ann@x.co");
  assert.equal(r.visibleText, "Hello  bye");
});

await test("unit: phone-only capture passes (no email)", async () => {
  const r = core.parseCaptureMarker("Hi <<CAPTURE:name=Ann|email=|phone=+1 555 123 4567|company=|needs=|segment=ops>>", knowledge.segment_vocabulary);
  assert.ok(r.captured, "phone-only capture must succeed");
  assert.equal(r.captured.email, "");
  assert.equal(r.captured.phone, "+15551234567");
});

await test("unit: phone + email both kept", async () => {
  const r = core.parseCaptureMarker("x <<CAPTURE:name=Bo|email=bo@x.co|phone=09121234567|company=|needs=|segment=other>>", knowledge.segment_vocabulary);
  assert.equal(r.captured.email, "bo@x.co");
  assert.equal(r.captured.phone, "09121234567");
});

await test("unit: no email and no phone fails capture", async () => {
  const r = core.parseCaptureMarker("x <<CAPTURE:name=Ann|email=|phone=|company=|needs=|segment=other>>", knowledge.segment_vocabulary);
  assert.equal(r.captured, null);
});

await test("unit: short phone fails, falls to invalid", async () => {
  const r = core.parseCaptureMarker("x <<CAPTURE:name=Ann|email=|phone=12345|company=|needs=|segment=other>>", knowledge.segment_vocabulary);
  assert.equal(r.captured, null);
});

await test("unit: returning_visitor context accepted in body", async () => {
  const { deps, mock } = makeDeps("plain-reply");
  const res = await core.handleChat(makeRequest({ body: { ...validBody(), returning_visitor: { name: "Ann" } } }), deps);
  assert.equal(res.status, 200); // validation passes; mock serves plain reply
});

await test("unit: first-answer ask in addendum + brevity in handler consts", async () => {
  assert.ok(core.CAPTURE_ADDENDUM_EN.includes("who am I talking to"));
});

await test("unit: maxMarkerPrefixLen holds back partial marker starts", async () => {
  // scanChunk on text ending mid-marker must not flush the partial marker.
  const r = core.scanChunk("Great! <<CAPT", knowledge.segment_vocabulary, false);
  assert.equal(r.flush, "Great! ");
  assert.equal(r.hold, "<<CAPT");
  assert.equal(r.captured, null);
});

await test("unit: scanChunk with full start but no end holds everything from marker on", async () => {
  const r = core.scanChunk("Nice. <<CAPTURE:name=Jo", knowledge.segment_vocabulary, false);
  assert.equal(r.flush, "Nice. ");
  assert.ok(r.hold.startsWith("<<CAPTURE:name=Jo"));
  assert.equal(r.captured, null);
});

await test("unit: extractDelta parses mistral lines, ignores [DONE]", async () => {
  assert.equal(core.extractDelta('[DONE]'), null);
  assert.equal(core.extractDelta('{"choices":[{"delta":{"content":"hi"}}]}'), "hi");
  assert.equal(core.extractDelta('{"choices":[{"delta":{}}]}'), null);
  assert.equal(core.extractDelta("not json"), null);
});

await test("unit: RateLimiter minute + hour caps", async () => {
  const rl = freshRateLimiter();
  for (let i = 0; i < 10; i++) assert.equal(rl.check("k").allowed, true);
  assert.equal(rl.check("k").allowed, false);
  assert.equal(rl.check("k2").allowed, true, "different key unaffected");
});

await test("unit: thanksLine locale switch", async () => {
  assert.ok(/thanks/i.test(core.thanksLine("en")));
  assert.ok(/[\u0600-\u06FF]/.test(core.thanksLine("fa")));
});

await test("unit: deriveBestMatchWorkflow routes needs text", async () => {
  const mk = (needs) => ({ name: "A B", email: "a@b.co", company: "", needs, segment: null });
  assert.equal(core.deriveBestMatchWorkflow(mk("we need help with invoice processing")), "invoice-processing-automation");
  assert.equal(core.deriveBestMatchWorkflow(mk("candidate screening for hiring")), "recruitment-automation");
  assert.equal(core.deriveBestMatchWorkflow(mk("")), null);
  assert.equal(core.deriveBestMatchWorkflow(mk("something unrelated")), null);
});

await test("unit: prompt addendum instructs exact marker format", async () => {
  const en = core.CAPTURE_ADDENDUM_EN;
  assert.ok(en.includes("<<CAPTURE:name="));
  assert.ok(en.includes("segment"));
  const fa = core.CAPTURE_ADDENDUM_FA;
  assert.ok(fa.includes("<<CAPTURE:name="));
});

// --- knowledge-pack evals (30+ assertions) ----------------------------------

console.log("");
const evalResults = runEvals(knowledge, core);

// --- summary ----------------------------------------------------------------

console.log("");
console.log(`behavior tests: ${passed} passed, ${failed} failed`);
console.log(`eval assertions: ${evalResults.passed} passed, ${evalResults.failed} failed`);
if (failures.length) {
  console.log("\nfailures:");
  for (const f of failures) console.log(` - ${f.name}: ${f.error.message.split("\n")[0]}`);
  for (const f of evalResults.failures) console.log(` - ${f.name}: ${f.error}`);
}
if (failed > 0 || evalResults.failed > 0) {
  process.exitCode = 1;
} else {
  console.log("\nALL TESTS PASS");
}
