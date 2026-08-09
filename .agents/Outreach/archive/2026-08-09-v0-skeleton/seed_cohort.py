#!/usr/bin/env python3
"""Seed the shared outreach store from the Outbound master + AI research.

Orchestrator action: after each cohort's research/content pass, run this to
sync leads into the channel-neutral store (ready state, research facts) and
register the email goal. The daemon remains the email executor; the store is
the orchestration record (append-only actions, goal status).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Outbound", "scripts"))

from Outreach.models import Action, Lead, LeadState, WorkflowGoal
from Outreach.store import OutreachStore
from Outreach.policy import check_lead

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "state", "outreach.sqlite")

EMAILS = [  # web-researched cohorts 2026-08-08 (published founder/CEO/MD emails)
    # cohort 1
    "nick@lodestonerecruitment.co.uk", "grant@peridotpartners.co.uk",
    "stella@cubedtalent.co.uk", "nickmc@star-recruit.co.uk", "dani@dwrecruitment.co.uk",
    "matthew@mfkrecruitment.co.uk", "ben@thompsonandterry.co.uk",
    "hello@pointrecruitment.co.uk", "uae@devsdata.com", "info@mbrrecruitment.com",
    "phumphrey@talentsphere.ca", "tonyl@harbingernetwork.ca", "doug@blueshock.ca",
    "trevorw@blueshock.ca", "perry@mandrake.ca", "katie@foundpeople.ca",
    "wbongard@zsa.ca", "csweeney@zsa.ca", "mgoldstein@masongroup.ca",
    "chantellejames@jivaro.com.au", "gregm@axr.com.au", "moreinfo@s2m.com.au",
    "miezzi@mitalent.com.au", "nikki@beaumontpeople.com.au",
    "sophie@sestrapeople.com.au",
    # cohort 2
    "liz@logjec.co.uk", "amanda@khr.co.uk", "mike@khr.co.uk",
    "craig@plethorarg.co.uk", "luke@plethorarg.co.uk", "jay.plant@wentworthjames.co.uk",
    "jweeden@vr-group.co.uk", "richard.cade@orchardrecruitment.co.uk",
    "stephensimpson@simwestengineering.co.uk", "cblunden@rgb.co.uk",
    "rhys@sigmarecruitment.co.uk", "m.trillot@totemtalent.ca",
    "jamesp@coxpurtell.com.au", "maryann@mckrg.com.au", "claire@keeganadams.com.au",
    "ihackett@deanling.com.au", "ben.wheeler@people2people.com.au",
    "brent@resourcefulrecruitment.com.au", "nick@osbornerichardson.com.au",
    "peter@fluidrecruitment.com", "shannon@frogrecruitment.co.nz",
    "ian.taylor@sheffield.co.nz", "guy@potentia.co.nz", "gareth@scitex.co.nz",
    "carl.church@nicherecruitment.co.nz", "warwick@yourpeople.co.nz",
    "mkhan@mahadmanpower.ae",
]


def main() -> int:
    import outbound
    from pipeline import compose_researched, segment_variant

    store = OutreachStore(DB)
    by_email = {str(c.get("email") or "").lower(): c for c in outbound.read_contacts()}
    leads = []
    for email in EMAILS:
        c = by_email.get(email)
        if not c:
            print(f"skip {email}: not in master")
            continue
        pain = (c.get("pain_hypothesis") or "").strip().rstrip(".")
        hook = (c.get("personalization_hook") or "").strip()
        rendered = compose_researched(c, segment_variant(c.get("segment") or ""), seq=0)
        pain_body = pain
        if pain.startswith("The company likely has"):
            pain_body = pain[len("The company likely has"):].strip().capitalize()
        leads.append(Lead(
            lead_id=str(c.get("lead_id") or email),
            name=(c.get("contact_name") or email).strip(),
            company=(c.get("company") or "").strip(),
            role=(c.get("title") or "").strip(),
            location=(c.get("country") or "").strip(),
            channels=["email"],
            company_url=(c.get("website") or "").strip(),
            state=LeadState.READY,
            icp_score=92,  # published founder email + named role + niche research
            research_fact=pain or hook[:200],
            operational_consequence=(
                f"At {c.get('company') or ''}, {pain_body} "
                f"= hours of manual work each week and slower responses to clients."
            ),
            message=(rendered["body_text"] if rendered else "")[:4000],
            source_urls=[(c.get("website") or "")],
            metadata={"segment": c.get("segment") or "", "email": email,
                      "source": "webresearch-2026-08-08"},
        ))
    added = store.upsert_leads(leads)
    goal = WorkflowGoal(
        workflow_id="email-warmup-d2-200",
        channel="email",
        action="send_email",
        target=200,
        min_icp_score=75,
        queue_target=100,
    )
    store.add_goal(goal)
    n = len(store.ready_queue("email", 500, 75))
    blocked = [l.lead_id for l in leads if not check_lead(l, 75).allowed]
    print(f"upserted {added} leads | ready email queue: {n} | policy-blocked: {blocked or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
