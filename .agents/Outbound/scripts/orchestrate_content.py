#!/usr/bin/env python3
"""Orchestrator content pass 2026-08-08: write per-lead research (hook,
pain_hypothesis, cta) for the web-researched recruitment cohort into the master."""
import openpyxl
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from outbound import COL_MAP

CONTENT = {
    "nick@lodestonerecruitment.co.uk": {
        "hook": "Reference Nick Brennan's role as Founder & Managing Director and one observable: he launched Lodestone in the middle of the pandemic and still personally leads skilled and trades placements.",
        "pain": "The company likely has a manual shortlist stage for skilled trades candidates, with the founder personally reviewing CVs before they reach clients.",
        "cta": "Reply 'map' and I'll walk you through the ten-minute version.",
    },
    "grant@peridotpartners.co.uk": {
        "hook": "Reference Grant Taylor's role as Founder & CEO and one observable: he built a values-led executive search firm of over 50 professionals from a 2009 start.",
        "pain": "The company likely has senior hire shortlists reviewed personally by the founder, with client reporting still drafted by hand after every search.",
        "cta": "Reply 'map' and I'll show you where the hours go.",
    },
    "stella@cubedtalent.co.uk": {
        "hook": "Reference Stella Redgrave-Nevison's role as Founder & Managing Director and one observable: she built Cubed's healthcare and international recruitment division from scratch.",
        "pain": "The company likely has a manual international placement pipeline, with each healthcare candidate tracked through spreadsheets before the offer stage.",
        "cta": "Reply 'map' and I'll show you the candidate loop.",
    },
    "nickmc@star-recruit.co.uk": {
        "hook": "Reference Nicholas McVeigh-Crabbe's role as Founder & Director and one observable: he heads STAR's property division with a 100 percent client retention record.",
        "pain": "The company likely has a manual property placement loop, with consultants chasing candidate updates and client feedback through email threads.",
        "cta": "Reply 'map' and I'll sketch the placement loop for you.",
    },
    "dani@dwrecruitment.co.uk": {
        "hook": "Reference Danielle Ward's role as Owner & Director and one observable: she built a fashion and textile agency with service targets instead of bums on seats.",
        "pain": "The company likely has a manual candidate sourcing stage for fashion and textile roles, with briefs reworked from scratch for every new client.",
        "cta": "Reply 'map' and I'll map the sourcing stage with you.",
    },
    "matthew@mfkrecruitment.co.uk": {
        "hook": "Reference Matthew Mills's role as Founder and one observable: he launched MFK in 2019 on a people-first, honest recruitment promise.",
        "pain": "The company likely has a manual shortlist stage, with every CV still personally vetted by the founder before client submission.",
        "cta": "Reply 'map' and I'll walk you through the shortlist loop.",
    },
    "ben@thompsonandterry.co.uk": {
        "hook": "Reference Ben's role as Managing Director and one observable: he built the agency on only submitting candidates he would personally employ.",
        "pain": "The company likely has a manual candidate screening stage, with the managing director personally reviewing every submission before it goes out.",
        "cta": "Reply 'map' and I'll show you the screening loop.",
    },
    "hello@pointrecruitment.co.uk": {
        "hook": "Reference Will Granger's role as Managing Director and one observable: he acquired the business in April 2025 and now steers its growth.",
        "pain": "The company likely has a manual client reporting loop, with placement updates compiled by hand for every hiring manager.",
        "cta": "Reply 'map' and I'll draft the reporting loop.",
    },
    "uae@devsdata.com": {
        "hook": "Reference Tom Potanski's role as Founding Partner and one observable: DevsData assembles full engineering teams for clients from its Dubai and Warsaw bases.",
        "pain": "The company likely has a manual technical interview pipeline, with every engineering candidate tracked through multiple consultant stages before offer.",
        "cta": "Reply 'map' and I'll map the interview pipeline.",
    },
    "info@mbrrecruitment.com": {
        "hook": "Reference Piyushh Ganatra's role as Founder & CEO and one observable: he has led advertising and marketing headhunting in the region for over 30 years.",
        "pain": "The company likely has a manual creative candidate sourcing stage, with media and marketing briefs reworked from scratch for every agency client.",
        "cta": "Reply 'map' and I'll walk you through the sourcing stage.",
    },
    "phumphrey@talentsphere.ca": {
        "hook": "Reference Peter Humphrey's role as Founder & Managing Director and one observable: he built TalentSphere across Canada and the US with an IT and accounting focus.",
        "pain": "The company likely has a manual shortlist stage for IT and accounting roles, with candidate notes spread across consultant spreadsheets.",
        "cta": "Reply 'map' and I'll show you the shortlist loop.",
    },
    "tonyl@harbingernetwork.ca": {
        "hook": "Reference Tony Labora's role as Founder & President and one observable: he founded Harbinger in 2010 after two decades building recruitment businesses.",
        "pain": "The company likely has a manual construction placement loop, with trade candidate availability tracked by phone and email rather than a system.",
        "cta": "Reply 'map' and I'll sketch the placement loop.",
    },
    "doug@blueshock.ca": {
        "hook": "Reference Doug Ross's role as Co-founder & Partner and one observable: he has run hospitality and restaurant executive searches since 2003.",
        "pain": "The company likely has a manual executive search pipeline, with hospitality leadership candidates tracked through individual consultant notes.",
        "cta": "Reply 'map' and I'll map the search pipeline.",
    },
    "trevorw@blueshock.ca": {
        "hook": "Reference Trevor Wowniar's role as Co-founder & Partner and one observable: he drives Blue Shock's Western Canadian market from his Calgary base.",
        "pain": "The company likely has a manual candidate sourcing stage for western Canadian hospitality roles, with every search restarted from a blank brief.",
        "cta": "Reply 'map' and I'll walk you through the sourcing stage.",
    },
    "perry@mandrake.ca": {
        "hook": "Reference Harold Perry's role as Founder & Chairman and one observable: he has completed over 800 executive searches since founding Mandrake in 1970.",
        "pain": "The company likely has a manual succession planning stage, with board and CEO shortlists assembled through decades of personal relationship management.",
        "cta": "Reply 'map' and I'll show you the shortlist loop.",
    },
    "katie@foundpeople.ca": {
        "hook": "Reference Katie Dolgin's role as CEO & Founder and one observable: she built Canada's most respected boutique digital and technology search firm.",
        "pain": "The company likely has a manual technical shortlist stage, with senior tech candidates sourced through consultant networks rather than a system.",
        "cta": "Reply 'map' and I'll sketch the shortlist stage.",
    },
    "wbongard@zsa.ca": {
        "hook": "Reference Warren Bongard's role as President & Co-Founder and one observable: he co-founded Canada's largest legal recruitment firm in 1997.",
        "pain": "The company likely has a manual legal candidate pipeline, with lawyer moves tracked across practice areas through individual consultant files.",
        "cta": "Reply 'map' and I'll map the candidate pipeline.",
    },
    "csweeney@zsa.ca": {
        "hook": "Reference Christopher Sweeney's role as CEO and one observable: he leads a national legal recruitment team across four Canadian cities.",
        "pain": "The company likely has a manual client reporting loop, with placement updates compiled by hand for every law firm client.",
        "cta": "Reply 'map' and I'll draft the reporting loop.",
    },
    "mgoldstein@masongroup.ca": {
        "hook": "Reference Mitch Goldstein's role as President & Founder and one observable: he founded The Mason Group in 2007 for accounting and finance recruitment.",
        "pain": "The company likely has a manual accounting candidate shortlist stage, with finance profiles updated by hand across GTA and Vancouver teams.",
        "cta": "Reply 'map' and I'll show you the shortlist loop.",
    },
    "chantellejames@jivaro.com.au": {
        "hook": "Reference Chantelle James's role as CEO & Founder and one observable: she founded JIVARO in 2006 to raise recruitment standards in fashion and travel.",
        "pain": "The company likely has a manual executive search pipeline, with fashion and consumer candidates tracked through consultant spreadsheets.",
        "cta": "Reply 'map' and I'll map the search pipeline.",
    },
    "gregm@axr.com.au": {
        "hook": "Reference Greg Madden's role as Founder & Managing Director and one observable: he established axr in 2003 to specialise in accounting and finance search.",
        "pain": "The company likely has a manual finance shortlist stage, with CFO and senior finance candidates sourced through personal networks.",
        "cta": "Reply 'map' and I'll walk you through the shortlist stage.",
    },
    "moreinfo@s2m.com.au": {
        "hook": "Reference David Jackson's role as Founder & CEO and one observable: he built S2M into Australia's digital recruitment specialist alongside S2P Technology.",
        "pain": "The company likely has a manual digital candidate pipeline, with developer profiles tracked across consultant inboxes rather than a system.",
        "cta": "Reply 'map' and I'll sketch the candidate pipeline.",
    },
    "miezzi@mitalent.com.au": {
        "hook": "Reference Mariella Iezzi's role as Founding Director and one observable: she established Mitalent in 2008 as a true boutique talent agency.",
        "pain": "The company likely has a manual talent management stage, with client briefs and candidate follow-ups tracked through individual notes.",
        "cta": "Reply 'map' and I'll show you the brief loop.",
    },
    "nikki@beaumontpeople.com.au": {
        "hook": "Reference Nikki Beaumont's role as Founder & Director and one observable: she has run Beaumont People with a purpose-driven approach since 2001.",
        "pain": "The company likely has a manual membership and NFP candidate pipeline, with volunteer and committee roles sourced through outreach spreadsheets.",
        "cta": "Reply 'map' and I'll map the candidate pipeline.",
    },
    "sophie@sestrapeople.com.au": {
        "hook": "Reference Sophie Lane's role as Managing Director & Founder and one observable: she built Sestra around scaling high-growth tech and construction teams.",
        "pain": "The company likely has a manual technical shortlist stage, with mobile and product candidates tracked through consultant notes rather than a system.",
        "cta": "Reply 'map' and I'll walk you through the shortlist stage.",
    },
}


def main() -> None:
    wb = openpyxl.load_workbook(config.DATABASE_PATH)
    ws = wb[config.SHEET_NAME]
    updated = 0
    for row in ws.iter_rows(min_row=2):
        email = str(row[COL_MAP["email"]].value or "").strip().lower()
        if email in CONTENT:
            c = CONTENT[email]
            row[COL_MAP["personalization_hook"]].value = c["hook"]
            row[COL_MAP["pain_hypothesis"]].value = c["pain"]
            row[COL_MAP["suggested_cta"]].value = c["cta"]
            updated += 1
    wb.save(config.DATABASE_PATH)
    print(f"content written: {updated}/{len(CONTENT)} leads")


if __name__ == "__main__":
    main()
