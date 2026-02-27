"""Immutable message envelope passed on the software bus."""

from dataclasses import dataclass, field
import time
from typing import Any

from pyfs.common.fs_mid import Mid


@dataclass(frozen=True, slots=True)
class FSMessage:
    """A MID, an optional payload, and a monotonic timestamp."""

    mid:       Mid
    payload:   Any
    timestamp: float = field(default_factory=time.monotonic)