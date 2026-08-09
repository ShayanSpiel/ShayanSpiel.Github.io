#!/usr/bin/env python3
"""Build cohort-3 discovery CSV (2026-08-09): recruitment/staffing firms with
published founder/CEO/MD emails, researched via web sessions. Same column
format as cohort-2/webresearch files. Emails are taken ONLY from published
sources (team pages / bios) — nothing guessed."""
import csv

HEADERS = [
    "lead_id", "send_recommendation", "outreach_tier", "company_contact_rank",
    "contactability", "market", "company", "company_domain", "contact_name",
    "title", "email", "email_status", "person_linkedin", "website", "segment",
    "country", "employees", "annual_revenue", "technologies",
    "need_buying_signals", "icp_confidence", "qualification_rationale",
    "pain_hypothesis", "recommended_pilot", "personalization_hook",
    "suggested_cta", "language", "source",
]

A = "Ready to personalized"
S = "Publicly listed; not deliverability-verified"

L = [
    # ── UK ─────────────────────────────────────────────────────────────
    dict(company="Ashdown Group", domain="ashdowngroup.com", name="John Lynes",
         title="Founder & Managing Director", email="jlynes@ashdowngroup.com",
         website="https://www.ashdowngroup.com", segment="Recruitment", country="United Kingdom",
         hook="Reference John Lynes founding Ashdown Group in 1999 and one observable: he runs a 25-year specialist recruitment consultancy across IT, HR, marketing and finance, still personally shaping the strategic direction.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    dict(company="MFK Recruitment", domain="mfkrecruitment.co.uk", name="Matthew Mills",
         title="Founder", email="matthew@mfkrecruitment.co.uk",
         website="https://www.mfkrecruitment.co.uk", segment="Recruitment", country="United Kingdom",
         hook="Reference Matthew Mills launching MFK in 2019 and one observable: he started it after spotting a gap in the market — recruitment too focused on targets and not enough on people.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    dict(company="Zenith People", domain="zenithpeople.com", name="Angela Anderson",
         title="Owner & Managing Director", email="AngelaAnderson@zenithpeople.com",
         website="https://zenithpeople.com", segment="Recruitment", country="United Kingdom",
         hook="Reference Angela Anderson as owner and MD of Zenith People and one observable: she oversees strategic direction personally and is known for building a positive team culture within the business.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    dict(company="Thompson & Terry Recruitment", domain="thompsonandterry.co.uk", name="Ben",
         title="Managing Director", email="ben@thompsonandterry.co.uk",
         website="https://thompsonandterry.co.uk", segment="Recruitment", country="United Kingdom",
         hook="Reference Ben launching Thompson & Terry in 2014 and one observable: he founded it on the rule of only submitting a candidate he'd personally employ himself.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    dict(company="ARV Solutions", domain="arvsolutions.co.uk", name="Jim Roach",
         title="Founder & Managing Director", email="Jim.Roach@arvsolutions.co.uk",
         website="https://arvsolutions.co.uk", segment="Construction recruitment", country="United Kingdom",
         hook="Reference Jim Roach founding ARV Solutions in 2003 and one observable: he built it around a service level 'more often seen in search and selection' at sensible fee levels.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    dict(company="Farrer Barnes", domain="farrer-barnes.com", name="Tom Farrer-Newey",
         title="Managing Director", email="tom.fn@farrer-barnes.com",
         website="https://www.farrer-barnes.com", segment="Finance recruitment", country="United Kingdom",
         hook="Reference Tom Farrer-Newey as MD of Farrer Barnes and one observable: he focuses on senior accountancy and executive finance placements, built around consultative, discreet searches.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    dict(company="HW Group", domain="hwfinance.co.uk", name="Rafi Davies",
         title="Managing Director", email="rafid@hwfinance.co.uk",
         website="https://hwgroup.co", segment="Finance recruitment", country="United Kingdom",
         hook="Reference Rafi Davies leading HW Finance and one observable: he has spent 14 years in a national finance recruitment specialist, leading senior and executive finance appointments across Yorkshire.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    dict(company="Network IT Recruitment", domain="networkitr.co.uk", name="Richard Chorley",
         title="Managing Director & Owner", email="richard.chorley@networkitr.co.uk",
         website="https://www.networkitr.co.uk", segment="IT recruitment", country="United Kingdom",
         hook="Reference Richard Chorley as owner and MD of Network IT Recruitment since 2008 and one observable: with almost 30 years in IT recruitment he is still the firm's leading permanent consultant.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    dict(company="Greystone", domain="greystone-engineering.com", name="Simon Wilson",
         title="Founder & Director", email="simonwilson@greystone-engineering.com",
         website="https://www.greystone-engineering.com", segment="Engineering recruitment", country="United Kingdom",
         hook="Reference Simon Wilson founding Greystone and one observable: he left a global recruitment group to build a consultancy that manages the careers of candidates for life, not just placements.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    dict(company="Sigma Recruitment", domain="sigmarecruitment.co.uk", name="Rhys Williams",
         title="Founder & Managing Director", email="rhys@sigmarecruitment.co.uk",
         website="https://www.sigmarecruitment.co.uk", segment="Engineering recruitment", country="United Kingdom",
         hook="Reference Rhys Williams founding Sigma in 2005 and one observable: with 20 years in engineering and manufacturing recruitment, he still takes a hands-on approach to every assignment.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    dict(company="Engenious Recruitment", domain="engenious.co.uk", name="Philippa Dickinson",
         title="Founder & Managing Director", email="philippa@engenious.co.uk",
         website="https://engenious.co.uk", segment="Construction recruitment", country="United Kingdom",
         hook="Reference Philippa Dickinson founding Engenious and one observable: she built a boutique construction and civil engineering agency on a consultative approach that questions the job brief rather than just filling it.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    dict(company="Civilstruct Recruitment", domain="civilstruct.co.uk", name="Tom Sheehan",
         title="Managing Director", email="tom@civilstruct.co.uk",
         website="https://www.civilstruct.co.uk", segment="Construction recruitment", country="United Kingdom",
         hook="Reference Tom Sheehan launching Civilstruct and one observable: after leading civil engineering recruitment for a major group, he started a specialist agency focused on consultancies and contractors across the UK, Europe and USA.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    dict(company="BSV Recruitment", domain="bsvrecruitment.co.uk", name="Darren Warmington",
         title="Managing Director", email="darren.warmington@bsvrecruitment.co.uk",
         website="https://www.bsvrecruitment.co.uk", segment="Building services recruitment", country="United Kingdom",
         hook="Reference Darren Warmington as director of BSV Recruitment and one observable: he specialises in senior and management assignments across mechanical and electrical engineering within building services.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    # ── UAE ────────────────────────────────────────────────────────────
    # (Kinetic, The Finders Group, Connect Resources excluded: no published
    # founder email verifiable at build time — never guess.)
    dict(company="JIVARO Recruitment", domain="jivaro.com.au", name="Chantelle James",
         title="CEO & Founder", email="chantellejames@jivaro.com.au",
         website="https://www.jivaro.com.au", segment="Recruitment", country="Australia",
         hook="Reference Chantelle James founding JIVARO in 2006 and one observable: she runs a boutique agency matching C-suite and executive talent in fashion, consumer goods and travel, raising the standard of recruitment.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    dict(company="Alexander Appointments", domain="alexanderappointments.com.au", name="Danijela Negro",
         title="Co-Founder", email="danijela@alexanderappointments.com.au",
         website="https://www.alexanderappointments.com.au", segment="Recruitment", country="Australia",
         hook="Reference Danijela Negro as co-founder of Alexander Appointments and one observable: with over 20 years in recruitment and a background in accounting, she built a partnership-over-placement agency.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    dict(company="axr", domain="axr.com.au", name="Greg Madden",
         title="Founder & Managing Director", email="gregm@axr.com.au",
         website="https://www.axr.com.au", segment="Finance recruitment", country="Australia",
         hook="Reference Greg Madden establishing axr in 2003 and one observable: he and his co-founder built a specialist accounting and finance search firm and he still works closely with ASX 300 and private companies.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    dict(company="HIR Talent", domain="hirtalent.com.au", name="Belinda Mundy",
         title="Founder & Managing Director", email="belinda@hirtalent.com.au",
         website="https://www.hirtalent.com.au", segment="Property recruitment", country="Australia",
         hook="Reference Belinda Mundy founding HIR Talent and one observable: she built a purpose-driven agency partnering with Australia's most respected developers, builders and design consultancies.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    dict(company="Vinova", domain="vinova.com.au", name="Jill Ryder",
         title="Founder", email="jill@vinova.com.au",
         website="https://vinova.com.au", segment="Energy recruitment", country="Australia",
         hook="Reference Jill Ryder and one observable: after founding Precision Sourcing, she created Vinova to serve the growing need for a dedicated renewable-energy recruitment partner in Australia.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    # ── Canada ──────────────────────────────────────────────────────────
    dict(company="TalentSphere Staffing Solutions", domain="talentsphere.ca", name="Peter Humphrey",
         title="Founder & Managing Director", email="phumphrey@talentsphere.ca",
         website="https://talentsphere.ca", segment="Recruitment", country="Canada",
         hook="Reference Peter Humphrey founding TalentSphere and one observable: 12+ years building a staffing firm across Canada and the USA with a personal focus on IT and accounting & finance.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    dict(company="ZSA Legal Recruitment", domain="zsa.ca", name="Christopher Sweeney",
         title="CEO & Co-Founder", email="csweeney@zsa.ca",
         website="https://www.zsa.ca", segment="Legal recruitment", country="Canada",
         hook="Reference Christopher Sweeney bringing London-style recruiting to Canada with ZSA in 1997 and one observable: it remains Canada's largest and only national legal recruitment firm.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    dict(company="Harbinger Network", domain="harbingernetwork.ca", name="Tony Labora",
         title="Founder & President", email="tonyl@harbingernetwork.ca",
         website="https://harbingernetwork.ca", segment="Recruitment", country="Canada",
         hook="Reference Tony Labora founding Harbinger Network in 2010 and one observable: after helping build one of Canada's largest agencies, he started a recruitment partner with a construction and engineering focus.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    dict(company="Stoakley-Stewart Consultants", domain="stoakley.com", name="Trevor Stewart",
         title="President & Owner", email="tstewart@stoakley.com",
         website="https://www.stoakley.com", segment="Recruitment", country="Canada",
         hook="Reference Trevor Stewart purchasing Stoakley-Stewart in 2007 and one observable: he still personally runs his specialist freight forwarding and logistics recruitment desk as president.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    # ── United States ───────────────────────────────────────────────────
    dict(company="Debbie's Staffing Services", domain="debbiesstaffing.com", name="Debbie Peoples Little",
         title="CEO & Founder", email="dlittle@DebbiesStaffing.com",
         website="https://www.debbiesstaffing.com", segment="Staffing", country="United States",
         hook="Reference Debbie Peoples Little founding the firm in 1986 and one observable: nearly four decades of entrepreneurial leadership in search and temporary staffing built on customer service.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    dict(company="Staffing Boutique", domain="staffingboutique.org", name="Katie Warnock",
         title="Founder & President", email="katie@staffingboutique.org",
         website="https://staffingboutique.org", segment="Nonprofit recruitment", country="United States",
         hook="Reference Katie Warnock founding Staffing Boutique in 2011 and one observable: she turned a niche nonprofit staffing firm into a standout leader in nonprofit recruitment.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    dict(company="5 Star Recruiting", domain="5starrecruiting.com", name="Janet Rivera Jones",
         title="Founder & President", email="Janet@5StarRecruiting.com",
         website="https://www.5starrecruiting.com", segment="Manufacturing recruitment", country="United States",
         hook="Reference Janet Rivera Jones founding 5 Star and one observable: she built one of North America's leading recruiting firms for automotive and manufacturing, known for placing executives, mid-managers and engineers.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    # ── Ireland ─────────────────────────────────────────────────────────
    dict(company="Celtic Careers", domain="celticcareers.ie", name="Deirdre Moore",
         title="Founder & Managing Director", email="dmoore@celticcareers.com",
         website="https://www.celticcareers.ie", segment="Recruitment", country="Ireland",
         hook="Reference Deirdre Moore founding Celtic Careers in 1999 and one observable: she started the agency with no candidates, clients or equivalent experience, built on grit and a client-centric service.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    dict(company="Eos Talent", domain="eostalents.com", name="Emma Anglim",
         title="Founder & Managing Director", email="emma@eostalents.com",
         website="https://eostalents.com", segment="HR recruitment", country="Ireland",
         hook="Reference Emma Anglim founding Eos Talent and one observable: after 18 years in HR recruitment she built a specialist consultancy for HR leadership, executive search and talent advisory.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
    dict(company="Propeller Recruitment", domain="propellerrecruitment.ie", name="John Farrelly",
         title="Founder & Managing Director", email="jfarrelly@sigmar.ie",
         website="https://www.propellerrecruitment.ie", segment="Aviation recruitment", country="Ireland",
         hook="Reference John Farrelly founding Propeller and one observable: an award-winning aviation recruiter who manages start-up airline campaigns across Europe and LATAM, winner of Recruiter of the Year.",
         cta="Reply 'map' and I'll show you the shortlist loop."),
    # ── Netherlands ─────────────────────────────────────────────────────
    dict(company="DeRecruiter", domain="derecruiter.nl", name="Sita Keilman",
         title="Managing Partner & Co-Owner", email="sita@derecruiter.nl",
         website="https://www.derecruiter.nl", segment="IT recruitment", country="Netherlands",
         hook="Reference Sita Keilman as managing partner and co-owner of DeRecruiter and one observable: she combines running the team with hands-on IT recruitment at management level, built on long-term relationships.",
         cta="Reply 'map' and I'll walk you through the placement loop."),
]

def main() -> None:
    out = "experiments/auto/discovery-cohort3-2026-08-09.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS)
        w.writeheader()
        for lead in L:
            row = {h: "" for h in HEADERS}
            row.update({
                "send_recommendation": A,
                "outreach_tier": "A",
                "company_contact_rank": 1,
                "contactability": "Publicly listed",
                "market": "English",
                "company_domain": lead["domain"],
                "company": lead["company"],
                "contact_name": lead["name"],
                "title": lead["title"],
                "email": lead["email"],
                "email_status": S,
                "website": lead["website"],
                "segment": lead["segment"],
                "country": lead["country"],
                "need_buying_signals": "operational workload in placements, shortlisting, client delivery",
                "icp_confidence": 0.9,
                "qualification_rationale": "boutique recruitment firm, founder-led, published business email",
                "pain_hypothesis": "placement process is manual: shortlisting, screening, follow-ups eat the founder's day",
                "recommended_pilot": "AI employee handling the shortlist loop",
                # Hook format must match pipeline's regexes: "Reference
                # {name}'s role as {role} and one observable: ..." — any other
                # format silently falls through to the generic template.
                "personalization_hook": (
                    f"Reference {lead['name']}'s role as {lead['title']} and "
                    f"one observable: {lead['hook'].split('one observable:', 1)[1].strip().strip(chr(34))}"
                ),
                "suggested_cta": lead["cta"],
                "language": "English",
                "source": "webresearch-2026-08-09-cohort3",
            })
            w.writerow(row)
    print(f"wrote {len(L)} leads -> {out}")

if __name__ == "__main__":
    main()
