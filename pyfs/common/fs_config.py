"""Static configuration namespaces for PyFS. Instantiate nothing here."""

from __future__ import annotations

import logging
from typing import Final


class FSLogCfg:
    """Logging format constants."""

    LEVEL:       Final[int] = logging.INFO
    FORMAT:      Final[str] = (
        "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-20s | %(message)s"
    )
    DATE_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S"


class FSCfg:
    """General framework configuration constants."""

    NAME:         Final[str] = "PyFS"
    TLM_OUT_HOST: Final[str] = "127.0.0.1"
    TLM_OUT_PORT: Final[int] = 5010
    CMD_IN_HOST:  Final[str] = "0.0.0.0"
    CMD_IN_PORT:  Final[int] = 5020