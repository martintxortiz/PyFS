"""Flight-software executive — the top-level orchestrator.

The ``FSExecutive`` owns the software bus, maintains the registry of nodes,
and runs the deterministic single-threaded main loop.  It installs signal
handlers for ``SIGINT`` and ``SIGTERM`` so the system shuts down gracefully.

Execution Model:
    The main loop runs cooperatively on a single thread::

        while not shutdown:
            scheduler.dispatch_pending()
            sleep(minor_frame_s)

    All handler invocations happen synchronously and deterministically.
    No application-level threads exist.
"""

from __future__ import annotations

import logging
import signal
import time
import types

from pyfs.common.config import SystemConfig
from pyfs.core.bus import FSBus
from pyfs.core.node import FSNode
from pyfs.nodes.scheduler import FSSchedulerNode


class FSExecutive:
    """Top-level orchestrator for the flight-software framework.

    Usage::

        exe = FSExecutive(config)
        exe.register_node(my_node)
        exe.start()
    """

    __slots__ = ("_log", "_cfg", "_nodes", "_bus", "_shutdown")

    def __init__(self, cfg: SystemConfig) -> None:
        assert isinstance(cfg, SystemConfig), "cfg must be a SystemConfig"

        self._log: logging.Logger = logging.getLogger("fs.executive")
        self._cfg: SystemConfig = cfg
        self._nodes: list[FSNode] = []
        self._bus: FSBus = FSBus(cfg.bus)
        self._shutdown: bool = False

        self._log.info("executive initialized")

    # -- Public properties ---------------------------------------------

    @property
    def bus(self) -> FSBus:
        """Read-only access to the shared software bus."""
        return self._bus

    # -- Public API ----------------------------------------------------

    def register_node(self, node: FSNode) -> None:
        """Add *node* to the executive's registry.

        Asserts that the node limit from ``SystemConfig`` is not exceeded.
        """
        assert isinstance(node, FSNode), "node must be an FSNode"
        assert len(self._nodes) < self._cfg.max_nodes, (
            f"node capacity exceeded ({self._cfg.max_nodes})"
        )

        self._nodes.append(node)
        self._log.info("registered node (%s)", node.name)

    def start(self) -> None:
        """Start all nodes, launch the scheduler, and run the main loop.

        Installs ``SIGINT`` / ``SIGTERM`` handlers for graceful shutdown.
        Blocks until a shutdown signal is received, then stops all nodes
        in reverse-registration order.
        """
        self._install_signal_handlers()

        # -- Bootstrap scheduler ---------------------------------------
        scheduler: FSSchedulerNode = FSSchedulerNode(self._bus)
        scheduler.configure(self._cfg.rate_groups)

        # -- Start user nodes ------------------------------------------
        for node in self._nodes:
            node._start()

        # -- Start scheduler -------------------------------------------
        scheduler._start()

        self._log.info(
            "system running — %d node(s), %d rate group(s)",
            len(self._nodes), len(self._cfg.rate_groups),
        )

        # -- Deterministic main loop -----------------------------------
        while not self._shutdown:
            scheduler.dispatch_pending()
            time.sleep(self._cfg.minor_frame_s)

        # -- Graceful shutdown -----------------------------------------
        self._log.info("shutdown sequence initiated")
        scheduler._stop()
        for node in reversed(self._nodes):
            node._stop()
        self._log.info("all nodes stopped — shutdown complete")

    # -- Internal ------------------------------------------------------

    def _install_signal_handlers(self) -> None:
        """Register ``SIGINT`` / ``SIGTERM`` to trigger shutdown."""

        def _handler(signum: int, _frame: types.FrameType | None) -> None:
            sig_name: str = signal.Signals(signum).name
            self._log.info("received %s — requesting shutdown", sig_name)
            self._shutdown = True

        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)