"""The loop: a phase state machine over the workflow contract.

Manual cadence (owner rule 2026-08-09): one `run.py once` invocation
advances the loop as far as it can WITHOUT a human — through OBSERVE,
DECIDE, PREPARE, VALIDATE, GATE — and then parks:

  phase review   → awaiting batch approval (`run.py approve`)
  phase evaluate → awaiting the evidence window (time, not human)
  phase hold     → awaiting owner GO (`run.py approve --next`)

Phases and their meaning:

  observe   OBSERVE: filtered, timestamped snapshot -> artifact
  decide    DECIDE: one intervention (or a hold/stop verdict)
  prepare   ACT 1/5: build the batch artifact + human preview
  validate  ACT 2/5: mechanical artifact rules (drop invalid emails)
  gate      ACT 3/5: POLICY hard veto on a FRESH observation
  review    ACT 4/5: human approval of the preview
  execute   ACT 5/5: run the action (paced sends), arm the evidence window
  evaluate  EVALUATE: wait, then MEASURE + LEARN + GOAL CHECK + report
  hold      parked; owner GO starts the next batch cycle
  goal_met  terminal; a new goal in control.json + `reset` starts over

Every step re-loads its inputs from the persisted artifacts — a crash
mid-cycle restarts cleanly from the last completed step.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from . import act, decide as decide_step, evaluate as evaluate_step, hold as hold_step
from . import observe as observe_step, report as report_step, status as status_step
from ..models import Phase


class Loop:
    def __init__(self, ctx):
        self.ctx = ctx
        self.phase = ctx.store.phase()

    # ── helpers ────────────────────────────────────────────────────────────

    def _set(self, phase: str) -> None:
        self.ctx.store.set_phase(phase)
        self.phase = phase

    def _say(self, say, line: str) -> None:
        """One conversational line per step: streamed live to the caller
        (say=print in the CLI) and collected for the final summary."""
        if say:
            say(line)

    def _stopped(self) -> bool:
        return Path(self.ctx.stop_file).exists()

    def _load_artifact(self, path_key: str) -> dict:
        path = self.ctx.store.get_state(path_key)
        if not path or not Path(path).exists():
            raise RuntimeError(f"{path_key} artifact missing ({path})")
        with open(path) as f:
            return json.load(f)

    def _load_batch(self) -> dict:
        batch_id = self.ctx.store.current_batch_id()
        batch = self.ctx.store.get_batch(batch_id) if batch_id else None
        if batch is None:
            raise RuntimeError(f"current batch row missing ({batch_id})")
        return batch

    # ── the machine ────────────────────────────────────────────────────────

    def advance(self, dry: bool = False, say=None) -> dict:
        """Advance the loop as far as it can without a human. `say(line)`
        receives one conversational line per step as it happens."""
        msgs = []
        report_path = None
        self.ctx.artifacts.log(f"advance: entering phase={self.phase} dry={dry}")
        while True:
            phase = self.phase

            if self._stopped():
                self._set(Phase.STOPPED.value)
                self._say(say, "stopped — STOP file present, engine parked.")
                msgs.append("STOP file present — the engine is stopped.")
                msgs.append("  remove it with `python3 -m Outreach clear-stop` to enable `once`.")
                break

            if phase == Phase.OBSERVE.value:
                self._say(say, "observe — reading campaign state…")
                snapshot = observe_step.run(self.ctx)
                cap = snapshot.get("cap", {})
                self._say(say, (
                    f"observe — sent {snapshot.get('totals', {}).get('sent', 0)} total · "
                    f"today {cap.get('sent_today', 0)}/{cap.get('cap', 0)} · "
                    f"queue {snapshot.get('queue', {}).get('size', 0)} · "
                    f"gate ok={bool(snapshot.get('gate', {}).get('ok'))}"))
                self._set(Phase.DECIDE.value)
                continue

            if phase == Phase.DECIDE.value:
                self._say(say, "decide — diagnosing the weakest link…")
                snapshot = self._load_artifact("last_snapshot")
                intervention = decide_step.run(self.ctx, snapshot)
                if intervention is None:
                    hold_step.enter(self.ctx, "no action available — decider returned nothing")
                    self._say(say, "decide — nothing to act on; holding.")
                    self._set(Phase.HOLD.value)
                    continue
                if intervention.get("action") == "hold":
                    hold_step.enter(self.ctx, intervention.get("reason", "hold"),
                                    intervention.get("detail", ""))
                    self._say(say, f"decide — HOLD: {intervention.get('reason') or 'hold'} "
                                   f"({intervention.get('detail', '')})")
                    self._set(Phase.HOLD.value)
                    continue
                if intervention.get("action") == "stop":
                    self.ctx.store.set_hold_reason(intervention.get("reason", "goal reached"))
                    self._say(say, f"decide — STOP: {intervention.get('reason')}")
                    self._set(Phase.GOAL_MET.value)
                    continue
                self._say(say, (
                    f"decide — {intervention.get('action')} · "
                    f"variable={intervention.get('variable') or '—'} · "
                    f"{str(intervention.get('detail'))[:100]}"))
                self._set(Phase.PREPARE.value)
                continue

            if phase == Phase.PREPARE.value:
                intervention = self._load_artifact("last_intervention")
                row = act.prepare(self.ctx, intervention)
                if not row["batch"].get("emails"):
                    reason = row["batch"].get("reason") or "no sendable leads after strict composition"
                    hold_step.enter(self.ctx, reason, "approve --next after fixing the queue")
                    self._say(say, f"prepare — batch {row['id']}: nothing sendable ({reason})")
                    self._set(Phase.HOLD.value)
                    continue
                self._say(say, (
                    f"prepare — batch {row['id']}: {len(row['batch']['emails'])} emails composed, "
                    f"{len(row['batch'].get('skipped', []))} skipped"))
                self._set(Phase.VALIDATE.value)
                continue

            if phase == Phase.VALIDATE.value:
                row = self._load_batch()
                self._say(say, "validate — running mechanical rules on the batch…")
                issues = act.validate(self.ctx, row)
                if issues and row["batch"].get("emails"):
                    issues = act.validate(self.ctx, row)
                self._say(say, (
                    f"validate — {len(row['batch'].get('emails', []))} emails kept "
                    f"after {len(issues)} issue(s) dropped"))
                if not row["batch"].get("emails"):
                    hold_step.enter(self.ctx, "all emails invalidated by validators — batch aborted",
                                    "approve --next after fixing the queue")
                    self._set(Phase.HOLD.value)
                    continue
                self._set(Phase.GATE.value)
                continue

            if phase == Phase.GATE.value:
                guardrails = self._gate_names()
                self._say(say, f"gate — evaluating guardrails: {', '.join(guardrails) or 'policy rules'}…")
                result = act.gate(self.ctx)
                if not result.get("ok"):
                    detail = _gate_detail(result)
                    hold_step.enter(self.ctx, "gate blocked", detail)
                    self._say(say, f"gate — BLOCKED: {detail}")
                    self._set(Phase.HOLD.value)
                    continue
                self._say(say, f"gate — ok, all {len(result.get('guardrails', []))} guardrails within limits")
                self._set(Phase.REVIEW.value)
                continue

            if phase == Phase.REVIEW.value:
                batch = self._load_batch()
                if act.review_ok(self.ctx, batch["id"]):
                    self._say(say, f"review — batch {batch['id']} approved by owner.")
                    self._set(Phase.EXECUTE.value)
                    continue
                self._say(say, f"review — batch {batch['id']} awaiting your approval.")
                msgs.append(f"AWAITING APPROVAL — batch {batch['id']}")
                msgs.append(f"  preview: {batch.get('preview_path', '?')}")
                if dry:
                    msgs.append("  DRY RUN: nothing was sent and no approval was recorded.")
                    msgs.append("  Approve for real with `python3 -m Outreach approve`.")
                else:
                    msgs.append("  Review the preview, then `python3 -m Outreach approve`.")
                break

            if phase == Phase.EXECUTE.value:
                batch = self._load_batch()
                if self._stopped():
                    self._set(Phase.STOPPED.value)
                    msgs.append("STOP file appeared before execute — no sends happened.")
                    break
                if dry:
                    hold_step.enter(self.ctx, "dry run complete — nothing sent",
                                    "approve --next to start a real cycle")
                    self._set(Phase.HOLD.value)
                    continue
                self._say(say, f"execute — sending {len(batch['batch'].get('emails', []))} emails…")
                result = act.execute(self.ctx, batch)
                hours = float(self.ctx.control.goal().get("evidence_window_hours", 48))
                due = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
                self.ctx.store.set_evidence_due(due)
                self._say(say, (
                    f"execute — sent {result.get('sent', 0)}, failed {result.get('failed', 0)}, "
                    f"deduped {result.get('deduped', 0)} · {result.get('note', '')}"))
                report_path = report_step.write_entry(self.ctx, batch, "EXECUTE", result)
                self._say(say, f"report — cycle journal updated: {report_path}")
                msgs.append(f"EXECUTED {batch['id']} — sent {result.get('sent', 0)}, "
                            f"failed {result.get('failed', 0)} · {result.get('note', '')}")
                self._set(Phase.EVALUATE.value)
                continue

            if phase == Phase.EVALUATE.value:
                batch = self._load_batch()
                if evaluate_step.waiting(self.ctx, batch):
                    self._say(say, f"evaluate — waiting for evidence until {evaluate_step.evidence_due(self.ctx)}")
                    msgs.append(f"WAITING FOR EVIDENCE — evaluation opens {evaluate_step.evidence_due(self.ctx)}")
                    msgs.append("  (run `once` again after that timestamp; the loop sleeps meanwhile)")
                    break
                self._say(say, "evaluate — measuring batch against the goal…")
                outcome = evaluate_step.run(self.ctx, batch)
                gc = outcome["goal_check"]
                verdict = outcome.get("verdict") or {}
                report_step.write_entry(self.ctx, batch, "EVALUATE", outcome)
                self._say(say, (
                    f"evaluate — verdict={verdict.get('verdict', '?')} · "
                    f"goal={gc.get('state')}: {gc.get('detail', '')}"))
                if gc.get("state") == "achieved":
                    msgs.append(f"GOAL MET — {gc.get('detail', '')}")
                    msgs.append(f"  report: {outcome.get('report_path', '?')}")
                    self.ctx.store.set_hold_reason(f"goal met: {gc.get('detail', '')}")
                    self._set(Phase.GOAL_MET.value)
                    break
                if gc.get("state") == "blocked":
                    hold_step.enter(self.ctx, "data blocked", gc.get("detail", ""))
                    self._set(Phase.HOLD.value)
                    continue
                hold_step.enter(self.ctx, "awaiting owner GO for the next batch",
                                f"{gc.get('detail', '')} · report: {outcome.get('report_path', '?')}")
                self._set(Phase.HOLD.value)
                continue

            if phase == Phase.HOLD.value:
                if self.ctx.control.next_approved():
                    self.ctx.control.clear_next()
                    self.ctx.store.set_hold_reason(None)
                    self._say(say, "hold — owner GO received; starting the next batch cycle.")
                    msgs.append("OWNER GO — starting the next batch cycle.")
                    self._set(Phase.OBSERVE.value)
                    continue
                reason = self.ctx.store.hold_reason() or "parked"
                self._say(say, f"hold — {reason}")
                msgs.append(f"HOLD — {reason}")
                msgs.append("  release with `python3 -m Outreach approve --next`.")
                break

            if phase == Phase.GOAL_MET.value:
                self._say(say, f"goal met — {self.ctx.store.hold_reason() or ''}")
                msgs.append(f"GOAL MET — {self.ctx.store.hold_reason() or ''}")
                msgs.append("  set a new goal in data/control.json, then `python3 -m Outreach reset`.")
                break

            if phase == Phase.STOPPED.value:
                self._say(say, "stopped — clear STOP then run `once` to resume.")
                msgs.append("STOPPED — `clear-stop` then `once` to resume.")
                break

            msgs.append(f"UNKNOWN PHASE {phase!r} — inspect data/engine.sqlite (engine_state).")
            break

        status_step.write(self.ctx)
        return {"msgs": msgs, "phase": self.phase, "report_path": report_path}

    def _gate_names(self) -> list:
        """Guardrail names for the conversational gate line (local read of
        the last snapshot; empty on failure — the gate still runs fresh)."""
        try:
            snapshot_path = self.ctx.store.last_snapshot_path()
            if snapshot_path and Path(snapshot_path).exists():
                with open(snapshot_path) as f:
                    return [g.get("name") for g in
                            (json.load(f).get("meta") or {}).get("guardrails", [])]
        except Exception:
            pass
        return []


def _gate_detail(result: dict) -> str:
    parts = [f"{b.get('name')} {b.get('current', 0)*100:.2f}% > {b.get('max', 0)*100:.2f}%"
             for b in result.get("breaches", [])]
    parts += list(result.get("problems", []))
    return "; ".join(parts) or "policy gate not ok"


from datetime import timedelta  # noqa: E402
