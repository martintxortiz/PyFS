import threading
import time
from typing import Dict, Callable, Any

from pyfs.core.node import FSNode

TELEMETRY_MSG_ID = 0x0001
SCHEDULE_NODE_1HZ = 0x0003
SCHEDULE_NODE_10HZ = 0x0004
SCHEDULE_NODE_50HZ = 0x0005
SCHEDULE_NODE_100HZ = 0x0006


class ScheduleNode(FSNode):
    _thread: threading.Thread

    def __init__(self, bus):
        super().__init__( "tlm", bus)
        self.count = 0
        self.running = False
        self._thread = threading.Thread(target=self.run)
        self._tasks: Dict[int, int] = {}  # instantiate a dict
        self.rate_hz = 0

    def start(self):
        self.running = True
        self.rate_hz = max(self._tasks.values())
        time.sleep(0.1)

        self._thread.start()
        super().start()

    def run(self) -> None:
        print(f"thread started rate_hz {self.rate_hz}")
        tick_count = 0
        while self.running:
            cycle_start = time.perf_counter()
            tick_count += 1
            for task in self._tasks:
                if tick_count % self._tasks[task] == 0:
                    self.bus.publish(task)

            elapsed = time.perf_counter() - cycle_start
            sleep_time = max(0.0, 1.0 / self.rate_hz - elapsed)
            time.sleep(sleep_time)

    def register_task(self, message_id:int, rate_hz: int):
        self._tasks[message_id] = rate_hz
        self._log.info(f"task: ({message_id}) registered @ {rate_hz}HZ")

class TestNode(FSNode):
    def __init__(self, bus):
        super().__init__("tlm", bus)
        self.bus.subscribe(SCHEDULE_NODE_1HZ, self.tick)
        self.count = 0

    def tick(self, msg):
        self.count += 1
        self.bus.publish(TELEMETRY_MSG_ID, {"count": self.count})

class TestNode2(FSNode):
    def __init__(self, bus):
        super().__init__("gnc", bus)
        self.bus.subscribe(TELEMETRY_MSG_ID, self._on_telemetry)
        self.bus.subscribe(SCHEDULE_NODE_10HZ, self._on_10hz)

    def _on_telemetry(self, tlm):
        print(tlm)

    def _on_10hz(self, tlm):
        print("test")


