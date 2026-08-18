import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class ContentAttributionContractTests(unittest.TestCase):
    def test_shared_helper_keeps_content_context_without_consent_gate(self):
        source = (ROOT / "src/layouts/BaseLayout.astro").read_text()
        for token in (
            "__spielosAnalyticsConsent",
            "spielos.analytics-consent",
            "analytics-consent",
            "spielos:analytics-consent",
            "gtag('consent'",
        ):
            self.assertNotIn(token, source)
        self.assertIn("sessionStorage.getItem('spielos.content-attribution')", source)
        self.assertIn("track('content_landing'", source)
        self.assertIn("params.page_path", source)
        self.assertIn("person_profiles: 'always'", source)
        self.assertIn("mask_all_inputs: true", source)

    def test_lead_forms_emit_normalized_events(self):
        contact = (ROOT / "src/pages/contact.astro").read_text()
        modal = (ROOT / "src/components/ContactModal.astro").read_text()
        agent_brief = (ROOT / "src/components/AgentBriefForm.astro").read_text()
        for event in (
            "lead_form_view",
            "lead_form_start",
            "lead_form_submit",
            "lead_form_success",
            "lead_form_error",
        ):
            self.assertIn(event, contact)
            self.assertIn(event, agent_brief)
        self.assertIn("lead_form_view", modal)
        self.assertIn("form_type: 'contact'", contact)
        self.assertIn("form_type: 'agent_brief'", agent_brief)


if __name__ == "__main__":
    unittest.main()