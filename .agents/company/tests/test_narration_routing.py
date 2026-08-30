"""Narration routing rule presence checks.

Bounded repair goal-84e845dfed: enforce that every narration ask for a
workflow demo routes through the demo-owned narration.json instance and the
canonical contract before any copy is drafted.

Asserts:
- SKILL.md contains the verbatim "Narration routing:" rule text, the canonical
  contract path (.agents/company/departments/design/templates/video/narration.json)
  and the "No ad-hoc narration JSON shapes." sentence;
- SKILL.md guards against drafting narration copy outside the demo-owned
  instance shape;
- the session handoff doc 2026-08-30-receipt-ledger-narration-routing.md
  exists and records both goal ids (goal-9428806afb, goal-84e845dfed).

Deterministic: pure string/file checks, no network, no runtime state.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILL = REPO / ".agents" / "skills" / "company" / "videography" / "SKILL.md"
HANDOFF = (
    REPO / ".agents" / "company" / "handoffs"
    / "2026-08-30-receipt-ledger-narration-routing.md"
)
CANONICAL_CONTRACT = (
    ".agents/company/departments/design/templates/video/narration.json"
)
DEMO_INSTANCE = ".spielos/artifacts/videography/{workflow}/narration.json"


class VideographySkillNarrationRoutingTests(unittest.TestCase):
    def test_skill_contains_routing_rule_verbatim(self):
        self.assertTrue(SKILL.exists(), "videography SKILL.md missing")
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("Narration routing:", text)
        self.assertIn(DEMO_INSTANCE, text)
        self.assertIn("before drafting any copy", text)
        self.assertIn(CANONICAL_CONTRACT, text)
        self.assertIn("required reading", text)
        self.assertIn("No ad-hoc narration JSON shapes.", text)

    def test_skill_mentions_narration_routing_pipeline_step(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("3. **narration routing**", text)

    def test_skill_guards_demo_owned_instance_shape(self):
        text = SKILL.read_text(encoding="utf-8")
        # Collapse newlines so wrapped markdown lines still match content.
        flat = " ".join(text.split())
        self.assertIn(
            "Never draft narration copy outside the demo-owned narration.json "
            "instance shape", flat)

    def test_skill_references_routing_in_operating_commands(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("# Narration routing", text)


class HandoffNarrationRoutingTests(unittest.TestCase):
    def test_handoff_exists_and_records_goal_ids(self):
        self.assertTrue(HANDOFF.exists(),
                        "handoff doc 2026-08-30-receipt-ledger-narration-routing.md missing")
        text = HANDOFF.read_text(encoding="utf-8")
        self.assertIn("goal-9428806afb", text)
        self.assertIn("goal-84e845dfed", text)
        self.assertIn("PAUSED", text)
        self.assertIn("routing", text.lower())


if __name__ == "__main__":
    unittest.main()