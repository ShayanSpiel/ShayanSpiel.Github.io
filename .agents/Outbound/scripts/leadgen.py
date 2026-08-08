#!/usr/bin/env python3
"""
SpielOS Outbound — leadgen.py: the lead generation engine.

When the queue runs dry, this machine does three things in order:
  1. L2-verify the pool (verify.py probe-queue) — upgrades Plausible → Verified
  2. Auto-ingest anything dropped in leads/staging (the daemon does this)
  3. Tell the owner/AI what to research — ICP-grounded discovery queries

The research is executed by the assistant (websearch + website visits per
session — the "Company website" source), and the CSVs it produces are
dropped into leads/staging. The daemon picks them up within 30 min.
Never scrapes: it consumes what it is given, against a fixed ICP.

Usage:
    python3 leadgen.py audit                 # pool health by tier/segment/country
    python3 leadgen.py research [segment]    # ICP discovery queries (paste into
                                             # websearch; compile results to CSV)
    python3 leadgen.py ingest-all            # digest every file in staging now
"""

import os
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import outbound  # noqa: E402

MIN_VERIFIED_POOL = 30      # below this, the engine warns "research needed"
MIN_PLAUSIBLE_POOL = 40     # below this, the pool is genuinely thin

# ICP anchor rules — mirror leads.py; canonical doc: ../../spielos-icp.md
SEGMENT_TARGETS = ("recruit", "staff", "talent", "headhunt", "agency", "digital",
                   "marketing", "saas", "property", "real estate", "ecommerce",
                   "logistics", "legal", "construction", "estate", "consult",
                   "coach", "educ", "train", "travel", "marketplace",
                   "online service")
TARGET_COUNTRIES = ("united kingdom", "us", "united states", "canada", "australia",
                    "germany", "france", "netherlands", "sweden", "norway", "denmark",
                    "ireland", "uae", "dubai", "saudi", "qatar", "finland")
EXCLUDE = ("ai", "software", "development", "consult", "studio", "dev",
           "automation", "chatbot", "llm", "gpt")


def audit() -> dict:
    contacts = outbound.read_contacts()
    log = outbound.load_sent_log()
    sent = {s["lead_id"] for s in log.get("sent", [])}
    tiers = Counter()
    seg = Counter()
    country = Counter()
    for c in contacts:
        s = (c.get("email_status") or "").strip().lower()
        if s == "verified":
            tiers["Verified"] += 1
        elif "bounced" in s or "invalid" in s:
            tiers["Invalid"] += 1
        elif "catch-all" in s:
            tiers["Catch-all"] += 1
        else:
            tiers["Plausible"] += 1
        if c["lead_id"] not in sent:
            seg[(c.get("segment") or "?").strip()] += 1
            country[(c.get("country") or "?").strip()] += 1
    return {
        "total": len(contacts),
        "tiers": dict(tiers),
        "unsent_segments": seg.most_common(8),
        "unsent_countries": country.most_common(8),
        "verified_pool": tiers["Verified"],
        "plausible_pool": tiers["Plausible"],
    }


def research(segment: str = "") -> list:
    """ICP-grounded websearch queries. Run these in a search engine; for each
    hit, visit the site, find the founder/owner/CEO email, and add a row to a
    CSV (columns: email, first name, last name, company, title, country,
    segment, employees, website, personalization_hook)."""
    queries = []
    segs = [segment] if segment else SEGMENT_TARGETS
    for s in segs:
        for c in ("United Kingdom", "United Arab Emirates", "Canada",
                  "Australia", "United States"):
            queries.append(
                f"site:linkedin.com/company \"{s}\" \"{c}\" founder CEO owner -ai -software"
            )
    queries.append(
        "recruitment agencies 5-50 employees UAE London Canada Australia "
        "\"contact\" \"@\" -ai -software"
    )
    queries.append(
        "digital marketing agency small team managing director email contact -ai -software"
    )
    queries.append(
        "property management company 10-50 staff CEO email contact UK UAE -ai"
    )
    return queries


def ingest_all() -> int:
    """Digest every CSV/xlsx in leads/staging right now (daemon does this on
    its own, but the command is useful for a manual push)."""
    staging = os.path.join(os.path.dirname(HERE), "leads", "staging")
    if not os.path.isdir(staging):
        print("ingest-all: no staging dir")
        return 0
    files = sorted(f for f in os.listdir(staging)
                   if f.lower().endswith((".csv", ".xlsx", ".xlsm")))
    n = 0
    for fn in files:
        src = os.path.join(staging, fn)
        r = subprocess.run([sys.executable, os.path.join(HERE, "leads.py"),
                            "ingest", src], cwd=HERE, capture_output=True,
                           text=True, timeout=300)
        print(f"{fn}: {(r.stdout + r.stderr).strip()[-200:]}")
        if r.returncode == 0:
            done = os.path.join(staging, "done")
            os.makedirs(done, exist_ok=True)
            os.replace(src, os.path.join(done, fn))
            n += 1
    return n


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        sys.exit(1)
    cmd = argv[0]
    if cmd == "audit":
        a = audit()
        print(f"total: {a['total']} | tiers: {a['tiers']}")
        print(f"verified pool: {a['verified_pool']} (min {MIN_VERIFIED_POOL})"
              f" | plausible pool: {a['plausible_pool']} (min {MIN_PLAUSIBLE_POOL})")
        print("unsent segments:", a["unsent_segments"])
        print("unsent countries:", a["unsent_countries"])
        if a["verified_pool"] < MIN_VERIFIED_POOL:
            print("WARNING: verified pool low — run `leadgen.py research` and "
                  "drop the compiled CSVs into leads/staging")
    elif cmd == "research":
        seg = argv[1] if len(argv) > 1 else ""
        for q in research(seg):
            print(q)
    elif cmd == "ingest-all":
        n = ingest_all()
        print(f"ingest-all: {n} files digested")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
