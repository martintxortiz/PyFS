import logging
import threading
import time

from pyfs.core.bus import Bus


class FSNode:
    name:str
    _log: logging.Logger
    bus: Bus

    def __init__(self, name: str , bus: Bus):
        super().__init__()
        self.bus = bus

        self.name = name
        self._log = logging.getLogger(f"fs.{self.name}")

        self._log.info(f"Node ({self.name}) initialized")

    def start(self):
        self._log.info(f"Node ({self.name}) started")

    def stop(self):
        self._log.info(f"Node ({self.name}) stopped")