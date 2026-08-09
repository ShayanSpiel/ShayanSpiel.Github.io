"""The channel-neutral outreach engine.

`python3 -m Outreach once` advances the goal-driven loop. The loop is
domain-free; workflow bundles (workflows/email is the first) provide the
domain behavior through the Workflow contract.
"""

from . import engine, models, store, workflows

__all__ = ["engine", "models", "store", "workflows"]
