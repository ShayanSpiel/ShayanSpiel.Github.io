"""Engine context: the bundle of substrate every step receives.

The loop passes this one object around. It holds the STATE (store), the
human-written CONTROL (control.json), the active WORKFLOW bundle, and the
artifact/report/log locations. Steps never reach for global paths.
"""

from dataclasses import dataclass
from pathlib import Path

from .. import workflows
from ..store import OutreachStore
from .artifacts import Artifacts
from .control import Control
from .policy import Policy


@dataclass
class Context:
    store: OutreachStore
    control: Control
    workflow: workflows.Workflow
    artifacts: Artifacts
    policy: Policy
    stop_file: Path
    data_dir: Path
    reports_dir: Path
    dry: bool = False
