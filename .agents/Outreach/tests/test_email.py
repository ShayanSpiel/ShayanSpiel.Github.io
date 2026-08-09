"""Email bundle tests: strict composition, validators, policy rules,
decider, evaluator. Synthetic data only — no network, no real master."""

import json
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Outreach.engine.control import Control  # noqa: E402
from Outreach.store import OutreachStore  # noqa: E402
from Outreach.workflows.email import compose, decider, evaluator, policy_rules  # noqa: E402
from Outreach.workflows.email import config, outbound, report as report_data  # noqa: E402
from Outreach.workflows.email.validators import validate  # noqa: E402


def make_ctx():
    tmp = Path(tempfile.mkdtemp())
    config.SENT_LOG_PATH = tmp / "sent.json"
    config.METRICS_PATH = tmp / "metrics.json"
    config.CONTENT_PATH = tmp / "content.json"
    config.DATABASE_PATH = tmp / "master.xlsx"
    outbound.save_sent_log({"sent": [], "failed": []})
    with open(config.METRICS_PATH, "w") as f:
        json.dump({"emails": {}, "replies": []}, f)
    store = OutreachStore(tmp / "engine.sqlite")
    return tmp, store, Control(tmp / "control.json")


RESEARCHED = {
    "lead_id": "EN-100",
    "email": "owner@acme-uk.com",
    "company": "Acme UK",
    "contact_name": "Jane Doe",
    "title": "Head of Recruitment",
    "segment": "recruitment agency",
    "country": "United Kingdom",
    "language": "English",
    "send_recommendation": "Ready to personalized",
    "outreach_tier": "A",
    "email_status": "Verified",
    "personalization_hook": ("Reference Jane Doe's role as Head of Recruitment by name "
                             "and one observable fact about Acme UK's staffing work"),
    "pain_hypothesis": ("Acme UK staffs 40 agency clients across the UK, and the shortlist "
                        "coordination is likely still handled by hand"),
    "suggested_cta": "map the shortlist stage with you",
}

PLACEHOLDER_PAIN = dict(RESEARCHED, **{
    "lead_id": "EN-101",
    "email": "owner2@acme2-uk.com",
    "pain_hypothesis": "The company likely has a staffing workflow",
})


class ComposeTests(unittest.TestCase):
    def test_researched_lead_composes(self):
        subject, html, text, reason = compose.render_checked(RESEARCHED, seq=0)
        self.assertIsNone(reason)
        self.assertIn("Acme UK", subject)
        self.assertIn("Jane", text)
        self.assertIn("shortlist", text.lower())

    def test_placeholder_pain_is_skipped(self):
        subject, html, text, reason = compose.render_checked(PLACEHOLDER_PAIN, seq=0)
        self.assertIsNone(subject)
        self.assertIn("unprepared", reason)

    def test_short_pain_is_skipped(self):
        c = dict(RESEARCHED, lead_id="EN-102", email="x@y-uk.com",
                 pain_hypothesis="They have staffing work")
        subject, *_rest, reason = compose.render_checked(c, seq=0)
        self.assertIsNone(subject)
        self.assertIn("unprepared", reason)

    def test_missing_hook_is_skipped(self):
        c = dict(RESEARCHED, lead_id="EN-103", email="x@z-uk.com",
                 personalization_hook="")
        subject, *_rest, reason = compose.render_checked(c, seq=0)
        self.assertIsNone(subject)
        self.assertIn("unprepared", reason)

    def test_em_dash_normalized(self):
        c = dict(RESEARCHED, lead_id="EN-104", email="x@w-uk.com",
                 pain_hypothesis="Acme UK staffs clients, and coordination is likely handled by hand — week after week")
        subject, html, text, reason = compose.render_checked(c, seq=0)
        self.assertIsNone(reason)
        self.assertNotIn("\u2014", text)

    def test_build_batch_dedupes_domains_and_skips_unprepared(self):
        c2 = dict(RESEARCHED, lead_id="EN-105", email="partner@acme-uk.com")
        built = compose.build_batch_emails("B1", [RESEARCHED, c2, PLACEHOLDER_PAIN], "h")
        self.assertEqual(len(built["emails"]), 1)
        skipped_ids = [s["lead_id"] for s in built["skipped"]]
        self.assertIn("EN-105", skipped_ids)  # same domain as EN-100
        self.assertIn("EN-101", skipped_ids)  # placeholder pain


class ValidatorTests(unittest.TestCase):
    def test_segment_fallback_flagged(self):
        batch = {"emails": [{
            "lead_id": "L1",
            "subject": "Staffing loop at X",
            "body_html": "<p>hi</p>",
            "body_text": ("Recruitment runs on repeated shortlisting of candidates "
                          "with resume review and feedback email threads."),
        }]}
        issues = validate(None, batch)
        self.assertTrue(any(i["code"] == "segment_fallback" for i in issues))

    def test_clean_email_passes(self):
        batch = {"emails": [{
            "lead_id": "L1",
            "subject": "Staffing loop at Acme",
            "body_html": "<p>hi Jane</p>",
            "body_text": "Hi Jane, your shortlist stage looks manual. What do you think?",
        }]}
        self.assertEqual(validate(None, batch), [])

    def test_over_word_limit_flagged(self):
        words = "word " * 90
        batch = {"emails": [{"lead_id": "L1", "subject": "s",
                             "body_html": "<p>t</p>", "body_text": words}]}
        issues = validate(None, batch)
        self.assertTrue(any(i["code"] == "over_word_limit" for i in issues))


class PolicyRuleTests(unittest.TestCase):
    def _snapshot(self, **window):
        return {"window_totals": window, "meta": {"guardrails": [
            {"name": "bounce rate", "metric": "bounce_rate", "max": 0.02},
            {"name": "spam rate", "metric": "spam_rate", "max": 0.0008}]}}

    def test_bounce_breach_blocks(self):
        r = policy_rules.evaluate(self._snapshot(bounce_rate=0.05, spam_rate=0.0))
        self.assertFalse(r["ok"])
        self.assertEqual(r["breaches"][0]["name"], "bounce rate")

    def test_bounce_suppressed_is_downgraded(self):
        with unittest.mock.patch.object(outbound, "read_contacts", return_value=[
                {"email": "b@x.com", "email_status": "Bounced; suppressed"}]):
            snap = self._snapshot(bounce_rate=0.05, spam_rate=0.0)
            snap["bounced_emails"] = ["b@x.com"]
            r = policy_rules.evaluate(snap)
        self.assertTrue(r["ok"])

    def test_spam_override_timeboxed(self):
        snap = self._snapshot(bounce_rate=0.0, spam_rate=0.01)
        knobs = {"gate_spam_override_until": "2099-01-01T00:00:00+00:00"}
        r = policy_rules.evaluate(snap, knobs)
        self.assertTrue(r["ok"])
        knobs = {"gate_spam_override_until": "2001-01-01T00:00:00+00:00"}
        r = policy_rules.evaluate(snap, knobs)
        self.assertFalse(r["ok"])

    def test_noisy_data_is_a_problem(self):
        snap = self._snapshot(bounce_rate=0.0, spam_rate=0.0, sent=10, unknown=5)
        r = policy_rules.evaluate(snap)
        self.assertFalse(r["ok"])
        self.assertTrue(r["problems"])


class DeciderTests(unittest.TestCase):
    def _ctx(self, store, control):
        return type("Ctx", (), {"control": control, "store": store})()

    def _snap(self, **over):
        snap = {
            "gate": {"ok": True, "breaches": []},
            "cap": {"remaining": 100, "cap": 200, "sent_today": 0, "phase": "t"},
            "queue": {"size": 5},
            "totals": {"sent": 60},
            "window_totals": {"sent": 60, "open_rate": 0.4, "reply_rate": 0.1,
                              "bounce_rate": 0.0, "spam_rate": 0.0},
            "meta": {"goal": {"metric": "reply_rate", "target": 0.3},
                     "guardrails": [{"metric": "bounce_rate", "max": 0.02},
                                    {"metric": "spam_rate", "max": 0.0008}],
                     "supporting_kpis": [{"metric": "open_rate", "target": 0.8}]},
        }
        snap.update(over)
        return snap

    def test_config_broken_holds(self):
        _, store, control = make_ctx()
        ctx = self._ctx(store, control)
        i = decider.decide(ctx, self._snap(config={"ok": False, "error": "no key"}))
        self.assertEqual(i["action"], "hold")
        self.assertIn("config", i["reason"])

    def test_gate_blocked_holds(self):
        _, store, control = make_ctx()
        ctx = self._ctx(store, control)
        i = decider.decide(ctx, self._snap(
            gate={"ok": False, "breaches": [{"name": "bounce rate", "current": 0.05, "max": 0.02}]}))
        self.assertEqual(i["action"], "hold")
        self.assertIn("gate blocked", i["reason"])

    def test_cap_reached_holds(self):
        _, store, control = make_ctx()
        ctx = self._ctx(store, control)
        i = decider.decide(ctx, self._snap(
            cap={"remaining": 0, "cap": 200, "sent_today": 200, "phase": "steady"}))
        self.assertEqual(i["action"], "hold")
        self.assertIn("cap", i["reason"])

    def test_queue_empty_holds(self):
        _, store, control = make_ctx()
        ctx = self._ctx(store, control)
        i = decider.decide(ctx, self._snap(queue={"size": 0}))
        self.assertEqual(i["action"], "hold")
        self.assertIn("queue", i["reason"])

    def test_sample_too_small_keeps_sending(self):
        _, store, control = make_ctx()
        ctx = self._ctx(store, control)
        i = decider.decide(ctx, self._snap(totals={"sent": 5}, window_totals={
            "sent": 5, "open_rate": 0.0, "reply_rate": 0.0}))
        self.assertEqual(i["action"], "prepare_batch")
        self.assertIn("need 30", i["detail"])

    def test_open_stage_picks_subject_lever(self):
        _, store, control = make_ctx()
        ctx = self._ctx(store, control)
        i = decider.decide(ctx, self._snap())
        self.assertEqual(i["variable"], "subject")
        self.assertTrue(i["levers"].get("rotate_subjects"))

    def test_knowledge_reject_vetoes_repeat(self):
        _, store, control = make_ctx()
        store.record_trial("subject", {"verdict": "reject", "batch": "B0"})
        ctx = self._ctx(store, control)
        i = decider.decide(ctx, self._snap())
        self.assertEqual(i["variable"], "subject")
        self.assertIn("NEW angle", i["detail"])


class EvaluatorTests(unittest.TestCase):
    def _ctx(self):
        _, store, control = make_ctx()
        return type("Ctx", (), {"control": control, "store": store})()

    def test_verdict_inconclusive_without_baseline(self):
        outcome = evaluator.measure(self._ctx(), {"id": "B1", "intervention": {}})
        self.assertEqual(outcome["verdict"]["verdict"], "inconclusive")

    def test_verdict_keep_when_improved(self):
        ctx = self._ctx()
        ctx.store.upsert_batch({"id": "B0", "workflow": "email", "phase": "evaluate",
                                "metrics": {"sent": 30, "reply_rate": 0.10}})
        with unittest.mock.patch.object(evaluator.analytics, "aggregate",
                                        return_value={"sent": 30, "reply_rate": 0.20}):
            outcome = evaluator.measure(ctx, {"id": "B1", "intervention": {}})
        self.assertEqual(outcome["verdict"]["verdict"], "keep")

    def test_verdict_reject_when_worse(self):
        ctx = self._ctx()
        ctx.store.upsert_batch({"id": "B0", "workflow": "email", "phase": "evaluate",
                                "metrics": {"sent": 30, "reply_rate": 0.10}})
        with unittest.mock.patch.object(evaluator.analytics, "aggregate",
                                        return_value={"sent": 30, "reply_rate": 0.02}):
            outcome = evaluator.measure(ctx, {"id": "B1", "intervention": {}})
        self.assertEqual(outcome["verdict"]["verdict"], "reject")

    def test_verdict_inconclusive_within_noise(self):
        ctx = self._ctx()
        ctx.store.upsert_batch({"id": "B0", "workflow": "email", "phase": "evaluate",
                                "metrics": {"sent": 30, "reply_rate": 0.10}})
        with unittest.mock.patch.object(evaluator.analytics, "aggregate",
                                        return_value={"sent": 30, "reply_rate": 0.11}):
            outcome = evaluator.measure(ctx, {"id": "B1", "intervention": {}})
        self.assertEqual(outcome["verdict"]["verdict"], "inconclusive")

    def test_goal_check_states(self):
        ctx = self._ctx()
        with unittest.mock.patch.object(outbound, "load_sent_log", return_value={
                "sent": [], "failed": []}):
            with unittest.mock.patch.object(evaluator, "_window_totals", return_value={
                    "sent": 40, "reply_rate": 0.35, "unknown": 0,
                    "denied": 0, "unresolved": 0}):
                r = evaluator.goal_check(ctx, {"sent": 40})
                self.assertEqual(r["state"], "achieved")

            with unittest.mock.patch.object(evaluator, "_window_totals", return_value={
                    "sent": 40, "reply_rate": 0.10, "unknown": 0,
                    "denied": 0, "unresolved": 0}):
                r = evaluator.goal_check(ctx, {"sent": 40})
                self.assertEqual(r["state"], "not_yet")

            with unittest.mock.patch.object(evaluator, "_window_totals", return_value={
                    "sent": 40, "reply_rate": 0.10, "unknown": 12,
                    "denied": 0, "unresolved": 0}):
                r = evaluator.goal_check(ctx, {"sent": 40})
                self.assertEqual(r["state"], "blocked")


class ReportTests(unittest.TestCase):
    def _ctx(self):
        _, store, control = make_ctx()
        return type("Ctx", (), {"control": control, "store": store,
                                "workflow": type("W", (), {"name": "email"})})()

    def test_domain_report_has_all_sections(self):
        ctx = self._ctx()
        batch = {"id": "EMAIL-2026-08-09-b01", "batch": {
            "hypothesis": "research-first",
            "emails": [{"lead_id": "EN-100", "subject": "Shortlist stage",
                        "body_text": "Jane, the shortlist coordination is manual.",
                        "body_html": "<p>x</p>"}]},
            "intervention": {"variable": "subject", "detail": "rotate",
                             "prediction": "opens up"}}
        data = report_data.report(ctx, batch, None)
        self.assertIn("campaign", data)
        self.assertIn("providers", data)
        self.assertIn("example", data)
        self.assertIn("guardrails", data)
        self.assertIn("window", data)
        self.assertIn("leads", data)
        self.assertEqual(data["example"]["lead_id"], "EN-100")
        self.assertEqual(data["example"]["subject"], "Shortlist stage")
        self.assertIn("needed_to_gather", data["leads"])

    def test_domain_report_survives_missing_master(self):
        ctx = self._ctx()
        config.DATABASE_PATH = Path(tempfile.mkdtemp()) / "missing.xlsx"
        data = report_data.report(ctx, {"id": "B1", "batch": {}}, None)
        self.assertEqual(data["leads"]["total"], 0)
        self.assertEqual(data["leads"]["queue"], 0)


if __name__ == "__main__":
    unittest.main()
