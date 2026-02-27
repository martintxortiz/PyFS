"""Base class for all PyFS nodes.

Concrete subclasses placed in ``pyfs/nodes/`` are auto-registered via
FSNodeMeta at import time.  FSExecutive queries the registry to init and
start every node in a deterministic order.

Each node owns a private queue and a dispatch thread.  The bus delivers
messages as (mid, message, handler) tuples; the dispatch thread calls the
handler.  A slow node cannot delay another node.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import ClassVar

from pyfs.core.fs_bus import FSBus
from pyfs.common.fs_mid import Mid


_QUEUE_MAXSIZE: int = 64  # drop messages rather than let memory grow unbounded


class FSNodeMeta(type):
    """Metaclass that auto-appends every FSNode subclass to FSNode._registry."""

    def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, object],
    ) -> None:
        super().__init__(name, bases, attrs)
        if not bases:
            cls._registry: list[type[FSNode]] = []
        else:
            FSNode._registry.append(cls)


class FSNode(metaclass=FSNodeMeta):
    """Abstract base class for all PyFS nodes.

    Override on_init, on_start, and on_stop in subclasses.
    Use sub() to subscribe to a MID — never call bus.sub() directly,
    as the node needs to wire its own queue into the delivery path.

    Attributes:
        bus:  Shared message bus singleton.
        log:  Logger named after the concrete class.
        name: Short identifier string, override in subclass.
    """

    _registry: ClassVar[list[type["FSNode"]]]

    #: Set to False on a subclass to exclude it from the executive entirely.
    enabled: ClassVar[bool] = True

    bus:  FSBus
    log:  logging.Logger
    name: str = "node"

    def __init__(self) -> None:
        self.bus: FSBus = FSBus()
        self.log: logging.Logger = logging.getLogger(f"fs.{self.name}")
        self._queue: queue.Queue = queue.Queue(maxsize=_QUEUE_MAXSIZE)
        self._dispatch_stop: threading.Event = threading.Event()
        self._dispatch_thread: threading.Thread = threading.Thread(
            target=self._dispatch_loop,
            name=f"fs.{self.name}.dispatch",
            daemon=True,
        )
        self._sub_count: int = 0

    # ── Subscription ──────────────────────────────────────────────────────────

    def sub(self, mid: Mid, handler) -> None:
        """Subscribe *handler* to *mid* through this node's private queue."""
        self.bus.sub(mid, self._queue, handler)
        self._sub_count += 1

    # ── Registry ──────────────────────────────────────────────────────────────

    @classmethod
    def get_registry(cls) -> list[type["FSNode"]]:
        """Return the list of registered concrete node classes."""
        return cls._registry

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def init(self) -> None:
        """Initialise the node. Called once before start()."""
        self.on_init()
        self.log.info("%s initialized", self.name)

    def start(self) -> None:
        """Start the node. The dispatch thread is only started if the node has subscribers."""
        if self._sub_count > 0:
            self._dispatch_thread.start()
        self.on_start()
        self.log.info("%s started", self.name)

    def stop(self) -> None:
        """Signal the dispatch thread to exit, join it, then call on_stop."""
        self._dispatch_stop.set()
        if self._dispatch_thread.is_alive():
            self._dispatch_thread.join(timeout=2)
            if self._dispatch_thread.is_alive():
                self.log.warning("%s dispatch thread did not exit cleanly", self.name)
        self.on_stop()
        self.log.info("%s stopped", self.name)

    # ── Dispatch loop ─────────────────────────────────────────────────────────

    def _dispatch_loop(self) -> None:
        """Pull (mid, msg, handler) from the queue and invoke the handler."""
        while not self._dispatch_stop.is_set():
            try:
                mid, msg, handler = self._queue.get(timeout=0.1)
                try:
                    handler(msg)
                except Exception as exc:
                    self.log.error(
                        "handler [%s] raised on mid [%s]: %s",
                        handler.__name__,
                        mid.name,
                        exc,
                    )
                finally:
                    self._queue.task_done()
            except queue.Empty:
                continue

    # ── Overridable hooks ─────────────────────────────────────────────────────

    def on_init(self) -> None:
        pass

    def on_start(self) -> None:
        pass

    def on_stop(self) -> None:
        pass