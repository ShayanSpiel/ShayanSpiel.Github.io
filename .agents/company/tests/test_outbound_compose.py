"""Change task change-fc83e94094 (goal-email-copy-v1-20260810) acceptance tests.

Covered:
  - compose_researched renders exactly one of the four OFFER_VARIANTS and never
    the retired "supervised AI employees" line (html AND text);
  - the chosen offer variant is tagged in the composed email features
    (offer-1..offer-4, rotated with the VARIANT_ROTATE cadence) so reply-rate
    A/B is measurable;
  - pick_queue honors cohort_filters.language (English-only, case-insensitive);
  - the new agentic subject additions are present in the content banks;
  - rendered English bodies stay <= 85 words;
  - validators mechanically ban the retired offer phrase (code retired_offer).

Hermetic: synthetic contacts only; read_contacts and the sent log are mocked;
no network, no real sends.
"""

import json
import sys
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from company.departments.outbound.workflows.email import (  # noqa: E402
    compose, config, content, outbound,
)
from company.departments.outbound.workflows.email.templates import SIGNATURE_TEXT  # noqa: E402
from company.departments.outbound.workflows.email.validators import validate  # noqa: E402

# The real, committed content bank (allowed file for this change) — read-only.
REPO_CONTENT_PATH = (
    Path(__file__).resolve().parents[3]
    / ".spielos" / "state" / "outbound" / "content_variables.json"
)

RETIRED_PHRASE = "supervised AI employees"

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


def _contact(lead_id: str, language: str) -> dict:
    return {"lead_id": lead_id, "send_recommendation": "Ready to personalized",
            "email_status": "Verified", "language": language}


class OfferVariantTests(unittest.TestCase):
    def test_each_render_has_one_offer_variant_and_never_the_old_line(self):
        for seq in (0, 1, 5, 10, 11, 20, 30, 40):
            subject, html, text, reason = compose.render_checked(RESEARCHED, seq=seq)
            self.assertIsNone(reason, f"seq={seq} should render")
            idx = compose.offer_variant_index(seq)
            expected = compose.OFFER_VARIANTS[idx].format(company=RESEARCHED["company"])
            self.assertIn(expected, text, f"seq={seq} should carry offer variant {idx}")
            self.assertNotIn(RETIRED_PHRASE, text, f"seq={seq} text")
            self.assertNotIn(RETIRED_PHRASE, html, f"seq={seq} html")

    def test_rotation_covers_all_four_variants_at_rotate_cadence(self):
        idxs = {compose.offer_variant_index(n * config.VARIANT_ROTATE)
                for n in range(len(compose.OFFER_VARIANTS))}
        self.assertEqual(idxs, set(range(len(compose.OFFER_VARIANTS))))

    def test_compose_researched_reports_the_chosen_variant(self):
        composed = compose.compose_researched(RESEARCHED, "recruitment-workflow", seq=0)
        self.assertIsNotNone(composed)
        self.assertEqual(composed["variant"], f"offer-{compose.offer_variant_index(0) + 1}")
        seq_flipped = config.VARIANT_ROTATE * 2
        composed2 = compose.compose_researched(RESEARCHED, "recruitment-workflow", seq=seq_flipped)
        self.assertEqual(composed2["variant"], f"offer-{compose.offer_variant_index(seq_flipped) + 1}")


class FeatureTaggingTests(unittest.TestCase):
    def test_chosen_variant_is_tagged_in_email_features(self):
        built = compose.build_batch_emails("B1", [RESEARCHED], "h")
        self.assertEqual(len(built["emails"]), 1)
        self.assertEqual(built["emails"][0]["features"]["variant"],
                         f"offer-{compose.offer_variant_index(0) + 1}")

    def test_variant_tag_follows_lead_index(self):
        c2 = dict(RESEARCHED, lead_id="EN-200", email="owner@acme-de.com")
        built = compose.build_batch_emails("B1", [RESEARCHED, c2], "h")
        self.assertEqual([e["features"]["variant"] for e in built["emails"]],
                         [f"offer-{compose.offer_variant_index(i) + 1}" for i in (0, 1)])


class CohortFilterTests(unittest.TestCase):
    def _contacts(self):
        return [_contact("EN-1", "English"), _contact("EN-2", "english"),
                _contact("FA-1", "Persian"), _contact("EN-3", "")]

    @unittest.mock.patch.object(outbound, "load_sent_log",
                                return_value={"sent": [], "failed": []})
    @unittest.mock.patch.object(outbound, "read_contacts")
    def test_language_filter_keeps_only_matching_contacts(self, read, _log):
        read.return_value = self._contacts()
        q = compose.pick_queue({"min_tier": "plausible", "language": "English"})
        self.assertEqual([c["lead_id"] for c in q], ["EN-1", "EN-2"])

    @unittest.mock.patch.object(outbound, "load_sent_log",
                                return_value={"sent": [], "failed": []})
    @unittest.mock.patch.object(outbound, "read_contacts")
    def test_no_language_filter_keeps_english_first_then_rest(self, read, _log):
        read.return_value = self._contacts()
        q = compose.pick_queue({"min_tier": "plausible"})
        self.assertEqual([c["lead_id"] for c in q], ["EN-1", "EN-2", "EN-3", "FA-1"])


class SubjectBankTests(unittest.TestCase):
    def setUp(self):
        self._old = config.CONTENT_PATH
        config.CONTENT_PATH = REPO_CONTENT_PATH

    def tearDown(self):
        config.CONTENT_PATH = self._old

    def test_agentic_subject_additions_are_in_the_banks(self):
        data = json.loads(REPO_CONTENT_PATH.read_text())
        banks = data["subject_patterns"]
        expected = {
            "recruitment-workflow": ["Agentic recruiting at {company}",
                                     "Screening, supervised at {company}"],
            "agency-delivery": ["Agentic delivery at {company}",
                                "Delivery, supervised at {company}"],
            "saas-ops": ["Agentic support at {company}",
                         "Triage, supervised at {company}"],
            "generic-workflow": ["Agentic ops at {company}",
                                 "Supervised agents at {company}"],
        }
        for segment, additions in expected.items():
            for addition in additions:
                self.assertIn(addition, banks[segment], segment)

    def test_bank_loader_exposes_the_additions(self):
        bank = content.subject_bank_for("generic-workflow")
        self.assertIn("Agentic ops at {company}", bank)
        self.assertIn("Supervised agents at {company}", bank)


class WordBudgetTests(unittest.TestCase):
    def test_rendered_body_stays_within_85_words(self):
        for seq in range(0, config.VARIANT_ROTATE * 4, max(1, config.VARIANT_ROTATE)):
            _s, html, text, reason = compose.render_checked(RESEARCHED, seq=seq)
            self.assertIsNone(reason, f"seq={seq} must pass the word gate")
            text_only = text.replace(SIGNATURE_TEXT, "").strip()
            self.assertLessEqual(len(text_only.split()), 85, f"seq={seq}")


class RetiredOfferValidatorTests(unittest.TestCase):
    def test_validator_flags_the_retired_offer_phrase(self):
        batch = {"emails": [{
            "lead_id": "L1",
            "subject": "Staffing loop at Acme",
            "body_html": "<p>hi</p>",
            "body_text": ("I build supervised AI employees that carry that loop, "
                          "one workflow at a time, with a person approving each step."),
        }]}
        issues = validate(None, batch)
        self.assertTrue(any(i["code"] == "retired_offer" for i in issues))

    def test_fresh_compose_passes_the_validator(self):
        _s, html, text, reason = compose.render_checked(RESEARCHED, seq=0)
        self.assertIsNone(reason)
        batch = {"emails": [{"lead_id": RESEARCHED["lead_id"],
                             "subject": _s, "body_html": html, "body_text": text}]}
        self.assertEqual(validate(None, batch), [])


if __name__ == "__main__":
    unittest.main()
