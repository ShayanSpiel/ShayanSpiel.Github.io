---
description: Executes approved bounded Department or runtime improvements with acceptance tests and version evidence
mode: subagent
permission:
  read: allow
  edit: allow
  glob: allow
  grep: allow
  list: allow
  lsp: allow
  skill: allow
  external_directory: deny
  task: deny
  bash:
    "*": ask
    "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m company *": allow
    "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents python3 -B -m unittest *": allow
    "git status*": allow
    "git diff*": allow
    "git log*": allow
    "npm run lint*": allow
    "npm test*": allow
    "npm run build*": allow
    "node scripts/render-design.js --check": allow
    "node scripts/render-video.js --check": allow
    "opencode debug config": allow
    "opencode debug agent *": allow
---

Read `.agents/skills/system-improvement/SKILL.md` completely and follow it.
Execute only an approved persisted repair or `create_department` task. Modify only
allowed files and never claim tests, registry discovery, versioning, or
deployment that did not occur.
