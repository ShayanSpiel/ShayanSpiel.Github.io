#!/usr/bin/env python3
"""
SpielOS Outbound — email providers.

Sending contract:
  send_email(to_email, subject, html, text, reply_to="")
    Success:  {"id": "<provider message id>"}
    Failure:  {"error": True, "status": <int>, "message": "<detail>"}

Email Data contract (used by analytics.py / strategy.py):
  cap_status()            -> can this provider report per-email status?
  cap_list_sent()         -> can we list sent emails (id backfill)?
  cap_received()          -> can we list received emails (auto-replies)?
  fetch_email_status(id)  -> {"last_event": <canonical event>, ...}
  list_sent_emails()      -> sent emails
  list_received_emails()  -> received emails

Supported providers (EMAIL_PROVIDER env var):

  Provider  status  list_sent  received   notes
  resend    yes     yes        yes        GET /emails/{id} for status; /emails
                                         to backfill ids; /emails/receiving for
                                         replies. Key must have Full access
                                         (sending-only keys return 404 on reads).
  mailgun   yes*    no         no         events API per message-id for status.
                                         Delivery/engagement only; no listing.
  sendgrid  no      no         no         v3 send has no free read API; open/click
                                         need the Event Webhook + their plans.
  smtp      no      no         no         relays have no tracking; replies are
                                         manual only.

Canonical event vocabulary (whatever the provider calls it, every status
buckets to one of): sent, delivered, delivery_delayed, opened, clicked,
bounced, complained (marked spam), failed, suppressed, replied.

Transport resilience: every HTTP call retries with backoff, and caches the
provider host IPs so a flaky VPN / broken DNS can be bypassed on later calls
(see IP_CACHE_PATH).
"""

import base64
import json
import smtplib
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    EMAIL_PROVIDER,
    IP_CACHE_PATH,
    RESEND_API_KEY,
    SENDGRID_API_KEY,
    MAILGUN_API_KEY,
    MAILGUN_DOMAIN,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASS,
    SMTP_TLS,
    FROM_EMAIL,
    FROM_NAME,
)

_UA = "SpielOS-Outbound/1.1"

_CAPABILITIES = {
    "resend": {"status": True, "list_sent": True, "received": True},
    "mailgun": {"status": True, "list_sent": True, "received": False},
    "sendgrid": {"status": False, "list_sent": False, "received": False},
    "smtp": {"status": False, "list_sent": False, "received": False},
}


def cap_status() -> bool:
    return _CAPABILITIES.get(EMAIL_PROVIDER, {}).get("status", False)


def cap_list_sent() -> bool:
    return _CAPABILITIES.get(EMAIL_PROVIDER, {}).get("list_sent", False)


def cap_received() -> bool:
    return _CAPABILITIES.get(EMAIL_PROVIDER, {}).get("received", False)


# ── Transport (retry + DNS/IP fallback) ──────────────────────────────────────

_real_getaddrinfo = socket.getaddrinfo


def _remember_ips(host: str) -> None:
    try:
        ips = [r[4][0] for r in _real_getaddrinfo(host, 443, socket.AF_INET)]
        if not ips:
            return
        cache = {}
        if IP_CACHE_PATH.exists():
            cache = json.loads(IP_CACHE_PATH.read_text())
        if cache.get(host) != ips:
            cache[host] = ips
            IP_CACHE_PATH.write_text(json.dumps(cache, indent=2))
    except Exception:
        pass


def _cached_ips(host: str):
    try:
        if IP_CACHE_PATH.exists():
            cache = json.loads(IP_CACHE_PATH.read_text())
            return cache.get(host) or []
    except Exception:
        pass
    return []


def _patched_getaddrinfo(ip: str):
    def patched(host, port, *args, **kwargs):
        args = (socket.AF_INET, socket.SOCK_STREAM) + tuple(args[2:])
        return _real_getaddrinfo(ip, port, *args, **kwargs)
    return patched


class _TransportError(Exception):
    pass


def _request_once(url: str, headers: dict, payload=None, method: str = "GET", host_ip: str = None) -> dict:
    """One HTTP attempt. Returns a dict (possibly {"error": ...}) for HTTP-level
    failures, or raises _TransportError for connect/DNS/SSL failures."""
    orig = None
    if host_ip:
        orig = socket.getaddrinfo
        socket.getaddrinfo = _patched_getaddrinfo(host_ip)
    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"User-Agent": _UA, **headers},
            method=method,
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            result = json.loads(body) if body else {}
            # SendGrid returns 202 with no body; expose its tracking id header.
            msg_id = resp.headers.get("X-Message-Id")
            if msg_id:
                result["id"] = msg_id
            if "id" not in result and not body:
                result["id"] = f"{EMAIL_PROVIDER}:{resp.status}"
            return result
    except urllib.error.HTTPError as e:
        return {"error": True, "status": e.code, "message": e.read().decode("utf-8", errors="replace")}
    except Exception as e:
        raise _TransportError(str(e)) from e
    finally:
        if orig:
            socket.getaddrinfo = orig


def _open(url: str, method: str = "GET", payload=None, headers: dict = None, retries: int = 3) -> dict:
    host = urllib.parse.urlparse(url).hostname or ""
    headers = headers or {}
    last = None
    for attempt in range(retries):
        try:
            r = _request_once(url, headers, payload, method)
            if not r.get("error"):
                _remember_ips(host)
                return r
            last = r
            # Auth/permission/not-found: retrying will not help.
            if r.get("status") in (401, 403, 404):
                return r
        except _TransportError as e:
            last = {"error": True, "status": 0, "message": str(e)}
            # DNS broken? Try the cached provider IP directly.
            for ip in _cached_ips(host):
                try:
                    r = _request_once(url, headers, payload, method, host_ip=ip)
                    if not r.get("error"):
                        return r
                    if r.get("status") in (401, 403, 404):
                        return r
                except _TransportError:
                    continue
        if attempt < retries - 1:
            time.sleep(2 * (attempt + 1))
    return last or {"error": True, "status": 0, "message": "unknown transport failure"}


# ── Sending ──────────────────────────────────────────────────────────────────

def _from() -> str:
    return f"{FROM_NAME} <{FROM_EMAIL}>"


def _send_resend(to_email: str, subject: str, html: str, text: str, reply_to: str) -> dict:
    payload = {
        "from": _from(),
        "to": to_email,
        "subject": subject,
        "html": html,
        "text": text,
    }
    if reply_to:
        payload["reply_to"] = [reply_to]
    return _open(
        "https://api.resend.com/emails",
        method="POST",
        payload=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
    )


def _send_sendgrid(to_email: str, subject: str, html: str, text: str, reply_to: str) -> dict:
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": FROM_EMAIL, "name": FROM_NAME},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text},
            {"type": "text/html", "value": html},
        ],
    }
    if reply_to:
        payload["reply_to"] = {"email": reply_to}
    return _open(
        "https://api.sendgrid.com/v3/mail/send",
        method="POST",
        payload=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}", "Content-Type": "application/json"},
    )


def _send_mailgun(to_email: str, subject: str, html: str, text: str, reply_to: str) -> dict:
    data = {
        "from": _from(),
        "to": to_email,
        "subject": subject,
        "text": text,
        "html": html,
    }
    if reply_to:
        data["h:Reply-To"] = reply_to
    token = base64.b64encode(f"api:{MAILGUN_API_KEY}".encode()).decode()
    return _open(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        method="POST",
        payload=urllib.parse.urlencode(data).encode("utf-8"),
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/x-www-form-urlencoded"},
    )


def _send_smtp(to_email: str, subject: str, html: str, text: str, reply_to: str) -> dict:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = _from()
    msg["To"] = to_email
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        if SMTP_TLS:
            server.starttls()
        if SMTP_USER:
            server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        server.quit()
        return {"id": f"smtp:{datetime.utcnow().isoformat()}"}
    except Exception as e:
        return {"error": True, "status": 0, "message": str(e)}


def send_email(to_email: str, subject: str, html: str, text: str, reply_to: str = "") -> dict:
    if EMAIL_PROVIDER == "resend":
        return _send_resend(to_email, subject, html, text, reply_to)
    if EMAIL_PROVIDER == "sendgrid":
        return _send_sendgrid(to_email, subject, html, text, reply_to)
    if EMAIL_PROVIDER == "mailgun":
        return _send_mailgun(to_email, subject, html, text, reply_to)
    if EMAIL_PROVIDER == "smtp":
        return _send_smtp(to_email, subject, html, text, reply_to)
    return {"error": True, "status": 0, "message": f"unknown provider: {EMAIL_PROVIDER}"}


# ── Email Data (analytics) ───────────────────────────────────────────────────

def fetch_email_status(email_id: str) -> dict:
    """Latest status for one sent email -> {"last_event": <canonical>}.

    resend:   GET /emails/{id} -> {"last_event": ...}
    mailgun:  events API per message-id (opened > clicked/delivered > ...)
    sendgrid: not available (needs Event Webhook / paid activity API)
    smtp:     no tracking at all
    """
    if EMAIL_PROVIDER == "resend":
        return _open(
            f"https://api.resend.com/emails/{urllib.parse.quote(email_id)}",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
        )
    if EMAIL_PROVIDER == "mailgun":
        return _mailgun_status(email_id)
    return {"error": True, "status": 0, "message": f"{EMAIL_PROVIDER} does not report email status (no API-level tracking)"}


_MAILGUN_EVENT_RANK = {
    "rejected": "failed",
    "failed": "failed",
    "delivered": "delivered",
    "opened": "opened",
    "clicked": "clicked",
    "complained": "complained",
    "unsubscribed": "complained",
    "stored": "delivered",
}
_MAILGUN_ORDER = ["complained", "clicked", "opened", "delivered", "stored", "unsubscribed", "failed", "rejected"]


def _mailgun_status(msg_id: str) -> dict:
    token = base64.b64encode(f"api:{MAILGUN_API_KEY}".encode()).decode()
    base = f"https://api.mailgun.net/v3/{urllib.parse.quote(MAILGUN_DOMAIN)}/events"
    headers = {"Authorization": f"Basic {token}"}
    found = None
    # Query most-significant events first; the first hit wins (rank-ordered).
    for event in _MAILGUN_ORDER:
        qs = urllib.parse.urlencode({
            "event": event,
            "message-id": msg_id,
            "limit": 5,
        })
        r = _open(f"{base}?{qs}", headers=headers)
        if r.get("error"):
            err = r
            continue
        items = r.get("items") or []
        if items:
            found = _MAILGUN_EVENT_RANK.get(event, event)
            break
    if found is None:
        # Look for plain "accepted" as the lowest-signal confirmation.
        qs = urllib.parse.urlencode({"event": "accepted", "message-id": msg_id, "limit": 1})
        r = _open(f"{base}?{qs}", headers=headers)
        if not r.get("error") and r.get("items"):
            found = "sent"
    if found is None:
        return {"error": True, "status": 0, "message": "mailgun: no events found for message id (not yet processed, or wrong id)"}
    return {"last_event": found}


def list_sent_emails() -> dict:
    """Sent emails, used to backfill missing/truncated ids in the log."""
    if EMAIL_PROVIDER == "resend":
        return _open("https://api.resend.com/emails", headers={"Authorization": f"Bearer {RESEND_API_KEY}"})
    return {"error": True, "status": 0, "message": f"{EMAIL_PROVIDER} has no sent-email listing API"}


def list_received_emails() -> dict:
    """Received emails, used to auto-detect replies (Resend receiving)."""
    if EMAIL_PROVIDER == "resend":
        return _open("https://api.resend.com/emails/receiving", headers={"Authorization": f"Bearer {RESEND_API_KEY}"})
    return {"error": True, "status": 0, "message": f"{EMAIL_PROVIDER} has no received-email listing API"}
