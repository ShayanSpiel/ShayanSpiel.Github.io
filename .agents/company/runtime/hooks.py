"""Transition notification compatibility seam.

Legacy SpielOS releases allowed a shell command from .spielos/.env to run after
any goal transition. That ambient command execution is intentionally disabled.
Current runtimes should publish typed transition events through an explicit,
bounded adapter instead of executing repository-controlled shell text.
"""

from __future__ import annotations

HOOK_ENV = "SPIELOS_TRANSITION_HOOK"


def _hook_template() -> str:
    """Return no command: ambient transition shell hooks are retired."""
    return ""


def run_transition_hook(event: str, payload: dict, *,
                        timeout: float | None = None) -> None:
    """Compatibility no-op retained for callers in the legacy loop."""
    return None
