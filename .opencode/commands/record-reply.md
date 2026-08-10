---
description: Record reply evidence for a controlled email goal
agent: director
---

Treat `$ARGUMENTS` as a goal ID and recipient supplied by the user. Record one
reply through `python3 -B -m company evidence reply`; do not invent replies.
Then advance EVALUATE only when the persisted goal threshold is met or the user
explicitly ends the evidence window.
