#!/usr/bin/env python3
"""
SpielOS Outbound — auto-dispatch pipeline (non-stop daily sending).

Usage:
    python3 pipeline.py once            run ONE block (up to BLOCK_SIZE=50) now
    python3 pipeline.py daemon          keep running forver: 50-block -> check
                                        data -> reflect -> next block, until the
                                        daily cap, then sleep to UTC midnight.
    python3 pipeline.py status          one-line state summary
    python3 pipeline.py refill          ingest any lead files dropped in
                                        leads/staging/ (auto-refill helper)

Cadence (owner rule 2026-08-08): SEND 50 in 2 hours, STOP, check data,
reflect, send next 50, keep going. The engine never exceeds
min(daily_cap, PROVIDER_DAILY_TOTAL, queue) per UTC day, never duplicates
(sent_log + provider dedupe guard), and stops 60s after any safety breach
(bounce ≥2% / spam ≥0.08% / delivery <99% / 429).

Block flow:
    1. Queue = English leads, unsent, recommendation in ALLOWED_RECS.
    2. Content guard per lead (85 words, no em dash, no http outside sig).
    3. send_batch.py paces 50 emails at THROTTLE_SECONDS (~2h for a block).
    4. After the block: metrics --force + experiment entry (the "check").
    5. Loop: next block immediately (the check is the pause), until cap.
"""

import html as html_mod
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import outbound
import providers

HERE = os.path.dirname(os.path.abspath(__file__))
OUTBOUND_DIR = os.path.dirname(HERE)
AUTO_DIR = os.path.join(HERE, "experiments", "auto")
LOG_FILE = os.path.join(AUTO_DIR, "pipeline.log")
PID_FILE = os.path.join(AUTO_DIR, "pipeline.pid")
STAGING_DIR = os.path.join(OUTBOUND_DIR, "leads", "staging")

ALLOWED_RECS = {"Routing email only", "Ready to personalized", "Research and verify"}
FORBIDDEN = {"Backup; wait", "Do not automate"}


def log(msg: str) -> None:
    os.makedirs(AUTO_DIR, exist_ok=True)
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}  {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


ORCH_JOURNAL = os.path.join(OUTBOUND_DIR, "orchestration", "journal.md")


def journal(msg: str) -> None:
    """Append a 'needs AI' marker to the orchestration journal — the executor
    never decides; it records what the orchestrator must act on."""
    os.makedirs(os.path.dirname(ORCH_JOURNAL), exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(ORCH_JOURNAL, "a") as f:
        f.write(f"\n- **{ts} — EXECUTOR → AI:** {msg}\n")


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
    for v in outbound.TEMPLATES.get(lang, outbound.TEMPLATES["English"]):
        if v["label"] == label:
            return v
    return None


_HOOK_PERSON = re.compile(r"(?:Reference|Address)\s+(.+?)(?:'s role as|\s+by name)")
_HOOK_ROLE = re.compile(r"'s role as\s+(.+?)(?:\s+and one observable|\.)")
_HOOK_WORK = re.compile(r"Reference\s+(.+?)'s work in\s+(.+?)(?:\.|$)")
_PLACEHOLDER_TITLES = {"general / new business", "general enquiries", "named company contact"}


def _hook_fields(contact: dict) -> dict:
    """Extract per-lead research from personalization_hook. Returns
    {person, role, company_hook} where any field may be None. The hook was
    written per lead during research, so the person+role it names IS the
    research; the pain_hypothesis and suggested_cta columns carry the copy."""
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
        "Is the shortlist stage still done by hand, or have you systemized it?",
        "If it is still manual, I'd be happy to map it with you.",
    ),
    "agency-delivery": (
        "Which stage is still manual: first drafts, or the client reporting?",
        "If either is, I'd be happy to map that one stage with you.",
    ),
    "saas-ops": (
        "Is triage still manual, or do you already run it through a system?",
        "If it is manual, I'd be happy to map it.",
    ),
    "generic-workflow": (
        "Which workflow at {company} is the most manual right now?",
        "If it is still manual, I'd be happy to map it with you.",
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
    the lead has no usable research (caller falls back to the template)."""
    pain = (contact.get("pain_hypothesis") or "").strip().rstrip(".")
    if not pain or len(pain.split()) < 8:
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

    if pain.startswith("The company likely has"):
        observation = pain.replace("The company likely has", "Your kind of operation runs", 1).lower()
        observation = observation[0].upper() + observation[1:]
    else:
        observation = pain.replace(" are likely ", " are ")
        observation = observation.replace(" is likely ", " is ")
        observation = observation.replace(" likely require ", " require ")
        observation = observation.replace(" likely have ", " have ")

    # Subject from the harness-owned bank (variables.json), rotated by batch
    # sequence so consecutive emails never share a subject pattern.
    from harness import variables as hvars
    bank = hvars.subject_bank_for(label)
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
    """Render subject/body for one lead. Research-first: compose from the
    lead's own research columns (pain_hypothesis, personalization_hook);
    fall back to the segment template when the lead has no usable research.
    Returns (subject, html, text) or (None, None, None, reason) when content
    rules are violated. The signature (spielos.xyz + social links) is allowed
    by the content rules, so it is stripped before the word/link/dash
    checks."""
    label = segment_variant(contact.get("segment") or "")
    if label in ("recruitment-workflow", "agency-delivery") and not contact.get("country"):
        label = "generic-workflow"

    composed = compose_researched(contact, label, seq)
    tmpl = variant_by_label(contact["language"], label) or outbound.pick_variant(contact["language"], 0)
    if composed:
        subject = outbound.render_template(composed["subject"], contact)
        body_html = outbound.render_template(composed["body_html"], contact)
        body_text = outbound.render_template(composed["body_text"], contact)
    else:
        subject = outbound.render_template(tmpl["subject"], contact)
        body_html = outbound.render_template(tmpl["body_html"], contact)
        body_text = outbound.render_template(tmpl["body_text"], contact)

    from templates import SIGNATURE_HTML, SIGNATURE_TEXT
    text_only = body_text.replace(SIGNATURE_TEXT, "").strip()
    html_only = body_html.replace(SIGNATURE_HTML, "")
    words = len(text_only.split())
    if words > 85:
        return None, None, None, f"body {words} words > 85"
    if "\u2014" in subject + text_only:
        return None, None, None, "em dash found"
    if "http" in subject + html_only:
        return None, None, None, "external link found"
    if not subject or not body_html or not body_text:
        return None, None, None, "empty render"
    return subject, body_html, body_text, None


TIER_ORDER = {
    "Verified": 0,
    "Catch-all; unverified": 1,
    "Publicly listed; not deliverability-verified": 2,
}
UNSENDABLE = ("Bounced; suppressed", "Invalid", "Bounced")


def pick_queue() -> list:
    contacts = outbound.read_contacts(lang_filter="English")
    log_data = outbound.load_sent_log()

    # Harness-owned cohort filters (state.json variables — applied by the
    # engine after evidence, never hardcoded here). min_tier decides how
    # deep into the verification ladder the queue reaches:
    #   verified  -> only L2/Apollo-verified leads
    #   plausible -> verified + catch-all + publicly-listed (they open/click —
    #                bounce guardrail + bounce-sync still protect the domain)
    try:
        from harness import state as hstate
        filters = hstate.get_variable(hstate.load(), "cohort_filters", {}) or {}
    except Exception:
        filters = {}
    min_tier = str(filters.get("min_tier") or "plausible").lower()

    queued = []
    for c in contacts:
        if outbound.already_sent(c["lead_id"], log_data):
            continue
        if c["send_recommendation"] not in ALLOWED_RECS:
            continue
        status = (c.get("email_status") or "").strip()
        if status in UNSENDABLE:
            continue
        tier = TIER_ORDER.get(status, 2)
        if min_tier == "verified" and tier != 0:
            continue
        queued.append((tier, c))
    order = {"Routing email only": 0, "Ready to personalized": 1, "Research and verify": 2}
    queued.sort(key=lambda tc: (tc[0], order.get(tc[1]["send_recommendation"], 9), tc[1]["lead_id"]))
    q = [c for _t, c in queued]
    if min_tier == "verified":
        log(f"queue: min_tier=verified — only Apollo/L2-verified leads ({len(q)})")
    return q


def _email_type(email: str) -> str:
    """personal vs company: role addresses (info@, hello@, contact@, ...)
    are company-type — a known cohort feature for diagnosis."""
    local = (email or "").split("@")[0].lower()
    role = {"info", "hello", "contact", "support", "admin", "office", "sales",
            "team", "hr", "careers", "jobs", "enquiries", "mail", "noreply",
            "business", "billing"}
    if local in role or local.startswith(("info.", "hello.", "contact.")):
        return "company"
    return "personal"


def build_batch(batch_id: str, leads: list, hypothesis: str) -> str | None:
    os.makedirs(AUTO_DIR, exist_ok=True)
    emails = []
    for i, c in enumerate(leads):
        subject, html, text, reason = render_checked(c, seq=i)
        if reason:
            log(f"  SKIP {c['lead_id']} {c['company']}: {reason}")
            continue
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
    if not emails:
        log("  batch empty (all leads skipped by content guard)")
        return None
    path = os.path.join(AUTO_DIR, f"{batch_id}.json")
    with open(path, "w") as f:
        json.dump({"batch": batch_id, "hypothesis": hypothesis, "emails": emails},
                  f, indent=2, ensure_ascii=False)
    return {"path": path, "count": len(emails), "skipped": len(leads) - len(emails)}


def refill_staging(verbose: bool = True) -> int:
    """Auto-refill: ingest any lead file dropped into leads/staging/ (the
    background bowl for cheap leads: exports, browser-extraction sessions).
    Never scrapes; only consumes files the machine was given. Returns the
    number of files digested (0 = nothing new)."""
    if not os.path.isdir(STAGING_DIR):
        return 0
    files = sorted(f for f in os.listdir(STAGING_DIR)
                   if f.lower().endswith((".csv", ".xlsx", ".xlsm")))
    if not files:
        return 0
    done = os.path.join(STAGING_DIR, "done")
    os.makedirs(done, exist_ok=True)
    count = 0
    for fn in files:
        src = os.path.join(STAGING_DIR, fn)
        try:
            r = subprocess.run([sys.executable, os.path.join(HERE, "leads.py"), "ingest", src],
                               cwd=HERE, capture_output=True, text=True, timeout=180)
            out = (r.stdout + r.stderr).strip()
            log(f"refill {fn}: {out[-200:]}")
            os.rename(src, os.path.join(done, fn))
            count += 1
        except Exception as e:
            log(f"refill {fn}: FAILED {e}")
    if count:
        subprocess.run([sys.executable, os.path.join(HERE, "leads.py"), "reclassify"],
                       cwd=HERE, capture_output=True, text=True)
    return count


def run_block() -> int:
    """Send up to one block (BLOCK_SIZE, default 50) then check+score. Returns:
    0 sent · 1 cap reached · 2 queue empty (after refill attempt) · 3 gate blocked."""
    log_data = outbound.load_sent_log()
    cap, phase = outbound.daily_cap()
    used_today = outbound.sent_today(log_data)
    remaining = cap - used_today
    if remaining <= 0:
        log(f"block: cap reached ({used_today}/{cap}, {phase}) — sleeping to UTC midnight")
        return 1

    # GUARDRAIL GATE — deterministic halt before any send (bounce/spam/delivery)
    from harness import core as hcore
    g = hcore.gate()
    if not g["ok"]:
        for b in g["breaches"]:
            log(f"block: GATE BLOCKED — {b['name']} {b['current']*100:.2f}% > {b['max']*100:.2f}%")
        for p in g["problems"]:
            log(f"block: GATE BLOCKED — data problem: {p}")
        log("block: halting until the breach is fixed (see experiments/report.md)")
        return 3

    queued = pick_queue()
    if not queued:
        filed = refill_staging()
        log(f"block: queue empty (+{filed} staged files refilled?) — checking again")
        queued = pick_queue()
        if not queued:
            # idle time = verification time: L2-probe unverified leads so the
            # next check has a deeper Verified pool
            log("block: queue empty after refill; running L2 verification pass")
            r = subprocess.run([sys.executable, os.path.join(HERE, "verify.py"),
                                "probe-queue", "--limit", "25"],
                               cwd=HERE, capture_output=True, text=True, timeout=300)
            log(f"  verify pass: {(r.stdout + r.stderr).strip()[-160:]}")
            queued = pick_queue()
            if not queued:
                log("block: queue empty after refill+verify; holding for new lead files")
                return 2

    n = min(remaining, config.BLOCK_SIZE, len(queued))
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    block_no = 0
    for i in range(100):  # safety loop; each pass is one block
        log_data = outbound.load_sent_log()
        used_now = outbound.sent_today(log_data)
        if used_now >= cap:
            log(f"block: cap reached mid-cycle ({used_now}/{cap}) — overnight loop ends")
            return 1
        slice_leads = queued[block_no * config.BLOCK_SIZE: (block_no + 1) * config.BLOCK_SIZE]
        slice_leads = [c for c in slice_leads if not outbound.already_sent(c["lead_id"], log_data)]
        if not slice_leads:
            break
        block_no += 1
        batch_id = f"auto-{day}-b{block_no:02d}"
        built = build_batch(batch_id, slice_leads, "research-first: per-lead hook + pain hypothesis, supervised AI employees, conditional close")
        if not built:
            return 3
        log(f"block {block_no}: {built['count']}/{len(slice_leads)} standards, {built['skipped']} skipped")
        # A batch child from a previous (killed) daemon must never pace in
        # parallel — kill any stray send_batch.py before this block starts.
        subprocess.run(["pkill", "-9", "-f", "send_batch.py"],
                       capture_output=True, text=True)
        r = subprocess.run([sys.executable, os.path.join(HERE, "send_batch.py"), built["path"]],
                           cwd=HERE, capture_output=True, text=True)
        sent_n, failed_n = None, None
        for line in r.stdout.strip().splitlines():
            clean = line.strip()
            m = re.search(r"BATCH COMPLETE — Sent: (\d+), Failed: (\d+)", clean)
            if m:
                sent_n, failed_n = int(m.group(1)), int(m.group(2))
            if clean and ("BATCH" in clean or "✅" in clean or "❌" in clean
                          or "ALREADY" in clean or "dedupe" in clean or "cap" in clean):
                log(f"    {clean[:160]}")
        if r.returncode != 0:
            log(f"  batch {batch_id} exited {r.returncode}; stderr: {r.stderr.strip()[-300:]}")
        log(f"  block {batch_id} done: fetching metrics + running the core cycle")
        try:
            subprocess.run([sys.executable, os.path.join(HERE, "outbound.py"), "metrics", "--force"],
                           cwd=HERE, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            log("  metrics --force timed out (300s) — continuing with last metrics")
        # Bounce feedback: suppress any bounced addresses in the master so the
        # gate's "all window bounces suppressed" downgrade condition holds.
        try:
            subprocess.run([sys.executable, os.path.join(HERE, "verify.py"), "sync-bounces"],
                           cwd=HERE, capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            log("  sync-bounces timed out (180s) — continuing")
        try:
            subprocess.run([sys.executable, os.path.join(HERE, "..", "harness", "core.py"),
                            batch_id, "--apply"],
                           cwd=HERE, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            log("  core cycle timed out (120s) — continuing")
        from harness import status as hstatus
        hstatus.bump(
            "batch-done",
            f"Batch {batch_id}: {sent_n if sent_n is not None else built['count']} sent, "
            f"{failed_n if failed_n is not None else 0} failed — cycle measured, loop continues",
            detail=f"{built['count']} in batch, {built['skipped']} skipped by content guard",
        )
    log(f"cycle: {outbound.sent_today(outbound.load_sent_log())}/{cap} used after {block_no} block(s)")
    return 0


def _next_midnight_utc(now) -> float:
    import calendar as _cal
    secs = _cal.timegm((now.year, now.month, now.day, 0, 0, 0)) + 86400
    return secs - now.timestamp()


def _pid_alive(pid: str) -> bool:
    """True if the pid is a live process. A kill -9 leaves a stale PID file
    (SIGKILL cannot run the finally cleanup); without this check the daemon
    refuses to start forever after any hard kill."""
    try:
        os.kill(int(pid), 0)
    except (OSError, ValueError):
        return False
    return True


def daemon() -> None:
    if os.path.exists(PID_FILE):
        pid = ""
        try:
            pid = open(PID_FILE).read().strip()
        except OSError:
            pass
        if pid and _pid_alive(pid):
            log(f"daemon already running (pid {pid}); refusing second instance")
            return
        if pid:
            log(f"stale PID file (pid {pid} not alive) — removing and starting fresh")
            os.remove(PID_FILE)
    os.makedirs(AUTO_DIR, exist_ok=True)
    open(PID_FILE, "w").write(str(os.getpid()))
    log("daemon start: 50-email blocks, metrics check between blocks, "
        "runs until cap or queue empty, refills from staging at empty")
    try:
        last_hold = None  # state-change tracking: notify only once per hold
        while True:
            code = run_block()
            if code == 1:
                now = datetime.now(timezone.utc)
                wait = _next_midnight_utc(now)
                log(f"daily cap done — sleeping {wait / 3600:.1f}h to UTC midnight")
                if last_hold != "cap":
                    from harness import status as hstatus
                    cap, phase = outbound.daily_cap()
                    hstatus.bump("cap-reached",
                                 f"Daily cap reached: {outbound.sent_today(outbound.load_sent_log())}/{cap}",
                                 f"phase {phase} — sleeping until UTC midnight")
                    journal(f"daily cap reached ({outbound.sent_today(outbound.load_sent_log())}/{cap}) — AI: decide next experiment before UTC midnight")
                    last_hold = "cap"
                time.sleep(wait)
            elif code == 2:
                # wait quietly for new drops; also re-check staging every 30 min
                if last_hold != "empty":
                    from harness import status as hstatus
                    hstatus.bump("queue-empty", "Queue empty — holding",
                                 "no unsent verified leads; drop new lead files in "
                                 "leads/staging, daemon re-checks every 30 min")
                    journal("queue empty after refill+probe — AI: research/qualify/ingest a new cohort")
                    last_hold = "empty"
                time.sleep(1800)
            elif code == 3:
                # gate blocked (bounce/spam/delivery breach or data problem):
                # do NOT spin — re-check every 30 min; the breach only clears
                # when metrics improve or the AI applies a lever
                log("gate blocked — re-checking in 30 min (fix in report.md)")
                if last_hold != "gate":
                    from harness import status as hstatus
                    from harness import core as hcore
                    g = hcore.gate()
                    why = "; ".join(
                        f"{b['name']} {b['current']*100:.2f}% > {b['max']*100:.2f}%"
                        for b in g["breaches"]) or "; ".join(g["problems"])
                    hstatus.bump("gate-blocked", "⛔ GATE BLOCKED — no sends until fixed",
                                 why + " — see experiments/report.md")
                    journal(f"gate blocked: {why} — AI: resolve (sync bounces, adjust cohort, or override with a reason)")
                    last_hold = "gate"
                time.sleep(1800)
            else:
                last_hold = None  # a batch went through — re-arm the notifier
                time.sleep(90)  # small pause between blocks of the same cycle
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    log("daemon stop")


def status() -> None:
    log_data = outbound.load_sent_log()
    cap, phase = outbound.daily_cap()
    used = outbound.sent_today(log_data)
    queued = pick_queue()
    ready = providers.available_providers()
    print("=" * 55)
    print("  PIPELINE STATUS")
    print("=" * 55)
    print(f"  Sent today (UTC):   {used}/{cap} ({phase})")
    print(f"  Daily budget:       {config.DAILY_SEND_BUDGET}")
    print(f"  Queue (English):    {len(queued)}")
    print(f"  Providers ready:    {', '.join(ready)}")
    print(f"  Provider caps:      {dict(config.PROVIDER_DAILY_CAPS)}")
    print(f"  Block:              {config.BLOCK_SIZE} emails @ {config.THROTTLE_SECONDS:.0f}s "
          f"(~{config.BLOCK_SIZE * config.THROTTLE_SECONDS / 3600:.1f}h per block)")
    print(f"  Log:                {LOG_FILE}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "once":
        sys.exit(run_block())
    elif cmd == "daemon":
        daemon()
    elif cmd == "status":
        status()
    elif cmd == "refill":
        print(f"staged files refilled: {refill_staging()}")
    else:
        print(__doc__)
        sys.exit(1)