"""Framework executive — owns the node lifecycle and signal handling."""

from __future__ import annotations

import logging
import sys
import signal
import threading

from pyfs.common.fs_config import FSLogCfg
from pyfs.core.fs_bus import FSBus
from pyfs.core.fs_node import FSNode


class FSExecutive:
    """Top-level controller.

    Instantiate, init, and start every enabled node in registry order.
    Block until SIGINT / SIGTERM, then stop all nodes in reverse order.
    """

    def __init__(self) -> None:
        self._setup_logging()
        self.log = logging.getLogger("fs.exec")
        self._register_signals()

        self.bus = FSBus()
        self._shutdown_event = threading.Event()

        self.nodes = []
        for cls in FSNode.get_registry():
            if not cls.enabled:
                self.log.warning("[%s] is disabled, skipping", cls.name)
                continue
            self.nodes.append(cls())

        self.init()
        self.log.info("exec initialized")

    def init(self) -> None:
        """Call init() on every registered node."""
        for node in self.nodes:
            node.init()

    def start(self) -> None:
        """Start all nodes, then block until a shutdown signal is received."""
        for node in self.nodes:
            node.start()
        self.log.info("all nodes started")
        self._shutdown_event.wait()
        self.log.info("shutdown signal received")
        self.shutdown()

    def shutdown(self) -> None:
        """Stop all nodes and exit the process."""
        self.stop()
        sys.exit(0)

    def stop(self) -> None:
        """Stop every node in reverse start order."""
        self.log.info("stopping all nodes")
        for node in reversed(self.nodes):
            try:
                node.stop()
            except Exception as exc:
                self.log.error("error stopping node %s: %s", node, exc)
        self.log.info("all nodes stopped")

    def _register_signals(self) -> None:
        # Signal handlers must be registered from the main thread.
        signal.signal(signal.SIGINT,  self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        self.log.info("signal handlers registered")

    def _handle_signal(self, signum: int, frame) -> None:
        self.log.info("%s received — initiating shutdown", signal.Signals(signum).name)
        self._shutdown_event.set()

    def _setup_logging(self) -> None:
        logging.basicConfig(
            level=FSLogCfg.LEVEL,
            format=FSLogCfg.FORMAT,
            datefmt=FSLogCfg.DATE_FORMAT,
            stream=sys.stdout,
            force=True,
        )
