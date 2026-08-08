#!/usr/bin/env python3
"""Harness — notify: email the owner a status line on state changes.

The engine is a daemon; the owner is blind. Every meaningful state change
(batch done, queue hold, gate block, cap reached) sends ONE short email via
the working provider (resend). Throttled: only on state change, never on
the 30-min hold re-checks. Recipient: OWNER_EMAIL env (default
shayan@spielos.xyz, the same domain as the sender).
"""

import html as html_mod
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import providers  # noqa: E402

OWNER_EMAIL = os.environ.get("OWNER_EMAIL", "shayan@spielos.xyz").strip()


def send_status(subject: str, lines: list, tag: str = "") -> bool:
    """Send one short status email. Returns True on send success."""
    try:
        body_html = "<br>\n".join(
            f"<p>{html_mod.escape(l)}</p>" for l in lines
        )
        body_text = "\n".join(lines)
        r = providers.send_email_via(
            "resend", OWNER_EMAIL, subject, body_html, body_text,
            reply_to=OWNER_EMAIL,
        )
        ok = isinstance(r, dict) and r.get("id") is not None
        if not ok:
            print(f"[notify] send failed: {r}")
        return ok
    except Exception as e:  # never break the loop over a notification
        print(f"[notify] exception: {e}")
        return False
