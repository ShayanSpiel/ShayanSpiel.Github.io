#!/usr/bin/env python3
"""
Harness — report: the human-readable cycle report (experiments/report.md).

Every cycle appends one section: sent totals, KPIs vs goals, guardrails,
weakest link, the verdict on the previous experiment, the next lever + its
hypothesis. The user reads this file; it is the conversation with the loop.
"""

import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(os.path.dirname(HERE), "experiments", "report.md")


def _pct(x):
    return f"{x*100:.1f}%" if x is not None else "—"


def _line(name, cur, target=None, is_goal=True):
    if target is None:
        return f"  {name:<16} {_pct(cur)}"
    ok = "✅" if (cur >= target if is_goal else cur <= target) else "❌"
    return f"  {name:<16} {_pct(cur):>7}  target {_pct(target):>7}  {ok}"


def write_report(record: dict) -> None:
    """record: {id, batch, sent_total, sent_today, cap, totals, goals,
    guardrail_breaches, weakest, previous_verdict, next_lever, hypothesis}"""
    t = record.get("totals", {})
    meta = record.get("meta", {})
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append(f"## {record.get('id', 'cycle')} — {ts}")
    lines.append("")
    lines.append(f"Batch: {record.get('batch', '?')} · sent total: {record.get('sent_total', '?')}"
                 f" · sent today: {record.get('sent_today', '?')}/{record.get('cap', '?')}")
    lines.append("")

    lines.append("**KPIs vs goals**")
    for g in meta.get("goal", []) and [meta["goal"]] or []:
        lines.append(_line(g["name"], t.get(g["metric"]), g["target"]))
    for k in meta.get("supporting_kpis", []):
        lines.append(_line(k["name"], t.get(k["metric"]), k["target"]))
    lines.append("")
    lines.append("**Guardrails**")
    for gr in meta.get("guardrails", []):
        lines.append(_line(gr["name"], t.get(gr["metric"]), gr["max"], is_goal=False))
    if record.get("guardrail_breaches"):
        lines.append("  ⛔ BREACH: " + "; ".join(b["name"] for b in record["guardrail_breaches"]))
    lines.append("")

    lines.append(f"**Weakest link:** {record.get('weakest_text', '—')}")
    lines.append("")
    prev = record.get("previous_verdict")
    if prev:
        lines.append(f"**Previous experiment verdict:** {prev.get('verdict', '—')} — {prev.get('reason', '')}")
    lines.append("")
    nl = record.get("next_lever")
    if nl:
        lines.append(f"**Next lever:** {nl}")
    hyp = record.get("hypothesis")
    if hyp:
        lines.append(f"**Hypothesis:** {hyp}")
    lines.append("")
    lines.append("---")
    lines.append("")

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "a") as f:
        f.write("\n".join(lines))


def status_line(record: dict) -> str:
    t = record.get("totals", {})
    return (f"reply {_pct(t.get('reply_rate'))} open {_pct(t.get('open_rate'))} "
            f"delivered {_pct(t.get('delivered_rate'))} bounce {_pct(t.get('bounce_rate'))} "
            f"| weakest: {record.get('weakest_text', '—')}")
