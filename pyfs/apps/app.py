from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Any

class AppState(Enum):
    UNREGISTERED = auto()
    REGISTERED = auto()
    RUNNING = auto()
    STOPPED = auto()
    FAILED = auto()

@dataclass
class AppInfo:
    app_id: int
    name: str
    priority: int
    state: AppState
    metadata: Dict[str, Any]