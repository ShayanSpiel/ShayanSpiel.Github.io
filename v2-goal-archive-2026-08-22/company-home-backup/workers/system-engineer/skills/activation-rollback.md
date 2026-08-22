# Activation & Rollback

Activation and rollback are **separate facts** from the candidate
change.

## Process

1. Candidate change passes acceptance → it is `candidate`.
2. Activation flips the runtime to `candidate` → it is `active`.
3. Verification runs against `active` → it is either `verified` or
   requires a rollback.
4. Rollback flips the runtime to the last known-good version.

## Hard rules

- An untested candidate may never be activated.
- A failed activation must be rollback, not hope.
- A rollback must be recorded as its own attempt, not a deletion.
