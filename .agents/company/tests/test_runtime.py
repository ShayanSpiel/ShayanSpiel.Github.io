import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from company.engines.director import DirectorEngine
from company.engines.email import EmailEngine, outbound_context
from company.engines.system_improvement import SystemImprovementEngine
from company.models import Engine, EngineContext, Goal, GoalStatus, RunStatus, Stage, StageResult
from company.runner import Runner
from company.runtime import Runtime
from company.__main__ import render_report


class ApprovalEngine(Engine):
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


class ImmediateEngine(Engine):
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


class IterativeEngine(Engine):
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
        runtime = self.runtime({"approval_test": ApprovalEngine()})
        goal = runtime.create_goal(name="Approval", engine_id="approval_test", metric="done",
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
        runtime = self.runtime({"approval_test": ApprovalEngine()})
        goal = runtime.create_goal(name="Safe", engine_id="approval_test", metric="done",
                                   operator="eq", target=True, config={})
        first = runtime.once(goal["id"])
        second = runtime.once(goal["id"])
        self.assertEqual(first["cycle"]["data"], second["cycle"]["data"])
        self.assertEqual(len(runtime.store.events(goal["id"])), 4)

    def test_expired_goal_never_runs(self):
        runtime = self.runtime({"immediate_test": ImmediateEngine()})
        goal = runtime.create_goal(name="Expired", engine_id="immediate_test", metric="done",
                                   operator="eq", target=True, deadline="2000-01-01T00:00:00Z", config={})
        result = runtime.once(goal["id"])
        self.assertEqual(result["goal"]["goal_status"], "expired")
        self.assertEqual(result["cycle"]["stage"], "OBSERVE")

    def test_lease_prevents_two_clients_running_same_goal(self):
        runtime = self.runtime({"immediate_test": ImmediateEngine()})
        goal = runtime.create_goal(name="Exclusive", engine_id="immediate_test", metric="done",
                                   operator="eq", target=True, config={})
        self.assertTrue(runtime.store.acquire(goal["id"], "opencode"))
        with self.assertRaisesRegex(RuntimeError, "already running"):
            runtime.once(goal["id"], holder="codex")
        runtime.store.release(goal["id"], "opencode")

    def test_completed_run_parks_until_explicit_next(self):
        runtime = self.runtime({"iterative_test": IterativeEngine()})
        goal = runtime.create_goal(name="Improve score", engine_id="iterative_test",
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
        runtime = self.runtime({"email": EmailEngine()})
        goal = runtime.create_goal(name="Email batch", engine_id="email", metric="reply_rate",
                                   operator="ge", target=0.3, run_type="business_experiment",
                                   config={"execution_mode": "dry_run", "batch_size": 10})
        fake = SimpleNamespace(
            stop_file=Path(self.temp.name) / "STOP",
            workflow=SimpleNamespace(observe=lambda _ctx: {"queue": {"size": 3}}),
            control=SimpleNamespace(knobs=lambda: {"block_size": 10,
                                                   "cohort_filters": {"min_tier": "Verified"}}),
        )
        with patch("company.engines.email.outbound_context", return_value=fake):
            blocked = runtime.once(goal["id"])
        self.assertEqual(blocked["cycle"]["run_status"], "blocked")
        self.assertEqual(blocked["cycle"]["data"]["decision"]["needed_leads"], 7)
        note = runtime.store.notifications("pending")[0]
        self.assertEqual(note["kind"], "action_required")
        self.assertEqual(note["payload"]["attention"]["capability"], "lead_research")
        self.assertIn("company retry", note["payload"]["next_trigger"])

    def test_director_dispatches_child_and_completes(self):
        runtime = self.runtime({"director": DirectorEngine(), "immediate_test": ImmediateEngine()})
        parent = runtime.create_goal(name="Company outcome", engine_id="director",
                                     metric="all_children_achieved", operator="eq", target=True, config={})
        child = runtime.create_goal(name="Child outcome", engine_id="immediate_test", metric="done",
                                    operator="eq", target=True, parent_id=parent["id"], config={})
        result = runtime.once(parent["id"])
        self.assertEqual(runtime.status(child["id"])["goal"]["goal_status"], "achieved")
        self.assertEqual(result["goal"]["goal_status"], "achieved")
        self.assertEqual(runtime.store.memories("immediate_test", child["id"])[0]["claim"],
                         "Immediate action worked")

    def test_director_surfaces_child_approval_without_approving_it(self):
        runtime = self.runtime({"director": DirectorEngine(), "approval_test": ApprovalEngine()})
        parent = runtime.create_goal(name="Company outcome", engine_id="director",
                                     metric="all_children_achieved", operator="eq", target=True, config={})
        child = runtime.create_goal(name="Guarded child", engine_id="approval_test", metric="done",
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
        self.assertEqual(EmailEngine.id, "email")
        self.assertEqual(context.workflow.name, "email")

    def test_email_bridge_honors_existing_stop_switch(self):
        with tempfile.TemporaryDirectory() as directory:
            stop = Path(directory) / "STOP"
            stop.touch()
            goal = Goal("g", "Email", "email", "reply_rate", "ge", 0.3, None, None,
                        "active", {"execution_mode": "dry_run"})
            context = EngineContext(goal, {"data": {}}, (), lambda key: None)
            with patch("company.engines.email.outbound_context", return_value=SimpleNamespace(stop_file=stop)):
                result = EmailEngine().observe(context)
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
            first_ctx = EngineContext(goal, {"data": {}}, (), lambda key: None)
            with patch("company.engines.email.outbound_context", return_value=outbound), \
                 patch("company.departments.outbound.execution.prepare", return_value=row), \
                 patch("company.departments.outbound.execution.validate", return_value=[]), \
                 patch("company.departments.outbound.execution.gate", return_value={"ok": True}):
                parked = EmailEngine().act(first_ctx, {"action": "prepare_batch"})
            self.assertEqual(parked.run_status, RunStatus.AWAITING_APPROVAL)

            second_ctx = EngineContext(goal, {"data": {"action_result": parked.payload}}, (),
                                       lambda key: "approved")
            with patch("company.engines.email.outbound_context", return_value=outbound), \
                 patch("company.departments.outbound.execution.execute", return_value={"sent": 0, "note": "dry"}) as execute:
                result = EmailEngine().act(second_ctx, {"action": "prepare_batch"})
            execute.assert_called_once_with(outbound, row, dry=True)
            self.assertEqual(result.run_status, RunStatus.WAITING)
            self.assertEqual(result.next_stage, Stage.EVALUATE)

    def test_live_business_reply_goal_requires_observable_capture(self):
        goal = Goal("g", "Replies", "email", "reply_rate", "ge", 0.3, None, None,
                    "active", {"execution_mode": "live", "evidence_window_hours": 48})
        context = EngineContext(goal, {"data": {}}, (), lambda key: None)
        result = EmailEngine().act(context, {"action": "prepare_batch"})
        self.assertEqual(result.run_status, RunStatus.BLOCKED)
        self.assertEqual(result.attention["capability"], "inbound_email_setup")
        self.assertIn("reply evidence source", result.payload["reason"])

    def test_typed_run_preserves_hypothesis_variables_and_version(self):
        runtime = self.runtime({"immediate_test": ImmediateEngine()})
        goal = runtime.create_goal(
            name="Typed", engine_id="immediate_test", metric="done", operator="eq", target=True,
            run_type="business_experiment", evidence_validity="business",
            hypothesis={"statement": "Changing X improves Y", "variable": "x", "prediction": "Y rises"},
            controlled_variables={"offer": "fixed"}, changed_variables={"x": "variant-b"}, config={})
        state = runtime.status(goal["id"])
        self.assertEqual(state["run"]["run_type"], "business_experiment")
        self.assertEqual(state["run"]["engine_version"], "1.0.0")
        self.assertEqual(state["run"]["controlled_variables"], {"offer": "fixed"})
        self.assertTrue(state["run"]["hypothesis_id"].startswith("hyp-"))

    def test_system_improvement_requires_approval_then_versions_result(self):
        runtime = self.runtime({"system-improvement": SystemImprovementEngine()})
        goal = runtime.create_goal(
            name="Repair sender", engine_id="system-improvement",
            metric="acceptance_tests_passed", operator="eq", target=True,
            run_type="system_improvement", evidence_validity="technical_only", config={
                "engine_id": "email", "from_version": "2.0.0", "target_version": "2.0.1",
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
        versions = runtime.store.engine_versions("email")
        self.assertEqual(versions[-1]["version"], "2.0.1")

    def test_test_inbox_batch_prepares_without_sending(self):
        runtime = self.runtime({"email": EmailEngine()})
        goal = runtime.create_goal(name="Test replies", engine_id="email", metric="reply_rate",
                                   operator="ge", target=0.3, run_type="system_test",
                                   evidence_validity="technical_only", config={
                                       "audience_type": "test_inbox", "execution_mode": "live",
                                       "test_recipients": ["one@example.com", "two@example.com"],
                                       "throttle_seconds": 0, "evidence_window_hours": 24,
                                       "reply_capture": "manual_inbox"})
        with patch("company.engines.email._write_test_preview", return_value=Path("/tmp/preview.md")):
            parked = runtime.once(goal["id"])
        self.assertEqual(parked["cycle"]["run_status"], "awaiting_approval")
        self.assertEqual(parked["cycle"]["step"], "review")
        self.assertEqual(parked["cycle"]["data"]["action_result"]["recipients"],
                         ["one@example.com", "two@example.com"])

    def test_four_inbox_flow_wakes_at_two_replies_and_achieves_goal(self):
        runtime = self.runtime({"email": EmailEngine()})
        recipients = [f"test-{index}@example.com" for index in range(4)]
        goal = runtime.create_goal(name="Four inboxes", engine_id="email", metric="reply_rate",
                                   operator="ge", target=0.3, run_type="system_test",
                                   evidence_validity="technical_only", config={
                                       "audience_type": "test_inbox", "execution_mode": "live",
                                       "test_recipients": recipients, "throttle_seconds": 0,
                                       "evidence_window_hours": 24,
                                       "reply_capture": "manual_inbox"})
        with patch("company.engines.email._write_test_preview", return_value=Path("/tmp/preview.md")):
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
        with patch("company.engines.email._observe_test_provider", return_value=[]):
            complete = runtime.once(goal["id"])
        self.assertEqual(complete["goal"]["goal_status"], "achieved")
        self.assertEqual(complete["evaluation"]["metrics"]["reply_rate"], 0.5)

    def test_email_run_completes_reports_and_waits_for_next_run_approval(self):
        runtime = self.runtime({"email": EmailEngine()})
        recipients = [f"loop-{index}@example.com" for index in range(4)]
        goal = runtime.create_goal(name="Improve replies", engine_id="email", metric="reply_rate",
                                   operator="ge", target=0.3, run_type="system_test",
                                   evidence_validity="technical_only", config={
                                       "audience_type": "test_inbox", "execution_mode": "live",
                                       "test_recipients": recipients, "throttle_seconds": 0,
                                       "evidence_window_hours": 0,
                                       "reply_capture": "manual_inbox"})
        with patch("company.engines.email._write_test_preview", return_value=Path("/tmp/preview.md")):
            runtime.once(goal["id"])
        runtime.approve(goal["id"])
        with patch("company.departments.outbound.workflows.email.providers.send_email",
                   side_effect=[{"id": f"provider-{index}"} for index in range(4)]), \
             patch("company.engines.email._observe_test_provider", return_value=[]):
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
        with patch("company.engines.email._write_test_preview", return_value=Path("/tmp/preview-2.md")):
            Runner(runtime).tick(goal["id"])
        next_state = runtime.status(goal["id"])
        self.assertEqual(next_state["cycle"]["sequence"], 2)
        self.assertEqual(next_state["cycle"]["run_status"], "awaiting_approval")
        self.assertEqual(next_state["run"]["changed_variables"], {"test_token": "new_run_token"})

    def test_resend_observer_imports_opens_and_replies_then_achieves_goal(self):
        runtime = self.runtime({"email": EmailEngine()})
        recipients = [f"auto-{index}@example.com" for index in range(4)]
        goal = runtime.create_goal(name="Automatic replies", engine_id="email", metric="reply_rate",
                                   operator="ge", target=0.3, run_type="system_test",
                                   evidence_validity="technical_only", config={
                                       "audience_type": "test_inbox", "execution_mode": "live",
                                       "provider": "resend", "test_recipients": recipients,
                                       "throttle_seconds": 0, "evidence_window_hours": 24,
                                       "observer_interval_seconds": 300,
                                       "reply_capture": "resend_inbound"})
        with patch("company.engines.email._write_test_preview", return_value=Path("/tmp/preview.md")):
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
        runtime = self.runtime({"email": EmailEngine()})
        goal = runtime.create_goal(name="Missing inbound", engine_id="email", metric="reply_rate",
                                   operator="ge", target=0.3, run_type="system_test",
                                   evidence_validity="technical_only", config={
                                       "audience_type": "test_inbox", "execution_mode": "live",
                                       "provider": "resend", "test_recipients": ["one@example.com"],
                                       "throttle_seconds": 0, "evidence_window_hours": 24,
                                       "reply_capture": "resend_inbound"})
        with patch("company.engines.email._write_test_preview", return_value=Path("/tmp/preview.md")):
            runtime.once(goal["id"])
        runtime.approve(goal["id"])
        with patch("company.departments.outbound.workflows.email.config.REPLY_TO", ""):
            blocked = runtime.once(goal["id"])
        self.assertEqual(blocked["cycle"]["run_status"], "blocked")
        self.assertIn("REPLY_TO", blocked["cycle"]["data"]["action_result"]["error"])

    def test_event_only_waiting_does_not_advance_without_wake(self):
        runtime = self.runtime({"director": DirectorEngine(), "approval_test": ApprovalEngine()})
        parent = runtime.create_goal(name="Company outcome", engine_id="director",
                                     metric="all_children_achieved", operator="eq", target=True, config={})
        runtime.create_goal(name="Guarded child", engine_id="approval_test", metric="done",
                            operator="eq", target=True, parent_id=parent["id"], config={})
        runtime.once(parent["id"])
        waiting = runtime.once(parent["id"])
        self.assertEqual(waiting["cycle"]["run_status"], "waiting")
        self.assertIsNone(waiting["cycle"]["resume_at"])
        unchanged = runtime.once(parent["id"])
        self.assertEqual(unchanged["cycle"], waiting["cycle"])

    def test_runner_continues_child_evaluation_and_parent_goal(self):
        runtime = self.runtime({"director": DirectorEngine(), "email": EmailEngine()})
        parent = runtime.create_goal(name="Reply outcome", engine_id="director",
                                     metric="reply_rate", operator="ge", target=0.3,
                                     evidence_validity="technical_only",
                                     config={"accepted_evidence_validity": ["technical_only"]})
        recipients = [f"runner-{index}@example.com" for index in range(4)]
        child = runtime.create_goal(name="Email child", engine_id="email", metric="reply_rate",
                                    operator="ge", target=0.3, parent_id=parent["id"],
                                    run_type="system_test", evidence_validity="technical_only", config={
                                        "audience_type": "test_inbox", "execution_mode": "live",
                                        "test_recipients": recipients, "throttle_seconds": 0,
                                        "evidence_window_hours": 24,
                                        "reply_capture": "manual_inbox"})
        runner = Runner(runtime)
        with patch("company.engines.email._write_test_preview", return_value=Path("/tmp/preview.md")):
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
        with patch("company.engines.email._observe_test_provider", return_value=[]):
            outcome = runner.tick(child["id"])
        self.assertTrue(outcome["advanced"])
        self.assertEqual(runtime.status(child["id"])["goal"]["goal_status"], "achieved")
        self.assertEqual(runtime.status(parent["id"])["goal"]["goal_status"], "achieved")
        kinds = {item["kind"] for item in runtime.store.notifications("pending")}
        self.assertIn("goal_achieved", kinds)

    def test_new_engine_task_requires_and_persists_engine_spec(self):
        runtime = self.runtime({"system-improvement": SystemImprovementEngine()})
        invalid = runtime.create_goal(
            name="Build content engine", engine_id="system-improvement",
            metric="acceptance_tests_passed", operator="eq", target=True,
            run_type="system_improvement", evidence_validity="technical_only", config={
                "change_kind": "create_engine", "engine_id": "content",
                "from_version": "new", "target_version": "1.0.0",
                "problem": "Create content distribution capability",
                "allowed_files": [".agents/company/engines/content.py"],
                "acceptance_tests": ["python -m unittest"]})
        blocked = runtime.once(invalid["id"])
        self.assertIn("engine_spec", blocked["cycle"]["data"]["decision"]["missing"])

        valid = runtime.create_goal(
            name="Build content engine", engine_id="system-improvement",
            metric="acceptance_tests_passed", operator="eq", target=True,
            run_type="system_improvement", evidence_validity="technical_only", config={
                "change_kind": "create_engine", "engine_id": "content",
                "from_version": "new", "target_version": "1.0.0",
                "problem": "Create content distribution capability",
                "allowed_files": [".agents/company/engines/content.py"],
                "acceptance_tests": ["python -m unittest"],
                "engine_spec": {"purpose": "distribute content", "metrics": ["qualified_views"],
                                "external_actions": ["publish"], "approval_points": ["publish"],
                                "evidence_sources": ["analytics"]}})
        parked = runtime.once(valid["id"])
        task = parked["change_tasks"][0]
        self.assertEqual(task["change_kind"], "create_engine")
        self.assertEqual(task["specification"]["purpose"], "distribute content")


class DirectorIdentityContractTests(unittest.TestCase):
    def test_opencode_director_is_not_generic_build_agent(self):
        root = Path(__file__).resolve().parents[3]
        prompt = (root / ".opencode/agents/director.md").read_text()
        self.assertIn("You are the operating Director of SpielOS", prompt)
        self.assertIn("must never introduce yourself as a coding or website assistant", prompt)
        self.assertIn("reports do not require a new goal", prompt)
        self.assertIn("edit: false", prompt)
        self.assertIn("write: false", prompt)

    def test_codex_director_has_same_identity_boundary(self):
        root = Path(__file__).resolve().parents[3]
        prompt = (root / ".codex/agents/director.toml").read_text()
        self.assertIn("You are the operating Director of SpielOS", prompt)
        self.assertIn("Route unrelated repository implementation", prompt)

    def test_opencode_notification_hook_wakes_director(self):
        root = Path(__file__).resolve().parents[3]
        config = (root / "opencode.json").read_text()
        plugin = (root / ".opencode/plugins/spielos-notifications.ts").read_text()
        self.assertIn("spielos-notifications.ts", config)
        self.assertIn('event.type === "session.idle"', plugin)
        self.assertIn('agent: "director"', plugin)
        self.assertIn("Do not create or start another run without user approval", plugin)


if __name__ == "__main__":
    unittest.main()
