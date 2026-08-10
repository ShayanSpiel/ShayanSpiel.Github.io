"""One human-readable catalog for Departments, workflows, agents, and skills."""

from pathlib import Path

from .agents import agents as installed_agents
from .models import Department
from .registry import engines
from .tools import tools as installed_tools
from .connections import connections as installed_connections

COMPANY_ROOT = Path(__file__).resolve().parent
SKILLS_ROOT = COMPANY_ROOT.parent / "skills"


def _workflow(item):
    return {
        "id": item.id,
        "description": item.description,
        "steps": list(item.steps),
        "agents": list(item.agent_ids),
        "skills": list(item.skill_ids),
        "approval_points": list(item.approval_points),
        "evidence_sources": list(item.evidence_sources),
        "external_actions": list(item.external_actions),
    }


def _skills():
    values = []
    for path in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
        name, description = path.parent.name, ""
        for line in path.read_text().splitlines()[1:20]:
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("description:"):
                description = line.split(":", 1)[1].strip().strip('"')
        values.append({"id": name, "description": description, "path": str(path.relative_to(COMPANY_ROOT.parent))})
    return values


def catalog():
    departments = []
    control_engines = []
    compatibility_engines = []
    for engine_id, engine in sorted(engines().items()):
        if isinstance(engine, Department):
            departments.append({
                "id": engine.department_id or engine_id,
                "engine_id": engine_id,
                "version": engine.version,
                "description": engine.description,
                "production_ready": engine.production_ready,
                "workflows": [_workflow(item) for item in engine.workflows],
                "agents": list(engine.agent_ids),
            })
        elif getattr(engine, "deprecated", False):
            compatibility_engines.append({"id": engine_id, "version": engine.version,
                                          "description": engine.description})
        else:
            control_engines.append({"id": engine_id, "version": engine.version,
                                    "description": engine.description})
    return {
        "runtime": {"loop": ["GOAL", "OBSERVE", "DECIDE", "ACT", "EVALUATE"],
                    "goal_authority": ".spielos/state/company.sqlite"},
        "departments": departments,
        "agents": [vars(item) for _, item in sorted(installed_agents().items())],
        "skills": _skills(),
        "tools": [vars(item) for _, item in sorted(installed_tools().items())],
        "connections": [vars(item) for _, item in sorted(installed_connections().items())],
        "control_engines": control_engines,
        "compatibility_engines": compatibility_engines,
    }
