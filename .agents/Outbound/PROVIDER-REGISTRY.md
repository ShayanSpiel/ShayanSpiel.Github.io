# Provider Registry — SpielOS Outbound

Every provider credential lives in `.env` (gitignored — never committed).
This file is the receipt: which env var holds which key, and the live
status. If `.env` is ever lost, re-paste the values into these variables.

| Provider | Env var(s) | Status (2026-08-08) | What it's for |
|---|---|---|---|
| Resend | `RESEND_API_KEY` | ✅ LIVE — sending | Transactional + status reads |
| Mailgun | `MAILGUN_API_KEY`, `MAILGUN_DOMAIN` (mg.spielos.xyz) | ✅ LIVE — sending | Transactional + status reads |
| Brevo | `BREVO_API_KEY` | ✅ LIVE — sending | Transactional + status reads (IP allowlist must keep this server's IP) |
| Postmark | `POSTMARK_API_TOKEN` (server), `POSTMARK_ACCOUNT_TOKEN` (account), `POSTMARK_DOMAIN` (pm.spielos.xyz) | ⏸ Account PENDING APPROVAL; token situation unresolved — see notes below | Transactional + status reads |
| EmailOctopus | `EMAILOCTOPUS_API_KEY` | ⚠ Key valid — **not usable for this engine**: marketing ESP, campaign/list-based, NO transactional send API | Broadcast campaigns only |
| SendGrid | `SENDGRID_API_KEY` (missing) | 🔴 No key | — |
| SMTP/Gmail | `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` | 🔴 Not configured; would break the metrics loop (no status reads) | Last-resort only |

## Postmark notes (2026-08-08)
- User-provided "server token" `a84154f2…` is answered by the API as an
  ACCOUNT token ("Server token is not allowed, please use a valid Account
  token") — it cannot send.
- User-provided "account token" `f16b9bc8…` fails as a server token and the
  account endpoint is unreachable from this server (HTML 404 / transport
  failures — network path to postmark edges is flaky from this box).
- Account itself is PENDING APPROVAL: sends to non-`pm.spielos.xyz`
  recipients return 412 until approved.
- Needed: the real **Server API Token** from the Postmark dashboard
  (Servers → "My First Server" → API Tokens) + account approval.

## How to replace a key
1. Edit `.env` (never `.env.example`, never commit).
2. Restart the daemon: `kill $(cat scripts/experiments/auto/pipeline.pid)` then
   `nohup python3 scripts/pipeline.py daemon ...` (see SKILL Part 5).
3. Confirm via `experiments/status.json` → `metrics.providers`.
