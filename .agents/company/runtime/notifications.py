"""Delivery of persisted company notifications (runner -> humans/ops).

Notifications are durable rows in the SQLite store, accumulated by the runtime
while goals advance. Delivery marks a pending notification as delivered via
``store.acknowledge_notification`` so it stops piling up unseen while the
runner daemon is on. The daemon's watch loop (the CLI ``runner watch``
command spawned by ``RunnerService.start``) calls ``deliver_pending`` after
every tick.

Delivery only records that the notification was surfaced — it never changes
the goal's run state. An ``approval_required`` notification is *seen*, not
approved; ``company approve`` remains the only gate for the prepared action.
"""

from __future__ import annotations


def deliver_pending(store, limit: int = 100) -> int:
    """Deliver up to ``limit`` pending notifications; return how many.

    Delivery is persistent: every pending row (oldest first, matching the
    store's ordering) is marked ``delivered`` with a ``delivered_at``
    timestamp through the same store call the CLI ``notifications ack``
    command uses.
    """
    pending = store.notifications("pending", limit)
    for row in pending:
        store.acknowledge_notification(row["id"])
    return len(pending)


def dispatch(store, limit: int = 100) -> int:
    """Alias of :func:`deliver_pending` for callers that prefer a dispatch verb."""
    return deliver_pending(store, limit=limit)


def deliver(store, notification_id: str) -> dict:
    """Deliver one notification by id; returns the updated notification row."""
    return store.acknowledge_notification(notification_id)
