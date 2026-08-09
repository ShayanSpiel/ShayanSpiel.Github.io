"""Goal-driven loop. It chooses work; adapters decide how an action executes."""

from dataclasses import dataclass

from .models import Action, Lead, LeadState, WorkflowGoal
from .policy import check_action, check_lead
from .store import OutreachStore


@dataclass
class NextWork:
    lead: Lead | None
    action: Action | None
    reason: str


class OutreachLoop:
    def __init__(self, store: OutreachStore, goal: WorkflowGoal):
        self.store = store
        self.goal = goal
        self.store.add_goal(goal)

    def status(self) -> dict:
        sent = self.store.action_count(self.goal.channel, self.goal.action, "sent")
        connected = self.store.action_count(self.goal.channel, "send_connection", "connection_sent")
        queue = len(self.store.ready_queue(self.goal.channel, self.goal.queue_target, self.goal.min_icp_score))
        return {"workflow_id": self.goal.workflow_id, "channel": self.goal.channel,
                "target": self.goal.target, "sent": sent, "connections": connected,
                "remaining": max(0, self.goal.target - sent), "ready_queue": queue,
                "complete": sent >= self.goal.target}

    def next_work(self) -> NextWork:
        status = self.status()
        if status["complete"]:
            return NextWork(None, None, "goal reached")
        for lead in self.store.ready_queue(self.goal.channel, 1, self.goal.min_icp_score):
            lead_check = check_lead(lead, self.goal.min_icp_score)
            if not lead_check.allowed:
                self.store.record_action(lead.lead_id, self.goal.channel, "qualify", "rejected", lead_check.reason)
                continue
            action = Action(self.goal.action)
            action_check = check_action(self.goal.channel, action)
            if not action_check.allowed:
                return NextWork(lead, action, action_check.reason)
            return NextWork(lead, action, "ready")
        return NextWork(None, None, "ready queue empty")

    def record(self, lead_id: str, action: str, result: str, note: str = "") -> None:
        self.store.record_action(lead_id, self.goal.channel, action, result, note)

