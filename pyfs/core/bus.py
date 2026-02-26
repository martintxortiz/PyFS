import logging
from typing import Dict, Callable, Any


class Bus:
    _log: logging.Logger = logging.getLogger("fs.bus")
    def __init__(self):
        self.routing: Dict[int, Callable] = {}  # instantiate a dict
        self._log.info("bus started")

    def subscribe(self, message_id: int, callback: Callable):
        self.routing[message_id] = callback
        self._log.info(f"new subscriber to: {message_id}")

    def publish(self, message_id: int, message: Any = None):
        #self._log.info(f"{message_id} called")
        if message_id in self.routing:
            self.routing[message_id](message)