"""Production SEO Department."""

from ._evidence import EvidenceDepartment
from ..models import Department, WorkflowSpec


class SeoDepartment(EvidenceDepartment, Department):
    id = department_id = "seo"
    version = "1.0.0"
    description = "Researches search demand, improves technical and on-page SEO, and evaluates Search Console evidence."
    agent_ids = ("seo-researcher", "seo-operator")
    production_ready = True
    workflows = (
        WorkflowSpec("keyword-research", "Build an evidence-backed ICP-aligned opportunity map without invented volume.",
                     ("seeds", "query", "cluster", "score", "validate"), ("seo-researcher",), ("seo",), (),
                     ("search_console_query", "keyword_opportunity"), ("query_search_console",)),
        WorkflowSpec("seo-content-brief", "Turn a validated opportunity into a content brief.",
                     ("select", "intent", "serp_evidence", "outline", "review"), ("seo-researcher",),
                     ("seo", "copywriting-en"), (), ("keyword_opportunity", "seo_brief"), ()),
        WorkflowSpec("technical-audit", "Audit crawl, index, canonical, locale, schema, and performance contracts.",
                     ("crawl", "inspect", "prioritize", "brief"), ("seo-operator",), ("seo",), (),
                     ("site_audit", "search_console_query"), ("query_search_console",)),
        WorkflowSpec("seo-improvement", "Apply one approved SEO change and measure its effect.",
                     ("observe", "propose", "approve", "implement", "measure"), ("seo-operator",),
                     ("seo", "analytics"), ("modify_site",), ("seo_change", "search_console_query"), ("modify_site",)),
        WorkflowSpec("search-performance", "Monitor queries, pages, CTR, position, and indexing changes.",
                     ("query", "validate", "compare", "report"), ("seo-operator",), ("seo", "analytics"), (),
                     ("search_console_query", "seo_report"), ("query_search_console",)),
    )
    goal_schema = {"metrics": ["keyword_opportunities", "seo_briefs", "seo_reports", "indexed_pages"],
                   "config": {"workflow": {"enum": [w.id for w in workflows]},
                              "required_count": {"type": "integer"},
                              "connection": {"enum": ["search-console"]}}}
    evidence_metrics = {"keyword_opportunities": ("keyword_opportunity",),
                        "seo_briefs": ("seo_brief",), "seo_reports": ("seo_report",),
                        "indexed_pages": ("indexed_page",)}
    workflow_agents = {"keyword-research": "seo-researcher", "seo-content-brief": "seo-researcher",
                       "technical-audit": "seo-operator", "seo-improvement": "seo-operator",
                       "search-performance": "seo-operator"}
