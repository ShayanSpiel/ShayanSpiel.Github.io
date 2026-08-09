#!/usr/bin/env python3
"""batch_hook.py — wakes the AI orchestrator session when the engine has
something to act on.

Event-driven cadence (owner rule 2026-08-08): after each batch cycle AND after
the daily cap is reached, the hook posts a compact event message into the
CURRENT opencode session via the local V2 server API
(POST /api/session/{id}/prompt). The orchestrator (the session) then observes,
hypothesizes, tweaks, and runs the next batch — no polling, no stale waiting.

Triggers (deduped by a persistent offset; one wake per event):
  1. "BATCH COMPLETE" line followed by a "cycle:" line  -> batch done + analyzed
  2. "daily cap done" line                               -> day-end planning event

Runs outside any agent sandbox (launchd com.spielos.outbound.hook, or
`nohup python3 batch_hook.py` from a normal terminal). If the session id file
is missing (no session open), the event is journaled for the next session.

Kill switch: exits within 60s of a STOP file appearing (see stop.sh).
"""

import json
import os
import subprocess
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUTBOUND_DIR = os.path.dirname(HERE)
PIPELINE_LOG = os.path.join(HERE, "experiments", "auto", "pipeline.log")
OFFSET_FILE = os.path.join(HERE, "experiments", "auto", "hook_offset")
JOURNAL = os.path.join(OUTBOUND_DIR, "orchestration", "journal.md")
SESSION_FILE = os.path.join(OUTBOUND_DIR, "orchestration", "session.txt")
HOOK_LOG = os.path.join(HERE, "experiments", "auto", "hook.log")
STOP_FILE = os.path.join(HERE, "STOP")

POLL_SECONDS = 60
WAKE_RETRIES = 3
WAKE_RETRY_DELAY = 15


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}  {msg}"
    print(line, flush=True)
    with open(HOOK_LOG, "a") as f:
        f.write(line + "\n")


def journal(msg: str) -> None:
    os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(JOURNAL, "a") as f:
        f.write(f"\n- **{ts} — HOOK → AI:** {msg}\n")


def _line_pos(lines, i):
    return sum(len(l) + 1 for l in lines[:i])


def _events_since(offset: int, text: str) -> tuple:
    """Scan new log content; return (event, new_offset) where event is one of
    "batch" | "cap" | "approval" | None — the FIRST complete event after the
    offset."""
    lines = text.splitlines()
    last_complete = None
    for i, ln in enumerate(lines):
        pos = _line_pos(lines, i)
        if pos <= offset:
            continue
        if "BATCH COMPLETE" in ln:
            last_complete = i
        elif "cycle:" in ln and last_complete is not None and i > last_complete:
            last_complete = None
            return "batch", pos
        elif "daily cap done" in ln:
            return "cap", pos
        elif "AWAITING APPROVAL" in ln:
            return "approval", pos
    return None, max(0, len(text))


def _last_line(text: str, needle: str) -> str:
    for ln in reversed(text.splitlines()):
        if needle in ln:
            return ln.strip()
    return ""


def wake_session(event: str, text: str) -> None:
    if not os.path.exists(SESSION_FILE):
        journal(f"{event} event fired but no session file at {SESSION_FILE} — orchestrator not reachable")
        log("no session file — journaled only")
        return
    sid = open(SESSION_FILE).read().strip()
    if not sid:
        return
    if event == "approval":
        line = _last_line(text, "AWAITING APPROVAL")
        prompt = (
            f"EVENT from the outbound engine: {line.strip()} "
            "You are the orchestrator in your own session. A batch is BUILT and "
            "PAUSED waiting for your content review — nothing was sent. Read the "
            "preview file named in the line and QA every email (real workflow "
            "named, per-lead hook, no generic filler, no links outside the "
            "signature). Then set engine.json {\"approval\": {\"experiment\": "
            "<the CURRENT experiment string verbatim>, \"approved\": true, "
            "\"by\": \"orchestrator\", \"note\": \"...\"}} to greenlight the "
            "send, or touch the STOP file if the copy is bad. Reply briefly "
            "with your verdict."
        )
    elif event == "cap":
        line = _last_line(text, "daily cap done")
        prompt = (
            f"EVENT from the outbound engine: DAY-END — {line.strip()} "
            "You are the orchestrator in your own session. This is the daily "
            "planning event: review today's batches and metrics in the journal "
            "and metrics.json, decide tomorrow's experiment, write the knobs to "
            "experiments/auto/engine.json if needed, and journal your decision. "
            "Reply briefly with the decision."
        )
    else:
        batch = _last_line(text, "BATCH COMPLETE")
        cycle = _last_line(text, "cycle:")
        prompt = (
            f"EVENT from the outbound engine: {batch.strip()} | {cycle.strip()} "
            "You are the orchestrator in your own session. Do the post-batch "
            "routine: observe metrics/queue/journal, update the orchestration "
            "journal, decide and apply any tweaks (engine.json / harness state), "
            "then ensure the next batch runs. Reply briefly with your "
            "observation and next action."
        )
    for attempt in range(1, WAKE_RETRIES + 1):
        try:
            r = subprocess.run(
                ["opencode2", "api", "post", f"/api/session/{sid}/prompt",
                 "--data", json.dumps({"text": prompt})],
                capture_output=True, text=True, timeout=120,
            )
            if r.returncode == 0:
                log(f"wake OK ({event}) attempt {attempt} — {r.stdout[-200:] if r.stdout else ''}")
                return
            log(f"wake attempt {attempt}/{WAKE_RETRIES} failed (exit {r.returncode}) — "
                f"{r.stderr[-150:] if r.stderr else r.stdout[-150:] if r.stdout else ''}")
        except Exception as e:
            log(f"wake attempt {attempt}/{WAKE_RETRIES} error: {e}")
        time.sleep(WAKE_RETRY_DELAY)
    journal(f"wake failed after {WAKE_RETRIES} attempts ({event}) — next session should process the pending marker")


def main() -> None:
    offset = 0
    if os.path.exists(OFFSET_FILE):
        try:
            offset = int(open(OFFSET_FILE).read().strip())
        except ValueError:
            offset = 0
    else:
        # First boot: seed to the end of the log so the hook only wakes on
        # events that happen AFTER it starts (owner rule 2026-08-08: with
        # offset 0 it replayed the whole history — one wake per past batch).
        try:
            with open(PIPELINE_LOG) as f:
                offset = len(f.read())
            log(f"first boot — seeded offset to end of log ({offset})")
        except OSError:
            offset = 0
    log(f"hook up (offset {offset}, poll {POLL_SECONDS}s, STOP-aware)")
    while True:
        try:
            if os.path.exists(STOP_FILE):
                log("STOP file present — hook exiting")
                return
            with open(PIPELINE_LOG) as f:
                text = f.read()
            event, new_offset = _events_since(offset, text)
            if event:
                wake_session(event, text)
            offset = new_offset
            with open(OFFSET_FILE, "w") as f:
                f.write(str(offset))
        except Exception as e:
            log(f"poll error: {e}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
