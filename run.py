# import logging
# import sys
#
# from pyfs.core.executive_services import ExecutiveServices
#
# def main() -> int:
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-20s | %(message)s",
#         datefmt="%Y-%m-%dT%H:%M:%S",
#         stream=sys.stdout,
#         force=True,   # ensures config is applied even if handlers exist
#     )
#
#     try:
#         es = ExecutiveServices()
#         es.run()
#         return 0
#
#     except Exception:
#         logging.exception("Exception occurred in main fs", exc_info=True)
#         return 1
#
# if __name__ == "__main__":
#     sys.exit(main())
import sys
import time
import logging

from pyfs.core.bus import Bus
from pyfs.test_node import TestNode, TestNode2, ScheduleNode, SCHEDULE_NODE_1HZ, SCHEDULE_NODE_10HZ

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

    node_3.register_task(SCHEDULE_NODE_1HZ, 1)
    node_3.register_task(SCHEDULE_NODE_10HZ, 10)

    node_1.start()
    node_2.start()
    node_3.start()

    while True:
        time.sleep(2)


if __name__ == "__main__":
    sys.exit(main())