"""Data contracts shared by discovery, qualification, execution, and reporting."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LeadState(str, Enum):
    DISCOVERED = "discovered"
    QUALIFIED = "qualified"
    RESEARCHED = "researched"
    READY = "ready"
    ACTION_PENDING = "action_pending"
    ACTIONED = "actioned"
    REPLIED = "replied"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    DO_NOT_CONTACT = "do_not_contact"


class Action(str, Enum):
    RESEARCH = "research"
    QUALIFY = "qualify"
    DRAFT = "draft"
    SEND_EMAIL = "send_email"
    SEND_DM = "send_dm"
    SEND_CONNECTION = "send_connection"
    PUBLISH = "publish"
    RECORD_REPLY = "record_reply"


@dataclass
class Lead:
    lead_id: str
    name: str
    company: str
    role: str = ""
    location: str = ""
    channels: list[str] = field(default_factory=list)
    profile_url: str = ""
    company_url: str = ""
    state: LeadState = LeadState.DISCOVERED
    icp_score: int = 0
    research_fact: str = ""
    operational_consequence: str = ""
    message: str = ""
    source_urls: list[str] = field(default_factory=list)
    exclusion_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowGoal:
    workflow_id: str
    channel: str
    action: str
    target: int
    min_icp_score: int = 75
    queue_target: int = 100
    enabled: bool = True

