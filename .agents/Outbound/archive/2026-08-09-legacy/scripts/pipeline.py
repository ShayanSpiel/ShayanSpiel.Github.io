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
    1. Pull fresh provider statuses, then the guardrail gate decides (gate
       never judges a stale snapshot).
    2. Queue = unsent leads in ALLOWED_RECS (EN researched-personal + FA
       prepared ladder), ordered by verification tier.
    3. Content guard per lead (85 words, no em dash, no http outside sig).
    4. Reflection evidence written BEFORE the send (preview + skip count).
    5. Approval gate: the first block of an experiment sends only after the
       orchestrator reviewed the preview (engine.json approval).
    6. send_batch.py paces emails at THROTTLE_SECONDS (~2h for a block).
    7. After the block: metrics --force + core cycle (the "check") + goal
       check (reply target met -> stop for the day).
    8. Loop: next block immediately (the check is the pause), until cap.
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

# KILL SWITCH — `touch STOP` (or run stop.sh) and every engine process stops
# within 60s: daemon exits, hook exits, supervisor stops restarting. Sends are
# impossible while STOP exists (checked before every block and every slice).
STOP_FILE = os.path.join(HERE, "STOP")

# HOT-RELOAD KNOBS — engine.json is re-read before every block, so the
# orchestrator (the opencode session) can run experiments without restarting
# the daemon: {"block_size": 20, "throttle_seconds": 120, "daily_cap": 300}.
# Missing keys or a missing file fall back to env defaults. The daemon logs
# which knobs are active so the journal shows the experiment in flight.
ENGINE_CONFIG_FILE = os.path.join(AUTO_DIR, "engine.json")


def stopped() -> bool:
    return os.path.exists(STOP_FILE)


def load_engine() -> dict:
    """Fresh runtime knobs for the next block. Never raises; invalid or
    missing entries fall back to env defaults. The orchestrator writes this
    file between batches — it IS the experiment dial."""
    knobs = {}
    try:
        with open(ENGINE_CONFIG_FILE) as f:
            raw = json.load(f)
        for key, cast in (("block_size", int), ("throttle_seconds", int), ("daily_cap", int)):
            v = raw.get(key)
            if v is None:
                continue
            knobs[key] = cast(v)
            if knobs[key] <= 0:
                knobs.pop(key)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        knobs = {}
    return knobs


def _log_knobs(knobs: dict) -> str:
    if not knobs:
        return "engine.json: defaults"
    return "engine.json: " + ", ".join(f"{k}={v}" for k, v in sorted(knobs.items()))

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
    # Suggestion-first (owner rule 2026-08-09): the email names a specific
    # workflow, then asks a light opinion question — never makes the lead
    # identify the workflow for us.
    "recruitment-workflow": (
        "If that loop is still manual at {company}, I'd be happy to map it "
        "with you — what do you think?",
        "",
    ),
    "agency-delivery": (
        "If either of those is still manual at {company}, I'd be happy to map "
        "that stage with you — what do you think?",
        "",
    ),
    "saas-ops": (
        "If triage is still manual at {company}, I'd be happy to map it with "
        "you — what do you think?",
        "",
    ),
    "generic-workflow": (
        "If that loop is still manual at {company}, I'd be happy to map it "
        "with you — what do you think?",
        "",
    ),
}

_SEGMENT_SUBJECT = {
    "recruitment-workflow": "Staffing loop at {company}",
    "agency-delivery": "Delivery loop at {company}",
    "saas-ops": "Support loop at {company}",
    "generic-workflow": "One workflow at {company}",
}

# Segment observations NAME the workflow (owner rule 2026-08-09): the email
# is only allowed when it identifies a concrete loop in the lead's business —
# never a generic "you run repeated work" placeholder.
_SEGMENT_OBSERVATION = {
    "recruitment-workflow": (
        "Recruitment runs on repeated shortlisting: sourcing, screening and "
        "follow-up emails spread across your ATS, inbox and LinkedIn"),
    "agency-delivery": (
        "Delivery runs on repeated drafts, client updates and reporting "
        "moving between several tools"),
    "saas-ops": (
        "Support and product feedback get triaged by hand and routed "
        "between people"),
    "generic-workflow": (
        "Every scaling business has one repetitive workflow that eats the "
        "week: the follow-ups, the handoffs, the reporting between tools"),
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
        # Auto-generated placeholder pain -> use the segment observation,
        # which names a concrete workflow in that business type.
        observation = _SEGMENT_OBSERVATION.get(
            label, _SEGMENT_OBSERVATION["generic-workflow"])
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
    """Render subject/body for one lead. STRICT (owner rule 2026-08-09):
    an English lead is sent ONLY when the research columns compose real
    content (parseable hook + pain_hypothesis). No research -> skip with a
    reason — the silent generic fallback is removed; unprepared leads never
    reach an inbox. Persian leads use the Persian prepared template ladder.
    Returns (subject, html, text) or (None, None, None, reason)."""
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

    from templates import SIGNATURE_HTML, SIGNATURE_TEXT
    # Content normalization (owner rule 2026-08-09): research copy may carry
    # em dashes from the source data — normalize them to commas so the
    # no-em-dash rule holds in the FINAL render (the guard below still
    # validates the result). Regex handles the spaces AROUND the dash too:
    # "word — word" must become "word, word", never "word ,  word".
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
    # External-link rule applies to the English research-first path only
    # (compose never emits links outside the signature). The Persian ladder is
    # owner-prepared template copy whose links are intentional.
    if lang == "English" and "http" in subject + html_only:
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
    contacts = outbound.read_contacts()  # EN + FA (owner rule 2026-08-09: both
    # template sets exist; the Persian ladder was idle with 161 unsent leads)
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
    # Market order: English (the buyer market) sends first; Persian fills
    # only after every English lead is exhausted. Stable sort — the tier
    # ordering inside each language is preserved.
    q.sort(key=lambda c: 0 if str(c.get("language") or "").strip().lower() == "english" else 1)
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
    seen_domains = set()
    for i, c in enumerate(leads):
        domain = str(c.get("email") or "").split("@")[-1].lower()
        if domain in seen_domains:
            log(f"  SKIP {c['lead_id']} {c['company']}: domain {domain} already in this batch")
            continue
        subject, html, text, reason = render_checked(c, seq=i)
        if reason:
            log(f"  SKIP {c['lead_id']} {c['company']}: {reason}")
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
    if not emails:
        log("  batch empty (all leads skipped by content guard)")
        return None
    path = os.path.join(AUTO_DIR, f"{batch_id}.json")
    with open(path, "w") as f:
        json.dump({"batch": batch_id, "hypothesis": hypothesis, "emails": emails},
                  f, indent=2, ensure_ascii=False)
    # Batch preview: every rendered email to a readable file so the
    # reflection pass can do content QA BEFORE the send (owner rule
    # 2026-08-09: emails are prepared and reviewed, never trusted blindly).
    preview = os.path.join(AUTO_DIR, f"{batch_id}.preview.md")
    skipped = len(leads) - len(emails)
    with open(preview, "w") as f:
        f.write(f"# {batch_id} — {len(emails)} emails · {skipped} skipped\n\n")
        f.write(f"hypothesis: {hypothesis}\n\n")
        for i, e in enumerate(emails):
            f.write(f"## {i + 1}. {e['lead_id']} — {e['subject']}\n\n")
            f.write(e["body_text"][:700].strip() + "\n\n---\n\n")
    log(f"preview: {preview}")
    return {"path": path, "preview": preview, "count": len(emails),
            "skipped": skipped}


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
    0 sent · 1 cap reached · 2 queue empty (after refill attempt) · 3 gate blocked
    · 4 STOP file · 5 goal achieved (hold to midnight) · 6 awaiting approval."""
    log_data = outbound.load_sent_log()
    cap, phase = outbound.daily_cap()
    used_today = outbound.sent_today(log_data)
    remaining = cap - used_today
    if remaining <= 0:
        log(f"block: cap reached ({used_today}/{cap}, {phase}) — sleeping to UTC midnight")
        return 1

    # OBSERVE — pull fresh provider statuses BEFORE judging. The gate must
    # decide on current data, not the last post-block snapshot: a long hold
    # otherwise re-judges stale metrics forever.
    try:
        subprocess.run([sys.executable, os.path.join(HERE, "outbound.py"), "metrics", "--force"],
                       cwd=HERE, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        log("pre-gate metrics pull timed out (300s) — using stored metrics")

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

    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    knobs = load_engine()
    log(f"block: {_log_knobs(knobs)}")
    eng_block = knobs.get("block_size") or config.BLOCK_SIZE
    throttle = knobs.get("throttle_seconds")
    if knobs.get("daily_cap") and knobs["daily_cap"] < cap:
        cap = knobs["daily_cap"]
    block_no = 0
    for i in range(100):  # safety loop; each pass is one block
        if stopped():
            log("block: STOP file present — halting engine")
            return 4
        log_data = outbound.load_sent_log()
        used_now = outbound.sent_today(log_data)
        if used_now >= cap:
            log(f"block: cap reached mid-cycle ({used_now}/{cap}) — overnight loop ends")
            return 1
        # The slice must never exceed today's remaining cap: with a partial
        # day the last block is smaller than BLOCK_SIZE (owner rule 2026-08-08:
        # "n was computed but never used — 14 slots stuck in a refusal loop").
        bsize = min(eng_block, cap - used_now)
        if bsize <= 0:
            return 1
        slice_leads = queued[block_no * eng_block: block_no * eng_block + bsize]
        block_no += 1
        batch_id = f"auto-{day}-b{block_no:02d}"
        slice_leads = [c for c in slice_leads if not outbound.already_sent(c["lead_id"], log_data)]
        if not slice_leads:
            log(f"block {block_no}: slice empty (all sent) — stopping slice loop")
            break
        built = build_batch(batch_id, slice_leads, "research-first: per-lead hook + pain hypothesis, supervised AI employees, conditional close")
        if not built:
            # All-skipped slice is NOT a gate block — the engine moves to the
            # next slice instead of holding in the wrong hold (the old code
            # returned 3 and stalled the whole day on a content problem).
            log(f"block {block_no}: no sendable leads in this slice (content guard) — moving to next slice")
            continue
        log(f"block {block_no}: {built['count']}/{len(slice_leads)} standards, {built['skipped']} skipped")
        # REFLECT — content evidence BEFORE the send: the preview + skip count
        # land in experiments/reflection.md so the wake event can QA the copy
        # while the block paces (owner rule 2026-08-09: emails are prepared
        # and reviewed, never trusted blindly).
        try:
            from harness import reflect as hreflect
            hreflect.run_reflection(batch_id, built["preview"], built["skipped"])
        except Exception as e:
            log(f"reflection evidence failed: {e}")

        # APPROVAL GATE — the first block of every experiment sends only after
        # the orchestrator reviewed the preview and set engine.json
        # {"approval": {"experiment": <current experiment string>,
        #                "approved": true, "by": "orchestrator", "note": "..."}}.
        # Blocks inside an already-approved experiment free-run; changing the
        # experiment string (or editing content) resets the gate. Nothing is
        # ever trusted blindly — the daemon holds and the hook wakes the AI.
        _raw = {}
        try:
            with open(ENGINE_CONFIG_FILE) as f:
                _raw = json.load(f)
        except Exception:
            _raw = {}
        _exp = str(_raw.get("experiment") or "")
        _appr = _raw.get("approval") or {}
        if _appr.get("experiment") != _exp or not _appr.get("approved"):
            log(f"block {batch_id}: AWAITING APPROVAL — review {built['preview']}, "
                f"then set engine.json approval (experiment == current string)")
            journal(f"approval needed for {batch_id}: review {built['preview']} "
                    "and set engine.json approval before the engine sends")
            return 6
        # A batch child from a previous (killed) daemon must never pace in
        # parallel — kill any stray send_batch.py before this block starts.
        subprocess.run(["pkill", "-9", "-f", "send_batch.py"],
                       capture_output=True, text=True)
        env = dict(os.environ)
        if throttle:
            env["THROTTLE_SECONDS"] = str(throttle)
        r = subprocess.run([sys.executable, os.path.join(HERE, "send_batch.py"), built["path"]],
                           cwd=HERE, capture_output=True, text=True, env=env)
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
        if sent_n is None:
            # Child exited without a BATCH COMPLETE line (refusal or crash) —
            # never report built counts as sent (owner rule 2026-08-08: the
            # bump used to lie "50 sent" while send_batch refused the batch).
            sent_n, failed_n = 0, 0
        hstatus.bump(
            "batch-done",
            f"Batch {batch_id}: {sent_n} sent, {failed_n} failed"
            + ("" if r.returncode == 0 else f" — child exited {r.returncode}"),
            detail=f"{built['count']} in batch, {built['skipped']} skipped by content guard",
        )
        # GOAL CHECK — the loop's YES/STOP branch: when the primary goal is
        # met with no guardrail breach, the engine stops sending for the day
        # and the orchestrator decides the next goal (raise target or stop).
        try:
            import analytics as _an
            _log2 = outbound.load_sent_log()
            _met = _an.load_metrics()
            _cut = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
            _wl = {"sent": [s for s in _log2.get("sent", [])
                            if str(s.get("timestamp", "")) >= _cut],
                   "failed": _log2.get("failed", [])}
            _tot = _an.aggregate(_wl, _met)
            from harness import reflect as _hr
            from harness import state as _hs
            _st = _hs.load()
            _filt = _hs.get_variable(_st, "cohort_filters", {}) or {}
            _gb = hcore.gate().get("breaches") or []
            _weak = _hr.weakest_link(_tot, _st["meta"], _tot["sent"],
                                     bool(_filt.get("skip_unverified")),
                                     breaches=_gb)
            if _weak and _weak["stage"] == "goal-met":
                log(f"cycle: {outbound.sent_today(outbound.load_sent_log())}/{cap} used after {block_no} block(s)")
                log(f"GOAL ACHIEVED — {_weak['detail']}; holding until UTC midnight")
                journal(f"goal achieved: {_weak['detail']} — "
                        "orchestrator: raise the target or stop the engine")
                return 5
        except Exception as e:
            log(f"goal check failed: {e}")
    # Loop exhausted without a send: every slice was all-skipped (content
    # guard) — the engine must not pretend a gate block or a 90s spin; hold
    # like an empty queue until the AI prepares content or drops new leads.
    if block_no == 0:
        log("block: no sendable leads across all slices (content guard) — holding for content prep")
        return 2
    log(f"cycle: {outbound.sent_today(outbound.load_sent_log())}/{cap} used after {block_no} block(s)")
    return 0


def _next_midnight_utc(now) -> float:
    import calendar as _cal
    secs = _cal.timegm((now.year, now.month, now.day, 0, 0, 0)) + 86400
    return secs - now.timestamp()


def _sleep_interruptible(secs: float, chunk: float = 60.0) -> bool:
    """Sleep in chunks so a STOP file halts the engine within ~60s even
    during the long cap/empty/gate holds. Returns False when STOP appears."""
    end = time.time() + secs
    while time.time() < end:
        if stopped():
            log("STOP file present — exiting hold early")
            return False
        time.sleep(min(chunk, max(0.5, end - time.time())))
    return True


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
            if code == 4:
                log("engine stopped by STOP file — exiting cleanly")
                break
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
                if not _sleep_interruptible(wait):
                    break
            elif code == 2:
                # wait quietly for new drops; also re-check staging every 30 min
                if last_hold != "empty":
                    from harness import status as hstatus
                    hstatus.bump("queue-empty", "Queue empty — holding",
                                 "no unsent verified leads; drop new lead files in "
                                 "leads/staging, daemon re-checks every 30 min")
                    journal("queue empty after refill+probe — AI: research/qualify/ingest a new cohort")
                    last_hold = "empty"
                if not _sleep_interruptible(1800):
                    break
            elif code == 3:
                # gate blocked (bounce/spam/delivery breach or data problem):
                # do NOT spin — re-check every 30 min. Self-heal before the
                # hold: refresh metrics + sync-bounces, because bounce
                # suppression only happens after a successful block — a
                # blocked engine would otherwise wait forever for the AI.
                try:
                    subprocess.run([sys.executable, os.path.join(HERE, "outbound.py"),
                                    "metrics", "--force"],
                                   cwd=HERE, capture_output=True, text=True, timeout=300)
                except subprocess.TimeoutExpired:
                    pass
                try:
                    subprocess.run([sys.executable, os.path.join(HERE, "verify.py"),
                                    "sync-bounces"],
                                   cwd=HERE, capture_output=True, text=True, timeout=180)
                except subprocess.TimeoutExpired:
                    pass
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
                if not _sleep_interruptible(1800):
                    break
            elif code == 5:
                # GOAL ACHIEVED — stop sending for the day (owner loop: YES -> stop).
                if last_hold != "goal":
                    from harness import status as hstatus
                    hstatus.bump("goal-met",
                                 "GOAL ACHIEVED — engine holding until midnight",
                                 "primary goal met; orchestrator decides: raise the target or stop")
                    last_hold = "goal"
                if not _sleep_interruptible(_next_midnight_utc(datetime.now(timezone.utc))):
                    break
            elif code == 6:
                # AWAITING APPROVAL — poll quietly until the orchestrator sets
                # engine.json approval (the hook wakes the session on the event).
                if not _sleep_interruptible(120):
                    break
            else:
                last_hold = None  # a batch went through — re-arm the notifier
                if not _sleep_interruptible(90):
                    break
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