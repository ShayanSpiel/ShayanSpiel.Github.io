import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class ContentAttributionContractTests(unittest.TestCase):
    def test_shared_helper_keeps_content_context_consent_gated(self):
        source = (ROOT / "src/layouts/BaseLayout.astro").read_text()
        self.assertIn("if(!window.__spielosAnalyticsConsent) return;", source)
        self.assertIn("sessionStorage.getItem('spielos.content-attribution')", source)
        self.assertIn("track('content_landing'", source)
        self.assertIn("params.page_path", source)

    def test_both_lead_forms_emit_normalized_success_events(self):
        contact = (ROOT / "src/pages/contact.astro").read_text()
        modal = (ROOT / "src/components/ContactModal.astro").read_text()
        self.assertIn("lead_form_success", contact)
        self.assertIn("lead_form_success", modal)
        self.assertIn("form_type: 'contact'", contact)
        self.assertIn("form_type: 'agent_briefing'", modal)


if __name__ == "__main__":
    unittest.main()
