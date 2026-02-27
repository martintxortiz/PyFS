"""Health and Safety node — monitors liveness of watched message sources."""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from pyfs.common.fs_mid import Mid
from pyfs.core.fs_message import FSMessage
from pyfs.core.fs_node import FSNode


@dataclass
class WatchEntry:
    """Per-source liveness record maintained by HealthAndSafety."""
    label:        str
    timeout_s:    float
    last_rx_mono: Optional[float] = None  # None until first message received
    connected:    bool            = False
    missed_count: int             = 0


class HealthAndSafetyNode(FSNode):
    """Watches subscribed MIDs for silence and logs faults when a source goes quiet."""

    name = "hs"

    _WATCH_TABLE: List[Tuple[Mid, str, float]] = [
        # (mid,                    label,          timeout_s)
        (Mid.CMD_GS_HEARTBEAT_MID, "GS_HEARTBEAT", 15.0),
    ]

    _entries: Dict[Mid, WatchEntry]

    def on_init(self) -> None:
        """Subscribe to every watched MID and to the 1 Hz scheduler tick."""
        self._entries = {}
        for mid, label, timeout_s in self._WATCH_TABLE:
            self._entries[mid] = WatchEntry(label=label, timeout_s=timeout_s)
            self.sub(mid, self._on_receive)

        self.sub(Mid.SCH_WAKEUP_1HZ, self._tick)

    def _on_receive(self, msg: FSMessage) -> None:
        """Record receipt time and clear any prior fault state."""
        entry = self._entries[msg.mid]
        was_connected      = entry.connected
        entry.last_rx_mono = time.monotonic()
        entry.missed_count = 0
        entry.connected    = True
        if not was_connected:
            self.log.info("OK (%s)", entry.label)

    def _tick(self, _msg: FSMessage) -> None:
        """Check every watched entry for silence and raise a fault when overdue."""
        now = time.monotonic()
        for entry in self._entries.values():
            if entry.last_rx_mono is None:
                continue  # never heard from; stay silent

            if now - entry.last_rx_mono >= entry.timeout_s:
                entry.connected     = False
                entry.missed_count += 1
                self.log.error(
                    "KO (%s) silent for %.1fs, missed=%d",
                    entry.label,
                    now - entry.last_rx_mono,
                    entry.missed_count,
                )