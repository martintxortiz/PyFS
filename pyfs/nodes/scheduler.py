"""Deterministic periodic scheduler node.

``FSSchedulerNode`` fires wakeup messages at configurable rates using a
simple linear scan of rate-group entries.  No heap, no threading — the
executive calls ``dispatch_pending()`` every minor frame from the main loop.

The number of rate groups is small and fixed (typically <= 4), so a linear
scan is both simpler and equally fast compared to a heap.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from pyfs.common.config import RateGroupConfig
from pyfs.common.mid import MID
from pyfs.core.bus import FSBus
from pyfs.core.message import FSMessage
from pyfs.core.node import FSNode


@dataclass(slots=True)
class _RateGroupState:
    """Mutable runtime state for one rate group."""

    mid: MID
    interval_ns: int
    next_tick_ns: int


class FSSchedulerNode(FSNode):
    """Deterministic inline scheduler driven by the executive main loop.

    The executive calls ``dispatch_pending()`` each minor frame.  For every
    rate group whose deadline has passed, the scheduler publishes the
    corresponding wakeup MID on the bus and advances the deadline.
    """

    __slots__ = ("_groups",)

    def __init__(self, bus: FSBus) -> None:
        super().__init__("sch", bus)
        self._groups: list[_RateGroupState] = []

    def configure(self, rate_groups: tuple[RateGroupConfig, ...]) -> None:
        """Load rate-group definitions from the system configuration.

        Must be called before ``_start()``.  Each entry creates an internal
        ``_RateGroupState`` seeded with the current high-resolution clock.
        """
        assert len(rate_groups) > 0, "at least one rate group required"
        assert len(self._groups) == 0, "configure must only be called once"

        now_ns: int = time.perf_counter_ns()

        for rg in rate_groups:
            assert isinstance(rg, RateGroupConfig), "each entry must be a RateGroupConfig"
            interval_ns: int = 1_000_000_000 // rg.rate_hz
            self._groups.append(_RateGroupState(
                mid=rg.mid,
                interval_ns=interval_ns,
                next_tick_ns=now_ns,
            ))

        self._log.info(
            "%d rate group(s) configured", len(self._groups),
        )

        assert len(self._groups) == len(rate_groups), "post: all rate groups loaded"

    def dispatch_pending(self) -> None:
        """Publish wakeup MIDs for all rate groups whose deadline has passed.

        Called once per minor frame by the executive.  The loop has a fixed
        upper bound equal to the number of configured rate groups.
        """
        now_ns: int = time.perf_counter_ns()

        # Bounded loop: exactly len(self._groups) iterations.
        for group in self._groups:
            if now_ns >= group.next_tick_ns:
                self._bus.publish(FSMessage(mid=group.mid, sender=self.name))
                group.next_tick_ns += group.interval_ns