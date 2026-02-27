"""Singleton software bus — routes messages between node queues."""

import logging
import queue
from typing import Callable, Dict, List, Optional, Tuple

from pyfs.common.fs_mid import Mid
from pyfs.core.fs_message import FSMessage

MessageReceiver = Callable[[FSMessage], None]
_Subscriber = Tuple["queue.Queue[Tuple[Mid, FSMessage, MessageReceiver]]", MessageReceiver]


class FSBus:
    """Singleton publish-subscribe bus.

    pub() places (mid, message, handler) into each subscriber's private queue
    and returns immediately — no subscriber can stall the publisher.
    """

    __slots__ = {"log", "routes", "_initialized"}
    _instance: Optional["FSBus"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.log = logging.getLogger("fs.bus")
        self.routes: Dict[Mid, List[_Subscriber]] = {}
        self.log.info("bus initialized")

    def sub(
            self,
            mid: Mid,
            q: "queue.Queue[Tuple[Mid, FSMessage, MessageReceiver]]",
            handler: MessageReceiver,
    ) -> None:
        """Register *handler* as a subscriber of *mid*, delivered via *q*."""
        self.routes.setdefault(mid, []).append((q, handler))

        # Resolve a human-readable handler name for the log line.
        if hasattr(handler, "__self__") and handler.__self__:
            full_name = f"{handler.__self__.__class__.__name__}.{handler.__name__}"
        else:
            full_name = handler.__name__

        self.log.info("(%s) subscribed [%s (%s)]", full_name, mid.name, mid)

    def pub(self, mid: Mid, message: FSMessage) -> None:
        """Publish *message* to every subscriber of *mid*.

        Each subscriber's queue receives (mid, message, handler).
        This call never blocks.
        """
        for q, handler in self.routes.get(mid, []):
            try:
                q.put_nowait((mid, message, handler))
            except queue.Full:
                self.log.warning(
                    "queue full for handler [%s] on mid [%s] — message dropped",
                    handler.__name__,
                    mid.name,
                )