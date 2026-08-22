# Bounded Repair

How the System Engineer performs a code change inside an approved
scope.

## Process

1. Read the approval row. Confirm files / paths match.
2. Make the smallest change that satisfies the acceptance tests.
3. Do not reformat unrelated code.
4. Do not introduce new dependencies without explicit approval.
5. Each new attempt is a fresh attempt. Append the diff to the
   attempt history.

## Anti-patterns

- "Just touch this file while you're in there" — out of scope.
- Refactoring unrelated code in the same attempt.
- Adding a new dependency without a stated reason.
