"""Dispatch isolation test.

Verifies that a slow handler in one node does not delay message delivery
to another node — each node processes its queue on an independent thread.
"""

import queue
import threading
import time

import pytest

from pyfs.core.fs_bus import FSBus
from pyfs.core.fs_message import FSMessage
from pyfs.common.fs_mid import Mid


class FakeSlowNode:
    """Simulates a node whose handler blocks for 0.5 s per message."""

    def __init__(self):
        self._queue  = queue.Queue(maxsize=64)
        self._stop   = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                mid, msg, handler = self._queue.get(timeout=0.05)
                handler(msg)
                self._queue.task_done()
            except queue.Empty:
                continue

    def _handle(self, msg: FSMessage) -> None:
        time.sleep(0.5)  # simulates heavy work or blocking I/O


class FakeFastNode:
    """Simulates a lightweight counter node."""

    def __init__(self):
        self._queue  = queue.Queue(maxsize=64)
        self._stop   = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self.count:  int = 0

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                mid, msg, handler = self._queue.get(timeout=0.05)
                handler(msg)
                self._queue.task_done()
            except queue.Empty:
                continue

    def _handle(self, msg: FSMessage) -> None:
        self.count += 1


def test_slow_node_does_not_block_fast_node():
    """FastNode must process all 5 ticks even though SlowNode stalls on each one."""
    FSBus._instance = None  # reset singleton for test isolation

    bus  = FSBus()
    slow = FakeSlowNode()
    fast = FakeFastNode()

    bus.sub(Mid.SCH_WAKEUP_10HZ, slow._queue, slow._handle)
    bus.sub(Mid.SCH_WAKEUP_10HZ, fast._queue, fast._handle)

    slow.start()
    fast.start()

    msg = FSMessage(Mid.SCH_WAKEUP_10HZ, payload=None)
    for _ in range(5):
        bus.pub(Mid.SCH_WAKEUP_10HZ, msg)

    time.sleep(0.2)  # 0.2 s >> (5 × near-zero fast-handler cost)

    assert fast.count == 5, (
        f"FastNode only processed {fast.count}/5 messages — nodes are not isolated!"
    )

    slow.stop()
    fast.stop()

    FSBus._instance = None  # reset singleton for downstream tests
