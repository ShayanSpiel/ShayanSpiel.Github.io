"""Safety policy for deciding what the orchestration layer may prepare."""

from dataclasses import dataclass

from .models import Action, Lead


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


EXCLUDED_TERMS = ("ai agency", "ai consultant", "software development", "agent builder", "developer")


def check_lead(lead: Lead, min_score: int = 75) -> Decision:
    text = " ".join((lead.company, lead.role, lead.metadata.get("segment", ""))).lower()
    if any(term in text for term in EXCLUDED_TERMS):
        return Decision(False, "excluded ICP category")
    if lead.icp_score < min_score:
        return Decision(False, f"ICP score {lead.icp_score} below {min_score}")
    if not lead.research_fact or not lead.operational_consequence:
        return Decision(False, "missing operative fact or consequence")
    return Decision(True, "qualified")


def check_action(channel: str, action: Action, *, recipient_requested_contact: bool = False) -> Decision:
    if channel == "linkedin" and action in {Action.SEND_DM, Action.SEND_CONNECTION}:
        return Decision(False, "platform action requires controlled permitted execution")
    if channel == "x" and action == Action.SEND_DM and not recipient_requested_contact:
        return Decision(False, "unsolicited automated X DM is not eligible")
    return Decision(True, "eligible for adapter")

