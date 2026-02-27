"""Command Ingest Node.

Listens for UDP commands on a dedicated recv thread.  Does NOT subscribe to
the scheduler — blocking I/O is fully isolated to its own thread.
"""

import json
import socket
import threading

from pyfs.common.fs_config import FSCfg
from pyfs.common.fs_mid import Mid
from pyfs.core.fs_message import FSMessage
from pyfs.core.fs_node import FSNode


class CommandIngestNode(FSNode):
    name = "ci"

    _sock: socket.socket
    _recv_stop: threading.Event
    _recv_thread: threading.Thread

    def on_init(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.settimeout(1.0)   # timeout lets recv_loop check stop event
        self._sock.bind((FSCfg.CMD_IN_HOST, FSCfg.CMD_IN_PORT))
        self._recv_stop = threading.Event()
        self._recv_thread = threading.Thread(
            target=self._recv_loop,
            name="fs.ci.recv",
            daemon=True,
        )

    def on_start(self) -> None:
        self._recv_thread.start()

    def on_stop(self) -> None:
        self._recv_stop.set()
        self._recv_thread.join(timeout=3)
        if self._recv_thread.is_alive():
            self.log.warning("recv thread did not exit cleanly")
        self._sock.close()

    def _recv_loop(self) -> None:
        """Block on recvfrom in own thread — never touches the SCH thread."""
        while not self._recv_stop.is_set():
            try:
                data, _addr = self._sock.recvfrom(4096)
            except socket.timeout:
                continue   # check stop event and loop
            except OSError:
                break      # socket was closed during shutdown

            try:
                cmd = json.loads(data.decode())
                mid_val = cmd.get("mid", "")
                payload = cmd.get("payload", {})
                mid = Mid(mid_val)
                self.bus.pub(mid, FSMessage(mid, payload=payload))
            except Exception as exc:
                self.log.error("recv parse error: %s", exc)