#!/usr/bin/env bash
# infra/cloudflare/setup.sh
# One-shot Cloudflare bootstrap for spielos.xyz + PostHog proxy worker.
#
# Required env:
#   CLOUDFLARE_API_TOKEN   — API token with Zone:Edit, DNS:Edit, Workers:Edit on spielos.xyz
#   CLOUDFLARE_ACCOUNT_ID  — your Cloudflare account ID
#
# What it does (idempotent — safe to re-run):
#   1. Looks up the spielos.xyz zone. If not active, exits with instructions.
#   2. Adds the four GitHub Pages A records for the apex.
#   3. Adds a www CNAME → shayanspiel.github.io.
#   4. Deploys the posthog-proxy worker with the t.spielos.xyz custom-domain binding.
#
# After this script finishes, the only remaining step is:
#   • Update nameservers at parspack.co to the ones Cloudflare gives you.
#   • Add "spielos.xyz" as a custom domain in GitHub Pages settings.

set -euo pipefail

: "${CLOUDFLARE_API_TOKEN:?Set CLOUDFLARE_API_TOKEN}"
: "${CLOUDFLARE_ACCOUNT_ID:?Set CLOUDFLARE_ACCOUNT_ID}"

ZONE_NAME="spielos.xyz"
GH_PAGES_TARGET="shayanspiel.github.io"
GH_PAGES_IPS=(
  "185.199.108.153"
  "185.199.109.153"
  "185.199.110.153"
  "185.199.111.153"
)
CF_API="https://api.cloudflare.com/client/v4"

api() {
  curl -sS -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
       -H "Content-Type: application/json" "$@"
}

# ---- 1. Zone ----
echo "==> Looking up zone ${ZONE_NAME}"
zone_resp=$(api "${CF_API}/zones?name=${ZONE_NAME}")
zone_id=$(echo "$zone_resp" | jq -r '.result[0].id // empty')
if [ -z "$zone_id" ]; then
  echo ""
  echo "Zone not active on Cloudflare yet. Steps:"
  echo "  1. In Cloudflare dashboard, click 'Add a site' for ${ZONE_NAME} on the Free plan."
  echo "  2. Cloudflare will assign two nameservers (e.g. anna.ns.cloudflare.com)."
  echo "  3. Log in to parspack.co → DNS settings → change NS records to those values."
  echo "  4. Wait 5-30 minutes for propagation, then re-run this script."
  echo ""
  echo "API response: $zone_resp"
  exit 1
fi
echo "    zone_id=${zone_id}"

# ---- 2 + 3. DNS records ----
upsert_record() {
  local type=$1 name=$2 content=$3 proxied=${4:-true}
  local existing
  existing=$(api "${CF_API}/zones/${zone_id}/dns_records?type=${type}&name=${name}" \
             | jq -r '.result[0].id // empty')
  if [ -n "$existing" ]; then
    echo "    (exists) ${type} ${name} → ${content}"
    return
  fi
  echo "==> Add ${type} ${name} → ${content} (proxied=${proxied})"
  api "${CF_API}/zones/${zone_id}/dns_records" -X POST \
    -d "$(jq -n --arg t "$type" --arg n "$name" --arg c "$content" \
         --argjson p "$proxied" \
         '{type:$t, name:$n, content:$c, proxied:$p, ttl:1}')" \
    | jq -r '"    -> " + (.success|tostring) + " " + (.errors[0].message // "ok")'
}

for ip in "${GH_PAGES_IPS[@]}"; do
  upsert_record A "@" "$ip" true
done
upsert_record CNAME "www" "${GH_PAGES_TARGET}" true

# ---- 4. Worker deploy ----
echo "==> Deploying posthog-proxy worker"
CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN}" \
CLOUDFLARE_ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID}" \
  npx --yes wrangler@latest deploy \
      --config "$(dirname "$0")/wrangler.toml" \
      "$(dirname "$0")/posthog-proxy.js"

echo ""
echo "Done. Next steps:"
echo "  • Update NS at parspack.co to the Cloudflare-assigned nameservers (if you haven't)."
echo "  • In GitHub: Settings → Pages → Custom domain → spielos.xyz → Save."
echo "  • In PostHog: Project Settings → Proxy → confirm the t.spielos.xyz host is recorded."
echo "  • Verify: curl -sI https://t.spielos.xyz/static/array.js | head -1"
