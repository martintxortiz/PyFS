from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Dict

class ResetType(Enum):
    POWER_ON = auto()
    PROCESSOR = auto()
    COMMAND = auto()