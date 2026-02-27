"""Base node (application) for the flight-software framework.

Every component that participates on the software bus extends ``FSNode``.
Subclasses override the lifecycle hooks ``on_init``, ``on_start``, and
``on_stop`` to perform application-specific work.

Lifecycle State Machine::

    INIT ──_start()──> STARTED ──_stop()──> STOPPED

Invalid transitions are assertion failures — they indicate a logic error
in the executive or node code and must be caught during development.
"""

from __future__ import annotations

import logging
from enum import IntEnum, unique

from pyfs.core.bus import FSBus


@unique
class NodeState(IntEnum):
    """Lifecycle states a node can be in."""

    __slots__ = ()

    INIT    = 0
    STARTED = 1
    STOPPED = 2


class FSNode:
    """Abstract base for every flight-software node.

    A node owns a name, a reference to the shared ``FSBus``, and a current
    ``NodeState``.  The executive drives the lifecycle by calling ``_start``
    and ``_stop``; subclasses hook into them via the ``on_*`` callbacks.
    """

    __slots__ = ("name", "_bus", "state", "_log")

    def __init__(self, name: str, bus: FSBus) -> None:
        assert isinstance(name, str) and len(name) > 0, "name must be a non-empty string"
        assert isinstance(bus, FSBus), "bus must be an FSBus instance"

        self.name: str = name
        self._bus: FSBus = bus
        self.state: NodeState = NodeState.INIT
        self._log: logging.Logger = logging.getLogger(f"fs.{self.name}")

        self.on_init()
        self._log.info("[%s] initialized", self.name)

        assert self.state is NodeState.INIT, "on_init must not change node state"

    # -- Lifecycle — called by the executive ---------------------------

    def _start(self) -> None:
        """Transition ``INIT -> STARTED`` and invoke the ``on_start`` hook."""
        assert self.state is NodeState.INIT, (
            f"[{self.name}] cannot start from state {self.state.name}"
        )

        self.on_start()
        self.state = NodeState.STARTED
        self._log.info("[%s] started", self.name)

    def _stop(self) -> None:
        """Transition ``STARTED -> STOPPED`` and invoke the ``on_stop`` hook."""
        assert self.state is NodeState.STARTED, (
            f"[{self.name}] cannot stop from state {self.state.name}"
        )

        self.on_stop()
        self.state = NodeState.STOPPED
        self._log.info("[%s] stopped", self.name)

    # -- Hooks for subclasses ------------------------------------------

    def on_init(self) -> None:
        """Called once at the end of ``__init__``.  Override for setup."""

    def on_start(self) -> None:
        """Called when the executive starts this node.  Override to begin work."""

    def on_stop(self) -> None:
        """Called when the executive stops this node.  Override to clean up."""