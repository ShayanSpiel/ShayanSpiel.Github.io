import importlib.util
import io
import json
import os
import sqlite3
import subprocess
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout, contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from company.runtime.director import Director
from company.departments.outbound.email_workflow import EmailWorkflow, outbound_context
from company.runtime.system_improvement import SystemImprovement
from company.runtime.models import GoalHandler, GoalContext, Goal, GoalStatus, RunStatus, Stage, StageResult
from company.runtime.runner import Runner
from company.runtime.service import RunnerService
from company.runtime.store import Store
from company.runtime.loop import (Runtime, _completed_failed_runs, _env_file_value,
                                  _live_fingerprint, _live_push_gate)
from company.__main__ import main, render_report


class ApprovalHandler(GoalHandler):
    id = "approval_test"

    def observe(self, ctx):
        return StageResult("collect", {"real": True})

    def decide(self, ctx, observation):
        return StageResult("diagnose", {"action": "test", "observation": observation})

    def act(self, ctx, decision):
        if ctx.approval_status("execute") != "approved":
            return StageResult("review", {"prepared": True}, RunStatus.AWAITING_APPROVAL, Stage.ACT)
        return StageResult("execute", {"executed": True})

    def evaluate(self, ctx, action_result):
        return StageResult("goal_check", {"goal_met": action_result.get("executed")},
                           RunStatus.IDLE, goal_status=GoalStatus.ACHIEVED)


class ImmediateHandler(GoalHandler):
    id = "immediate_test"

    def observe(self, ctx):
        return StageResult("collect", {"ok": True})

    def decide(self, ctx, observation):
        return StageResult("diagnose", {"action": "finish"})

    def act(self, ctx, decision):
        return StageResult("execute", {"done": True})

    def evaluate(self, ctx, action_result):
        return StageResult("goal_check", {"done": True}, RunStatus.IDLE,
                           goal_status=GoalStatus.ACHIEVED,
                           learnings=[{"claim": "Immediate action worked", "evidence": {"done": True},
                                       "confidence": 1.0}])


class IterativeHandler(GoalHandler):
    id = "iterative_test"

    def observe(self, ctx):
        return StageResult("collect", {"sequence": ctx.cycle["sequence"]})

    def decide(self, ctx, observation):
        return StageResult("diagnose", {"action": "sample", **observation})

    def act(self, ctx, decision):
        return StageResult("execute", {"sample": decision["sequence"]})

    def evaluate(self, ctx, action_result):
        experiment = {"action": "sample_again", "change_one_variable": "sample"}
        return StageResult("goal_check", {"score": 0.2}, RunStatus.COMPLETED,
                           evaluation={"verdict": "continue", "goal_met": False,
                                       "metrics": {"score": 0.2}, "validity": "business",
                                       "next_experiment": experiment},
                           next_run={"run_type": "business_experiment",
                                     "changed_variables": {"sample": "next"}})


class RuntimeTests(unittest.TestCase):
    def runtime(self, registry):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        return Runtime(Path(self.temp.name) / "state.sqlite", registry)

    def test_stage_step_and_status_are_independent(self):
        runtime = self.runtime({"approval_test": ApprovalHandler()})
        goal = runtime.create_goal(name="Approval", owner_id="approval_test", metric="done",
                                   operator="eq", target=True, config={})
        parked = runtime.once(goal["id"])
        self.assertEqual(parked["cycle"]["stage"], "ACT")
        self.assertEqual(parked["cycle"]["step"], "review")
        self.assertEqual(parked["cycle"]["run_status"], "awaiting_approval")
        runtime.approve(goal["id"])
        complete = runtime.once(goal["id"])
        self.assertEqual(complete["goal"]["goal_status"], "achieved")
        self.assertEqual(complete["cycle"]["stage"], "OBSERVE")

    def test_unapproved_action_never_executes(self):
        runtime = self.runtime({"approval_test": ApprovalHandler()})
        goal = runtime.create_goal(name="Safe", owner_id="approval_test", metric="done",
                                   operator="eq", target=True, config={})
        first = runtime.once(goal["id"])
        second = runtime.once(goal["id"])
        self.assertEqual(first["cycle"]["data"], second["cycle"]["data"])
        self.assertEqual(len(runtime.store.events(goal["id"])), 4)

    def test_expired_goal_never_runs(self):
        runtime = self.runtime({"immediate_test": ImmediateHandler()})
        goal = runtime.create_goal(name="Expired", owner_id="immediate_test", metric="done",
                                   operator="eq", target=True, deadline="2000-01-01T00:00:00Z", config={})
        result = runtime.once(goal["id"])
        self.assertEqual(result["goal"]["goal_status"], "expired")
        self.assertEqual(result["cycle"]["stage"], "OBSERVE")

    def test_lease_prevents_two_clients_running_same_goal(self):
        runtime = self.runtime({"immediate_test": ImmediateHandler()})
        goal = runtime.create_goal(name="Exclusive", owner_id="immediate_test", metric="done",
                                   operator="eq", target=True, config={})
        self.assertTrue(runtime.store.acquire(goal["id"], "opencode"))
        with self.assertRaisesRegex(RuntimeError, "already running"):
            runtime.once(goal["id"], holder="codex")
        runtime.store.release(goal["id"], "opencode")

    def test_completed_run_parks_until_explicit_next(self):
        runtime = self.runtime({"iterative_test": IterativeHandler()})
        goal = runtime.create_goal(name="Improve score", owner_id="iterative_test",
                                   metric="score", operator="ge", target=0.8,
                                   run_type="business_experiment", config={})
        completed = runtime.once(goal["id"])
        self.assertEqual(completed["cycle"]["run_status"], "completed")
        self.assertEqual(completed["cycle"]["sequence"], 1)
        self.assertEqual(runtime.once(goal["id"])["cycle"]["sequence"], 1)
        notes = runtime.store.notifications("pending")
        self.assertEqual([note["kind"] for note in notes], ["run_completed"])
        self.assertEqual(notes[0]["payload"]["required_user_action"],
                         "Ask the Director to start the proposed next run")

        started = runtime.next(goal["id"])
        self.assertEqual(started["cycle"]["sequence"], 2)
        self.assertEqual(started["cycle"]["run_status"], "idle")
        self.assertEqual(started["run"]["changed_variables"], {"sample": "next"})

    def test_email_shortfall_emits_typed_director_action(self):
        runtime = self.runtime({"email": EmailWorkflow()})
        goal = runtime.create_goal(name="Email batch", owner_id="email", metric="reply_rate",
                                   operator="ge", target=0.3, run_type="business_experiment",
                                   config={"execution_mode": "dry_run", "batch_size": 10})
        fake = SimpleNamespace(
            stop_file=Path(self.temp.name) / "STOP",
            workflow=SimpleNamespace(observe=lambda _ctx: {"queue": {"size": 3}}),
            control=SimpleNamespace(knobs=lambda: {"block_size": 10,
                                                   "cohort_filters": {"min_tier": "Verified"}}),
        )
        with patch("company.departments.outbound.email_workflow.outbound_context", return_value=fake):
            blocked = runtime.once(goal["id"])
        self.assertEqual(blocked["cycle"]["run_status"], "blocked")
        self.assertEqual(blocked["cycle"]["data"]["decision"]["needed_leads"], 7)
        note = runtime.store.notifications("pending")[0]
        self.assertEqual(note["kind"], "action_required")
        self.assertEqual(note["payload"]["attention"]["capability"], "lead_research")
        self.assertIn("company retry", note["payload"]["next_trigger"])

    def test_director_dispatches_child_and_completes(self):
        runtime = self.runtime({"director": Director(), "immediate_test": ImmediateHandler()})
        parent = runtime.create_goal(name="Company outcome", owner_id="director",
                                     metric="all_children_achieved", operator="eq", target=True, config={})
        child = runtime.create_goal(name="Child outcome", owner_id="immediate_test", metric="done",
                                    operator="eq", target=True, parent_id=parent["id"], config={})
        result = runtime.once(parent["id"])
        self.assertEqual(runtime.status(child["id"])["goal"]["goal_status"], "achieved")
        self.assertEqual(result["goal"]["goal_status"], "achieved")
        self.assertEqual(runtime.store.memories("immediate_test", child["id"])[0]["claim"],
                         "Immediate action worked")

    def test_director_surfaces_child_approval_without_approving_it(self):
        runtime = self.runtime({"director": Director(), "approval_test": ApprovalHandler()})
        parent = runtime.create_goal(name="Company outcome", owner_id="director",
                                     metric="all_children_achieved", operator="eq", target=True, config={})
        child = runtime.create_goal(name="Guarded child", owner_id="approval_test", metric="done",
                                    operator="eq", target=True, parent_id=parent["id"], config={})
        runtime.once(parent["id"])
        blocked = runtime.once(parent["id"])
        self.assertEqual(blocked["cycle"]["run_status"], "waiting")
        self.assertEqual(runtime.status(child["id"])["cycle"]["run_status"], "awaiting_approval")
        runtime.approve(child["id"])
        runtime.once(child["id"])
        complete = runtime.once(parent["id"])
        self.assertEqual(complete["goal"]["goal_status"], "achieved")

    def test_email_bridge_loads_existing_engine_without_running_it(self):
        context = outbound_context(dry=True)
        self.assertEqual(EmailWorkflow.id, "email")
        self.assertEqual(context.workflow.name, "email")

    def test_email_bridge_honors_existing_stop_switch(self):
        with tempfile.TemporaryDirectory() as directory:
            stop = Path(directory) / "STOP"
            stop.touch()
            goal = Goal("g", "Email", "email", "reply_rate", "ge", 0.3, None, None,
                        "active", {"execution_mode": "dry_run"})
            context = GoalContext(goal, {"data": {}}, (), lambda key: None)
            with patch("company.departments.outbound.email_workflow.outbound_context", return_value=SimpleNamespace(stop_file=stop)):
                result = EmailWorkflow().observe(context)
            self.assertEqual(result.run_status, RunStatus.BLOCKED)
            self.assertEqual(result.next_stage, Stage.OBSERVE)

    def test_email_bridge_dry_run_still_requires_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            stop = Path(directory) / "STOP"
            row = {"id": "batch-1", "batch": {"emails": [{"lead_id": "lead-1"}]},
                   "preview_path": "/tmp/preview.md"}
            outbound = SimpleNamespace(stop_file=stop, store=SimpleNamespace(get_batch=lambda batch_id: row))
            goal = Goal("g", "Email", "email", "reply_rate", "ge", 0.3, None, None,
                        "active", {"execution_mode": "dry_run"})
            first_ctx = GoalContext(goal, {"data": {}}, (), lambda key: None)
            with patch("company.departments.outbound.email_workflow.outbound_context", return_value=outbound), \
                 patch("company.departments.outbound.execution.prepare", return_value=row), \
                 patch("company.departments.outbound.execution.validate", return_value=[]), \
                 patch("company.departments.outbound.execution.gate", return_value={"ok": True}):
                parked = EmailWorkflow().act(first_ctx, {"action": "prepare_batch"})
            self.assertEqual(parked.run_status, RunStatus.AWAITING_APPROVAL)

            second_ctx = GoalContext(goal, {"data": {"action_result": parked.payload}}, (),
                                       lambda key: "approved")
            with patch("company.departments.outbound.email_workflow.outbound_context", return_value=outbound), \
                 patch("company.departments.outbound.execution.execute", return_value={"sent": 0, "note": "dry"}) as execute:
                result = EmailWorkflow().act(second_ctx, {"action": "prepare_batch"})
            execute.assert_called_once_with(outbound, row, dry=True)
            self.assertEqual(result.run_status, RunStatus.WAITING)
            self.assertEqual(result.next_stage, Stage.EVALUATE)

    def test_live_business_reply_goal_requires_observable_capture(self):
        goal = Goal("g", "Replies", "email", "reply_rate", "ge", 0.3, None, None,
                    "active", {"execution_mode": "live", "evidence_window_hours": 48})
        context = GoalContext(goal, {"data": {}}, (), lambda key: None)
        result = EmailWorkflow().act(context, {"action": "prepare_batch"})
        self.assertEqual(result.run_status, RunStatus.BLOCKED)
        self.assertEqual(result.attention["capability"], "inbound_email_setup")
        self.assertIn("reply evidence source", result.payload["reason"])

    def test_typed_run_preserves_hypothesis_variables_and_version(self):
        runtime = self.runtime({"immediate_test": ImmediateHandler()})
        goal = runtime.create_goal(
            name="Typed", owner_id="immediate_test", metric="done", operator="eq", target=True,
            run_type="business_experiment", evidence_validity="business",
            hypothesis={"statement": "Changing X improves Y", "variable": "x", "prediction": "Y rises"},
            controlled_variables={"offer": "fixed"}, changed_variables={"x": "variant-b"}, config={})
        state = runtime.status(goal["id"])
        self.assertEqual(state["run"]["run_type"], "business_experiment")
        self.assertEqual(state["run"]["owner_version"], "1.0.0")
        self.assertEqual(state["run"]["controlled_variables"], {"offer": "fixed"})
        self.assertTrue(state["run"]["hypothesis_id"].startswith("hyp-"))

    def test_system_improvement_requires_approval_then_versions_result(self):
        runtime = self.runtime({"system-improvement": SystemImprovement()})
        goal = runtime.create_goal(
            name="Repair sender", owner_id="system-improvement",
            metric="acceptance_tests_passed", operator="eq", target=True,
            run_type="system_improvement", evidence_validity="technical_only", config={
                "owner_id": "email", "from_version": "2.0.0", "target_version": "2.0.1",
                "problem": "provider result mapping is wrong", "allowed_files": ["email.py"],
                "acceptance_tests": ["python -m unittest"], "originating_run_id": "run-origin"})
        parked = runtime.once(goal["id"])
        self.assertEqual(parked["cycle"]["run_status"], "awaiting_approval")
        runtime.approve(goal["id"])
        blocked = runtime.once(goal["id"])
        self.assertEqual(blocked["cycle"]["step"], "execute_change")
        task = blocked["change_tasks"][0]
        runtime.complete_change(task["id"], passed=True,
                                result={"passed": True, "commands": ["python -m unittest"]})
        complete = runtime.once(goal["id"])
        self.assertEqual(complete["goal"]["goal_status"], "achieved")
        versions = runtime.store.owner_versions("email")
        self.assertEqual(versions[-1]["version"], "2.0.1")

    def test_test_inbox_batch_prepares_without_sending(self):
        runtime = self.runtime({"email": EmailWorkflow()})
        goal = runtime.create_goal(name="Test replies", owner_id="email", metric="reply_rate",
                                   operator="ge", target=0.3, run_type="system_test",
                                   evidence_validity="technical_only", config={
                                       "audience_type": "test_inbox", "execution_mode": "live",
                                       "test_recipients": ["one@example.com", "two@example.com"],
                                       "throttle_seconds": 0, "evidence_window_hours": 24,
                                       "reply_capture": "manual_inbox"})
        with patch("company.departments.outbound.email_workflow._write_test_preview", return_value=Path("/tmp/preview.md")):
            parked = runtime.once(goal["id"])
        self.assertEqual(parked["cycle"]["run_status"], "awaiting_approval")
        self.assertEqual(parked["cycle"]["step"], "review")
        self.assertEqual(parked["cycle"]["data"]["action_result"]["recipients"],
                         ["one@example.com", "two@example.com"])

    def test_four_inbox_flow_wakes_at_two_replies_and_achieves_goal(self):
        runtime = self.runtime({"email": EmailWorkflow()})
        recipients = [f"test-{index}@example.com" for index in range(4)]
        goal = runtime.create_goal(name="Four inboxes", owner_id="email", metric="reply_rate",
                                   operator="ge", target=0.3, run_type="system_test",
                                   evidence_validity="technical_only", config={
                                       "audience_type": "test_inbox", "execution_mode": "live",
                                       "test_recipients": recipients, "throttle_seconds": 0,
                                       "evidence_window_hours": 24,
                                       "reply_capture": "manual_inbox"})
        with patch("company.departments.outbound.email_workflow._write_test_preview", return_value=Path("/tmp/preview.md")):
            runtime.once(goal["id"])
        runtime.approve(goal["id"])
        with patch("company.departments.outbound.workflows.email.providers.send_email",
                   side_effect=[{"id": f"provider-{index}"} for index in range(4)]):
            waiting = runtime.once(goal["id"])
        self.assertEqual(waiting["cycle"]["run_status"], "waiting")
        self.assertEqual(len([item for item in waiting["evidence"] if item["kind"] == "email_sent"]), 4)
        runtime.add_evidence(goal["id"], kind="reply", source="test",
                             payload={"recipient": recipients[0]}, validity="technical_only")
        one_reply = runtime.status(goal["id"])
        self.assertGreater(one_reply["cycle"]["resume_at"], datetime.now(timezone.utc).isoformat())
        runtime.add_evidence(goal["id"], kind="reply", source="test",
                             payload={"recipient": recipients[1]}, validity="technical_only")
        with patch("company.departments.outbound.email_workflow._observe_test_provider", return_value=[]):
            complete = runtime.once(goal["id"])
        self.assertEqual(complete["goal"]["goal_status"], "achieved")
        self.assertEqual(complete["evaluation"]["metrics"]["reply_rate"], 0.5)

    def test_email_run_completes_reports_and_waits_for_next_run_approval(self):
        runtime = self.runtime({"email": EmailWorkflow()})
        recipients = [f"loop-{index}@example.com" for index in range(4)]
        goal = runtime.create_goal(name="Improve replies", owner_id="email", metric="reply_rate",
                                   operator="ge", target=0.3, run_type="system_test",
                                   evidence_validity="technical_only", config={
                                       "audience_type": "test_inbox", "execution_mode": "live",
                                       "test_recipients": recipients, "throttle_seconds": 0,
                                       "evidence_window_hours": 0,
                                       "reply_capture": "manual_inbox"})
        with patch("company.departments.outbound.email_workflow._write_test_preview", return_value=Path("/tmp/preview.md")):
            runtime.once(goal["id"])
        runtime.approve(goal["id"])
        with patch("company.departments.outbound.workflows.email.providers.send_email",
                   side_effect=[{"id": f"provider-{index}"} for index in range(4)]), \
             patch("company.departments.outbound.email_workflow._observe_test_provider", return_value=[]):
            Runner(runtime).tick(goal["id"])

        completed = runtime.status(goal["id"])
        self.assertEqual(completed["goal"]["goal_status"], "active")
        self.assertEqual(completed["cycle"]["run_status"], "completed")
        self.assertEqual(completed["evaluation"]["verdict"], "not_yet")
        self.assertEqual(completed["evaluation"]["next_experiment"]["change_one_variable"],
                         "test_token")
        self.assertIn("Proposed next run", render_report(completed))
        self.assertIn("run_completed",
                      {item["kind"] for item in runtime.store.notifications("pending")})

        runtime.next(goal["id"])
        with patch("company.departments.outbound.email_workflow._write_test_preview", return_value=Path("/tmp/preview-2.md")):
            Runner(runtime).tick(goal["id"])
        next_state = runtime.status(goal["id"])
        self.assertEqual(next_state["cycle"]["sequence"], 2)
        self.assertEqual(next_state["cycle"]["run_status"], "awaiting_approval")
        self.assertEqual(next_state["run"]["changed_variables"], {"test_token": "new_run_token"})

    def test_resend_observer_imports_opens_and_replies_then_achieves_goal(self):
        runtime = self.runtime({"email": EmailWorkflow()})
        recipients = [f"auto-{index}@example.com" for index in range(4)]
        goal = runtime.create_goal(name="Automatic replies", owner_id="email", metric="reply_rate",
                                   operator="ge", target=0.3, run_type="system_test",
                                   evidence_validity="technical_only", config={
                                       "audience_type": "test_inbox", "execution_mode": "live",
                                       "provider": "resend", "test_recipients": recipients,
                                       "throttle_seconds": 0, "evidence_window_hours": 24,
                                       "observer_interval_seconds": 300,
                                       "reply_capture": "resend_inbound"})
        with patch("company.departments.outbound.email_workflow._write_test_preview", return_value=Path("/tmp/preview.md")):
            runtime.once(goal["id"])
        runtime.approve(goal["id"])
        with patch("company.departments.outbound.workflows.email.config.REPLY_TO", "runs@reply.example.com"), \
             patch("company.departments.outbound.workflows.email.providers.receiving_domain_status",
                   return_value={"ready": True, "domain": "reply.example.com"}), \
             patch("company.departments.outbound.workflows.email.providers.send_email_via",
                   side_effect=[{"id": f"resend-{index}"} for index in range(4)]):
            waiting = runtime.once(goal["id"])
        action = waiting["cycle"]["data"]["action_result"]
        runtime.store.update_cycle(waiting["cycle"]["id"], stage="EVALUATE", step="measure",
                                   run_status="waiting", resume_at=datetime.now(timezone.utc).isoformat(),
                                   data=waiting["cycle"]["data"])
        received = [{"id": f"received-{index}", "from": recipients[index],
                     "subject": f"Re: {action['subject']}",
                     "created_at": datetime.now(timezone.utc).isoformat()}
                    for index in range(2)]
        with patch("company.departments.outbound.workflows.email.providers.fetch_email_status",
                   return_value={"last_event": "opened"}), \
             patch("company.departments.outbound.workflows.email.providers.list_received_emails",
                   return_value={"data": received}):
            complete = runtime.once(goal["id"])
        self.assertEqual(complete["goal"]["goal_status"], "achieved")
        self.assertEqual(complete["evaluation"]["metrics"]["reply_rate"], 0.5)
        self.assertEqual(complete["evaluation"]["metrics"]["automatic_replies"], 2)
        kinds = [item["kind"] for item in complete["evidence"]]
        self.assertEqual(kinds.count("email_opened"), 4)
        self.assertEqual(kinds.count("reply"), 2)

    def test_resend_inbound_mode_blocks_without_reply_to(self):
        runtime = self.runtime({"email": EmailWorkflow()})
        goal = runtime.create_goal(name="Missing inbound", owner_id="email", metric="reply_rate",
                                   operator="ge", target=0.3, run_type="system_test",
                                   evidence_validity="technical_only", config={
                                       "audience_type": "test_inbox", "execution_mode": "live",
                                       "provider": "resend", "test_recipients": ["one@example.com"],
                                       "throttle_seconds": 0, "evidence_window_hours": 24,
                                       "reply_capture": "resend_inbound"})
        with patch("company.departments.outbound.email_workflow._write_test_preview", return_value=Path("/tmp/preview.md")):
            runtime.once(goal["id"])
        runtime.approve(goal["id"])
        with patch("company.departments.outbound.workflows.email.config.REPLY_TO", ""):
            blocked = runtime.once(goal["id"])
        self.assertEqual(blocked["cycle"]["run_status"], "blocked")
        self.assertIn("REPLY_TO", blocked["cycle"]["data"]["action_result"]["error"])

    def test_event_only_waiting_does_not_advance_without_wake(self):
        runtime = self.runtime({"director": Director(), "approval_test": ApprovalHandler()})
        parent = runtime.create_goal(name="Company outcome", owner_id="director",
                                     metric="all_children_achieved", operator="eq", target=True, config={})
        runtime.create_goal(name="Guarded child", owner_id="approval_test", metric="done",
                            operator="eq", target=True, parent_id=parent["id"], config={})
        runtime.once(parent["id"])
        waiting = runtime.once(parent["id"])
        self.assertEqual(waiting["cycle"]["run_status"], "waiting")
        self.assertIsNone(waiting["cycle"]["resume_at"])
        unchanged = runtime.once(parent["id"])
        self.assertEqual(unchanged["cycle"], waiting["cycle"])

    def test_runner_continues_child_evaluation_and_parent_goal(self):
        runtime = self.runtime({"director": Director(), "email": EmailWorkflow()})
        parent = runtime.create_goal(name="Reply outcome", owner_id="director",
                                     metric="reply_rate", operator="ge", target=0.3,
                                     evidence_validity="technical_only",
                                     config={"accepted_evidence_validity": ["technical_only"]})
        recipients = [f"runner-{index}@example.com" for index in range(4)]
        child = runtime.create_goal(name="Email child", owner_id="email", metric="reply_rate",
                                    operator="ge", target=0.3, parent_id=parent["id"],
                                    run_type="system_test", evidence_validity="technical_only", config={
                                        "audience_type": "test_inbox", "execution_mode": "live",
                                        "test_recipients": recipients, "throttle_seconds": 0,
                                        "evidence_window_hours": 24,
                                        "reply_capture": "manual_inbox"})
        runner = Runner(runtime)
        with patch("company.departments.outbound.email_workflow._write_test_preview", return_value=Path("/tmp/preview.md")):
            runner.tick(parent["id"])
        self.assertEqual(runtime.status(child["id"])["cycle"]["run_status"], "awaiting_approval")
        self.assertEqual(runtime.status(parent["id"])["cycle"]["run_status"], "waiting")

        runtime.approve(child["id"])
        with patch("company.departments.outbound.workflows.email.providers.send_email",
                   side_effect=[{"id": f"runner-provider-{index}"} for index in range(4)]):
            runner.tick(parent["id"])
        self.assertEqual(runtime.status(child["id"])["cycle"]["run_status"], "waiting")

        for recipient in recipients[:2]:
            runtime.add_evidence(child["id"], kind="reply", source="test",
                                 payload={"recipient": recipient}, validity="technical_only")
        with patch("company.departments.outbound.email_workflow._observe_test_provider", return_value=[]):
            outcome = runner.tick(child["id"])
        self.assertTrue(outcome["advanced"])
        self.assertEqual(runtime.status(child["id"])["goal"]["goal_status"], "achieved")
        self.assertEqual(runtime.status(parent["id"])["goal"]["goal_status"], "achieved")
        kinds = {item["kind"] for item in runtime.store.notifications("pending")}
        self.assertIn("goal_achieved", kinds)

    def test_new_department_task_requires_and_persists_department_spec(self):
        runtime = self.runtime({"system-improvement": SystemImprovement()})
        invalid = runtime.create_goal(
            name="Build Content Department", owner_id="system-improvement",
            metric="acceptance_tests_passed", operator="eq", target=True,
            run_type="system_improvement", evidence_validity="technical_only", config={
                "change_kind": "create_department", "owner_id": "content",
                "from_version": "new", "target_version": "1.0.0",
                "problem": "Create content distribution capability",
                "allowed_files": [".agents/company/departments/content/department.py"],
                "acceptance_tests": ["python -m unittest"]})
        blocked = runtime.once(invalid["id"])
        self.assertIn("department_spec", blocked["cycle"]["data"]["decision"]["missing"])

        valid = runtime.create_goal(
            name="Build Content Department", owner_id="system-improvement",
            metric="acceptance_tests_passed", operator="eq", target=True,
            run_type="system_improvement", evidence_validity="technical_only", config={
                "change_kind": "create_department", "owner_id": "content",
                "from_version": "new", "target_version": "1.0.0",
                "problem": "Create content distribution capability",
                "allowed_files": [".agents/company/departments/content/department.py"],
                "acceptance_tests": ["python -m unittest"],
                "department_spec": {"purpose": "distribute content", "metrics": ["qualified_views"],
                                "external_actions": ["publish"], "approval_points": ["publish"],
                                "evidence_sources": ["analytics"]}})
        parked = runtime.once(valid["id"])
        task = parked["change_tasks"][0]
        self.assertEqual(task["change_kind"], "create_department")
        self.assertEqual(task["specification"]["purpose"], "distribute content")


class DirectorIdentityContractTests(unittest.TestCase):
    def test_opencode_director_is_not_generic_build_agent(self):
        root = Path(__file__).resolve().parents[3]
        prompt = (root / ".opencode/agents/director.md").read_text()
        self.assertIn("You are the operating Director of SpielOS", prompt)
        self.assertIn("must never introduce yourself as a coding or website assistant", prompt)
        self.assertIn("reports do not require a new goal", prompt)
        self.assertIn("permissions:", prompt)
        self.assertIn("- action: edit", prompt)
        self.assertIn("effect: deny", prompt)
        self.assertIn("- action: shell", prompt)
        self.assertIn("effect: allow", prompt)

    def test_codex_director_has_same_identity_boundary(self):
        root = Path(__file__).resolve().parents[3]
        prompt = (root / ".codex/agents/director.toml").read_text()
        self.assertIn("You are the operating Director of SpielOS", prompt)
        self.assertIn("Route unrelated repository implementation", prompt)

    def test_opencode_notification_hook_is_passive_and_honors_stop(self):
        root = Path(__file__).resolve().parents[3]
        config = (root / "opencode.json").read_text()
        plugin = (root / ".opencode/plugins/spielos-notifications.ts").read_text()
        self.assertIn("spielos-notifications.ts", config)
        self.assertIn('event.type === "session.idle"', plugin)
        self.assertIn('input.command === "stop"', plugin)
        self.assertIn("company runner stop", plugin)
        self.assertNotIn("promptAsync", plugin)

    def test_system_improvement_groups_safe_permissions(self):
        root = Path(__file__).resolve().parents[3]
        prompt = (root / ".opencode/agents/system-improvement.md").read_text()
        self.assertIn("permissions:", prompt)
        self.assertIn("- action: edit", prompt)
        self.assertIn("effect: allow", prompt)
        self.assertIn("- action: external_directory", prompt)
        self.assertIn("effect: ask", prompt)


class RuntimeControlTests(unittest.TestCase):
    def test_stop_is_persistent_and_runner_honors_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = root / ".spielos/state/company.sqlite"
            runtime = Runtime(db, {"immediate_test": ImmediateHandler()})
            runtime.create_goal(name="test", owner_id="immediate_test", metric="done",
                                operator="eq", target=True)
            service = RunnerService(root, db)
            self.assertTrue(service.status()["enabled"])
            self.assertFalse(service.stop()["enabled"])
            self.assertTrue(Runner(runtime).tick()["stopped"])
            self.assertTrue(service.enable()["enabled"])

    def test_v4_storage_columns_migrate_without_losing_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "company.sqlite"
            with sqlite3.connect(db) as con:
                con.execute("""CREATE TABLE goals (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, engine_id TEXT NOT NULL,
                    metric TEXT NOT NULL, operator TEXT NOT NULL, target_json TEXT NOT NULL,
                    deadline TEXT, parent_id TEXT, goal_status TEXT NOT NULL,
                    config_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
                con.execute("INSERT INTO goals VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            ("legacy", "Legacy", "outbound", "reply_rate", "ge", "0.3",
                             None, None, "active", "{}", "now", "now"))
            store = Store(db)
            goal = store.goal("legacy")
            self.assertEqual("outbound", goal["owner_id"])
            self.assertNotIn("engine_id", goal)


class LiveTimelineSyncTests(unittest.TestCase):
    """The /live snapshot hook: fires on every persisted transition, and its
    sync output is deterministic and idempotent (no mtime churn)."""

    def test_snapshot_hook_fires_on_recorded_transition(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory) / "state.sqlite",
                              {"immediate_test": ImmediateHandler()})
            goal = runtime.create_goal(name="Snapshot hook", owner_id="immediate_test",
                                       metric="done", operator="eq", target=True, config={})
            calls = []
            fake = SimpleNamespace(
                sync_live=lambda db, out, quiet: calls.append((db, out, quiet)) or {})
            with patch("company.runtime.loop._load_live_sync", return_value=fake):
                result = runtime.once(goal["id"])
            self.assertEqual(result["goal"]["goal_status"], "achieved")
            # ImmediateHandler advances OBSERVE -> DECIDE -> ACT -> EVALUATE,
            # so exactly four recorded transitions must each trigger the sync.
            self.assertEqual(len(calls), 4)
            for db, out, quiet in calls:
                self.assertEqual(db, ".spielos/state/company.sqlite")
                self.assertEqual(out, "src/data/live-goals.json")
                self.assertTrue(quiet)

    def test_hook_tolerates_missing_script_and_locked_db(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory) / "state.sqlite",
                              {"immediate_test": ImmediateHandler()})
            with patch("company.runtime.loop._load_live_sync", return_value=None):
                goal = runtime.create_goal(name="Tolerant hook", owner_id="immediate_test",
                                           metric="done", operator="eq", target=True, config={})
                result = runtime.once(goal["id"])  # missing script: skip, no raise
            self.assertEqual(result["goal"]["goal_status"], "achieved")

            broken = SimpleNamespace(sync_live=lambda db, out, quiet: (_ for _ in ()).throw(
                RuntimeError("database is locked")))
            with patch("company.runtime.loop._load_live_sync", return_value=broken):
                goal = runtime.create_goal(name="Locked hook", owner_id="immediate_test",
                                           metric="done", operator="eq", target=True, config={})
                result = runtime.once(goal["id"])  # locked DB: warn, no raise
            self.assertEqual(result["goal"]["goal_status"], "achieved")

    def test_sync_output_is_idempotent_without_mtime_churn(self):
        root = Path(__file__).resolve().parents[3]
        script = root / "scripts" / "sync-live-timeline.py"
        spec = importlib.util.spec_from_file_location("live_sync_under_test", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "company.sqlite"
            out = Path(directory) / "live-goals.json"
            store = Store(db)
            store.create_goal(name="Snapshot goal", owner_id="immediate_test",
                              metric="done", operator="eq", target=True)
            first = module.sync_live(str(db), str(out), quiet=True)
            first_mtime_ns = out.stat().st_mtime_ns
            second = module.sync_live(str(db), str(out), quiet=True)
            self.assertEqual(first, second)
            self.assertEqual(first_mtime_ns, out.stat().st_mtime_ns)


class PlainLanguageProjectionTests(unittest.TestCase):
    """The compact status projection speaks plain language; --raw keeps its
    machine shape, and notifications keep result.message while gaining a
    plain why/next read."""

    def runtime(self, registry=None):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        return Runtime(Path(self.temp.name) / "state.sqlite",
                       registry or {"approval_test": ApprovalHandler()})

    def capture(self, runtime, *arguments):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["--db", str(runtime.store.path), *arguments])
        self.assertEqual(0, code)
        return output.getvalue()

    def waiting_fixture(self, runtime):
        goal = runtime.create_goal(name="Evidence wait", owner_id="approval_test",
                                   metric="done", operator="eq", target=True, config={})
        cycle = runtime.store.cycle(goal["id"])
        runtime.store.update_cycle(
            cycle["id"], stage="EVALUATE", step="measure", run_status="waiting",
            resume_at="2026-08-11T11:59:00+00:00",
            data={"action_result": {"evidence_deadline": "2026-08-13T03:24:43.927977+00:00"}})
        return goal

    def test_compact_projection_has_plain_language_why_next_for_waiting_run(self):
        runtime = self.runtime()
        goal = self.waiting_fixture(runtime)
        row = runtime.store.goal_summaries(statuses=("active",), limit=10)[0]
        self.assertEqual(row["id"], goal["id"])
        # machine fields stay unchanged in shape
        self.assertEqual(row["run_status"], "waiting")
        self.assertEqual(row["resume_at"], "2026-08-11T11:59:00+00:00")
        self.assertIn("waiting —", row["why_next"])
        self.assertIn("evidence window open until 2026-08-13 03:24 UTC", row["why_next"])
        self.assertIn("next automatic check 2026-08-11 11:59 UTC", row["why_next"])

    def test_compact_status_render_shows_why_next_and_local_runner_header(self):
        runtime = self.runtime()
        self.waiting_fixture(runtime)
        output = self.capture(runtime, "status")
        self.assertIn("Local runner:", output)
        self.assertIn("goals only advance while this machine is on", output)
        self.assertIn("evidence window open until 2026-08-13 03:24 UTC", output)
        self.assertIn("next automatic check 2026-08-11 11:59 UTC", output)

    def test_paused_runner_header_prints_exact_start_hint(self):
        runtime = self.runtime()
        self.waiting_fixture(runtime)
        paused = {"enabled": True, "running": False, "pid": None, "started_at": None}
        with patch("company.__main__.RunnerService.status", return_value=paused):
            output = self.capture(runtime, "status")
        self.assertIn("Local runner: **paused** - start with `company runner start`", output)
        self.assertIn("goals only advance while this machine is on", output)

    def test_raw_status_keeps_token_identical_shape(self):
        runtime = self.runtime()
        goal = self.waiting_fixture(runtime)
        raw = json.loads(self.capture(runtime, "status", "--raw", goal["id"]))
        self.assertEqual(
            {"goal", "cycle", "run", "evidence", "decisions", "evaluation",
             "latest_result", "change_tasks", "children", "pending_notifications"},
            set(raw))
        self.assertEqual({"id", "goal_id", "sequence", "stage", "step", "run_status",
                          "resume_at", "data", "created_at", "updated_at"}, set(raw["cycle"]))
        self.assertEqual("waiting", raw["cycle"]["run_status"])
        self.assertNotIn("why_next", raw["cycle"])
        self.assertNotIn("why_next", raw["goal"])

        company = json.loads(self.capture(runtime, "status", "--raw"))
        self.assertNotIn("why_next", company[0]["goal"])
        self.assertNotIn("why_next", company[0]["cycle"])

    def test_notifications_keep_result_message_and_add_plain_wording(self):
        runtime = self.runtime()
        goal = runtime.create_goal(name="Guarded", owner_id="approval_test",
                                   metric="done", operator="eq", target=True, config={})
        cycle = runtime.store.cycle(goal["id"])
        runtime.store.update_cycle(cycle["id"], stage="ACT", step="review",
                                   run_status="awaiting_approval", data={})
        runtime.store.notify(goal["id"], cycle["id"], "approval_required", {
            "result": {"message": "Review the prepared batch"},
            "required_user_action": "Approve the prepared action",
        })
        runtime.store.notify(goal["id"], cycle["id"], "blocked", {
            "result": {"message": "Coding executor must modify only allowed files",
                       "metrics": {"task": {"status": "approved"}}},
        })
        rows = {row["kind"]: row for row in runtime.store.notifications("pending")}
        self.assertEqual(rows["approval_required"]["payload"]["result"]["message"],
                         "Review the prepared batch")
        self.assertEqual(rows["approval_required"]["why_next"],
                         "approval needed — prepared action needs your approval")
        self.assertEqual(rows["blocked"]["payload"]["result"]["message"],
                         "Coding executor must modify only allowed files")
        self.assertEqual(rows["blocked"]["why_next"], "blocked — needs coding executor")

    def test_runner_service_exposes_started_at_for_live_process(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = root / ".spielos/state/company.sqlite"
            Runtime(db, {"approval_test": ApprovalHandler()})
            service = RunnerService(root, db)
            self.assertIsNone(service.status()["started_at"])  # no pid file yet
            state_dir = root / ".spielos/state"
            state_dir.mkdir(parents=True, exist_ok=True)
            pid_file = state_dir / "runner.pid"
            pid_file.write_text(json.dumps({"pid": 424242, "command": ["-m", "company"],
                                            "db_path": str(db)}) + "\n")
            stamp = datetime(2026, 8, 11, 12, 17, 0, tzinfo=timezone.utc).timestamp()
            os.utime(pid_file, (stamp, stamp))
            with patch("company.runtime.service._alive", return_value=True):
                status = service.status()
            self.assertTrue(status["running"])
            self.assertEqual(status["pid"], 424242)
            self.assertTrue(status["started_at"].startswith("2026-08-11T12:17:00"))


class LivePushTests(unittest.TestCase):
    """SPIELOS_LIVE_PUSH gate: fingerprint + 120s debounce + light git push
    for the /live snapshot. Default OFF; every git failure is non-fatal."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.marker = self.root / ".live_push_state.json"
        self.out = self.root / "live-goals.json"
        self.state_out = self.root / "live-state.json"
        self.out.write_text("{}", encoding="utf-8")
        self.state_out.write_text("{}", encoding="utf-8")

    def runtime(self):
        return Runtime(self.root / "state.sqlite", {"immediate_test": ImmediateHandler()})

    def enabled(self):
        return patch.dict(os.environ, {"SPIELOS_LIVE_PUSH": "1"})

    def live_push_patches(self, db):
        return (
            patch("company.runtime.loop.LIVE_PUSH_MARKER", str(self.marker)),
            patch("company.runtime.loop.LIVE_SYNC_OUT", str(self.out)),
            patch("company.runtime.loop.LIVE_PUSH_STATE_OUT", str(self.state_out)),
            patch("company.runtime.loop.LIVE_SYNC_DB", str(db)),
        )

    @contextmanager
    def clock(self):
        frozen = [datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)]

        class FrozenDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return frozen[0]

        with patch("company.runtime.loop.datetime", FrozenDateTime), \
             patch("company.runtime.loop.time.time",
                   side_effect=lambda: frozen[0].timestamp()):
            yield frozen

    def git_fake(self, calls, diff_returncode=1):
        def run(args, check=True):
            calls.append(list(args))
            if list(args[:2]) == ["git", "diff"]:
                return SimpleNamespace(returncode=diff_returncode)
            return SimpleNamespace(returncode=0)
        return run

    def test_fires_on_state_flip_and_writes_marker(self):
        runtime = self.runtime()
        running = {"runtime_state": {"state": "running"},
                   "totals": {"goals_achieved": 1, "goals_abandoned": 0}}
        resting = {"runtime_state": {"state": "resting"},
                   "totals": {"goals_achieved": 1, "goals_abandoned": 0}}
        calls = []
        with ExitStack() as stack:
            frozen = stack.enter_context(self.clock())
            stack.enter_context(self.enabled())
            stack.enter_context(patch("company.runtime.loop._run_git",
                                      side_effect=self.git_fake(calls)))
            for item in self.live_push_patches(runtime.store.path):
                stack.enter_context(item)
            runtime._maybe_push_live_snapshot(running)
            frozen[0] = frozen[0] + timedelta(seconds=121)
            runtime._maybe_push_live_snapshot(resting)
        expected = [["git", "add", str(self.out), str(self.state_out)],
                    ["git", "diff", "--cached", "--quiet"],
                    ["git", "commit", "-m", "live: sync runtime state"],
                    ["git", "push", "origin", "HEAD"]] * 2
        self.assertEqual(expected, calls)
        marker = json.loads(self.marker.read_text(encoding="utf-8"))
        self.assertEqual("resting|1|0", marker["fingerprint"])
        self.assertIn("pushed_at", marker)

    def test_fires_on_terminal_goal_fingerprint_change(self):
        runtime = self.runtime()
        calls = []
        resting = {"runtime_state": {"state": "resting"},
                   "totals": {"goals_achieved": 1, "goals_abandoned": 0}}
        with ExitStack() as stack:
            frozen = stack.enter_context(self.clock())
            stack.enter_context(self.enabled())
            stack.enter_context(patch("company.runtime.loop._run_git",
                                      side_effect=self.git_fake(calls)))
            for item in self.live_push_patches(runtime.store.path):
                stack.enter_context(item)
            runtime._maybe_push_live_snapshot(resting)
            frozen[0] = frozen[0] + timedelta(seconds=121)
            runtime._maybe_push_live_snapshot(
                {"runtime_state": {"state": "resting"},
                 "totals": {"goals_achieved": 1, "goals_abandoned": 1}})
        pushes = [call for call in calls if call[:2] != ["git", "diff"]]
        self.assertEqual(6, len(pushes))  # add + commit + push per push
        marker = json.loads(self.marker.read_text(encoding="utf-8"))
        self.assertEqual("resting|2|0", marker["fingerprint"])

    def test_fires_on_run_completion_fingerprint_change(self):
        runtime = self.runtime()
        goal = runtime.create_goal(name="Runs", owner_id="immediate_test",
                                   metric="done", operator="eq", target=True, config={})
        snapshot = {"runtime_state": {"state": "resting"},
                    "totals": {"goals_achieved": 0, "goals_abandoned": 0}}
        calls = []
        with ExitStack() as stack:
            frozen = stack.enter_context(self.clock())
            stack.enter_context(self.enabled())
            stack.enter_context(patch("company.runtime.loop._run_git",
                                      side_effect=self.git_fake(calls)))
            for item in self.live_push_patches(runtime.store.path):
                stack.enter_context(item)
            runtime._maybe_push_live_snapshot(snapshot)  # 0 completed runs
            fake_sync = SimpleNamespace(sync_live=lambda db, out, quiet: snapshot)
            with patch("company.runtime.loop._load_live_sync", return_value=fake_sync):
                runtime.once(goal["id"])  # run completes in the DB
            frozen[0] = frozen[0] + timedelta(seconds=121)
            runtime._maybe_push_live_snapshot(snapshot)  # 1 completed run now
        pushes = [call for call in calls if call[:2] != ["git", "diff"]]
        self.assertEqual(6, len(pushes))
        marker = json.loads(self.marker.read_text(encoding="utf-8"))
        self.assertEqual("resting|0|1", marker["fingerprint"])

    def test_no_push_when_fingerprint_unchanged(self):
        runtime = self.runtime()
        self.marker.write_text(json.dumps(
            {"fingerprint": "resting|1|0", "pushed_at": "2026-08-10T12:00:00+00:00"}),
            encoding="utf-8")
        calls = []
        with ExitStack() as stack:
            stack.enter_context(self.clock())
            stack.enter_context(self.enabled())
            stack.enter_context(patch("company.runtime.loop._run_git",
                                      side_effect=self.git_fake(calls)))
            for item in self.live_push_patches(runtime.store.path):
                stack.enter_context(item)
            runtime._maybe_push_live_snapshot(
                {"runtime_state": {"state": "resting"},
                 "totals": {"goals_achieved": 1, "goals_abandoned": 0}})
        self.assertEqual([], calls)

    def test_noop_when_gate_disabled(self):
        runtime = self.runtime()
        calls = []
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {}, clear=True))
            stack.enter_context(patch("company.runtime.loop._env_file_value",
                                      return_value=None))
            stack.enter_context(patch("company.runtime.loop._run_git",
                                      side_effect=self.git_fake(calls)))
            for item in self.live_push_patches(runtime.store.path):
                stack.enter_context(item)
            runtime._maybe_push_live_snapshot(
                {"runtime_state": {"state": "running"},
                 "totals": {"goals_achieved": 1, "goals_abandoned": 0}})
        self.assertEqual([], calls)
        self.assertFalse(self.marker.exists())

    def test_git_failure_is_non_fatal_and_goal_still_achieves(self):
        runtime = self.runtime()
        goal = runtime.create_goal(name="Push fail", owner_id="immediate_test",
                                   metric="done", operator="eq", target=True, config={})
        snapshot = {"runtime_state": {"state": "running"},
                    "totals": {"goals_achieved": 0, "goals_abandoned": 0}}
        fake_sync = SimpleNamespace(sync_live=lambda db, out, quiet: snapshot)

        def failing_push(args, check=True):
            if list(args[:2]) == ["git", "diff"]:
                return SimpleNamespace(returncode=1)
            if list(args[:2]) == ["git", "push"]:
                raise subprocess.CalledProcessError(128, args, b"", b"fatal: no upstream")
            return SimpleNamespace(returncode=0)

        with ExitStack() as stack:
            stack.enter_context(self.clock())
            stack.enter_context(self.enabled())
            stack.enter_context(patch("company.runtime.loop._load_live_sync",
                                      return_value=fake_sync))
            stack.enter_context(patch("company.runtime.loop._run_git",
                                      side_effect=failing_push))
            for item in self.live_push_patches(runtime.store.path):
                stack.enter_context(item)
            with self.assertLogs("company.runtime.loop", level="WARNING") as logs:
                result = runtime.once(goal["id"])
        self.assertEqual("achieved", result["goal"]["goal_status"])
        self.assertFalse(self.marker.exists())  # marker written only after success
        self.assertTrue(any("live push" in line for line in logs.output))

    def test_debounce_blocks_pushes_within_120_seconds(self):
        runtime = self.runtime()
        running = {"runtime_state": {"state": "running"},
                   "totals": {"goals_achieved": 0, "goals_abandoned": 0}}
        resting = {"runtime_state": {"state": "resting"},
                   "totals": {"goals_achieved": 0, "goals_abandoned": 0}}
        calls = []
        with ExitStack() as stack:
            frozen = stack.enter_context(self.clock())
            stack.enter_context(self.enabled())
            stack.enter_context(patch("company.runtime.loop._run_git",
                                      side_effect=self.git_fake(calls)))
            for item in self.live_push_patches(runtime.store.path):
                stack.enter_context(item)
            runtime._maybe_push_live_snapshot(running)  # push 1 at T0
            runtime._maybe_push_live_snapshot(resting)  # changed but 0s < 120s -> skip
            self.assertEqual(1, len(calls) // 3)
            frozen[0] = frozen[0] + timedelta(seconds=120)  # exactly 120s -> allowed
            runtime._maybe_push_live_snapshot(resting)  # push 2
            self.assertEqual(2, len(calls) // 3)
            frozen[0] = frozen[0] + timedelta(seconds=119)  # 119s since push 2 -> skip
            runtime._maybe_push_live_snapshot(running)  # changed again, debounced
            self.assertEqual(2, len(calls) // 3)

    def test_skips_when_nothing_to_commit(self):
        runtime = self.runtime()
        calls = []
        with ExitStack() as stack:
            stack.enter_context(self.clock())
            stack.enter_context(self.enabled())
            stack.enter_context(patch("company.runtime.loop._run_git",
                                      side_effect=self.git_fake(calls, diff_returncode=0)))
            for item in self.live_push_patches(runtime.store.path):
                stack.enter_context(item)
            runtime._maybe_push_live_snapshot(
                {"runtime_state": {"state": "running"},
                 "totals": {"goals_achieved": 0, "goals_abandoned": 0}})
        self.assertEqual([["git", "add", str(self.out), str(self.state_out)],
                          ["git", "diff", "--cached", "--quiet"]], calls)
        self.assertFalse(self.marker.exists())

    def test_git_add_only_stages_existing_snapshot_files(self):
        runtime = self.runtime()
        self.state_out.unlink()  # only live-goals.json exists
        calls = []
        with ExitStack() as stack:
            frozen = stack.enter_context(self.clock())
            stack.enter_context(self.enabled())
            stack.enter_context(patch("company.runtime.loop._run_git",
                                      side_effect=self.git_fake(calls)))
            for item in self.live_push_patches(runtime.store.path):
                stack.enter_context(item)
            runtime._maybe_push_live_snapshot(
                {"runtime_state": {"state": "running"},
                 "totals": {"goals_achieved": 0, "goals_abandoned": 0}})
            self.assertEqual([["git", "add", str(self.out)],
                              ["git", "diff", "--cached", "--quiet"],
                              ["git", "commit", "-m", "live: sync runtime state"],
                              ["git", "push", "origin", "HEAD"]], calls)
            self.out.unlink()  # now neither snapshot file exists
            frozen[0] = frozen[0] + timedelta(seconds=121)
            runtime._maybe_push_live_snapshot(
                {"runtime_state": {"state": "resting"},
                 "totals": {"goals_achieved": 0, "goals_abandoned": 0}})
        self.assertEqual(4, len(calls))  # no new git calls without files to stage

    def test_fingerprint_combines_state_terminal_goals_and_runs(self):
        runtime = self.runtime()
        snapshot = {"runtime_state": {"state": "running"},
                    "totals": {"goals_achieved": 3, "goals_abandoned": 2}}
        self.assertEqual("running|5|0", _live_fingerprint(snapshot, str(runtime.store.path)))
        snapshot["runtime_state"]["state"] = "resting"
        self.assertEqual("resting|5|0", _live_fingerprint(snapshot, str(runtime.store.path)))
        self.assertIsNone(_live_fingerprint({}, str(runtime.store.path)))
        self.assertIsNone(_live_fingerprint(
            {"totals": {"goals_achieved": 1}}, str(runtime.store.path)))

    def test_fingerprint_counts_completed_and_failed_runs(self):
        runtime = self.runtime()
        goal = runtime.create_goal(name="Runs", owner_id="immediate_test",
                                   metric="done", operator="eq", target=True, config={})
        self.assertEqual(0, _completed_failed_runs(str(runtime.store.path)))
        with sqlite3.connect(str(runtime.store.path)) as con:
            for run_id, status in (("r-c", "completed"), ("r-f", "failed"), ("r-i", "idle")):
                con.execute(
                    "INSERT INTO runs (id, goal_id, run_type, owner_id, owner_version, "
                    "config_snapshot_json, controlled_variables_json, changed_variables_json, "
                    "evidence_validity, status, created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (run_id, goal["id"], "execution", "immediate_test", "1.0.0", "{}", "{}",
                     "{}", "business", status, "now", "now"))
        self.assertEqual(2, _completed_failed_runs(str(runtime.store.path)))

    def test_gate_env_var_and_env_file_fallback(self):
        env_file = self.root / ".env"
        env_file.write_text("# comment\nGEMINI_API_KEY=x\nSPIELOS_LIVE_PUSH = 1\n\n",
                            encoding="utf-8")
        self.assertEqual("1", _env_file_value(str(env_file), "SPIELOS_LIVE_PUSH"))
        self.assertIsNone(_env_file_value(str(self.root / "missing.env"), "SPIELOS_LIVE_PUSH"))
        # env var wins over the file
        with patch.dict(os.environ, {"SPIELOS_LIVE_PUSH": "0"}, clear=True), \
             patch("company.runtime.loop._env_file_value", return_value="1"):
            self.assertFalse(_live_push_gate())
        # file fallback when env var is unset
        with patch.dict(os.environ, {}, clear=True), \
             patch("company.runtime.loop._env_file_value", return_value="1"):
            self.assertTrue(_live_push_gate())
        # unset everywhere -> default OFF
        with patch.dict(os.environ, {}, clear=True), \
             patch("company.runtime.loop._env_file_value", return_value=None):
            self.assertFalse(_live_push_gate())


if __name__ == "__main__":
    unittest.main()
