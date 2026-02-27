import logging
from typing import Dict, Callable, Any

from pyfs.common.mid import Mid


class Bus:
    _log: logging.Logger = logging.getLogger("fs.bus")
    def __init__(self):
        self.routing: Dict[Mid, Callable] = {}  # instantiate a dict
        self._log.info("bus started")

    def subscribe(self, app_name:str, message_id: Mid, callback: Callable):
        self.routing[message_id] = callback
        self._log.info(f"({app_name}) subscribed to: ({message_id})")

    def publish(self, message_id: Mid, message: Any = None):
        #self._log.info(f"{message_id} called")
        if message_id in self.routing:
            self.routing[message_id](message)