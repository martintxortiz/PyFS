"""Dispatch isolation test.

Proves that a slow handler in NodeA does NOT delay NodeB's tick count.
If dispatch were single-threaded, NodeB.count would be 0 (all time consumed
by NodeA's sleep). With per-node dispatch threads, NodeB processes all
messages independently.
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
        self._queue: queue.Queue = queue.Queue(maxsize=64)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)

    def _loop(self):
        while not self._stop.is_set():
            try:
                mid, msg, handler = self._queue.get(timeout=0.05)
                handler(msg)
                self._queue.task_done()
            except queue.Empty:
                continue

    def _handle(self, msg: FSMessage):
        time.sleep(0.5)   # simulates heavy work / blocking IO


class FakeFastNode:
    """Simulates a fast counter node."""

    def __init__(self):
        self._queue: queue.Queue = queue.Queue(maxsize=64)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self.count: int = 0

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)

    def _loop(self):
        while not self._stop.is_set():
            try:
                mid, msg, handler = self._queue.get(timeout=0.05)
                handler(msg)
                self._queue.task_done()
            except queue.Empty:
                continue

    def _handle(self, msg: FSMessage):
        self.count += 1


def test_slow_node_does_not_block_fast_node():
    """FastNode should count all 5 ticks in < 0.5 s even though SlowNode stalls."""
    # Reset bus singleton for isolation
    FSBus._instance = None

    bus = FSBus()
    slow = FakeSlowNode()
    fast = FakeFastNode()

    bus.sub(Mid.SCH_WAKEUP_10HZ, slow._queue, slow._handle)
    bus.sub(Mid.SCH_WAKEUP_10HZ, fast._queue, fast._handle)

    slow.start()
    fast.start()

    msg = FSMessage(Mid.SCH_WAKEUP_10HZ, payload=None)
    for _ in range(5):
        bus.pub(Mid.SCH_WAKEUP_10HZ, msg)

    # Allow fast node time to process (0.2 s >> 5 × near-zero handler cost)
    time.sleep(0.2)

    assert fast.count == 5, (
        f"FastNode only processed {fast.count}/5 messages — nodes are not isolated!"
    )

    slow.stop()
    fast.stop()

    # Reset bus singleton for downstream tests
    FSBus._instance = None
