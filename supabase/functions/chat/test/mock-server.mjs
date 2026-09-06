// Mock upstreams for the chat edge-function tests. Plain Node, no deps.
// Provides:
//   - a fake Mistral /v1/chat/completions SSE endpoint (scenarios: plain,
//     capture-marker split across chunks, upstream-500, never-capture)
//   - a fake PostgREST (leads select/update/insert + email_events insert)
//   - a fake FormSubmit endpoint (configurable status)
// Everything is in-memory; no network is used.

export function sseChunk(obj) {
  return `data: ${JSON.stringify(obj)}\n\n`;
}

/** Build a Mistral SSE body from an array of content deltas. */
export function mistralBody(deltas, { done = true } = {}) {
  const parts = [];
  for (const d of deltas) {
    parts.push(sseChunk({ choices: [{ delta: { content: d } }] }));
  }
  parts.push("data: [DONE]\n\n");
  return parts.join("");
}

/** Split a string into N stream chunks the way a real socket would. */
export function chunkSplit(text, sizes) {
  const out = [];
  let i = 0;
  let k = 0;
  while (i < text.length) {
    const n = sizes[k % sizes.length];
    out.push(text.slice(i, i + n));
    i += n;
    k += 1;
  }
  return out;
}

/** A Response-like object backed by a web ReadableStream of Uint8Array chunks. */
export function sseResponse(text, { status = 200, chunkSizes = [17, 5, 23, 3, 11, 7] } = {}) {
  const parts = chunkSplit(text, chunkSizes).map((c) => new TextEncoder().encode(c));
  const stream = new ReadableStream({
    start(controller) {
      for (const p of parts) controller.enqueue(p);
      controller.close();
    },
  });
  return {
    ok: status >= 200 && status < 300,
    status,
    body: stream,
  };
}

/**
 * Creates a fetchImpl that routes by URL:
 *   - api.mistral.ai  -> scenario-driven SSE
 *   - localhost postgrest-ish SUPABASE_URL -> in-memory CRM
 *   - formsubmit.co   -> configurable status
 * Records every request into `log`.
 */
export function makeMockFetch({ scenario = "plain", postgrestStatus = 200, formsubmitStatus = 200, supabaseUrl = "https://test-supabase.local" } = {}) {
  const log = { mistral: [], postgrest: [], formsubmit: [] };
  const crm = makeMemoryCrm();

  async function fetchImpl(url, init = {}) {
    const u = String(url);
    if (u.startsWith("https://api.mistral.ai/")) {
      log.mistral.push({ url: u, body: JSON.parse(init.body ?? "{}") });
      if (scenario === "upstream-500") {
        return { ok: false, status: 500, body: null, json: async () => ({}) };
      }
      let deltas;
      if (scenario === "capture-split") {
        // marker split across chunks mid-stream
        deltas = [
          "Thanks for sharing! ",
          "Here's the plan.\n\n",
          "<<CAPTURE:name=John Doe|ema",
          "il=John@Example.com|company=Acme|needs=automate invoicing|segment=software/product>>",
          " I'll have the team reach out.",
        ];
      } else if (scenario === "capture-invalid-email") {
        deltas = ["Great. ", "<<CAPTURE:name=John Doe|email=not-an-email|company=|needs=|segment=bogus>>", " done."];
      } else if (scenario === "capture-bad-segment") {
        deltas = ["Sure. ", "<<CAPTURE:name=Jane Roe|email=jane@example.com|company=|needs=|segment=banana>>", " ok."];
      } else if (scenario === "capture-fa") {
        deltas = ["ممنون! ", "<<CAPTURE:name=Jane Doe|email=jane@example.com|company=|needs=فاکتورها|segment=finance>>", " باشه."];
      } else if (scenario === "capture-twice") {
        deltas = [
          "<<CAPTURE:name=John Doe|email=jd@example.com|company=|needs=|segment=ops>>",
          " one ",
          "<<CAPTURE:name=John Doe|email=jd@example.com|company=|needs=|segment=ops>>",
          " two.",
        ];
      } else if (scenario === "capture-marker-only") {
        deltas = ["<<CAPTURE:name=Solo Marker|email=solo@example.com|company=|needs=|segment=other>>"];
      } else {
        deltas = ["Hi there! ", "SpielOS runs real company work ", "through supervised AI departments."];
      }
      return sseResponse(mistralBody(deltas));
    }
    if (u.includes("formsubmit.co")) {
      log.formsubmit.push({ url: u, body: JSON.parse(init.body ?? "{}") });
      return { ok: formsubmitStatus < 400, status: formsubmitStatus, json: async () => ({}) };
    }
    if (u.startsWith(supabaseUrl)) {
      return postgrestHandler(u, init, { log, crm, status: postgrestStatus });
    }
    throw new Error(`mock fetch: unmocked URL ${u}`);
  }

  return { fetchImpl, log, crm };
}

export function makeMemoryCrm() {
  const leads = new Map();
  const events = [];
  let idSeq = 1;
  return {
    leads,
    events,
    reset() {
      leads.clear();
      events.length = 0;
      idSeq = 1;
    },
    nextId() {
      return idSeq++;
    },
  };
}

/** Extremely small PostgREST emulation for the paths supabase-js uses. */
function postgrestHandler(url, init, { log, crm, status }) {
  const parsed = new URL(url);
  const table = parsed.pathname.split("/").filter(Boolean).pop();
  const method = init.method ?? "GET";
  const body = init.body ? JSON.parse(init.body) : null;
  const selectMatch = parsed.searchParams.get("select");
  const emailFilter = parsed.searchParams.get("email") ?? parsed.searchParams.get("eq");
  log.postgrest.push({ method, table, selectMatch, emailFilter, body });

  const respond = (payload, code = 200) => ({
    ok: code < 400,
    status: code,
    json: async () => payload,
  });

  if (status !== 200) return respond({ message: "postgrest down" }, status);

  if (method === "GET" && table === "chat_leads" && selectMatch) {
    const leadKeyFilter = parsed.searchParams.get("lead_key");
    const found = leadKeyFilter
      ? [...crm.leads.values()].find((l) => l.lead_key === leadKeyFilter) ?? null
      : null;
    return respond(found ? [found] : [], 200);
  }
  if (method === "POST" && table === "chat_leads") {
    const rows = Array.isArray(body) ? body : [body];
    const withIds = rows.map((r) => ({ id: crm.nextId(), ...r }));
    for (const r of withIds) crm.leads.set(r.id, r);
    return respond(withIds, 201);
  }
  if (method === "POST" && table === "chat_conversations") {
    const rows = Array.isArray(body) ? body : [body];
    for (const r of rows) crm.events.push(r);
    return respond(rows, 201);
  }
  if (method === "PATCH" && table === "chat_leads") {
    const id = parsed.searchParams.get("id");
    const target = [...crm.leads.values()].find((l) => String(l.id) === String(id));
    if (target) Object.assign(target, body);
    return respond([target].filter(Boolean), 200);
  }
  return respond({ message: `unmocked postgrest ${method} ${table}` }, 404);
}

/**
 * A minimal supabase-js-compatible client over the mock fetch. Mirrors the
 * subset of the builder API core.ts uses: from().select().eq().maybeSingle(),
 * from().update().eq(), from().insert().
 */
export function makeMockSupabaseClient(fetchImpl, baseUrl) {
  const call = async (path, method, body, query) => {
    const qs = new URLSearchParams(query).toString();
    const res = await fetchImpl(`${baseUrl}/rest/v1/${path}${qs ? `?${qs}` : ""}`, {
      method,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    let data = null;
    try {
      data = await res.json();
    } catch {
      data = null;
    }
    return { data, error: res.ok ? null : { message: `HTTP ${res.status}` } };
  };

  return {
    from(table) {
      return {
        select(cols) {
          return {
            eq(col, val) {
              return {
                async maybeSingle() {
                  const r = await call(table, "GET", undefined, { select: cols, [col]: String(val) });
                  const rows = Array.isArray(r.data) ? r.data : [];
                  return { data: rows[0] ?? null, error: r.error };
                },
              };
            },
          };
        },
        update(patch) {
          return {
            async eq(col, val) {
              return call(table, "PATCH", patch, { [col]: String(val) });
            },
          };
        },
        async insert(rows) {
          return call(table, "POST", rows);
        },
      };
    },
  };
}
