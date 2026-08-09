"""HOLD — the parked state.

The loop holds when a human decision or an external condition is required:
gate breach, empty queue, cap reached, batch rejected in review, or the
owner's GO before the next batch. Releasing a hold (approve --next) starts
a fresh batch cycle.
"""


def enter(ctx, reason: str, detail: str = "") -> None:
    full = f"{reason}" + (f" — {detail}" if detail else "")
    ctx.store.set_hold_reason(full)
    ctx.artifacts.log(f"hold: {full}")
