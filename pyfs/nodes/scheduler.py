import threading
import time
from typing import Dict

from pyfs.core.node import FSNode


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


# """
# schedule_node.py — Deterministic periodic task scheduler node.
#
# Fixes applied vs previous revision:
#   FIX-1: bus.publish() return check uses `is False` not truthiness.
#           Bus returns None on success (void); None != False.
#   FIX-2: All logging removed from the hot dispatch loop.
#           Overrun/error metrics accumulated in counters only.
#           A separate low-priority diagnostics thread drains them.
#           This eliminates the logging→overrun→logging cascade.
# """
#
# from __future__ import annotations
#
# import heapq
# import logging
# import threading
# import time
# from typing import Dict, Final, List, Optional, Tuple
#
# from pyfs.common.mid import Mid
# from pyfs.core.bus import Bus
# from pyfs.core.node import FSNode
#
# # ---------------------------------------------------------------------------
# # Constants
# # ---------------------------------------------------------------------------
#
# _MAX_TASKS: Final[int] = 64
# _MIN_RATE_HZ: Final[int] = 1
# _MAX_RATE_HZ: Final[int] = 1_000
# _STOP_TIMEOUT_S: Final[float] = 2.0
# _SPIN_THRESHOLD_NS: Final[int] = 200_000        # 200 µs — tune per platform
# _DIAG_INTERVAL_S: Final[float] = 1.0            # Diagnostics log period
# _LOG_NAME: Final[str] = "sn"
#
# # ---------------------------------------------------------------------------
# # Types
# # ---------------------------------------------------------------------------
#
# _HeapEntry = Tuple[int, int]   # (absolute_deadline_ns, message_id)
#
#
# # ---------------------------------------------------------------------------
# # ScheduleNode
# # ---------------------------------------------------------------------------
#
# class ScheduleNode(FSNode):
#     """
#     Periodic task scheduler.
#
#     Lifecycle:
#         1. Construct
#         2. register_task()  — one or more times, BEFORE start()
#         3. start()
#         4. stop()           — call from finally block
#
#     Thread model:
#         _thread      : dispatcher — timing-critical, zero I/O
#         _diag_thread : diagnostics — logs metrics every _DIAG_INTERVAL_S
#     """
#
#     __slots__ = (
#         "_lock",
#         "_stop_event",
#         "_thread",
#         "_diag_thread",
#         "_tasks",
#         "_rate_hz",
#         "_overrun_count",
#         "_dispatch_count",
#         "_publish_fail_count",
#         "_started",
#         "_log",
#     )
#
#     def __init__(self, bus: Bus) -> None:
#         """
#         Initialise node. No threads started here.
#
#         Args:
#             bus: Non-null message bus. publish() may return None or bool.
#         """
#         assert bus is not None, "bus must not be None"
#
#         super().__init__("tlm", bus)
#
#         self._log: logging.Logger = logging.getLogger(_LOG_NAME)
#         self._lock: threading.RLock = threading.RLock()
#         self._stop_event: threading.Event = threading.Event()
#
#         self._thread: threading.Thread = threading.Thread(
#             target=self._run,
#             name="sn-dispatcher",
#             daemon=True,
#         )
#         self._diag_thread: threading.Thread = threading.Thread(
#             target=self._run_diagnostics,
#             name="sn-diagnostics",
#             daemon=True,
#         )
#
#         self._tasks: Dict[int, int] = {}
#         self._rate_hz: int = 0
#         self._overrun_count: int = 0        # Written only by _thread
#         self._dispatch_count: int = 0       # Written only by _thread
#         self._publish_fail_count: int = 0   # Written only by _thread
#         self._started: bool = False
#
#         assert not self._thread.is_alive(), "thread must not be alive after __init__"
#         assert not self._diag_thread.is_alive(), "diag thread must not be alive after __init__"
#
#     # ------------------------------------------------------------------
#     # Public API
#     # ------------------------------------------------------------------
#
#     def register_task(self, message_id: Mid, rate_hz: int) -> None:
#         """
#         Register a periodic task. Must be called BEFORE start().
#
#         Args:
#             message_id: Non-negative integer message identifier.
#             rate_hz:    Dispatch rate in [_MIN_RATE_HZ, _MAX_RATE_HZ].
#
#         Raises:
#             ValueError:   On invalid arguments or registration after start().
#             RuntimeError: If task table is full.
#         """
#         assert message_id >= 0, "message_id must be non-negative"
#         assert _MIN_RATE_HZ <= rate_hz <= _MAX_RATE_HZ, (
#             f"rate_hz must be in [{_MIN_RATE_HZ}, {_MAX_RATE_HZ}]"
#         )
#
#         if message_id < 0:
#             raise ValueError(f"message_id must be non-negative, got {message_id}")
#         if not (_MIN_RATE_HZ <= rate_hz <= _MAX_RATE_HZ):
#             raise ValueError(
#                 f"rate_hz={rate_hz} out of range [{_MIN_RATE_HZ}, {_MAX_RATE_HZ}]"
#             )
#
#         with self._lock:
#             if self._started:
#                 raise RuntimeError(
#                     "register_task() called after start(); "
#                     "stop the node first."
#                 )
#             if message_id not in self._tasks and len(self._tasks) >= _MAX_TASKS:
#                 raise RuntimeError(
#                     f"Task table full: maximum {_MAX_TASKS} tasks."
#                 )
#             self._tasks[message_id] = rate_hz
#
#         self._log.info("Task registered: message_id=%d @ %d Hz", message_id, rate_hz)
#
#     def start(self) -> None:
#         """
#         Start the dispatcher and diagnostics threads.
#
#         Raises:
#             RuntimeError: If no tasks registered or already started.
#         """
#         with self._lock:
#             assert not self._started, "start() called twice"
#             if self._started:
#                 raise RuntimeError("ScheduleNode already started.")
#             if not self._tasks:
#                 raise RuntimeError("No tasks registered; cannot start.")
#             self._rate_hz = max(self._tasks.values())
#             self._started = True
#
#         assert self._rate_hz > 0, "rate_hz must be positive after start"
#
#         self._log.info(
#             "Starting: %d task(s), master_rate=%d Hz",
#             len(self._tasks),
#             self._rate_hz,
#         )
#
#         self._thread.start()
#         self._diag_thread.start()
#         super().start()
#
#     def stop(self) -> None:
#         """
#         Signal all threads to stop and wait for clean exit.
#         Safe to call from any thread. Idempotent.
#         """
#         assert self._thread is not None, "_thread must not be None"
#         assert self._diag_thread is not None, "_diag_thread must not be None"
#
#         self._stop_event.set()
#
#         for t in (self._thread, self._diag_thread):
#             if t.is_alive():
#                 t.join(timeout=_STOP_TIMEOUT_S)
#                 if t.is_alive():
#                     self._log.error("Thread %s did not exit within %.1f s", t.name, _STOP_TIMEOUT_S)
#
#         self._log.info(
#             "Stopped. dispatched=%d overruns=%d publish_failures=%d",
#             self._dispatch_count,
#             self._overrun_count,
#             self._publish_fail_count,
#         )
#
#     # ------------------------------------------------------------------
#     # Properties — safe to read from any thread (int reads are atomic in CPython)
#     # ------------------------------------------------------------------
#
#     @property
#     def overrun_count(self) -> int:
#         """Monotonically increasing count of deadline overruns."""
#         return self._overrun_count
#
#     @property
#     def dispatch_count(self) -> int:
#         """Monotonically increasing count of successful dispatches."""
#         return self._dispatch_count
#
#     @property
#     def publish_fail_count(self) -> int:
#         """Monotonically increasing count of publish failures."""
#         return self._publish_fail_count
#
#     # ------------------------------------------------------------------
#     # Private: schedule builder
#     # ------------------------------------------------------------------
#
#     def _build_schedule(self) -> List[_HeapEntry]:
#         """
#         Build the initial absolute-deadline min-heap.
#         All arithmetic in integer nanoseconds — no float accumulation.
#         """
#         assert self._tasks, "_tasks must not be empty"
#
#         now_ns: int = time.perf_counter_ns()
#         heap: List[_HeapEntry] = []
#
#         for message_id, rate_hz in self._tasks.items():
#             assert rate_hz > 0, "rate_hz must be positive"
#             period_ns: int = 1_000_000_000 // rate_hz
#             heapq.heappush(heap, (now_ns + period_ns, message_id))
#
#         assert len(heap) == len(self._tasks), "heap size must equal task count"
#         return heap
#
#     # ------------------------------------------------------------------
#     # Private: dispatcher thread — NO logging, NO I/O
#     # ------------------------------------------------------------------
#
#     def _run(self) -> None:
#         """
#         Timing-critical dispatcher. Zero I/O permitted here.
#
#         All diagnostic output is deferred to _run_diagnostics().
#         Overruns and failures are counted only — never logged inline.
#
#         Absolute-deadline algorithm:
#           1. Pop task with earliest deadline from min-heap.
#           2. Sleep until (deadline - _SPIN_THRESHOLD_NS).
#           3. Busy-spin the final 200 µs for sub-millisecond accuracy.
#           4. Dispatch (publish).
#           5. Requeue with deadline += period (no drift accumulation).
#         """
#         assert self._tasks, "_tasks must not be empty at thread start"
#         assert self._rate_hz > 0, "_rate_hz must be positive at thread start"
#
#         heap: List[_HeapEntry] = self._build_schedule()
#
#         while not self._stop_event.is_set():
#
#             assert heap, "heap must not be empty during dispatch loop"
#
#             deadline_ns: int
#             message_id: int
#             deadline_ns, message_id = heapq.heappop(heap)
#
#             # --- Phase 1: coarse sleep (releases GIL) ---
#             remaining_ns: int = deadline_ns - time.perf_counter_ns()
#             if remaining_ns > _SPIN_THRESHOLD_NS:
#                 sleep_s: float = (remaining_ns - _SPIN_THRESHOLD_NS) / 1_000_000_000.0
#                 self._stop_event.wait(timeout=sleep_s)
#                 if self._stop_event.is_set():
#                     break
#
#             # --- Phase 2: precision busy-spin (bounded by _SPIN_THRESHOLD_NS) ---
#             while time.perf_counter_ns() < deadline_ns:
#                 pass
#
#             # --- Overrun accounting (no logging here) ---
#             actual_ns: int = time.perf_counter_ns()
#             if actual_ns > deadline_ns:
#                 self._overrun_count += 1
#
#             # --- Dispatch ---
#             # FIX-1: bus.publish() returns None (void), not False.
#             # Treat None as success. Only explicit False is a failure.
#             result: Optional[bool] = self.bus.publish(message_id)
#             if result is False:
#                 self._publish_fail_count += 1
#             else:
#                 self._dispatch_count += 1
#
#             # --- Advance deadline (absolute, no drift) ---
#             rate_hz: Optional[int] = self._tasks.get(message_id)
#             assert rate_hz is not None, (
#                 f"message_id={message_id} missing from task table"
#             )
#             period_ns: int = 1_000_000_000 // rate_hz
#             heapq.heappush(heap, (deadline_ns + period_ns, message_id))
#
#     # ------------------------------------------------------------------
#     # Private: diagnostics thread — all logging lives here
#     # ------------------------------------------------------------------
#
#     def _run_diagnostics(self) -> None:
#         """
#         Low-priority diagnostics thread.
#
#         Wakes every _DIAG_INTERVAL_S and logs a delta snapshot of
#         dispatch/overrun/failure counters. All I/O is isolated here,
#         completely decoupled from the dispatch hot path.
#         """
#         assert _DIAG_INTERVAL_S > 0.0, "_DIAG_INTERVAL_S must be positive"
#
#         prev_dispatch: int = 0
#         prev_overruns: int = 0
#         prev_failures: int = 0
#
#         while not self._stop_event.wait(timeout=_DIAG_INTERVAL_S):
#
#             cur_dispatch: int = self._dispatch_count
#             cur_overruns: int = self._overrun_count
#             cur_failures: int = self._publish_fail_count
#
#             delta_dispatch: int = cur_dispatch - prev_dispatch
#             delta_overruns: int = cur_overruns - prev_overruns
#             delta_failures: int = cur_failures - prev_failures
#
#             # Log only when something interesting happened
#             if delta_overruns > 0 or delta_failures > 0:
#                 self._log.warning(
#                     "Diag | dispatched=+%d overruns=+%d failures=+%d "
#                     "(totals: d=%d o=%d f=%d)",
#                     delta_dispatch, delta_overruns, delta_failures,
#                     cur_dispatch, cur_overruns, cur_failures,
#                 )
#             else:
#                 self._log.debug(
#                     "Diag | dispatched=+%d overruns=0 failures=0",
#                     delta_dispatch,
#                 )
#
#             prev_dispatch = cur_dispatch
#             prev_overruns = cur_overruns
#             prev_failures = prev_failures + delta_failures
#
#         self._log.info("Diagnostics thread exiting cleanly.")
