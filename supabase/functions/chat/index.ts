// SpielOS website chat assistant - Deno entrypoint for the Supabase Edge
// Function `chat`. WorkOrder work-e1c5f052f619 (WO2), Goal goal-3220ae01c4f7.
//
// All request/response logic lives in core.ts (platform-neutral, unit-tested
// from test/*.mjs under plain Node). This file only:
//   1. statically imports the knowledge pack (WO1 artifact),
//   2. adapts the Deno Request to the MinimalRequest core.ts expects,
//   3. adapts core's MinimalResponse into a Deno Response,
//   4. provides the supabase-js service client factory via esm.sh.
//
// Secrets (injected by the platform at deploy, never present in the repo):
//   MISTRAL_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

import { handleChat, type HandlerDeps, type MinimalResponse } from "./core.ts";
import knowledge from "./knowledge.json" with { type: "json" };
// deno-lint-ignore no-explicit-any
import { createClient as createClientEsm } from "https://esm.sh/@supabase/supabase-js@2";

function minimalHeaders(headers: Headers): { get(name: string): string | null } {
  return {
    get(name: string): string | null {
      return headers.get(name);
    },
  };
}

function toDenoResponse(res: MinimalResponse): Response {
  return new Response(res.body === "" ? null : res.body, {
    status: res.status,
    headers: res.headers,
  });
}

export const handlerDeps: HandlerDeps = {
  getEnv: (key: string) => Deno.env.get(key),
  fetchImpl: fetch,
  knowledge: {
    system_prompt_en: knowledge.system_prompt_en,
    system_prompt_fa: knowledge.system_prompt_fa,
    segment_vocabulary: knowledge.segment_vocabulary,
  },
  createClient: (url: string, key: string) => createClientEsm(url, key, { auth: { persistSession: false } }) as never,
};

export async function handler(req: Request): Promise<Response> {
  const res = await handleChat(
    {
      method: req.method,
      url: req.url,
      headers: minimalHeaders(req.headers),
      json: () => req.json(),
    },
    handlerDeps,
  );
  return toDenoResponse(res);
}

Deno.serve(handler);
