"""Humanistic demo scenario: a typed, validated sequence of browser actions.

A scenario is the written "story" of a demo — what a person would do and
read. Steps are JSON so new demo types (ActivePieces, an opencode session,
etc.) are just new scenario files; the recorder and renderer never change.
"""
from __future__ import annotations

import json
from pathlib import Path

ALLOWED_STEPS = {
    "goto", "click", "type", "press", "scroll", "wait", "wait_for",
    "read", "verify_text", "open_tab", "shot",
}


class ScenarioError(ValueError):
    pass


class Scenario:
    def __init__(self, name: str, steps: list[dict], viewport: tuple[int, int] = (1440, 900),
                 seed: int = 7, personality: str = "careful", title: str = ""):
        self.name = name
        self.title = title or name
        self.steps = steps
        self.viewport = tuple(viewport)
        self.seed = int(seed)
        self.personality = personality

    @classmethod
    def from_file(cls, path: str | Path) -> "Scenario":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict) -> "Scenario":
        steps = raw.get("steps") or []
        if not isinstance(steps, list) or not steps:
            raise ScenarioError("scenario needs a non-empty steps list")
        for i, step in enumerate(steps):
            stype = step.get("type")
            if stype not in ALLOWED_STEPS:
                raise ScenarioError(f"step {i}: unknown type {stype!r}")
            if stype in ("goto",) and not step.get("url"):
                raise ScenarioError(f"step {i}: goto needs url")
            if stype in ("click", "type", "scroll", "wait_for", "verify_text") \
                    and not step.get("selector") and stype not in ("click", "verify_text"):
                raise ScenarioError(f"step {i}: {stype} needs selector")
            if stype == "type" and not step.get("text"):
                raise ScenarioError(f"step {i}: type needs text")
            if stype == "open_tab" and not step.get("url"):
                raise ScenarioError(f"step {i}: open_tab needs url")
        viewport = tuple(raw.get("viewport") or (1440, 900))
        return cls(
            name=str(raw.get("name") or "demo"),
            steps=steps,
            viewport=viewport,
            seed=int(raw.get("seed") or 7),
            personality=str(raw.get("personality") or "careful"),
            title=str(raw.get("title") or ""),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name, "title": self.title, "seed": self.seed,
            "personality": self.personality, "viewport": list(self.viewport),
            "steps": self.steps,
        }
