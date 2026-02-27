import sys
import time
import logging

from pyfs.common.mid import Mid
from pyfs.core.bus import Bus
from pyfs.nodes.scheduler import ScheduleNode
from user_nodes.test_node import TestNode, TestNode2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
    force=True,   # ensures config is applied even if handlers exist
)

def main():
    bus = Bus()

    node_1 = TestNode(bus)
    node_2 = TestNode2(bus)
    node_3 = ScheduleNode(bus)

    node_3.register_task(Mid.SCHEDULE_NODE_1HZ, 1)
    node_3.register_task(Mid.SCHEDULE_NODE_10HZ, 10)

    node_1.start()
    node_2.start()
    node_3.start()

    while True:
        time.sleep(2)


if __name__ == "__main__":
    sys.exit(main())