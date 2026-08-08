# Shared outreach engine

This package separates lead discovery from channel execution. It stores leads,
qualification evidence, actions, goals, and outcomes in SQLite so the same
orchestrator can support email, social outreach, content publishing, and later
lead-generation workflows.

The package intentionally does not scrape LinkedIn or X and does not provide
bulk social sending. Platform adapters must enforce current platform policy and
return a controlled, auditable action result.
