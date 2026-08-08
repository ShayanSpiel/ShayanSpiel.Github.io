#!/usr/bin/env python3
"""
Harness — reflect: the evidence engine (DIAGNOSE + SELECT LEVER + HYPOTHESIS).

Pure functions. Input: current totals + state memory. Output: the weakest
link, the chosen lever (1, max 2), and the hypothesis. No side effects —
core.py applies the decision.

Order of diagnosis (never skip):
  1. Data problems (unknown/unresolved/denied) — rates can't be trusted.
  2. Guardrails (bounce, spam, delivery) — halt before any lever.
  3. Primary goal (reply rate) — distance to target.
  4. Diagnostic KPIs (open, click) — which stage limits the funnel.
  5. Cohort slices — is the weakness global or a subset (source, location,
     personal-vs-company)?
"""

MIN_TRUSTED_SAMPLE = 30
MIN_COHORT_SAMPLE = 10


def goals_status(totals: dict, meta: dict) -> list:
    """Every goal with current value, target, and relative gap
    gap = (current - target) / target  (negative = below target)."""
    out = []
    g = meta["goal"]
    out.append({**g, "current": totals[g["metric"]],
                "gap": (totals[g["metric"]] - g["target"]) / g["target"]})
    for k in meta["supporting_kpis"]:
        out.append({**k, "current": totals[k["metric"]],
                    "gap": (totals[k["metric"]] - k["target"]) / k["target"]})
    for gr in meta["guardrails"]:
        cur = totals[gr["metric"]]
        out.append({**gr, "current": cur, "gap": (gr["max"] - cur) / gr["max"]})
    return out


def data_problems(totals: dict) -> list:
    probs = []
    if totals.get("unknown"):
        probs.append(f"{totals['unknown']} emails unverified — metrics not trustworthy")
    if totals.get("denied"):
        probs.append(f"{totals['denied']} read-denied — API key lacks read access")
    if totals.get("unresolved"):
        probs.append(f"{totals['unresolved']} unresolved ids — no queryable provider id")
    return probs


def guardrail_breaches(totals: dict, meta: dict) -> list:
    breaches = []
    for gr in meta["guardrails"]:
        cur = totals[gr["metric"]]
        if cur > gr["max"]:
            breaches.append({"name": gr["name"], "metric": gr["metric"],
                             "current": cur, "max": gr["max"]})
    # Delivered rate is only judgeable when the statuses are verified:
    # unknown/denied/unresolved emails are NOT counted as delivered, so a
    # half-collected window would look like a breach. Treat it as
    # unjudgeable instead — the data-problem path handles it.
    bounce_rate = totals.get("bounce_rate", 0.0)
    if bounce_rate > meta["guardrails"][0]["max"]:
        return breaches  # low delivery is explained by bounces — the bounce
                         # breach already fired; never double-report
    unverified = totals.get("unknown", 0) + totals.get("denied", 0) + totals.get("unresolved", 0)
    if unverified < max(5, totals.get("sent", 0) * 0.1) and totals["delivered_rate"] < 0.99:
        breaches.append({"name": "delivered rate", "metric": "delivered_rate",
                         "current": totals["delivered_rate"], "max": 0.99})
    return breaches


def weakest_link(totals: dict, meta: dict, sent: int,
                 skip_unverified: bool = False) -> dict | None:
    """Return the single most limiting factor as a dict with .stage/.variable
    hint, or None when nothing is actionable (sample too small / all met)."""
    if sent < MIN_TRUSTED_SAMPLE:
        return {"stage": "sample", "detail": f"only {sent} sent; need {MIN_TRUSTED_SAMPLE}",
                "variable": None, "actionable": False}

    for gr in meta["guardrails"]:
        if totals[gr["metric"]] > gr["max"]:
            # the bounce guardrail's fix (skip_unverified) is already applied —
            # do not re-select the same lever; move to the next weakness
            if gr["name"] == "bounce rate" and skip_unverified:
                break
            return {"stage": "guardrail", "detail": gr["name"],
                    "variable": "cohort_unverified", "actionable": True}
    bounce_breaching = any(totals[gr["metric"]] > gr["max"]
                           for gr in meta["guardrails"] if gr["metric"] == "bounce_rate")
    if not bounce_breaching and totals["delivered_rate"] < 0.99:
        return {"stage": "guardrail", "detail": "delivered rate",
                "variable": "providers", "actionable": True}

    goal = meta["goal"]
    cur = totals[goal["metric"]]
    if cur >= goal["target"]:
        return {"stage": "goal-met", "detail": f"reply rate {cur*100:.1f}% >= {goal['target']*100:.0f}%",
                "variable": None, "actionable": False}

    open_r = totals["open_rate"]
    if open_r < 0.80:
        return {"stage": "open", "detail": f"open rate {open_r*100:.1f}% < 80%",
                "variable": "subject", "actionable": True}
    return {"stage": "reply", "detail": f"opens fine but reply {cur*100:.1f}% < {goal['target']*100:.0f}%",
            "variable": "cta", "actionable": True}


def cohort_slices(log_entries: list) -> dict:
    """Slice recent sends by the features we capture (source, country,
    email type) and return per-slice open/reply counts so the diagnosis can
    name a cohort instead of a global variable."""
    from collections import defaultdict
    slices = defaultdict(lambda: {"sent": 0, "opened": 0, "replied": 0})
    for e in log_entries:
        for feat in ("source", "country", "email_type", "verified"):
            key = f"{feat}={e.get(feat) or '?'}"
            s = slices[key]
            s["sent"] += 1
            if e.get("opened"):
                s["opened"] += 1
            if e.get("replied"):
                s["replied"] += 1
    return {k: {**v, "open_rate": v["opened"] / v["sent"] if v["sent"] else 0}
            for k, v in slices.items() if v["sent"] >= MIN_COHORT_SAMPLE}
