// Cloudflare Worker — PostHog reverse proxy
// Hides eu.posthog.com behind t.spielos.xyz so ad-blocker blocklists
// (which match "posthog", "analytics", "ph") don't drop our events.
//
// Deployed with `npx wrangler deploy` (see infra/cloudflare/README.md).

const POSTHOG_ORIGIN = "https://eu.posthog.com";

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(request) });
    }

    const url = new URL(request.url);
    const target = `${POSTHOG_ORIGIN}${url.pathname}${url.search}`;

    const upstream = await fetch(target, {
      method: request.method,
      headers: request.headers,
      body: request.body,
      redirect: "follow",
    });

    const headers = new Headers(upstream.headers);
    for (const [k, v] of Object.entries(corsHeaders(request))) {
      headers.set(k, v);
    }

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers,
    });
  },
};

function corsHeaders(request) {
  const origin = request.headers.get("Origin") || "*";
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}
