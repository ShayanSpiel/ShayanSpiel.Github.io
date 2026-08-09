#!/usr/bin/env python3
"""
Harness — measure: verdicts (LEARN). Sample-aware comparison of the current
batch vs the previous batch and the rolling baseline. Never rejects on a
small sample; "inconclusive" is the honest default.

Verdicts:
  keep         — the changed variable moved its target metric the right way
  reject       — the changed variable moved its target metric the wrong way
  inconclusive — sample too small, or the variable's target metric didn't
                 move enough to be distinguishable from noise
"""

MIN_COMPARE_SAMPLE = 20
MIN_IMPROVEMENT = 0.02  # absolute rate change to call it a real movement


def verdict(prev: dict, cur: dict, target_metric: str) -> dict:
    """prev/cur are batch records with .metrics. Compare the batch that
    carried the experiment (cur) against the one before it (prev)."""
    if prev is None or prev.get("metrics") is None:
        return {"verdict": "inconclusive",
                "reason": "no previous batch to compare against (baseline)"}

    prev_metrics = prev["metrics"]
    cur_metrics = cur["metrics"]
    n_prev = prev_metrics.get("sent", 0)
    n_cur = cur_metrics.get("sent", 0)
    if n_prev < MIN_COMPARE_SAMPLE or n_cur < MIN_COMPARE_SAMPLE:
        return {"verdict": "inconclusive",
                "reason": (f"sample too small (prev {n_prev}, cur {n_cur}; "
                           f"need >= {MIN_COMPARE_SAMPLE} per batch)")}

    before = prev_metrics.get(target_metric, 0.0)
    after = cur_metrics.get(target_metric, 0.0)
    delta = after - before

    if delta >= MIN_IMPROVEMENT:
        return {"verdict": "keep", "reason": f"{target_metric} {before*100:.1f}% -> {after*100:.1f}%",
                "delta": delta}
    if delta <= -MIN_IMPROVEMENT:
        return {"verdict": "reject", "reason": f"{target_metric} {before*100:.1f}% -> {after*100:.1f}%",
                "delta": delta}
    return {"verdict": "inconclusive",
            "reason": f"{target_metric} {before*100:.1f}% -> {after*100:.1f}% (within noise)",
            "delta": delta}


def compare_batches(prev: dict, cur: dict) -> dict:
    """Side-by-side of all key metrics between two batches."""
    if prev is None or cur is None:
        return {}
    pm, cm = prev.get("metrics", {}) or {}, cur.get("metrics", {}) or {}
    keys = ["sent", "delivered_rate", "open_rate", "click_rate", "reply_rate",
            "bounce_rate", "spam_rate"]
    return {k: {"before": pm.get(k), "after": cm.get(k)}
            for k in keys if k in pm or k in cm}
