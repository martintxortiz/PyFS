import threading
import time
import heapq
from typing import List, Tuple

from pyfs.common.fs_mid import Mid
from pyfs.core.fs_message import FSMessage
from pyfs.core.fs_node import FSNode


# (rate_hz, mid)
_TASK_TABLE: List[Tuple[int, Mid]] = [
    (1,   Mid.SCH_WAKEUP_1HZ),
    (10,  Mid.SCH_WAKEUP_10HZ),
    (50,  Mid.SCH_WAKEUP_50HZ),
]

class SchedulerNode(FSNode):
    name = "sch"
    _stop_event: threading.Event
    _thread: threading.Thread
    _heap: List[Tuple[int, int, Mid]]

    def on_init(self) -> None:
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._tick, daemon=True)
        self._heap: List[Tuple[int, int, Mid]] = []  # (next_tick_ns, period_ns, mid)

        now_ns = time.monotonic_ns()
        for rate_hz, mid in _TASK_TABLE:
            period_ns = 1_000_000_000 // rate_hz
            heapq.heappush(self._heap, (now_ns + period_ns, period_ns, mid))
            self.log.info("registered [%s (%s)] @ %dHz", mid.name, mid, rate_hz)

    def on_start(self) -> None:
        self._thread.start()

    def on_stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=2)
        if self._thread.is_alive():
            self.log.warning("Bad thread exit")

    def _tick(self) -> None:
        while not self._stop_event.is_set():
            now_ns = time.monotonic_ns()
            next_tick_ns, period_ns, mid = self._heap[0]

            sleep_ns = next_tick_ns - now_ns
            if sleep_ns > 0:
                self._stop_event.wait(timeout=sleep_ns / 1e9)
                if self._stop_event.is_set():
                    break

            now_ns = time.monotonic_ns()
            next_tick_ns, period_ns, mid = self._heap[0]
            if now_ns < next_tick_ns:
                continue  # spurious wakeup

            heapq.heapreplace(
                self._heap,
                (next_tick_ns + period_ns, period_ns, mid),
            )
            self.bus.pub(mid, FSMessage(mid, payload=None))
