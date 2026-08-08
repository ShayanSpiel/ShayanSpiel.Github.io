#!/usr/bin/env python3
"""
SpielOS Outbound — the engine core (channel-agnostic).

The loop (first principles): OBSERVE -> DIAGNOSE -> SELECT LEVER ->
HYPOTHESIS -> EXPERIMENT -> MEASURE -> LEARN -> UPDATE STATE -> REPEAT.

Everything the engine knows lives in experiments/state.json (the single
memory). Every cycle reads it before deciding and writes it after measuring.
The email-specific machinery stays in scripts/; this package only reasons
about goals, guardrails, levers and evidence.
"""
