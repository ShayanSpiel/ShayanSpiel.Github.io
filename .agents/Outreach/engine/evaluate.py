"""EVALUATE — the loop's closing arc: wait for evidence, then MEASURE,
LEARN, GOAL CHECK, and write the report for the owner.

EVALUATE asks "what changed because of what we did, and was it good?" —
its three outputs are verdict (-> STATE knowledge), goal check (-> loop
state), and report (-> human).
"""

from datetime import datetime, timezone

from . import act


def evidence_due(ctx) -> datetime:
    ts = ctx.store.evidence_due()
    try:
        return datetime.fromisoformat(ts) if ts else datetime.now(timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def waiting(ctx, row: dict) -> bool:
    return datetime.now(timezone.utc) < evidence_due(ctx)


def run(ctx, row: dict) -> dict:
    outcome = ctx.workflow.measure(ctx, row["batch"])
    verdict = outcome.get("verdict") or {}
    ctx.store.update_batch_metrics(row["id"], outcome.get("metrics") or {}, verdict)
    if ctx.workflow.learn:
        ctx.workflow.learn(ctx, row.get("intervention") or {}, verdict)
    goal_check = ctx.workflow.goal_check(ctx, outcome.get("metrics") or {})
    report_path = ctx.artifacts.write_report(row["id"], _report_markdown(ctx, row, outcome, goal_check))
    ctx.store.update_batch_report(row["id"], report_path)
    ctx.artifacts.log(
        f"evaluate: {row['id']} → verdict={verdict.get('verdict')} "
        f"goal={goal_check.get('state')} · {goal_check.get('detail', '')}")
    return {"verdict": verdict, "goal_check": goal_check, "report_path": report_path}


def _report_markdown(ctx, row: dict, outcome: dict, goal_check: dict) -> str:
    verdict = outcome.get("verdict") or {}
    payload = row.get("batch") or {}
    emails = payload.get("emails", [])
    skipped = payload.get("skipped", [])
    lines = [
        f"# Report — {row.get('id', '?')}",
        "",
        f"workflow: {ctx.workflow.name} · written {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"**intervention**: {row.get('intervention', {}).get('detail', '—')}",
        f"prediction: {row.get('intervention', {}).get('prediction', '—')}",
        "",
        f"**verdict**: {verdict.get('verdict', '?')} — {verdict.get('reason', '')}",
        "",
        f"**goal check**: {goal_check.get('state', '?')} — {goal_check.get('detail', '')}",
        "",
    ]
    if ctx.workflow.report_lines:
        lines += ctx.workflow.report_lines(ctx, row["batch"], outcome)
    lines += [
        "",
        f"sent: {len(emails)}/{len(emails) + len(skipped)} · skipped: {len(skipped)} · "
        f"preview: {row.get('preview_path', '—')}",
        "",
        "Next: the owner reviews the verdict, then `approve --next` starts the next batch cycle.",
        "",
    ]
    return "\n".join(lines)
