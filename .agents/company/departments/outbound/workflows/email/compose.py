#!/usr/bin/env python3
"""Outbound email composition used during the company runtime's ACT stage.

STRICT (owner rule 2026-08-09): an email is only composed when the lead's
research columns compose real, per-lead content (parseable hook + a
pain_hypothesis that is NOT an auto-generated placeholder). No research ->
skip with a reason. The segment-observation fallback that produced generic
copy is DELETED: unprepared leads never reach an inbox, and validators
(validators.py) mechanically reject any artifact that still contains a
segment-generic observation sentence.
"""

import html as html_mod
import re

from . import content as content_bank
from . import outbound
from .templates import SIGNATURE_HTML, SIGNATURE_TEXT

ALLOWED_RECS = {"Routing email only", "Ready to personalized", "Research and verify"}
FORBIDDEN = {"Backup; wait", "Do not automate"}

TIER_ORDER = {
    "Verified": 0,
    "Catch-all; unverified": 1,
    "Publicly listed; not deliverability-verified": 2,
}
UNSENDABLE = ("Bounced; suppressed", "Invalid", "Bounced")

# Placeholder pain marker: auto-generated research ("The company likely has
# ...") is NOT per-lead evidence — such leads are unprepared and are skipped.
PLACEHOLDER_PAIN_MARKER = "the company likely has"

# Segment-generic observation sentences that must never appear in a rendered
# email. VALIDATE bans these mechanically (the 2026-08-09 incident: the
# fallback produced "Recruitment runs on repeated shortlisting..." for an
# unresearched lead and it shipped).
FORBIDDEN_OBSERVATIONS = (
    "recruitment runs on repeated shortlisting",
    "delivery runs on repeated drafts",
    "support and product feedback get triaged by hand",
    "every scaling business has one repetitive workflow",
    "staffs {segment} roles for {country} clients",
)

_HOOK_PERSON = re.compile(r"(?:Reference|Address)\s+(.+?)(?:'s role as|\s+by name)")
_HOOK_ROLE = re.compile(r"'s role as\s+(.+?)(?:\s+and one observable|\.)")
_HOOK_WORK = re.compile(r"Reference\s+(.+?)'s work in\s+(.+?)(?:\.|$)")
_PLACEHOLDER_TITLES = {"general / new business", "general enquiries", "named company contact"}


def segment_variant(segment: str) -> str:
    s = segment.lower()
    if "recruit" in s:
        return "recruitment-workflow"
    if "agen" in s or "digital" in s:
        return "agency-delivery"
    if "saas" in s or "softwar" in s:
        return "saas-ops"
    return "generic-workflow"


def variant_by_label(lang: str, label: str) -> dict:
    from .templates import TEMPLATES
    for v in TEMPLATES.get(lang, TEMPLATES["English"]):
        if v["label"] == label:
            return v
    return None


def _hook_fields(contact: dict) -> dict:
    """Extract per-lead research from personalization_hook. Returns
    {person, role, company_hook} where any field may be None."""
    hook = contact.get("personalization_hook") or ""
    person = None
    role = None
    company_hook = None
    m = _HOOK_PERSON.search(hook)
    if m:
        person = m.group(1).strip().strip("'")
        role = contact.get("title") or ""
        rm = _HOOK_ROLE.search(hook)
        if rm:
            role = rm.group(1).strip().rstrip(".")
        if role.lower() in _PLACEHOLDER_TITLES:
            role = None
    wm = _HOOK_WORK.search(hook)
    if wm and not person:
        company_hook = wm.group(2).strip().rstrip(".")
    if person and person.lower() in (contact.get("company") or "").lower():
        person = None
    return {"person": person, "role": role, "company_hook": company_hook}


_SEGMENT_Q = {
    "recruitment-workflow": (
        "If that loop is still manual at {company}, I'd be happy to map it "
        "with you. What do you think?",
        "",
    ),
    "agency-delivery": (
        "If either of those is still manual at {company}, I'd be happy to map "
        "that stage with you. What do you think?",
        "",
    ),
    "saas-ops": (
        "If triage is still manual at {company}, I'd be happy to map it with "
        "you. What do you think?",
        "",
    ),
    "generic-workflow": (
        "If that loop is still manual at {company}, I'd be happy to map it "
        "with you. What do you think?",
        "",
    ),
}

_SEGMENT_SUBJECT = {
    "recruitment-workflow": "Staffing loop at {company}",
    "agency-delivery": "Delivery loop at {company}",
    "saas-ops": "Support loop at {company}",
    "generic-workflow": "One workflow at {company}",
}


def compose_researched(contact: dict, label: str, seq: int = 0) -> dict | None:
    """Research-first body: the lead's own pain_hypothesis as the observation,
    the hook's person+role as the opener, the segment question, and a
    conditional close. Returns {subject, body_html, body_text} or None when
    the lead has no usable research — the caller SKIPS the lead (no fallback)."""
    pain = (contact.get("pain_hypothesis") or "").strip().rstrip(".")
    if not pain or len(pain.split()) < 8:
        return None
    if pain.casefold().startswith(PLACEHOLDER_PAIN_MARKER):
        return None
    q, close = _SEGMENT_Q.get(label, _SEGMENT_Q["generic-workflow"])
    q = q.format(company=contact["company"])
    hook = _hook_fields(contact)
    first = outbound.get_first_name(contact) or "there"
    company = contact["company"]

    if hook["person"] and hook["role"]:
        opener = f"Hi {first}, I saw you are {hook['role']} at {company}."
    elif hook["person"]:
        seg_word = "recruitment" if label == "recruitment-workflow" else "delivery"
        opener = f"Hi {first}, I have been looking at {company}'s {seg_word} work."
    elif hook["company_hook"]:
        opener = f"Hi {first}, I have been looking at {company}'s {hook['company_hook']} work."
    else:
        return None

    observation = pain.replace(" are likely ", " are ")
    observation = observation.replace(" is likely ", " is ")
    observation = observation.replace(" likely require ", " require ")
    observation = observation.replace(" likely have ", " have ")

    bank = content_bank.subject_bank_for(label)
    if bank:
        subject = bank[seq % len(bank)].format(company=company)
    else:
        subject = _SEGMENT_SUBJECT.get(label, _SEGMENT_SUBJECT["generic-workflow"]).format(company=company)
    subject = subject[:45]

    html = (
        f"<p>{html_mod.escape(opener)}</p>\n"
        f"<p>{html_mod.escape(observation)}.</p>\n"
        "<p>I build supervised AI employees that carry that loop, one workflow at a time, with a person approving each step.</p>\n"
        f"<p>{html_mod.escape(q)} {html_mod.escape(close)}</p>\n"
        "<p>Best,<br>Shayan</p>\n"
        "{SIGNATURE_HTML}"
    )
    text = (
        f"{opener}\n\n"
        f"{observation}.\n\n"
        "I build supervised AI employees that carry that loop, one workflow at a time, with a person approving each step.\n\n"
        f"{q} {close}\n\n"
        "Best,\nShayan\n\n"
        "{SIGNATURE_TEXT}"
    )
    return {"subject": subject, "body_html": html, "body_text": text}


def render_checked(contact: dict, seq: int = 0) -> tuple:
    """Render subject/body for one lead. STRICT: an English lead is sent ONLY
    when the research columns compose real content (parseable hook +
    pain_hypothesis, never a placeholder). No research -> skip with a reason.
    Persian leads use the prepared Persian template ladder.
    Returns (subject, html, text, reason) — reason None means sendable."""
    label = segment_variant(contact.get("segment") or "")
    if label in ("recruitment-workflow", "agency-delivery") and not contact.get("country"):
        label = "generic-workflow"

    lang = str(contact.get("language") or "English").strip()
    if lang == "English":
        composed = compose_researched(contact, label, seq)
        if composed is None:
            return (None, None, None,
                    "unprepared: no parseable hook + pain research — "
                    "prepare content before send")
        subject = outbound.render_template(composed["subject"], contact)
        body_html = outbound.render_template(composed["body_html"], contact)
        body_text = outbound.render_template(composed["body_text"], contact)
    else:
        tmpl = variant_by_label(lang, label) or outbound.pick_variant(lang, 0)
        if not tmpl:
            return (None, None, None, f"no template for language {lang}")
        subject = outbound.render_template(tmpl["subject"], contact)
        body_html = outbound.render_template(tmpl["body_html"], contact)
        body_text = outbound.render_template(tmpl["body_text"], contact)

    def _norm(s: str) -> str:
        return re.sub(r"\s*\u2014\s*", ", ", s)
    subject = _norm(subject)
    body_html = _norm(body_html)
    body_text = _norm(body_text)
    text_only = body_text.replace(SIGNATURE_TEXT, "").strip()
    html_only = body_html.replace(SIGNATURE_HTML, "")
    words = len(text_only.split())
    if words > 85:
        return None, None, None, f"body {words} words > 85"
    if "\u2014" in subject + text_only:
        return None, None, None, "em dash found"
    if lang == "English" and "http" in subject + html_only:
        return None, None, None, "external link found"
    if not subject or not body_html or not body_text:
        return None, None, None, "empty render"
    return subject, body_html, body_text, None


def _email_type(email: str) -> str:
    """personal vs company: role addresses (info@, hello@, ...) are
    company-type — a known cohort feature for diagnosis."""
    local = (email or "").split("@")[0].lower()
    role = {"info", "hello", "contact", "support", "admin", "office", "sales",
            "team", "hr", "careers", "jobs", "enquiries", "mail", "noreply",
            "business", "billing"}
    if local in role or local.startswith(("info.", "hello.", "contact.")):
        return "company"
    return "personal"


def pick_queue(cohort_filters: dict | None = None) -> list:
    """Ordered, deduped send queue from the master database. Filters come
    from the owner's control knobs (min_tier, skip_unverified); the queue
    never lowers the ICP bar — it only deepens or shallowens by tier."""
    filters = cohort_filters or {}
    min_tier = str(filters.get("min_tier") or "plausible").lower()
    skip_unverified = bool(filters.get("skip_unverified"))
    contacts = outbound.read_contacts()
    log_data = outbound.load_sent_log()

    queued = []
    for c in contacts:
        if outbound.already_sent(c["lead_id"], log_data):
            continue
        if c["send_recommendation"] not in ALLOWED_RECS:
            continue
        if c["send_recommendation"] in FORBIDDEN:
            continue
        status = (c.get("email_status") or "").strip()
        if status in UNSENDABLE:
            continue
        if skip_unverified and status == "Publicly listed; not deliverability-verified":
            continue
        tier = TIER_ORDER.get(status, 2)
        if min_tier == "verified" and tier != 0:
            continue
        queued.append((tier, c))
    order = {"Routing email only": 0, "Ready to personalized": 1, "Research and verify": 2}
    queued.sort(key=lambda tc: (tc[0], order.get(tc[1]["send_recommendation"], 9), tc[1]["lead_id"]))
    q = [c for _t, c in queued]
    q.sort(key=lambda c: 0 if str(c.get("language") or "").strip().lower() == "english" else 1)
    return q


def build_batch_emails(batch_id: str, leads: list, hypothesis: str) -> dict:
    """Compose every lead in `leads` into the batch artifact. Strict mode:
    unprepared leads are skipped with a reason; domains are deduped within
    the batch. Returns {"emails": [...], "skipped": [...]}."""
    emails = []
    skipped = []
    seen_domains = set()
    for i, c in enumerate(leads):
        domain = str(c.get("email") or "").split("@")[-1].lower()
        if domain in seen_domains:
            skipped.append({"lead_id": c["lead_id"], "reason":
                            f"domain {domain} already in this batch"})
            continue
        subject, html, text, reason = render_checked(c, seq=i)
        if reason:
            skipped.append({"lead_id": c["lead_id"], "reason": reason})
            continue
        seen_domains.add(domain)
        emails.append({
            "lead_id": c["lead_id"],
            "subject": subject,
            "body_html": html,
            "body_text": text,
            "features": {
                "source": c.get("source") or "",
                "country": c.get("country") or "",
                "segment": c.get("segment") or "",
                "verified": c.get("email_status") or "",
                "email_type": _email_type(c.get("email") or ""),
                "title": c.get("title") or "",
            },
        })
    return {"emails": emails, "skipped": skipped}
