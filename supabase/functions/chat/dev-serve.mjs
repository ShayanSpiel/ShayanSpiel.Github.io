// Local dev server for the chat edge function (no Docker/Deno required).
// Runs the REAL handler from supabase/functions/chat/core.ts via Node's
// native TS stripping, with MISTRAL_API_KEY from the harness .spielos/.env.
// CRM capture is suppressed locally by design (SUPABASE_URL not provided);
// the CRM write goes live only on the approved production deploy.
// Usage: node supabase/functions/chat/dev-serve.mjs   (serves :8787)
import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const envPath = "/Users/shayan/Projects/SpielOS-Website/.spielos/.env";
const MISTRAL_KEYS = ["MISTRAL_API_KEY", "MISTRAL_API_KEY_2", "MISTRAL_API_KEY_3", "MISTRAL_API_KEY_4"];
let found = 0;
try {
  for (const line of readFileSync(envPath, "utf8").split("\n")) {
    const m = line.match(/^(MISTRAL_API_KEY(?:_\d)?)=(.+)$/);
    if (m && MISTRAL_KEYS.includes(m[1])) { process.env[m[1]] = m[2].trim(); found++; }
    const g = line.match(/^(GEMINI_API_KEY)=(.+)$/);
    if (g) process.env.GEMINI_API_KEY = g[2].trim();
  }
} catch {
  console.error("[dev-serve] harness .env not readable");
  process.exit(1);
}
if (found === 0 && !process.env.GEMINI_API_KEY) {
  console.error("[dev-serve] no mistral keys and no GEMINI_API_KEY");
  process.exit(1);
}
console.log(`[dev-serve] mistral keys loaded: ${found}`);
// CRM intentionally NOT set: capture events return thanks_line but skip the
// Supabase write locally (core logs it; the reply stream is unaffected).

const knowledge = JSON.parse(readFileSync(join(here, "knowledge.json"), "utf8"));

const { handleChat } = await import(
  pathToFileURL(join(here, "core.ts")).href
);

const server = createServer(async (req, res) => {
  try {
    const chunks = [];
    for await (const c of req) chunks.push(c);
    const body = Buffer.concat(chunks);
    const url = "http://127.0.0.1:8787" + (req.url || "");
    const request = new Request(url, {
      method: req.method,
      headers: {
        origin: req.headers.origin || "http://localhost:4321",
        "content-type": req.headers["content-type"] || "application/json",
        "x-forwarded-for": req.socket.remoteAddress || "127.0.0.1",
      },
      body: ["GET", "HEAD", "OPTIONS"].includes(req.method) ? undefined : body,
    });
    // handleChat uses MinimalRequest {method,url,headers,json()}
    const minimal = {
      method: req.method,
      url,
      headers: { get: (n) => req.headers[(n || "").toLowerCase()] ?? null },
      json: () => request.json(),
    };
    const response = await handleChat(minimal, {
      getEnv: (k) => process.env[k],
      fetchImpl: fetch,
      knowledge,
      createClient: () => {
        throw new Error("CRM disabled in local dev (by design)");
      },
    });
    const headers = { ...response.headers };
    res.writeHead(response.status, headers);
    if (typeof response.body === "string") res.end(response.body);
    else {
      const reader = response.body.getReader();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        res.write(Buffer.from(value));
      }
      res.end();
    }
  } catch (e) {
    console.error("[dev-serve] error:", e && e.message);
    if (!res.headersSent) res.writeHead(500, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "local dev server error" }));
  }
});

server.listen(8787, "127.0.0.1", () => {
  console.log("[dev-serve] chat on http://127.0.0.1:8787/functions/v1/chat (CRM writes suppressed locally)");
});
