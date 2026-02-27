"""Immutable message envelope carried on the software bus.

Every piece of data exchanged between nodes is wrapped in an ``FSMessage``.
The dataclass is frozen so messages cannot be mutated after creation.
A monotonically increasing sequence counter and a real timestamp are
automatically assigned at construction time.
"""

from __future__ import annotations

import itertools
import time
from dataclasses import dataclass, field
from typing import Any

from pyfs.common.mid import MID

# Thread-safe monotonic counter (itertools.count is implemented in C,
# lock-free, and will never overflow in Python).
_seq_counter: itertools.count[int] = itertools.count()


@dataclass(frozen=True, slots=True)
class FSMessage:
    """Immutable envelope carried on the software bus.

    Attributes:
        mid:       Message-type identifier from the ``MID`` registry.
        sender:    Name of the originating node.
        payload:   Application-defined data (``None`` for wakeup ticks).
        seq:       Auto-assigned monotonic sequence number.
        timestamp: ``time.monotonic()`` snapshot captured at creation.
    """

    mid: MID
    sender: str
    payload: Any = None
    seq: int = field(default_factory=lambda: next(_seq_counter))
    timestamp: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        assert isinstance(self.mid, MID), "mid must be a MID enum member"
        assert isinstance(self.sender, str) and len(self.sender) > 0, "sender must be a non-empty string"
        assert self.seq >= 0, "seq must be non-negative"
        assert self.timestamp >= 0.0, "timestamp must be non-negative"
