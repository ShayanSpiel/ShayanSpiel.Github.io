"""One human-readable catalog for the universal company vocabulary."""

from pathlib import Path

from ..agents import agents as installed_agents
from ..connections import connections as installed_connections
from .registry import departments as installed_departments

COMPANY_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = COMPANY_ROOT.parent / "skills"


def _workflow(item):
    return {
        "id": item.id,
        "description": item.description,
        "steps": list(item.steps),
        "agents": list(item.agent_ids),
        "skills": list(item.skill_ids),
        "approvals": list(item.approval_points),
        "evidence": list(item.evidence_sources),
        "connections": list(item.connection_ids),
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
        values.append({"id": name, "description": description,
                       "path": str(path.relative_to(COMPANY_ROOT.parent))})
    return values


def catalog():
    departments = [{
        "id": item.department_id,
        "version": item.version,
        "description": item.description,
        "workflows": [_workflow(workflow) for workflow in item.workflows],
        "agents": list(item.agent_ids),
    } for _, item in sorted(installed_departments().items())]
    return {
        "runtime": {
            "version": "5.1.0",
            "loop": ["GOAL", "OBSERVE", "DECIDE", "ACT", "EVALUATE"],
            "controls": ["director", "system-improvement"],
            "goal_authority": ".spielos/state/company.sqlite",
        },
        "departments": departments,
        "agents": [vars(item) for _, item in sorted(installed_agents().items())],
        "skills": _skills(),
        "connections": [vars(item) for _, item in sorted(installed_connections().items())],
        "artifact_authority": ".spielos/artifacts/",
    }
