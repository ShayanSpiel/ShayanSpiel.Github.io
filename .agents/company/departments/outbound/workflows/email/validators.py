#!/usr/bin/env python3
"""Outbound email mechanical artifact validation rules.

Every prepared email must pass these before it reaches the human REVIEW
gate. This is the machine checkpoint that caught the 2026-08-09 class of
bug (segment-generic fallback copy shipping because the human rubber-
stamped the preview). Issues are {lead_id, code, message, skippable}:
skippable issues drop that email from the batch; structural issues hold
the batch for owner attention.
"""

import re

from .compose import FORBIDDEN_OBSERVATIONS, FORBIDDEN_OFFER_PHRASES
from .templates import SIGNATURE_HTML, SIGNATURE_TEXT


def _text_only(body_text: str) -> str:
    return body_text.replace(SIGNATURE_TEXT, "").strip()


def validate(ctx, batch: dict) -> list:
    issues = []
    for e in batch.get("emails", []):
        lead_id = e.get("lead_id", "?")
        subject = e.get("subject") or ""
        body_text = _text_only(e.get("body_text") or "")
        body_html = e.get("body_html") or ""

        if not subject or not body_text or not body_html:
            issues.append({"lead_id": lead_id, "code": "empty_render",
                           "message": "subject/body missing", "skippable": True})

        lower = (subject + " " + body_text).casefold()
        for obs in FORBIDDEN_OBSERVATIONS:
            if obs in lower:
                issues.append({"lead_id": lead_id, "code": "segment_fallback",
                               "message": f"segment-generic observation detected: {obs!r}",
                               "skippable": True})
        for phrase in FORBIDDEN_OFFER_PHRASES:
            if phrase in lower:
                issues.append({"lead_id": lead_id, "code": "retired_offer",
                               "message": f"retired offer phrase detected: {phrase!r}",
                               "skippable": True})

        words = len(body_text.split())
        if words > 85:
            issues.append({"lead_id": lead_id, "code": "over_word_limit",
                           "message": f"body {words} words > 85", "skippable": True})
        if "\u2014" in subject + body_text:
            issues.append({"lead_id": lead_id, "code": "em_dash",
                           "message": "em dash found in rendered copy", "skippable": True})
        if "http" in subject + body_html.replace(SIGNATURE_HTML, ""):
            issues.append({"lead_id": lead_id, "code": "external_link",
                           "message": "external link outside the signature", "skippable": True})

    return issues
