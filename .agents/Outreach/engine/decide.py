"""DECIDE — one intervention from the snapshot + memory.

Chooses exactly one next action. Its output is an artifact the human can
review before it ever reaches ACT; the batch id is minted here so the
intervention, the preview, and the batch row share one identity.
"""

from datetime import datetime, timezone


def run(ctx, snapshot: dict) -> dict | None:
    intervention = ctx.workflow.decide(ctx, snapshot)
    if intervention is None:
        return None
    if intervention.get("action") in ("hold", "stop"):
        return intervention
    if not intervention.get("batch_id"):
        intervention["batch_id"] = _next_batch_id(ctx)
    ctx.store.set_last_intervention_path(ctx.artifacts.save_intervention(intervention))
    ctx.artifacts.log(
        f"decide: action={intervention.get('action')} variable={intervention.get('variable')} "
        f"detail={str(intervention.get('detail'))[:120]}")
    return intervention


def _next_batch_id(ctx) -> str:
    cycle = ctx.store.bump_cycle()
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{ctx.workflow.name.upper()}-{day}-b{cycle:02d}"
