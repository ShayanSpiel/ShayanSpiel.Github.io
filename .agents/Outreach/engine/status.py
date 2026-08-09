"""Status surface: data/status.json + the engine log.

Domain-free: it only knows the phase, the last snapshot headline, and the
hold reason. The owner/assistant reads `status` instead of grepping logs.
"""

import json
import os
from datetime import datetime, timezone


def write(ctx) -> dict:
    status = {
        "at": datetime.now(timezone.utc).isoformat(),
        "phase": ctx.store.phase(),
        "batch": ctx.store.current_batch_id(),
        "hold_reason": ctx.store.hold_reason(),
        "evidence_due": ctx.store.evidence_due(),
    }
    path = ctx.data_dir / "status.json"
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    return status
