"""Framework executive — owns the node lifecycle and signal handling."""

from __future__ import annotations

import logging
import signal
import sys
import threading

from pyfs.common.fs_config import FSLogCfg
from pyfs.core.fs_bus import FSBus
from pyfs.core.fs_node import FSNode

# Local imports for core nodes
import pyfs.nodes.sch_node as _sch
import pyfs.nodes.ci_node as _ci
import pyfs.nodes.hs_node as _hs
import pyfs.nodes.to_node as _to


class FSExecutive:
    """Top-level controller.

    Nodes are registered manually via register_node().
    Block until SIGINT / SIGTERM, then stop all nodes in reverse order.
    """

    def __init__(self) -> None:
        self._setup_logging()
        self.log = logging.getLogger("fs.exec")
        self._register_signals()

        self.bus = FSBus()
        self._shutdown_event = threading.Event()

        self.nodes: list[FSNode] = []
        
        # Auto-register core framework nodes
        self.register_node(_sch.SchedulerNode())
        self.register_node(_ci.CommandIngestNode())
        self.register_node(_hs.HealthAndSafetyNode())
        self.register_node(_to.TelemetryOutputNode())
        
        self.log.info("exec initialized")

    def register_node(self, node: FSNode) -> None:
        """Register a node with the executive and initialize it."""
        if not getattr(node.__class__, "enabled", True):
            self.log.warning("(%s) is disabled, skipping", node.name)
            return
        
        node.init()
        self.nodes.append(node)

    def start(self) -> None:
        """Start all nodes, then block until a shutdown signal is received."""
        for node in self.nodes:
            node.start()
        self.log.info("all nodes started")
        self._shutdown_event.wait()
        self.log.warning("shutdown signal received")
        self.shutdown()

    def shutdown(self) -> None:
        """Stop all nodes and exit the process."""
        self.stop()
        self.log.info("shutdown complete, goodbye.")
        sys.exit(0)

    def stop(self) -> None:
        """Stop every node in reverse start order."""
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
        self._shutdown_event.set()

    def _setup_logging(self) -> None:
        logging.basicConfig(
            level=FSLogCfg.LEVEL,
            format=FSLogCfg.FORMAT,
            datefmt=FSLogCfg.DATE_FORMAT,
            stream=sys.stdout,
            force=True,
        )
