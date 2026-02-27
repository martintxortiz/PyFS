import time
from dataclasses import dataclass

from pyfs.common.fs_mid import Mid
from pyfs.core.fs_message import FSMessage
from pyfs.core.fs_node import FSNode


@dataclass
class WatchEntry:
    label:        str
    timeout_s:    float
    last_rx_mono: float = 0.0
    connected:    bool  = False
    missed_count: int   = 0


class HealthAndSafety(FSNode):
    name = "hs"

    _WATCH_TABLE = [
        # (MID,                       label,           timeout_s)
        (Mid.CMD_GS_HEARTBEAT_MID,    "GS_HEARTBEAT",  15.0),
    ]

    def on_init(self) -> None:
        self._entries: dict[Mid, WatchEntry] = {}

        for mid, label, timeout_s in self._WATCH_TABLE:
            self._entries[mid] = WatchEntry(label=label, timeout_s=timeout_s)
            self.bus.sub(mid, self._on_rx(mid))

        self.bus.sub(Mid.SCH_WAKEUP_10HZ, self._on_tick)

    # ── called by the bus on every watched MID ─────────────────────────────────
    def _on_rx(self, mid: Mid):
        def _handler(msg: FSMessage) -> None:
            entry = self._entries[mid]
            entry.last_rx_mono = time.monotonic()
            entry.missed_count = 0
            if not entry.connected:
                entry.connected = True
                self.log.warning(f"[hs] LINK UP  [{entry.label}]")
        return _handler

    # ── called by the scheduler at 10 Hz — does all the watchdog work ──────────
    def _on_tick(self, _msg: FSMessage) -> None:
        now = time.monotonic()
        for entry in self._entries.values():
            if not entry.connected or entry.last_rx_mono == 0.0:
                continue
            if now - entry.last_rx_mono >= entry.timeout_s:
                entry.connected    = False
                entry.missed_count += 1
                self.log.error(
                    f"[hs] LINK DOWN  [{entry.label}]  "
                    f"silent for {now - entry.last_rx_mono:.1f}s  "
                    f"missed={entry.missed_count}"
                )