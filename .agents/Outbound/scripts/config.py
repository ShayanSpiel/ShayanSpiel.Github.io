#!/usr/bin/env python3
"""
SpielOS Outbound — configuration.

Everything is driven by environment variables (see .env.example).
The .env file lives at .agents/Outbound/.env and is gitignored.
"""

import os
from pathlib import Path


def load_env() -> None:
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


load_env()

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTBOUND_DIR = SCRIPT_DIR.parent

# ── Provider ───────────────────────────────────────────────────────────────────
# resend | sendgrid | mailgun | smtp
EMAIL_PROVIDER = os.environ.get("EMAIL_PROVIDER", "resend").strip().lower()

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "").strip()
MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY", "").strip()
MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN", "").strip()
SMTP_HOST = os.environ.get("SMTP_HOST", "").strip()
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "").strip()
SMTP_PASS = os.environ.get("SMTP_PASS", "")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "").strip()
SMTP_TLS = os.environ.get("SMTP_TLS", "true").strip().lower() in ("1", "true", "yes")

# ── Sender identity ────────────────────────────────────────────────────────────
FROM_EMAIL = os.environ.get("EMAIL_FROM", "shayan@spielos.xyz").strip()
FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "Shayan Spiel").strip()
SIGNATURE_TITLE = os.environ.get("SIGNATURE_TITLE", "Founder of SpielOS · Agent Harness Architect").strip()
SIGNATURE_AVATAR_URL = os.environ.get("SIGNATURE_AVATAR_URL", "https://spielos.xyz/assets/avatars/avatar.jpg").strip()
SIGNATURE_LINKEDIN = os.environ.get("SIGNATURE_LINKEDIN", "https://linkedin.com/in/shayantawabi").strip()
SIGNATURE_X = os.environ.get("SIGNATURE_X", "https://x.com/ShayanSpiel").strip()
SIGNATURE_SERVICES = os.environ.get("SIGNATURE_SERVICES", "https://spielos.xyz/services/").strip()

# ── Data ───────────────────────────────────────────────────────────────────────
def _resolve_path(value: str, default: str) -> Path:
    p = Path(os.environ.get(value, default)).expanduser()
    return p if p.is_absolute() else OUTBOUND_DIR / p


DATABASE_PATH = _resolve_path(
    "EMAIL_LIST_PATH",
    "spielos_master_outreach_database_updated_2026-08-06.xlsx",
)
SENT_LOG_PATH = _resolve_path("SENT_LOG_PATH", "scripts/sent_log.json")
SHEET_NAME = os.environ.get("EMAIL_SHEET_NAME", "Master Outreach").strip()

# ── Behavior ───────────────────────────────────────────────────────────────────
THROTTLE_SECONDS = float(os.environ.get("THROTTLE_SECONDS", "600"))
VARIANT_ROTATE = int(os.environ.get("VARIANT_ROTATE", "10"))
PERSONALIZATION_HOOK_MAX_LEN = 200


def validate() -> None:
    missing = None
    if EMAIL_PROVIDER == "resend":
        if not RESEND_API_KEY:
            missing = "RESEND_API_KEY"
    elif EMAIL_PROVIDER == "sendgrid":
        if not SENDGRID_API_KEY:
            missing = "SENDGRID_API_KEY"
    elif EMAIL_PROVIDER == "mailgun":
        if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
            missing = "MAILGUN_API_KEY / MAILGUN_DOMAIN"
    elif EMAIL_PROVIDER == "smtp":
        if not SMTP_HOST:
            missing = "SMTP_HOST"
    else:
        raise SystemExit(f"ERROR: unknown EMAIL_PROVIDER '{EMAIL_PROVIDER}' (resend|sendgrid|mailgun|smtp)")

    if missing:
        raise SystemExit(
            f"ERROR: {missing} not set for provider '{EMAIL_PROVIDER}'. "
            f"Add it to {OUTBOUND_DIR / '.env'} (see .env.example)."
        )

    if not DATABASE_PATH.exists():
        raise SystemExit(f"ERROR: email list not found at {DATABASE_PATH}. Set EMAIL_LIST_PATH.")

# ── Email Data (analytics) ───────────────────────────────────────────────────
# Where per-email provider status + recorded replies are stored
METRICS_PATH = _resolve_path("METRICS_PATH", "scripts/metrics.json")
# How often `metrics` re-checks provider status (hours). Cron-friendly: the
# command exits early when the last check is fresher than this.
METRICS_INTERVAL_HOURS = float(os.environ.get("METRICS_INTERVAL_HOURS", "12"))

# ── Goals (Email Data feedback loop) ─────────────────────────────────────────
# The loop keeps working until these are met (see strategy.py).
GOAL_REPLY_RATE = float(os.environ.get("GOAL_REPLY_RATE", "0.10"))       # replies / sent — THE goal
GOAL_OPEN_RATE = float(os.environ.get("GOAL_OPEN_RATE", "0.30"))         # opened / delivered
GOAL_CLICK_RATE = float(os.environ.get("GOAL_CLICK_RATE", "0.05"))       # clicked / delivered
GOAL_DELIVERED_RATE = float(os.environ.get("GOAL_DELIVERED_RATE", "0.95"))  # delivered / sent
MAX_BOUNCE_RATE = float(os.environ.get("MAX_BOUNCE_RATE", "0.04"))       # bounced / sent (Resend free limit)
MAX_SPAM_RATE = float(os.environ.get("MAX_SPAM_RATE", "0.0008"))         # complained / sent (Resend free limit)

# ── Replies ───────────────────────────────────────────────────────────────────
# Reply-To on outbound emails: point this at a Resend receiving domain
# (e.g. replies@in.spielos.xyz) so replies are auto-detected on every
# `metrics` run. Leave empty for no Reply-To (replies land in the From
# inbox and are recorded with `record-reply`).
REPLY_TO = os.environ.get("REPLY_TO", "").strip()
# Comma-separated subject markers that identify auto-replies (out-of-office,
# etc.) — recorded but excluded from the reply-rate goal.
AUTO_REPLY_KEYWORDS = os.environ.get(
    "AUTO_REPLY_KEYWORDS",
    "out of office,out of the office,automatic reply,auto reply,auto-reply,vacation",
).strip()

# ── Analytics behavior ────────────────────────────────────────────────────────
# Cache of provider-host IPs so flaky DNS/VPN can be bypassed (see providers.py)
IP_CACHE_PATH = _resolve_path("IP_CACHE_PATH", "scripts/ip_cache.json")
# Minimum sample before rates are trusted / variants compared
MIN_TOTAL_SAMPLE = int(os.environ.get("MIN_TOTAL_SAMPLE", "10"))
MIN_VARIANT_SAMPLE = int(os.environ.get("MIN_VARIANT_SAMPLE", "5"))

# ── Goals ─────────────────────────────────────────────────────────────────────
# Single source of truth for the goal engine (strategy.py). Each entry:
#   name, metric (key in analytics.aggregate), target, kind ("floor" = higher
#   is better; "ceiling" = lower is better), stage, severity, action text.
# Add a goal here (or via GOAL_*/MAX_* env vars) and the loop will enforce it.
GOALS = [
    {
        "name": "reply rate",
        "metric": "reply_rate",
        "target": GOAL_REPLY_RATE,
        "kind": "floor",
        "stage": "reply",
        "severity": "high",
        "action": "rewrite the question so only this lead can answer it, sharpen the offer, "
                  "cut anything generic (Part 1: Rules 3, 4, 7)",
    },
    {
        "name": "open rate",
        "metric": "open_rate",
        "target": GOAL_OPEN_RATE,
        "kind": "floor",
        "stage": "open",
        "severity": "medium",
        "action": "work the subject lines: 2-5 words, name the topic in the reader's vocabulary, "
                  "no spam words (Part 1: Rule 2)",
    },
    {
        "name": "click rate",
        "metric": "click_rate",
        "target": GOAL_CLICK_RATE,
        "kind": "floor",
        "stage": "click",
        "severity": "medium",
        "action": "make the CTA unmissable: one link, one action, a line that tells them "
                  "what happens when they click",
    },
    {
        "name": "delivered rate",
        "metric": "delivered_rate",
        "target": GOAL_DELIVERED_RATE,
        "kind": "floor",
        "stage": "deliverability",
        "severity": "medium",
        "action": "verify DNS records, check provider deliverability insights, keep the list clean",
    },
    {
        "name": "bounce rate",
        "metric": "bounce_rate",
        "target": MAX_BOUNCE_RATE,
        "kind": "ceiling",
        "stage": "deliverability",
        "severity": "high",
        "action": "verify emails before sending (see provider bounce reasons), check SPF/DKIM/DMARC",
    },
    {
        "name": "spam rate",
        "metric": "spam_rate",
        "target": MAX_SPAM_RATE,
        "kind": "ceiling",
        "stage": "deliverability",
        "severity": "high",
        "action": "slow the throttle, warm up the domain, cut spammy phrasing from the templates",
    },
]
