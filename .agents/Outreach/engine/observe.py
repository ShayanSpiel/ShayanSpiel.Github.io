"""OBSERVE — the loop's read of what is true now.

Pure, filtered, timestamped. Consumed by DECIDE (and re-run fresh by
ACT/GATE). Never mutates state beyond persisting its own artifact.
"""

from .artifacts import Artifacts


def run(ctx) -> dict:
    snapshot = ctx.workflow.observe(ctx, quick=False)
    ctx.store.set_last_snapshot_path(ctx.artifacts.save_snapshot(snapshot))
    ctx.artifacts.log(f"observe: {_headline(snapshot)}")
    return snapshot


def _headline(snapshot: dict) -> str:
    gate = snapshot.get("gate", {})
    cap = snapshot.get("cap", {})
    return (
        f"sent {snapshot.get('totals', {}).get('sent', 0)} total · "
        f"today {cap.get('sent_today', 0)}/{cap.get('cap', 0)} · "
        f"queue {snapshot.get('queue', {}).get('size', 0)} · "
        f"gate ok={bool(gate.get('ok'))} · "
        f"reply {snapshot.get('window_totals', {}).get('reply_rate', 0)*100:.1f}%"
    )
