"""Telemetry Output node — serialises telemetry messages and sends them via UDP."""

import json
import socket
from dataclasses import asdict
from typing import Any

from pyfs.common.fs_config import FSCfg
from pyfs.common.fs_mid import Mid
from pyfs.core.fs_message import FSMessage
from pyfs.core.fs_node import FSNode


class TelemetryOutputNode(FSNode):
    """Forwards every TLM_MESSAGE_MID message to the ground-station UDP endpoint."""

    name  = "to"
    _sock: socket.socket

    def on_init(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sub(Mid.TLM_MESSAGE_MID, self._handle_telemetry)

    def on_stop(self) -> None:
        if self._sock:
            self._sock.close()

    def _handle_telemetry(self, message: FSMessage) -> None:
        """Serialise *message* to JSON and send it to the configured TLM endpoint."""
        msg_payload: Any = message.payload
        pkt_payload      = asdict(msg_payload)
        pkt = {
            "mid":       message.mid,
            "timestamp": message.timestamp,
            "payload":   pkt_payload,
        }
        self._sock.sendto(json.dumps(pkt).encode(), (FSCfg.TLM_OUT_HOST, FSCfg.TLM_OUT_PORT))