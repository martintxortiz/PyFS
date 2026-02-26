from dataclasses import dataclass
from typing import Any
from pyfs.common.mid import MessageID

@dataclass
class Message:
    mid: MessageID
    timestamp: int
    payload: Any