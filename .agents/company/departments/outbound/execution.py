"""ACT — the composite step: PREPARE -> VALIDATE -> GATE -> REVIEW -> EXECUTE.

Each sub-step is its own artifact boundary. VALIDATE and GATE are the two
machine checkpoints; REVIEW is handled by the company runtime.

Row shape (persisted in the store): {id, workflow, phase, batch (payload),
intervention, preview_path, artifact_path, report_path, created_at,
updated_at}. The workflow bundle sees only the payload; the engine owns
the row.
"""

from datetime import datetime, timezone

from .models import Phase


def prepare(ctx, intervention: dict) -> dict:
    payload = ctx.workflow.prepare(ctx, intervention)
    payload.setdefault("id", intervention.get("batch_id", "unset"))
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": payload["id"],
        "workflow": ctx.workflow.name,
        "phase": Phase.PREPARE.value,
        "batch": payload,
        "intervention": intervention,
        "preview_path": ctx.artifacts.write_preview(payload, ctx.workflow.name),
        "artifact_path": ctx.artifacts.save_batch(payload),
        "created_at": now,
        "updated_at": now,
    }
    ctx.store.upsert_batch(row)
    ctx.store.set_current_batch(row["id"])
    ctx.artifacts.log(
        f"prepare: {row['id']} → {len(payload.get('emails', []))} emails, "
        f"{len(payload.get('skipped', []))} skipped")
    return row


def validate(ctx, row: dict) -> list:
    payload = row["batch"]
    issues = ctx.workflow.validate(ctx, payload)
    if issues:
        bad = {i["lead_id"] for i in issues}
        payload["emails"] = [e for e in payload.get("emails", [])
                             if e.get("lead_id") not in bad]
        payload["skipped"] = (payload.get("skipped") or []) + [
            {"lead_id": i["lead_id"], "reason": f"validation {i['code']}: {i['message']}"}
            for i in issues]
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        row["artifact_path"] = ctx.artifacts.save_batch(payload)
        ctx.store.upsert_batch(row)
    ctx.artifacts.log(f"validate: {len(issues)} issue(s) → {len(payload.get('emails', []))} emails kept")
    return issues


def gate(ctx) -> dict:
    fresh = ctx.workflow.observe(ctx, quick=True)
    result = ctx.policy.check(ctx, fresh)
    result["guardrails"] = [g.get("name") for g in
                            (fresh.get("meta") or {}).get("guardrails", [])]
    ctx.artifacts.log(
        f"gate: ok={result.get('ok')} breaches={[b.get('name') for b in result.get('breaches', [])]} "
        f"problems={len(result.get('problems', []))}")
    return result


def execute(ctx, row: dict, dry: bool = False) -> dict:
    result = ctx.workflow.execute(ctx, row["batch"], dry=dry)
    ctx.store.update_batch_metrics(row["id"], result)
    ctx.artifacts.log(
        f"execute{' (dry)' if dry else ''}: {row['id']} → sent {result.get('sent', 0)}, "
        f"failed {result.get('failed', 0)}, deduped {result.get('deduped', 0)} · {result.get('note', '')}")
    return result
