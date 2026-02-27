"""PyFS entry point — configure logging, register nodes, and launch."""

from __future__ import annotations

import logging
import sys

from pyfs.common.config import SYSTEM_CONFIG
from pyfs.core.executive import FSExecutive
from user_nodes.test_node import TelemetryNode, GNCNode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
    force=True,
)


def main() -> None:
    """Create the executive, register demo nodes, and start the system."""
    exe: FSExecutive = FSExecutive(SYSTEM_CONFIG)

    exe.register_node(TelemetryNode(exe.bus))
    exe.register_node(GNCNode(exe.bus))

    exe.start()


if __name__ == "__main__":
    main()