---
description: Advance a SpielOS goal tree until its next real suspension
agent: director
---

Read persisted status for `$ARGUMENTS`, run `company runner tick` for the goal
tree, and report goal, stage, step, run status, evidence, notifications, and
next trigger. Do not stop between internally runnable stages or child goals.
