"""Report + journal — the categorized owner-facing read of each batch cycle.

Every batch cycle appends two entries to reports/journal.md:

  EXECUTE  — right after the sends: batch, intervention, sends, providers,
             a random example email, guardrails, campaign state, leads.
  EVALUATE — when the evidence window closes: metrics & variables,
             hypothesis-vs-goal analysis, verdict, goal check.

`print_current(ctx)` renders the same categorized picture on demand
(`python3 -m Outreach status`).

The engine stays domain-free: this module renders the generic sections
(batch, sends, analysis) and pulls the domain sections (campaign totals,
providers, example email, leads, guardrails) from the workflow bundle's
optional `report(ctx, batch, outcome)` hook.
"""

from datetime import datetime, timezone


def build(ctx, batch: dict, outcome: dict | None = None) -> dict:
    """Assemble the categorized report data for one batch cycle.

    outcome is either the execute result ({sent, failed, deduped, ...}) or
    the measure result ({metrics, verdict, ...})."""
    payload = batch.get("batch") or {}
    intervention = batch.get("intervention") or {}
    if outcome:
        metrics = outcome.get("metrics") if "metrics" in outcome else outcome
        verdict = outcome.get("verdict") or {}
    else:
        metrics = batch.get("metrics") or {}
        verdict = batch.get("verdict") or {}
    goal = ctx.control.goal() or {}
    metric = goal.get("metric") or "reply_rate"

    data = {
        "batch": {
            "id": batch.get("id"),
            "workflow": ctx.workflow.name,
            "phase": batch.get("phase") or ctx.store.phase(),
            "hypothesis": payload.get("hypothesis") or intervention.get("prediction") or "—",
            "variable": intervention.get("variable") or "—",
            "detail": intervention.get("detail") or "—",
            "prediction": intervention.get("prediction") or "—",
        },
        "sends": {
            "sent": metrics.get("sent", 0),
            "failed": metrics.get("failed", 0),
            "deduped": metrics.get("deduped", 0),
            "emails": len(payload.get("emails") or []),
        },
        "analysis": {
            "goal_name": goal.get("name") or "—",
            "target": goal.get("target"),
            "metric": metric,
            "verdict": verdict.get("verdict") if verdict else None,
            "verdict_reason": verdict.get("reason") if verdict else None,
        },
    }
    hook = getattr(ctx.workflow, "report", None)
    if hook:
        try:
            data["domain"] = hook(ctx, batch, outcome) or {}
        except Exception as e:  # a report must never break the loop
            data["domain"] = {"error": f"{type(e).__name__}: {e}"}
    return data


def _pct(value, digits=1) -> str:
    if not isinstance(value, (int, float)):
        return str(value)
    return f"{value * 100:.{digits}f}%"


def _fmt_rates(metrics: dict) -> str:
    if not metrics:
        return "—"
    parts = []
    for k in ("delivered_rate", "open_rate", "click_rate", "reply_rate",
              "bounce_rate", "spam_rate"):
        if k in metrics:
            parts.append(f"{k.replace('_rate', '')} {_pct(metrics[k])}")
    return " · ".join(parts) if parts else "—"


def _render_domain(domain: dict) -> list:
    """Render the workflow-supplied domain sections in a fixed order."""
    lines = []

    campaign = domain.get("campaign") or {}
    if campaign:
        lines.append("### Campaign")
        lines.append(f"- all-time sent: {campaign.get('total_sent', 0)}")
        today = (f"- today: {campaign.get('sent_today', 0)}/{campaign.get('cap', 0)}"
                 f" · remaining {campaign.get('remaining', 0)}")
        if campaign.get("cap_phase"):
            today += f" · {campaign['cap_phase']}"
        lines.append(today)

    providers = domain.get("providers") or {}
    if providers:
        lines.append("### Providers")
        counts = providers.get("batch") or {}
        if counts:
            lines.append("- this batch: " + " · ".join(
                f"{name} {n}" for name, n in sorted(counts.items())))
        for h in providers.get("health") or []:
            lines.append(f"- health: {h}")

    example = domain.get("example") or {}
    if example:
        lines.append("### Example email (quality check)")
        to = example.get("contact_name") or example.get("email") or "?"
        company = example.get("company") or ""
        lines.append(f"- to: {to}" + (f" — {company}" if company else "")
                     + f" ({example.get('lead_id', '?')})")
        lines.append(f"- subject: {example.get('subject', '—')}")
        body = (example.get("body") or "—").strip()
        lines.append("- body: " + body[:400])

    guardrails = domain.get("guardrails") or []
    if guardrails:
        lines.append("### Guardrails (48h window)")
        for g in guardrails:
            state = "ok" if g.get("ok") else "BREACH"
            lines.append(f"- {g.get('name', '?')}: {_pct(g.get('current', 0))} "
                         f"<= {_pct(g.get('max', 0))} {state}")

    window = domain.get("window") or {}
    if window:
        lines.append("### 48h window")
        lines.append(f"- {_fmt_rates(window)}")

    leads = domain.get("leads") or {}
    if leads:
        lines.append("### Leads")
        lines.append(f"- total in master: {leads.get('total', 0)}")
        q = leads.get("queue", 0)
        q_line = f"- next queue: {q}"
        if q and leads.get("queue_english") is not None:
            q_line += f" (en {leads['queue_english']} · fa {leads['queue_persian']})"
        lines.append(q_line)
        if leads.get("needed_to_gather") is not None:
            lines.append(f"- needed to gather for next batch: {leads['needed_to_gather']}")

    error = domain.get("error")
    if error:
        lines.append(f"### Domain data")
        lines.append(f"- unavailable: {error}")

    return lines


def to_markdown(data: dict, title: str) -> str:
    b = data.get("batch") or {}
    sends = data.get("sends") or {}
    analysis = data.get("analysis") or {}
    lines = [
        f"## {b.get('id', '?')} · {title} · "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "### Batch",
        f"- workflow: {b.get('workflow', '?')} · phase: {b.get('phase', '?')}",
        f"- hypothesis: {b.get('hypothesis', '—')}",
        f"- intervention: {b.get('variable', '—')} — {b.get('detail', '—')}",
        "",
        "### Sends",
        f"- this batch: sent {sends.get('sent', 0)} · failed {sends.get('failed', 0)} · "
        f"deduped {sends.get('deduped', 0)} ({sends.get('emails', 0)} composed)",
        "",
        "### Hypothesis vs goal",
        f"- goal: {analysis.get('goal_name', '—')}"
        + (f" → {_pct(analysis.get('target'))}" if analysis.get("target") is not None else ""),
        f"- prediction: {b.get('prediction', '—')}",
        f"- measured (window): {_pct(data.get('domain', {}).get('window', {}).get(analysis.get('metric', 'reply_rate')))}",
    ]
    verdict = analysis.get("verdict")
    if verdict:
        reason = analysis.get("verdict_reason") or ""
        lines.append(f"- verdict: {verdict}" + (f" — {reason}" if reason else ""))
    lines.append("")

    domain = data.get("domain") or {}
    if domain:
        lines += _render_domain(domain)
        lines.append("")
    return "\n".join(lines)


def write_entry(ctx, batch: dict, title: str, outcome: dict | None = None) -> str:
    """Append one categorized entry to reports/journal.md. Returns the path."""
    data = build(ctx, batch, outcome)
    markdown = to_markdown(data, title)
    journal = Path(ctx.reports_dir) / "journal.md"
    body = markdown.rstrip() + "\n\n---\n\n"
    if journal.exists():
        with open(journal, "a") as f:
            f.write(body)
    else:
        header = ("# SpielOS Outbound — cycle journal\n\n"
                  "One entry per batch cycle: EXECUTE (after sends) and "
                  "EVALUATE (when the evidence window closes).\n\n---\n\n")
        with open(journal, "w") as f:
            f.write(header + body)
    ctx.artifacts.log(f"report: journal entry {title} for {batch.get('id')} → {journal}")
    return str(journal)


def print_current(ctx) -> str:
    """Render the current status picture on demand (`status` command)."""
    batch = ctx.store.latest_batch()
    outcome = None
    if batch and batch.get("metrics"):
        outcome = {"metrics": batch.get("metrics") or {},
                   "verdict": batch.get("verdict") or {}}
    if batch is None:
        batch = {"id": "—", "batch": {}, "intervention": {}, "metrics": {},
                 "verdict": {}}
    data = build(ctx, batch, outcome)
    title = "STATUS"
    if outcome:
        phase = batch.get("phase") or ""
        title = f"STATUS (after {phase})" if phase else "STATUS"
    return to_markdown(data, title)


from pathlib import Path  # noqa: E402
