"""Publish / subscribe software bus.

The ``FSBus`` is the single-threaded communication backbone of the
flight-software framework.  Nodes subscribe to specific ``MID`` values and
receive every ``FSMessage`` published under that ID.

Single-Threaded Model:
    The bus is designed for cooperative single-threaded execution driven by
    the executive's main loop.  No locks are needed — all access happens on
    the main thread.

Fixed Capacity:
    The subscriber table enforces a maximum number of handlers per MID and
    a maximum number of distinct MIDs, both configured via ``BusConfig``.

Fail-Fast:
    If a handler raises, the exception propagates immediately.  In safety-
    critical software, silent fault isolation hides bugs.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from pyfs.common.config import BusConfig
from pyfs.common.mid import MID
from pyfs.core.message import FSMessage

_log: logging.Logger = logging.getLogger("fs.bus")


class FSBus:
    """Central publish/subscribe message bus (single-threaded).

    The bus enforces capacity limits from ``BusConfig`` and validates all
    inputs.  No dynamic allocation occurs after ``subscribe`` calls complete.
    """

    __slots__ = ("_cfg", "_subscribers")

    def __init__(self, cfg: BusConfig) -> None:
        assert isinstance(cfg, BusConfig), "cfg must be a BusConfig"
        self._cfg: BusConfig = cfg
        self._subscribers: dict[MID, list[Callable[[FSMessage], None]]] = {}

    # -- Public API ----------------------------------------------------

    def subscribe(self, mid: MID, handler: Callable[[FSMessage], None]) -> bool:
        """Register *handler* for messages with *mid*.

        Returns ``True`` on success, ``False`` if capacity is reached or
        the handler is already subscribed.
        """
        assert isinstance(mid, MID), "mid must be a MID enum member"
        assert callable(handler), "handler must be callable"

        handlers: list[Callable[[FSMessage], None]] = self._subscribers.get(mid, [])

        # Duplicate check.
        if handler in handlers:
            return False

        # Capacity check — distinct MIDs.
        if mid not in self._subscribers:
            assert len(self._subscribers) < self._cfg.max_mids, (
                f"bus MID capacity exceeded ({self._cfg.max_mids})"
            )
            self._subscribers[mid] = handlers

        # Capacity check — handlers per MID.
        assert len(handlers) < self._cfg.max_subscribers_per_mid, (
            f"subscriber capacity for MID 0x{int(mid):04X} exceeded "
            f"({self._cfg.max_subscribers_per_mid})"
        )

        handlers.append(handler)
        return True

    def unsubscribe(self, mid: MID, handler: Callable[[FSMessage], None]) -> bool:
        """Remove *handler* from the subscriber list for *mid*.

        Returns ``True`` if removed, ``False`` if not found.
        """
        assert isinstance(mid, MID), "mid must be a MID enum member"

        handlers: list[Callable[[FSMessage], None]] | None = self._subscribers.get(mid)
        if handlers is None:
            return False

        try:
            handlers.remove(handler)
            return True
        except ValueError:
            return False

    def publish(self, msg: FSMessage) -> None:
        """Deliver *msg* to every handler subscribed to ``msg.mid``.

        Handlers are invoked synchronously in registration order.
        Exceptions propagate immediately (fail-fast).
        """
        assert isinstance(msg, FSMessage), "msg must be an FSMessage"

        handlers: list[Callable[[FSMessage], None]] | None = self._subscribers.get(msg.mid)
        if handlers is None:
            return

        for handler in handlers:
            handler(msg)
