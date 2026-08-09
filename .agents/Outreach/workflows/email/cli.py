"""Email workflow — admin commands (record-reply, replies, stats).

Domain-specific convenience commands for the owner session, dispatched by
`python3 -m Outreach ...`. The loop itself never touches these.
"""

from datetime import datetime, timezone

from . import analytics, outbound


def record_reply(identifier: str, note: str = "") -> None:
    log = outbound.load_sent_log()
    s = next(
        (x for x in log.get("sent", []) if x.get("lead_id") == identifier or x.get("email") == identifier),
        None,
    )
    if not s:
        print(f"ERROR: no sent email found for '{identifier}' (use lead_id or email).")
        raise SystemExit(1)

    metrics = analytics.load_metrics()
    for r in metrics.get("replies", []):
        if r["lead_id"] == s["lead_id"]:
            at = r.get("recorded_at") or r.get("received_at") or "?"
            print(f"ERROR: reply already recorded for {s['email']} on {at}.")
            raise SystemExit(1)

    metrics.setdefault("replies", []).append({
        "received_id": None,
        "lead_id": s["lead_id"],
        "email": s["email"],
        "company": s.get("company"),
        "variant": s.get("variant"),
        "subject": s.get("subject"),
        "message_id": None,
        "received_at": None,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "kind": "reply",
        "note": note or "",
    })
    analytics.save_metrics(metrics)
    print(f"✅ Reply recorded for {s.get('contact_name', '?')} <{s['email']}> ({s.get('company', '?')})")


def replies() -> None:
    metrics = analytics.load_metrics()
    rs = metrics.get("replies", [])
    if not rs:
        print("No replies recorded yet. Use `record-reply <email|lead_id>` when one lands "
              "in the inbox, or set REPLY_TO to a Resend receiving domain to auto-detect.")
        return
    print(f"\n{'='*60}")
    print(f"  REPLIES ({len(rs)})")
    print(f"{'='*60}")
    for r in rs:
        note = f" — {r['note']}" if r.get("note") else ""
        source = "auto" if r.get("received_id") else "manual"
        print(f"  {r['recorded_at'][:16]}  {r['email']} ({r.get('company', '?')})  "
              f"[{r.get('variant', '?')} · {r.get('kind')} · {source}]{note}")
    print(f"{'='*60}\n")


def stats() -> None:
    contacts = outbound.read_contacts()
    langs = {}
    tiers = {}
    statuses = {}
    recs = {}
    for c in contacts:
        langs[c["language"]] = langs.get(c["language"], 0) + 1
        tiers[c["outreach_tier"]] = tiers.get(c["outreach_tier"], 0) + 1
        statuses[c["sequence_status"]] = statuses.get(c["sequence_status"], 0) + 1
        recs[c["send_recommendation"]] = recs.get(c["send_recommendation"], 0) + 1

    log = outbound.load_sent_log()
    sent_count = len(log.get("sent", []))

    print(f"\n{'='*55}")
    print(f"  DATABASE STATS — Master Outreach")
    print(f"{'='*55}")
    print(f"  Total contacts:       {len(contacts)}")
    print(f"  Already sent:         {sent_count}")
    print(f"  Remaining:            {len(contacts) - sent_count}")
    print("")
    print("  By Language:")
    for k, v in sorted(langs.items()):
        print(f"    {k:<12} {v}")
    print("")
    print("  By Tier:")
    for k, v in sorted(tiers.items()):
        print(f"    {k:<12} {v}")
    print("")
    print("  By Sequence Status:")
    for k, v in sorted(statuses.items()):
        print(f"    {k:<12} {v}")
    print("")
    print("  By Send Recommendation:")
    for k, v in sorted(recs.items()):
        print(f"    {k:<12} {v}")
    print(f"{'='*55}\n")
