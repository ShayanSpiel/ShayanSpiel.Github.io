"""Production Analytics Department."""

from ._evidence import EvidenceDepartment
from ..models import Department, WorkflowSpec


class AnalyticsDepartment(EvidenceDepartment, Department):
    id = department_id = "analytics"
    version = "1.0.0"
    description = "Maintains company metrics, full-funnel evidence, attribution, diagnostics, and CRO experiments."
    agent_ids = ("analytics-operator", "cro-optimizer")
    production_ready = True
    workflows = (
        WorkflowSpec("company-scorecard", "Report canonical business and Department metrics.",
                     ("collect", "validate", "calculate", "report"), ("analytics-operator",), ("analytics",), (),
                     ("posthog_query", "department_evidence"), ("query_posthog",)),
        WorkflowSpec("funnel-analysis", "Measure acquisition through sale and locate the largest valid drop-off.",
                     ("validate", "query", "segment", "diagnose", "report"), ("analytics-operator",),
                     ("analytics",), (), ("posthog_query", "funnel_report"), ("query_posthog",)),
        WorkflowSpec("cro-experiment", "Propose and evaluate one bounded conversion experiment.",
                     ("diagnose", "hypothesis", "approve", "run", "evaluate"), ("cro-optimizer",),
                     ("analytics", "copywriting-en", "spielos-ui"), ("start_experiment",),
                     ("funnel_report", "cro_experiment"), ("modify_site",)),
        WorkflowSpec("department-insight", "Feed validated metrics to another Department goal.",
                     ("request", "query", "validate", "attach"), ("analytics-operator",), ("analytics",), (),
                     ("department_evidence",), ("query_posthog",)),
    )
    goal_schema = {"metrics": ["scorecards", "funnel_reports", "cro_experiments", "attributed_conversions"],
                   "config": {"workflow": {"enum": [w.id for w in workflows]},
                              "required_count": {"type": "integer"},
                              "connection": {"enum": ["posthog"]}}}
    evidence_metrics = {"scorecards": ("company_scorecard",),
                        "funnel_reports": ("funnel_report",),
                        "cro_experiments": ("cro_experiment",),
                        "attributed_conversions": ("attributed_conversion",)}
    workflow_agents = {"company-scorecard": "analytics-operator", "funnel-analysis": "analytics-operator",
                       "cro-experiment": "cro-optimizer", "department-insight": "analytics-operator"}
