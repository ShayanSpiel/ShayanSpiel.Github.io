"""Email bundle tests: strict composition, validators, policy rules,
decider, evaluator. Synthetic data only — no network, no real master."""

import json
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from company.departments.outbound.control import Control  # noqa: E402
from company.departments.outbound.data import OutboundStore  # noqa: E402
from company.departments.outbound.workflows.email import compose, decider, evaluator, policy_rules  # noqa: E402
from company.departments.outbound.workflows.email import config, outbound, providers, report as report_data  # noqa: E402
from company.departments.outbound.workflows.email.validators import validate  # noqa: E402


def make_ctx():
    tmp = Path(tempfile.mkdtemp())
    config.SENT_LOG_PATH = tmp / "sent.json"
    config.METRICS_PATH = tmp / "metrics.json"
    config.CONTENT_PATH = tmp / "content.json"
    config.DATABASE_PATH = tmp / "master.xlsx"
    outbound.save_sent_log({"sent": [], "failed": []})
    with open(config.METRICS_PATH, "w") as f:
        json.dump({"emails": {}, "replies": []}, f)
    store = OutboundStore(tmp / "outbound.sqlite")
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


class ProviderReplyTests(unittest.TestCase):
    def test_received_capability_can_be_selected_per_provider(self):
        self.assertTrue(providers.cap_received("resend"))
        self.assertFalse(providers.cap_received("smtp"))

    def test_received_listing_routes_by_explicit_provider(self):
        with unittest.mock.patch.object(providers, "_open", return_value={"data": []}) as opened:
            result = providers.list_received_emails("resend")
        self.assertEqual(result, {"data": []})
        self.assertIn("/emails/receiving", opened.call_args.args[0])
        unsupported = providers.list_received_emails("smtp")
        self.assertTrue(unsupported["error"])

    def test_receiving_domain_must_be_verified_and_enabled(self):
        domains = {"data": [{"name": "reply.spielos.xyz", "status": "verified",
                              "capabilities": {"sending": "enabled", "receiving": "enabled"}},
                            {"name": "spielos.xyz", "status": "verified",
                              "capabilities": {"sending": "enabled", "receiving": "disabled"}}]}
        with unittest.mock.patch.object(providers, "_open", return_value=domains):
            ready = providers.receiving_domain_status("runs@reply.spielos.xyz", "resend")
            disabled = providers.receiving_domain_status("shayan@spielos.xyz", "resend")
        self.assertTrue(ready["ready"])
        self.assertFalse(disabled["ready"])
        self.assertEqual(disabled["receiving"], "disabled")


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


class GmailCaptureTests(unittest.TestCase):
    """Unified Gmail reply capture (owner direction 2026-08-10): parsing,
    provider resolution, and sync_replies matching. Hermetic — no network."""

    @staticmethod
    def _raw_message(subject="Re: Agentic ops at Acme UK", sender="owner@acme-uk.com",
                     msg_id="<gmailtest123@acme-uk.com>", date="Mon, 10 Aug 2026 09:00:00 +0000",
                     body="Yes, let's talk. Best, Jane"):
        import email as email_mod
        msg = email_mod.message.EmailMessage()
        msg["From"] = f"Jane Doe <{sender}>"
        msg["To"] = "replies@spielos.xyz"
        msg["Subject"] = subject
        msg["Message-ID"] = msg_id
        msg["Date"] = date
        msg["In-Reply-To"] = "<sent-msg-1@resend>"
        msg.set_content(body)
        return msg.as_bytes()

    def test_parse_email_date_utc(self):
        from company.departments.outbound.workflows.email import providers
        iso = providers._parse_email_date("Mon, 10 Aug 2026 09:00:00 +0000")
        self.assertTrue(iso.startswith("2026-08-10T09:00:00"))

    def test_decode_mime_header_encoded(self):
        from company.departments.outbound.workflows.email import providers
        raw = "=?utf-8?B?UmU6IEFnZW50aWMgb3BzIGF0IEFjbWU=?="
        self.assertEqual(providers._decode_mime_header(raw), "Re: Agentic ops at Acme")

    def test_body_text_multipart(self):
        from company.departments.outbound.workflows.email import providers
        raw = self._raw_message()
        from email import message_from_bytes as mfb
        msg = mfb(raw)
        self.assertIn("let's talk", providers._gmail_body_text(msg))

    def test_list_received_emails_resolves_gmail(self):
        from company.departments.outbound.workflows.email import providers
        cfg = providers._cfg_module
        fake = {"data": [{"id": "gmail-<gmailtest123@acme-uk.com>", "from": "owner@acme-uk.com",
                          "subject": "Re: Agentic ops at Acme UK", "message_id": "<gmailtest123@acme-uk.com>",
                          "created_at": "2026-08-10T09:00:00+00:00", "text": "Yes, let's talk."}]}
        with unittest.mock.patch.object(cfg, "REPLY_CAPTURE", "gmail_imap"), \
             unittest.mock.patch.object(cfg, "GMAIL_IMAP_USER", "66shayan@gmail.com"), \
             unittest.mock.patch.object(cfg, "GMAIL_IMAP_APP_PASSWORD", "app-pass"), \
             unittest.mock.patch.object(providers, "_list_gmail_imap", return_value=fake):
            self.assertTrue(providers.cap_received())
            self.assertEqual(providers.list_received_emails(), fake)

    def test_sync_replies_records_gmail_reply_and_auto(self):
        import json as _json
        from company.departments.outbound.workflows.email import analytics, providers
        tmp = Path(tempfile.mkdtemp())
        config.METRICS_PATH = tmp / "metrics.json"
        with open(config.METRICS_PATH, "w") as f:
            _json.dump({"emails": {}, "replies": []}, f)
        sent = {"sent": [{"lead_id": "EN-100", "email": "owner@acme-uk.com",
                          "company": "Acme UK", "subject": "Agentic ops at Acme UK",
                          "variant": "offer-1"}]}
        listing = {"data": [
            {"id": "gmail-<one@acme-uk.com>", "from": "owner@acme-uk.com",
             "subject": "Re: Agentic ops at Acme UK", "message_id": "<one@acme-uk.com>",
             "created_at": "2026-08-10T09:00:00+00:00"},
            {"id": "gmail-<two@acme-uk.com>", "from": "owner@acme-uk.com",
             "subject": "Out of office: away until Friday", "message_id": "<two@acme-uk.com>",
             "created_at": "2026-08-10T09:05:00+00:00"},
        ]}
        with unittest.mock.patch.object(providers, "cap_received", return_value=True), \
             unittest.mock.patch.object(providers, "list_received_emails", return_value=listing):
            metrics = {"emails": {}, "replies": []}
            added = analytics.sync_replies(sent, metrics)
        self.assertEqual(added, 2)
        kinds = {r["received_id"]: r["kind"] for r in metrics["replies"]}
        self.assertEqual(kinds["gmail-<one@acme-uk.com>"], "reply")
        self.assertEqual(kinds["gmail-<two@acme-uk.com>"], "auto")
        self.assertEqual(metrics["replies"][0]["lead_id"], "EN-100")
        self.assertEqual(metrics["replies"][0]["email"], "owner@acme-uk.com")

    def test_sync_replies_dedupes_by_received_id(self):
        import json as _json
        from company.departments.outbound.workflows.email import analytics, providers
        tmp = Path(tempfile.mkdtemp())
        config.METRICS_PATH = tmp / "metrics.json"
        sent = {"sent": [{"lead_id": "EN-100", "email": "owner@acme-uk.com",
                          "company": "Acme UK", "subject": "Agentic ops at Acme UK",
                          "variant": "offer-1"}]}
        listing = {"data": [
            {"id": "gmail-<one@acme-uk.com>", "from": "owner@acme-uk.com",
             "subject": "Re: Agentic ops at Acme UK", "message_id": "<one@acme-uk.com>",
             "created_at": "2026-08-10T09:00:00+00:00"},
        ]}
        with unittest.mock.patch.object(providers, "cap_received", return_value=True), \
             unittest.mock.patch.object(providers, "list_received_emails", return_value=listing):
            metrics = {"emails": {}, "replies": []}
            analytics.sync_replies(sent, metrics)
            second = analytics.sync_replies(sent, metrics)
        self.assertEqual(second, 0)
        self.assertEqual(len(metrics["replies"]), 1)

    def test_gmail_imap_status_requires_credentials(self):
        from company.departments.outbound.workflows.email import providers
        cfg = providers._cfg_module
        with unittest.mock.patch.object(cfg, "GMAIL_IMAP_USER", ""), \
             unittest.mock.patch.object(cfg, "GMAIL_IMAP_APP_PASSWORD", ""):
            status = providers.gmail_imap_status()
        self.assertFalse(status["ready"])
        self.assertIn("not configured", status["reason"])


class PendingStatusGateTests(unittest.TestCase):
    """Delivery gate semantics (owner direction 2026-08-10): provider-accepted
    pending sends (sent/delivery_delayed) are not failures; real losses still
    breach. Hermetic — no network."""

    def test_pending_does_not_breach_delivered_rate(self):
        snap = {"window_totals": {"bounce_rate": 0.0, "spam_rate": 0.0,
                                  "sent": 73, "delivered": 70, "pending": 3,
                                  "unknown": 0, "denied": 0, "unresolved": 0},
                "meta": {"guardrails": [
                    {"name": "bounce rate", "metric": "bounce_rate", "max": 0.02},
                    {"name": "spam rate", "metric": "spam_rate", "max": 0.0008}]}}
        r = policy_rules.evaluate(snap)
        self.assertTrue(r["ok"], r)

    def test_real_losses_still_breach_delivered_rate(self):
        snap = {"window_totals": {"bounce_rate": 0.0, "spam_rate": 0.0,
                                  "sent": 73, "delivered": 68, "pending": 3,
                                  "unknown": 0, "denied": 0, "unresolved": 0},
                "meta": {"guardrails": [
                    {"name": "bounce rate", "metric": "bounce_rate", "max": 0.02},
                    {"name": "spam rate", "metric": "spam_rate", "max": 0.0008}]}}
        r = policy_rules.evaluate(snap)
        self.assertFalse(r["ok"])
        self.assertEqual(r["breaches"][0]["name"], "delivered rate")
        self.assertAlmostEqual(r["breaches"][0]["current"], 71 / 73, places=3)

    def test_aggregate_counts_pending(self):
        from company.departments.outbound.workflows.email import analytics
        log = {"sent": [
            {"lead_id": "L1", "email": "a@x.com", "timestamp": "2026-08-10T10:00:00"},
            {"lead_id": "L2", "email": "b@x.com", "timestamp": "2026-08-10T10:01:00"},
            {"lead_id": "L3", "email": "c@x.com", "timestamp": "2026-08-10T10:02:00"},
        ]}
        metrics = {"emails": {
            "L1": {"status": "delivered"},
            "L2": {"status": "sent"},
            "L3": {"status": "delivery_delayed"},
        }, "replies": []}
        agg = analytics.aggregate(log, metrics)
        self.assertEqual(agg["delivered"], 1)
        self.assertEqual(agg["pending"], 2)


class IdempotentExecuteTests(unittest.TestCase):
    """Bounded repair 2026-08-10: concurrent executors must not strand a
    batch. already_sent leads are skipped (deduped), not fatal. Hermetic."""

    def _execute(self, sent_log, batch_leads, contacts):
        from company.departments.outbound.workflows.email import actor, outbound as ob, config
        sent_calls = []
        with unittest.mock.patch.object(ob, "load_sent_log", return_value=sent_log), \
                unittest.mock.patch.object(ob, "save_sent_log", lambda log: None), \
                unittest.mock.patch.object(ob, "read_contacts", return_value=contacts), \
                unittest.mock.patch.object(actor, "_provider_sent_id", return_value=None), \
                unittest.mock.patch.object(actor, "_send_with_cap",
                                           side_effect=lambda *a, **k: sent_calls.append(a[1]) or {"id": "m1"}), \
                unittest.mock.patch.object(config, "THROTTLE_SECONDS", 0), \
                unittest.mock.patch.object(actor.providers, "pick_provider", return_value="resend"):
            _, store, _ = make_ctx()
            ctx = type("Ctx", (), {"store": store})()
            batch = {"id": "B1", "emails": batch_leads}
            result = actor.execute(ctx, batch, dry=False)
        return result, sent_calls

    def test_mixed_batch_sends_remainder(self):
        log = {"sent": [{"lead_id": "L1", "email": "a@x.com"}], "failed": []}
        contacts = [
            {"lead_id": "L1", "email": "a@x.com", "company": "A", "contact_name": "Ann"},
            {"lead_id": "L2", "email": "b@x.com", "company": "B", "contact_name": "Bob"},
        ]
        leads = [
            {"lead_id": "L1", "subject": "s1", "body_html": "h", "body_text": "t", "features": {}},
            {"lead_id": "L2", "subject": "s2", "body_html": "h", "body_text": "t", "features": {}},
        ]
        result, sent_calls = self._execute(log, leads, contacts)
        self.assertEqual(result["sent"], 1)
        self.assertEqual(result["deduped"], 1)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(sent_calls, ["b@x.com"])

    def test_all_already_sent_is_not_a_failure(self):
        log = {"sent": [{"lead_id": "L1", "email": "a@x.com"},
                        {"lead_id": "L2", "email": "b@x.com"}], "failed": []}
        contacts = [
            {"lead_id": "L1", "email": "a@x.com", "company": "A", "contact_name": "Ann"},
            {"lead_id": "L2", "email": "b@x.com", "company": "B", "contact_name": "Bob"},
        ]
        leads = [
            {"lead_id": "L1", "subject": "s1", "body_html": "h", "body_text": "t", "features": {}},
            {"lead_id": "L2", "subject": "s2", "body_html": "h", "body_text": "t", "features": {}},
        ]
        result, sent_calls = self._execute(log, leads, contacts)
        self.assertEqual(result["sent"], 0)
        self.assertEqual(result["deduped"], 2)
        self.assertIn("nothing to send", result["note"])
        self.assertEqual(sent_calls, [])


class SuppressedDeliveredRateTests(unittest.TestCase):
    """2026-08-11: suppressed window bounces leave the judged population
    for the delivered-rate rule too. Hermetic."""

    def _snap(self, **window):
        snap = {"window_totals": window, "meta": {"guardrails": [
            {"name": "bounce rate", "metric": "bounce_rate", "max": 0.02},
            {"name": "spam rate", "metric": "spam_rate", "max": 0.0008}]}}
        return snap

    def test_all_suppressed_bounces_do_not_block_delivered_rate(self):
        with unittest.mock.patch.object(outbound, "read_contacts", return_value=[
                {"email": "bad@x.com", "email_status": "Bounced; suppressed"}]):
            snap = self._snap(sent=37, delivered=28, bounced=5, pending=4,
                              bounce_rate=0.135, spam_rate=0.0,
                              unknown=0, denied=0, unresolved=0)
            snap["bounced_emails"] = ["bad@x.com"]
            r = policy_rules.evaluate(snap)
        self.assertTrue(r["ok"], r)

    def test_unsuppressed_bounce_still_blocks_delivered_rate(self):
        with unittest.mock.patch.object(outbound, "read_contacts", return_value=[
                {"email": "bad@x.com", "email_status": ""}]):
            snap = self._snap(sent=37, delivered=28, bounced=5, pending=4,
                              bounce_rate=0.135, spam_rate=0.0,
                              unknown=0, denied=0, unresolved=0)
            snap["bounced_emails"] = ["bad@x.com"]
            r = policy_rules.evaluate(snap)
        self.assertFalse(r["ok"])
        self.assertEqual(r["breaches"][0]["name"], "bounce rate")
