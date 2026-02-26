import logging
import time
from typing import Dict

from pyfs.apps.app import AppInfo
from pyfs.common.constants import ResetType


class ExecutiveServices:
    _log: logging.Logger = logging.getLogger("fs.es")
    _running = False

    apps: Dict[int, AppInfo] = {}
    next_app_id: int = 0

    reset_type: ResetType = ResetType.POWER_ON
    reset_count: int = 0

    def __init__(self) -> None:
        self._log.info("ES Started")

    def run(self) -> None:
        self._start_services()

    def _start_services(self):
        pass