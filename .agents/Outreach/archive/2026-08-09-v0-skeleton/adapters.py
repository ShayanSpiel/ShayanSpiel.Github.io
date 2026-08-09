"""Execution adapter contract.

Adapters are intentionally small. Discovery and policy remain outside them so
email, social, publishing, and future channels share the same orchestration.
"""

from dataclasses import dataclass
from typing import Protocol

from .models import Action, Lead


@dataclass(frozen=True)
class ActionResult:
    result: str
    note: str = ""
    external_id: str = ""


class ChannelAdapter(Protocol):
    channel: str

    def prepare(self, lead: Lead, action: Action) -> ActionResult:
        """Return a prepared action or a policy/platform block."""

    def execute(self, lead: Lead, action: Action) -> ActionResult:
        """Execute only actions permitted by the channel."""


class ManualExecutionAdapter:
    """Safe default for channels that prohibit scripted website actions."""

    def __init__(self, channel: str):
        self.channel = channel

    def prepare(self, lead: Lead, action: Action) -> ActionResult:
        return ActionResult("prepared", f"ready for controlled {self.channel} execution")

    def execute(self, lead: Lead, action: Action) -> ActionResult:
        return ActionResult(
            "blocked",
            f"{self.channel} execution is not automated by this engine; perform the permitted action in the platform UI",
        )
