# PostHog reverse proxy on Cloudflare

Hides `eu.posthog.com` behind `t.spielos.xyz` so ad-blocker blocklists
(which match `posthog`, `analytics`, `ph`, etc.) don't silently drop events.

The `t.` prefix is deliberately meaningless — blocklists use pattern matching
on suspicious labels, so a plain short label is what slips through.

## Files

| File                | Purpose                                       |
|---------------------|-----------------------------------------------|
| `posthog-proxy.js`  | The Worker — forwards any path to eu.posthog.com, sets CORS. |
| `wrangler.toml`     | Worker config. Binds the custom domain `t.spielos.xyz`. |
| `setup.sh`          | One-shot bootstrap: zone, DNS records, worker deploy. |

## One-time setup

### 1. Add the site to Cloudflare

Cloudflare dashboard → **Add a site** → `spielos.xyz` → Free plan.
Cloudflare will print two nameservers. Keep this page open.

### 2. Point the domain's nameservers to Cloudflare

Log in to **parspack.co** → DNS / Nameserver settings for `spielos.xyz`
→ replace the existing `ns1.parspack.co` / `ns2.parspack.co` with the two
Cloudflare nameservers. Save. Propagation usually takes 5–30 minutes.

### 3. Get an API token

Cloudflare dashboard → **My Profile** → **API Tokens** → **Create Token** →
**Edit zone DNS** template (or custom with: Zone:Read, DNS:Edit, Workers Scripts:Edit,
Workers Routes:Edit, scope to `spielos.xyz`).

Also grab your **Account ID** from the right sidebar of any zone's overview page.

### 4. Run the setup script

```bash
export CLOUDFLARE_API_TOKEN="…"
export CLOUDFLARE_ACCOUNT_ID="…"
./infra/cloudflare/setup.sh
```

This is idempotent — re-run after any partial failure.

### 5. Add the custom domain in GitHub Pages

`gh api -X PUT repos/ShayanSpiel/ShayanSpiel.Github.io/pages \
   -f cname=spielos.xyz -f https_only=true`

(or do it in the web UI: Settings → Pages → Custom domain → `spielos.xyz`)

### 6. Verify

```bash
curl -sI https://t.spielos.xyz/static/array.js | head -1
# → HTTP/2 200 (or 304), served by Cloudflare

curl -sI https://spielos.xyz/ | head -1
# → HTTP/2 200 from GitHub Pages (after DNS + GH Pages propagates)
```

Open the PostHog dashboard → Activity tab — you should see events arriving
within a few seconds of opening `https://spielos.xyz/`.

## Why `t.` and not `analytics.` or `posthog.`?

Smart blocklists match common tracker patterns, so anything obvious
(`analytics.`, `track.`, `posthog.`, `ph.`, `metrics.`) gets flagged too.
A meaningless one-letter label matches nothing.

## Re-deploying the worker

After any edit to `posthog-proxy.js`:

```bash
CLOUDFLARE_API_TOKEN=… CLOUDFLARE_ACCOUNT_ID=… \
  npx wrangler@latest deploy --config infra/cloudflare/wrangler.toml infra/cloudflare/posthog-proxy.js
```
