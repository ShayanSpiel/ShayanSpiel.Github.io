# Runtime Diagnostics

How the System Engineer narrows a runtime problem to a small
hypothesis.

## Process

1. Reproduce the symptom.
2. Capture the smallest possible Environment + Trigger + Effect note.
3. List candidate hypotheses, ranked by likelihood given the current
   source.
4. For each hypothesis, propose the **cheapest** observable that
   would falsify it.
5. Pick the hypothesis whose falsification is the cheapest.

## Anti-patterns

- "It's probably a race condition" — without a way to falsify it.
- Long debugging sessions without a falsifiable hypothesis.
- Patching symptoms instead of root causes.
