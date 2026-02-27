"""
spacecraft.py  --  cFS-style apps over UDP

Apps:
  TelemetryOutput  (TO)       -- publishes SC_HK_TlmPkt every 1 second
  CommandIngest    (CI)       -- receives commands from the ground station
  LinkWatchdog     (WATCHDOG) -- monitors heartbeat gaps, declares LINK UP/DOWN
"""

import socket
import threading
import time
import json
import logging
import signal
import sys
from dataclasses import dataclass, asdict, fields

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)

TLM_OUT_HOST = "127.0.0.1"
TLM_OUT_PORT = 5010
CMD_IN_HOST  = "0.0.0.0"
CMD_IN_PORT  = 5020


@dataclass
class SC_HK_TlmPkt:
    seq:             int   = 0
    altitude:        int   = 0
    velocity:        float = 0.0
    temperature:     float = 293.15
    battery:         float = 100.0
    link_connected:  bool  = False
    last_gs_time_ms: int   = 0


@dataclass
class LinkState:
    connected:       bool  = False
    last_rx_mono:    float = 0.0
    last_gs_time_ms: int   = 0
    missed_count:    int   = 0


class App:
    name: str = "app"

    def __init__(self):
        self._stop   = threading.Event()
        self._thread = None
        self.log     = logging.getLogger(f"sc.{self.name}")

    def on_start(self): ...
    def on_stop(self):  ...
    def run(self):      ...

    def start(self):
        self.on_start()
        self._thread = threading.Thread(target=self.run, name=self.name, daemon=True)
        self._thread.start()
        self.log.info(f"[{self.name}] started")

    def stop(self):
        self._stop.set()
        self.on_stop()
        if self._thread:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                self.log.warning(f"[{self.name}] thread did not exit cleanly")
        self.log.info(f"[{self.name}] stopped")


class LinkWatchdog(App):
    name = "WATCHDOG"
    TIMEOUT_S      = 15.0
    CHECK_PERIOD_S = 1.0

    def __init__(self):
        super().__init__()
        self._state = LinkState()
        self._lock  = threading.Lock()

    def notify_rx(self, gs_time_ms: int = 0) -> None:
        with self._lock:
            self._state.last_rx_mono    = time.monotonic()
            self._state.last_gs_time_ms = gs_time_ms
            self._state.missed_count    = 0
            if not self._state.connected:
                self._state.connected = True
                self.log.warning("[WATCHDOG] *** LINK UP ***")

    def get_snapshot(self) -> LinkState:
        with self._lock:
            return LinkState(**asdict(self._state))

    def run(self):
        while not self._stop.is_set():
            t0 = time.monotonic()
            with self._lock:
                last  = self._state.last_rx_mono
                linked = self._state.connected
            if linked and last > 0.0:
                age = time.monotonic() - last
                if age >= self.TIMEOUT_S:
                    with self._lock:
                        self._state.missed_count += 1
                        self._state.live     = False
                    self.log.error(
                        f"[WATCHDOG] *** LINK DOWN ***  "
                        f"no heartbeat for {age:.1f}s  "
                        f"missed_count={self._state.missed_count}"
                    )
            self._stop.wait(timeout=max(0.0, self.CHECK_PERIOD_S - (time.monotonic() - t0)))


class TelemetryOutput(App):
    name = "TO"

    def __init__(self, tlm: SC_HK_TlmPkt, watchdog: LinkWatchdog):
        super().__init__()
        self._sock     = None
        self._tlm      = tlm
        self._watchdog = watchdog

    def on_start(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def on_stop(self):
        if self._sock:
            self._sock.close()

    def _update(self):
        self._tlm.seq      += 1
        self._tlm.altitude += 1
        self._tlm.velocity    = 7800.0 + self._tlm.altitude * 0.01
        self._tlm.temperature = 293.15 + self._tlm.altitude * 0.001
        self._tlm.battery     = max(0.0, 100.0 - self._tlm.seq * 0.01)
        snap = self._watchdog.get_snapshot()
        self._tlm.link_connected  = snap.connected
        self._tlm.last_gs_time_ms = snap.last_gs_time_ms

    def run(self):
        while not self._stop.is_set():
            t0 = time.monotonic()
            self._update()
            payload = asdict(self._tlm)
            pkt = {"apid": 0x0001, "mid": "SC_HK_TLM", "ts": time.time(), "payload": payload}
            self._sock.sendto(json.dumps(pkt).encode(), (TLM_OUT_HOST, TLM_OUT_PORT))
            self.log.info(f"[TO] TLM  payload={payload}")
            self._stop.wait(timeout=max(0.0, 1.0 - (time.monotonic() - t0)))


class CommandIngest(App):
    name = "CI"

    def __init__(self, watchdog: LinkWatchdog):
        super().__init__()
        self._sock     = None
        self._watchdog = watchdog

    def on_start(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.settimeout(1.0)
        self._sock.bind((CMD_IN_HOST, CMD_IN_PORT))

    def on_stop(self):
        if self._sock:
            self._sock.close()

    def run(self):
        while not self._stop.is_set():
            try:
                data, addr = self._sock.recvfrom(4096)
                cmd     = json.loads(data.decode())
                mid     = cmd.get("mid", "")
                seq     = int(cmd.get("seq", 0))
                payload = cmd.get("payload", {})
                gs_time_ms = int(payload.get("gs_time_ms", 0))
                self._watchdog.notify_rx(gs_time_ms=gs_time_ms)
                self.log.info(f"[CI] CMD  mid={mid}  seq={seq:05d}  payload={payload}")
            except socket.timeout:
                continue
            except Exception as e:
                if not self._stop.is_set():
                    self.log.error(f"[CI] recv error: {e}")


class SpacecraftExecutive:
    def __init__(self):
        self._shutdown = threading.Event()
        signal.signal(signal.SIGINT,  self._on_signal)
        signal.signal(signal.SIGTERM, self._on_signal)
        self.log       = logging.getLogger("sc.exec")
        self._watchdog = LinkWatchdog()
        self._tlm      = SC_HK_TlmPkt()
        self._apps     = [
            self._watchdog,
            CommandIngest(self._watchdog),
            TelemetryOutput(self._tlm, self._watchdog),
        ]

    def _on_signal(self, sig, _):
        self.log.info(f"[exec] signal {sig} — shutting down")
        self._shutdown.set()

    def run(self):
        self.log.info("[exec] SPACECRAFT starting")
        for app in self._apps:
            app.start()
        self._shutdown.wait()
        self.log.info("[exec] shutting down")
        for app in reversed(self._apps):
            app.stop()


if __name__ == "__main__":
    SpacecraftExecutive().run()