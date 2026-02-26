from dataclasses import dataclass, field
from typing import Any
from fs.common.message_ids import MID_UNDEFINED

@dataclass(slots=True)
class Message:
    mid:       int       # who is this for — the routing key
    aid:       int       # who sent this — the sender app ID
    func_code: int = 0   # only meaningful for commands, 0 for telemetry
    payload:   dict[str, Any] = field(default_factory=dict) # the actual data — anything goes here
    _seq:      int = field(default=0, init=False, repr=False)
    _timestamp: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self):
        if self.mid == MID_UNDEFINED:
            raise ValueError("MID_UNDEFINED is never a valid routing key")

    @property
    def seq(self) -> int:
        return self._seq

    @property
    def timestamp(self) -> float:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        raise AttributeError("cannot mutate timestamp from outside")
