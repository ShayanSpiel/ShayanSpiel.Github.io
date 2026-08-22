# Acceptance Tests

How the System Engineer defines and runs acceptance tests.

## Definition

Acceptance tests are defined **before** writing code. They are part of
the approval scope.

## Process

1. List the smallest set of assertions that, if all pass, prove the
   original problem is fixed.
2. Each assertion must be mechanical — no LLM judgment.
3. Each assertion must be reversible — if a subsequent attempt
   fails, the original state must be restorable.

## Categories

- **Unit:** the function under repair behaves as specified.
- **Integration:** the relevant runtime path returns expected status.
- **Smoke:** a representative end-to-end scenario still works.

## What acceptance tests are NOT

- A subjective "looks better" check.
- A passing console output with no assertion.
- A single test that covers everything.
