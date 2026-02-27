"""
ground_station.py  --  cFS-style apps over UDP

Apps:
  TelemetryIngest  (TI)       -- receives and prints spacecraft telemetry
  CommandOutput    (CO)       -- sends a heartbeat command every 5 seconds
  LinkWatchdog     (WATCHDOG) -- monitors TLM gaps, declares LINK UP/DOWN
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

TLM_IN_HOST  = "0.0.0.0"
TLM_IN_PORT  = 5010
CMD_OUT_HOST = "127.0.0.1"
CMD_OUT_PORT = 5020


@dataclass
class SC_HK_TlmPkt:
    seq:             int   = 0
    altitude:        int   = 0
    velocity:        float = 0.0
    temperature:     float = 0.0
    battery:         float = 0.0
    link_connected:  bool  = False
    last_gs_time_ms: int   = 0


@dataclass
class GS_HEARTBEAT_CmdPkt:
    cmd_seq:    int = 0
    gs_time_ms: int = 0


@dataclass
class LinkState:
    connected:    bool  = False
    last_rx_mono: float = 0.0
    missed_count: int   = 0


class App:
    name: str = "app"

    def __init__(self):
        self._stop   = threading.Event()
        self._thread = None
        self.log     = logging.getLogger(f"gs.{self.name}")

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
    TIMEOUT_S      = 10.0
    CHECK_PERIOD_S = 1.0

    def __init__(self):
        super().__init__()
        self._state = LinkState()
        self._lock  = threading.Lock()

    def notify_rx(self) -> None:
        with self._lock:
            self._state.last_rx_mono = time.monotonic()
            self._state.missed_count = 0
            if not self._state.connected:
                self._state.connected = True
                self.log.warning("[WATCHDOG] *** LINK UP (receiving telemetry) ***")

    def get_snapshot(self) -> LinkState:
        with self._lock:
            return LinkState(**asdict(self._state))

    def run(self):
        while not self._stop.is_set():
            t0 = time.monotonic()
            with self._lock:
                last   = self._state.last_rx_mono
                linked = self._state.connected
            if linked and last > 0.0:
                age = time.monotonic() - last
                if age >= self.TIMEOUT_S:
                    with self._lock:
                        self._state.missed_count += 1
                        self._state.connected     = False
                    self.log.error(
                        f"[WATCHDOG] *** LINK DOWN (LOS) ***  "
                        f"no telemetry for {age:.1f}s  "
                        f"missed_count={self._state.missed_count}"
                    )
            self._stop.wait(timeout=max(0.0, self.CHECK_PERIOD_S - (time.monotonic() - t0)))


class TelemetryIngest(App):
    name = "TI"

    def __init__(self, watchdog: LinkWatchdog):
        super().__init__()
        self._sock     = None
        self._watchdog = watchdog

    def on_start(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.settimeout(1.0)
        self._sock.bind((TLM_IN_HOST, TLM_IN_PORT))

    def on_stop(self):
        if self._sock:
            self._sock.close()

    def run(self):
        while not self._stop.is_set():
            try:
                data, _ = self._sock.recvfrom(4096)
                raw     = json.loads(data.decode())
                payload = raw.get("payload", {})
                mid     = raw.get("mid", "")
                self._watchdog.notify_rx()
                self.log.info(f"[TI] TLM  mid={mid}  payload={payload}")
            except socket.timeout:
                continue
            except Exception as e:
                if not self._stop.is_set():
                    self.log.error(f"[TI] recv error: {e}")


class CommandOutput(App):
    name = "CO"
    HEARTBEAT_RATE_S = 5.0

    def on_start(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._cmd  = GS_HEARTBEAT_CmdPkt()

    def on_stop(self):
        self._sock.close()

    def run(self):
        while not self._stop.is_set():
            t0 = time.monotonic()
            self._cmd.cmd_seq    += 1
            self._cmd.gs_time_ms  = int(time.time() * 1000)
            payload = asdict(self._cmd)
            pkt = {
                # "apid":    0x1801,
                "mid":     0x0805,
                # "seq":     self._cmd.cmd_seq,
                "ts":      time.time(),
                "payload": payload,
            }
            self._sock.sendto(json.dumps(pkt).encode(), (CMD_OUT_HOST, CMD_OUT_PORT))
            self.log.info(f"[CO] CMD  mid=GS_HEARTBEAT_CC  payload={payload}")
            self._stop.wait(timeout=max(0.0, self.HEARTBEAT_RATE_S - (time.monotonic() - t0)))


class GroundStationExecutive:
    def __init__(self):
        self._shutdown = threading.Event()
        signal.signal(signal.SIGINT,  self._on_signal)
        signal.signal(signal.SIGTERM, self._on_signal)
        self.log       = logging.getLogger("gs.exec")
        self._watchdog = LinkWatchdog()
        self._apps     = [
            self._watchdog,
            TelemetryIngest(self._watchdog),
            CommandOutput(),
        ]

    def _on_signal(self, sig, _):
        self.log.info(f"[exec] signal {sig} — shutting down")
        self._shutdown.set()

    def run(self):
        self.log.info("[exec] GROUND STATION starting")
        for app in self._apps:
            app.start()
        self._shutdown.wait()
        self.log.info("[exec] shutting down")
        for app in reversed(self._apps):
            app.stop()


if __name__ == "__main__":
    GroundStationExecutive().run()