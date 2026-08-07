#!/usr/bin/env python3
"""
SpielOS Outbound — goal engine (Email Data feedback loop).

Runs after every metrics pull. It is driven entirely by the GOALS table in
config.py: for each goal/limit it compares the current funnel rate, then flags
data problems (unverified, read-denied, unresolved ids, failed sends), compares
variants, and picks ONE next action. The loop keeps running (send → metrics →
review → act → send ...) until every goal is met.

Status:
  ON_TRACK        all "floor" goals met (reply rate, opens, clicks, delivery)
  BELOW_GOAL      at least one goal under target
  BUILDING_SAMPLE fewer than MIN_TOTAL_SAMPLE sent — rates not trustworthy yet

Usage:
  python3 outbound.py review
"""

import analytics
import config

_SEVERITY = {"high": 0, "medium": 1, "low": 2}
_STAGE = {"data": 0, "deliverability": 1, "open": 2, "click": 3, "reply": 4, "variant": 5}


def review(log: dict, metrics: dict) -> dict:
    totals = analytics.aggregate(log, metrics)
    by_variant = analytics.by_variant(log, metrics)
    failed = len(log.get("failed", []))
    status, gaps = _status(totals)
    recs, next_action = _recommend(totals, by_variant, failed)
    return {
        "totals": totals,
        "by_variant": by_variant,
        "failed": failed,
        "status": status,
        "gaps": gaps,
        "recommendations": recs,
        "next_action": next_action,
    }


def _status(totals: dict):
    if totals["sent"] < config.MIN_TOTAL_SAMPLE:
        return "BUILDING_SAMPLE", []
    gaps = [g["name"] for g in config.GOALS if g["kind"] == "floor" and totals[g["metric"]] < g["target"]]
    if not gaps:
        return "ON_TRACK", []
    return "BELOW_GOAL", gaps


def _goal_recs(totals: dict) -> list:
    """Recommendations derived from the GOALS table in config."""
    out = []
    for g in config.GOALS:
        val = totals[g["metric"]]
        if g["kind"] == "floor":
            if totals["unknown"]:
                continue  # don't judge rates we couldn't verify
            if val < g["target"]:
                out.append({
                    "stage": g["stage"],
                    "severity": g["severity"],
                    "text": (f"{g['name']} {val*100:.1f}% is below the goal of "
                             f"{g['target']*100:.0f}%. {g['action']}."),
                })
        else:
            if val > g["target"]:
                out.append({
                    "stage": g["stage"],
                    "severity": g["severity"],
                    "text": (f"{g['name']} {val*100:.2f}% is over the limit of "
                             f"{g['target']*100:.2f}%. {g['action']}."),
                })
    return out


def _recommend(totals: dict, by_variant: dict, failed: int):
    recs = _goal_recs(totals)

    if totals["denied"]:
        recs.append({
            "stage": "data",
            "severity": "high",
            "text": (f"{totals['denied']} emails: the provider refused to reveal status "
                     f"(401/403/404), which usually means the API key lacks read access. "
                     f"Create a Full access key for {config.EMAIL_PROVIDER} (Resend: "
                     f"resend.com/api-keys -> Edit -> Permission), or check the email belongs "
                     f"to the current team/domain."),
        })

    if totals["unknown"]:
        recs.append({
            "stage": "data",
            "severity": "high",
            "text": (f"{totals['unknown']} emails could not be verified (provider fetch failed, "
                     f"likely a network/VPN issue). Re-run `metrics --force` before trusting "
                     f"deliverability numbers."),
        })

    if totals["unresolved"]:
        recs.append({
            "stage": "data",
            "severity": "high",
            "text": (f"{totals['unresolved']} sent emails have no queryable provider id and the "
                     f"backfill could not match them. Look them up in the provider dashboard and "
                     f"paste the id into scripts/sent_log.json, then run metrics again."),
        })

    if failed:
        recs.append({
            "stage": "data",
            "severity": "high",
            "text": (f"{failed} sends failed earlier (sent_log.json failed[]) and were never "
                     f"delivered — they count against the goal. Retry them with a fresh "
                     f"`send` run."),
        })

    if not totals["unknown"] and totals["opened"] and totals["replied"] == 0 and totals["sent"] >= config.MIN_TOTAL_SAMPLE:
        recs.append({
            "stage": "reply",
            "severity": "high",
            "text": ("Emails are being opened but nobody replies. The question or the offer is "
                     "the bottleneck: make the reply cost ~10 seconds (one-word answer), and "
                     "make the offer concrete enough to react to."),
        })

    if totals["opened"]:
        for variant, v in sorted(by_variant.items(), key=lambda kv: kv[1]["sent"], reverse=True):
            if v["sent"] < config.MIN_VARIANT_SAMPLE:
                continue
            if v["reply_rate"] < totals["reply_rate"] and v["open_rate"] < totals["open_rate"]:
                recs.append({
                    "stage": "variant",
                    "severity": "low",
                    "text": (f"Variant '{variant}' ({v['sent']} sent) underperforms the pack on "
                             f"opens ({v['open_rate']*100:.0f}%) and replies "
                             f"({v['reply_rate']*100:.0f}%). Rewrite or retire it."),
                })

    if not recs:
        return [], None
    next_action = sorted(recs, key=lambda r: (_SEVERITY[r["severity"]], _STAGE[r["stage"]]))[0]
    return recs, next_action


# ── Output ────────────────────────────────────────────────────────────────────

def summary(rep: dict) -> dict:
    """Machine-readable form of the review (for --json)."""
    t = rep["totals"]
    return {
        "status": rep["status"],
        "provider": config.EMAIL_PROVIDER,
        "metrics_capable": analytics.providers.cap_status(),
        "sent": t["sent"],
        "rates": {
            "reply": t["reply_rate"],
            "open": t["open_rate"],
            "click": t["click_rate"],
            "delivered": t["delivered_rate"],
            "bounce": t["bounce_rate"],
            "spam": t["spam_rate"],
        },
        "views": {
            "replied": t["replied"],
            "opened": t["opened"],
            "clicked": t["clicked"],
            "delivered": t["delivered"],
            "bounced": t["bounced"],
            "complained": t["complained"],
            "unverified": t["unknown"],
            "denied": t["denied"],
            "unresolved": t["unresolved"],
            "failed": rep["failed"],
        },
        "gaps": rep["gaps"],
        "next_action": rep["next_action"],
    }


def print_review(rep: dict) -> None:
    t = rep["totals"]

    print(f"\n{'='*64}")
    print(f"  GOAL REVIEW — reply rate > {_goal('reply rate')['target']*100:.0f}% · status: {rep['status']}")
    print(f"  Provider: {config.EMAIL_PROVIDER} · Email Data: "
          f"{'on' if analytics.cap_status_supported() else 'off (no API-level tracking for this provider)'}")
    print(f"{'='*64}")
    print(f"  Reply:  {t['reply_rate']*100:5.1f}% ({t['replied']}/{t['sent']})   goal {_goal('reply rate')['target']*100:.0f}%")
    print(f"  Open:   {t['open_rate']*100:5.1f}% ({t['opened']}/{t['delivered']})   goal {_goal('open rate')['target']*100:.0f}%")
    print(f"  Click:  {t['click_rate']*100:5.1f}% ({t['clicked']}/{t['delivered']})   goal {_goal('click rate')['target']*100:.0f}%")
    print(f"  Deliv:  {t['delivered_rate']*100:5.1f}% ({t['delivered']}/{t['sent']})   goal {_goal('delivered rate')['target']*100:.0f}%")
    print(f"  Bounce: {t['bounce_rate']*100:5.1f}%   Spam: {t['spam_rate']*100:.2f}%   "
          f"Failed earlier: {rep['failed']}   Unverified: {t['unknown']}   "
          f"Read denied: {t['denied']}   Unresolved: {t['unresolved']}   Auto: {t['auto']}")

    if rep["status"] == "BUILDING_SAMPLE":
        print(f"\n  Sample too small ({t['sent']} sent, need {config.MIN_TOTAL_SAMPLE}) — keep sending and "
              f"measuring; rates firm up as data accumulates.")
    if rep["status"] == "ON_TRACK":
        print(f"\n  All funnel goals met and reply rate > {_goal('reply rate')['target']*100:.0f}%.")
        print(f"  Hold the loop: keep sending at a safe throttle and re-check on schedule.")

    if rep["by_variant"]:
        print(f"\n  By variant:")
        for v, d in sorted(rep["by_variant"].items(), key=lambda kv: kv[1]["sent"], reverse=True):
            flag = "" if d["sent"] >= config.MIN_VARIANT_SAMPLE else "  (small sample)"
            print(f"    {v:<22} n={d['sent']:>2}  open {d['open_rate']*100:5.1f}%  "
                  f"click {d['click_rate']*100:5.1f}%  reply {d['reply_rate']*100:5.1f}%{flag}")

    if rep["recommendations"]:
        print(f"\n  Recommendations ({len(rep['recommendations'])}):")
        for i, r in enumerate(rep["recommendations"], 1):
            print(f"    {i}. [{r['severity']:>6} · {r['stage']}] {r['text']}")

    if rep["next_action"]:
        na = rep["next_action"]
        print(f"\n  NEXT ACTION ({na['severity']} · {na['stage']}):")
        print(f"    {na['text']}")
    print(f"{'='*64}\n")


def _goal(name: str) -> dict:
    for g in config.GOALS:
        if g["name"] == name:
            return g
    return {}
