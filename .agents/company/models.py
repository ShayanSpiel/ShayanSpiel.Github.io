"""Small, stable public contract shared by every engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class Stage(str, Enum):
    OBSERVE = "OBSERVE"
    DECIDE = "DECIDE"
    ACT = "ACT"
    EVALUATE = "EVALUATE"


class GoalStatus(str, Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    PAUSED = "paused"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"
    EXPIRED = "expired"


class RunStatus(str, Enum):
    RUNNING = "running"
    WAITING = "waiting"
    AWAITING_APPROVAL = "awaiting_approval"
    BLOCKED = "blocked"
    FAILED = "failed"
    IDLE = "idle"
    COMPLETED = "completed"


class RunType(str, Enum):
    BUSINESS_EXPERIMENT = "business_experiment"
    EXECUTION = "execution"
    DIAGNOSTIC = "diagnostic"
    SYSTEM_IMPROVEMENT = "system_improvement"
    EVALUATION = "evaluation"
    SYSTEM_TEST = "system_test"


class EvidenceValidity(str, Enum):
    BUSINESS = "business"
    TECHNICAL_ONLY = "technical_only"
    CONTAMINATED = "contaminated"
    INVALID = "invalid"


@dataclass(frozen=True)
class Goal:
    id: str
    name: str
    engine_id: str
    metric: str
    operator: str
    target: Any
    deadline: str | None
    parent_id: str | None
    goal_status: str
    config: dict[str, Any]


@dataclass(frozen=True)
class EngineContext:
    goal: Goal
    cycle: dict[str, Any]
    memory: tuple[dict[str, Any], ...]
    approval_status: Callable[[str], str | None]
    dispatch_goal: Callable[[str], dict[str, Any]] | None = None
    create_child_goal: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    create_change_task: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    update_change_task: Callable[[str, str, dict[str, Any]], dict[str, Any]] | None = None


@dataclass
class StageResult:
    step: str
    payload: dict[str, Any] = field(default_factory=dict)
    run_status: RunStatus = RunStatus.RUNNING
    next_stage: Stage | None = None
    goal_status: GoalStatus | None = None
    resume_at: str | None = None
    message: str = ""
    learnings: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    decision: dict[str, Any] | None = None
    evaluation: dict[str, Any] | None = None
    next_run: dict[str, Any] | None = None
    attention: dict[str, Any] | None = None


@dataclass(frozen=True)
class WorkflowSpec:
    """A named playbook inside a Department; never a second runtime loop."""

    id: str
    description: str
    steps: tuple[str, ...]
    agent_ids: tuple[str, ...] = ()
    skill_ids: tuple[str, ...] = ()
    approval_points: tuple[str, ...] = ()
    evidence_sources: tuple[str, ...] = ()
    external_actions: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentSpec:
    """A bounded executor identity used by one or more workflow steps."""

    id: str
    description: str
    skill_ids: tuple[str, ...]
    permissions: tuple[str, ...]
    produces: tuple[str, ...]


@dataclass(frozen=True)
class ContentPackage:
    """A run artifact grouping one idea and its coordinated deliverables."""

    id: str
    goal_id: str
    run_id: str
    brief: dict[str, Any]
    deliverables: tuple[dict[str, Any], ...] = ()
    evidence_ids: tuple[str, ...] = ()
    publication: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolSpec:
    """Stable business operation; Connections provide its transport."""

    id: str
    description: str
    operations: tuple[str, ...]
    approval_operations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConnectionSpec:
    """Replaceable adapter for an external or repository-local system."""

    id: str
    tool_id: str
    description: str
    capabilities: tuple[str, ...]
    required_environment: tuple[str, ...] = ()


class Engine:
    id = "base"
    description = ""
    goal_schema: dict[str, Any] = {}
    version = "1.0.0"
    deprecated = False

    def observe(self, ctx: EngineContext) -> StageResult:
        raise NotImplementedError

    def decide(self, ctx: EngineContext, observation: dict[str, Any]) -> StageResult:
        raise NotImplementedError

    def act(self, ctx: EngineContext, decision: dict[str, Any]) -> StageResult:
        raise NotImplementedError

    def evaluate(self, ctx: EngineContext, action_result: dict[str, Any]) -> StageResult:
        raise NotImplementedError


class Department(Engine):
    """Human-facing business unit plugged into the one company runtime."""

    department_id = ""
    workflows: tuple[WorkflowSpec, ...] = ()
    agent_ids: tuple[str, ...] = ()
    production_ready = True
