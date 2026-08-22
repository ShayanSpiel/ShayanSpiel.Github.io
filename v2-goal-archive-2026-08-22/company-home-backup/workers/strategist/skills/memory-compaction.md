# Memory Compaction

When the Strategist compacts Memory.

## Process

1. Group Memory by claim family (e.g. all "X outreach produced Y%"
   claims).
2. Find the strongest signal (confidence, number of evidence refs,
   recency).
3. Write a stronger consolidated Memory.
4. Mark the older Memory as `superseded` (or `archived` if the
   signal is no longer relevant).
5. Active retrieval should now prefer the consolidated claim.

## When to compact

- Three or more Memory items share a family.
- A new Memory item contradicts an older one.
- A Strategy change makes a cluster of Memory stale.

## What you do NOT do

- Delete old Memory. Supersede it.
- Invent consolidation if the signals disagree — escalate instead.
