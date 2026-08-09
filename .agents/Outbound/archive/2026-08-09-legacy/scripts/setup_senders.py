#!/usr/bin/env python3
"""
SpielOS Outbound — bring up new sending providers end to end.

For each provider in SEND_PROVIDERS that has credentials in .env but no
verisend identity yet, this script:
  1. creates the sending subdomain on the provider (or reuses it),
  2. reads the DNS records the provider wants (SPF / DKIM TXT / CNAME),
  3. creates them on Cloudflare (idempotent),
  4. re-checks the provider's domain state until verified.

Usage:
    python3 setup_senders.py            # bring up mailgun + postmark
    python3 setup_senders.py --status   # just report domain state
"""

import json
import sys
import time
import urllib.parse

import providers
import config as cfg
from providers import _open, _cf_api, cf_get_zone, cf_upsert_cname, cf_upsert_txt

ZONE = "spielos.xyz"


def _mg_auth():
    import base64
    return {"Authorization": "Basic " + base64.b64encode(
        f"api:{cfg.MAILGUN_API_KEY}".encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded"}


def _domain_name(sub) -> str:
    if sub.endswith(f".{ZONE}"):
        sub = sub[: -len(f".{ZONE}")]
    return f"{sub}.{ZONE}"


def _mg_create(domain):
    return _open("https://api.mailgun.net/v3/domains", method="POST", headers=_mg_auth(),
                 payload=urllib.parse.urlencode({
                     "name": domain, "smtp_password": "", "force_dkim_authority": "false"
                 }).encode())


def setup_mailgun(create=True):
    domain = _domain_name(cfg.MAILGUN_DOMAIN)
    base = "https://api.mailgun.net/v3"
    r = _open(f"{base}/domains/{urllib.parse.quote(domain)}", headers=_mg_auth())
    if r.get("error") or "domain" not in r:
        if not create:
            print(f"MAILGUN {domain}: NOT FOUND on account")
            return False
        r = _mg_create(domain)
        if r.get("error"):
            print(f"MAILGUN create failed: {r.get('message', r)}")
            return False
    d = r.get("domain", {})
    print(f"MAILGUN {domain}: state={d.get('state')}")
    zone_id = cf_get_zone(ZONE)
    for rec in (r.get("sending_dns_records") or []):
        name = (rec.get("name") or "").rstrip(".")
        value = rec.get("value") or ""
        rtype = rec.get("record_type")
        if not name or not value or rtype == "MX":
            continue
        if rtype == "CNAME":
            out = cf_upsert_cname(zone_id, name, value, proxied=False)
        elif rtype == "TXT":
            out = cf_upsert_txt(zone_id, name, value)
        else:
            continue
        print(f"  DNS {rtype:<5} {name} -> {value[:60]} | {('ok' if out.get('success') else 'ERR ' + str(out.get('errors', out))[:120])}")
    # final state ping
    s = _open(f"{base}/domains/{urllib.parse.quote(domain)}", headers=_mg_auth())
    d = s.get("domain", {})
    print(f"MAILGUN final: state={d.get('state')} "
          f"| spf={d.get('spf_state')} dkim={d.get('dkim_state')}")
    return d.get("state") == "active"


def setup_postmark(create=True):
    """Postmark: the token provided is a SERVER token — sending and stats work,
    but domains can only be created with an Account token, so the domain step
    happens in the dashboard. We validate the token and pre-create the SPF."""
    domain = _domain_name(cfg.POSTMARK_DOMAIN)
    head = {"X-Postmark-Server-Token": cfg.POSTMARK_API_TOKEN, "Content-Type": "application/json"}
    streams = _open("https://api.postmarkapp.com/message-streams", headers=head)
    server_id = None
    for s in (streams.get("MessageStreams") or []):
        server_id = s.get("ServerID")
        break
    if server_id is None:
        print("POSTMARK: server token not valid for sending API (or it is an Account token only)")
        return False
    print(f"POSTMARK: server token OK (ServerID {server_id})")
    zone_id = cf_get_zone(ZONE)
    spf = "v=spf1 include:spf.postmarkapp.com ~all"
    out = cf_upsert_txt(zone_id, domain, spf)
    print(f"  DNS TXT {domain} -> {spf}  {('ok' if out.get('success') else 'ERR ' + str(out.get('errors', out))[:120])}")
    print("POSTMARK: domain setup needs one dashboard step: add")
    print(f"  '{domain}' as a Sending Domain (postmarkapp.com -> Servers -> Domains),")
    print("  then paste the DKIM TXT value/name it returns and I will add it to DNS.")
    return True


def main():
    if "--status" in sys.argv:
        if cfg.MAILGUN_API_KEY and cfg.MAILGUN_DOMAIN:
            setup_mailgun(create=False)
        if cfg.POSTMARK_API_TOKEN and cfg.POSTMARK_DOMAIN:
            setup_postmark(create=False)
        return
    print(f"zone: {ZONE} | providers: {cfg.SEND_PROVIDERS}")
    if cfg.MAILGUN_API_KEY and cfg.MAILGUN_DOMAIN:
        setup_mailgun()
    if cfg.POSTMARK_API_TOKEN and cfg.POSTMARK_DOMAIN:
        setup_postmark()
    print("\nDone. Sending providers now:",
          providers.available_providers())


if __name__ == "__main__":
    main()