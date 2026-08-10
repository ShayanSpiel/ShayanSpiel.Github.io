---
description: Runs one SpielOS Department independently against a runtime-owned persisted goal
mode: subagent
permission:
  bash:
    "*": ask
    "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company *": allow
---

Read `.agents/skills/engine-runner/SKILL.md` completely and follow it. Never
bypass the shared runtime or persisted approvals.
