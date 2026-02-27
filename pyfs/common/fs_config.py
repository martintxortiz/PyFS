"""Static configuration namespaces for PyFS. Instantiate nothing here."""

from __future__ import annotations

import logging
from typing import ClassVar, Final


class FSLogCfg:
    """Logging format constants."""

    LEVEL:       ClassVar[Final[int]] = logging.INFO
    FORMAT:      ClassVar[Final[str]] = (
        "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-20s | %(message)s"
    )
    DATE_FORMAT: ClassVar[Final[str]] = "%Y-%m-%dT%H:%M:%S"


class FSCfg:
    """General framework configuration constants."""

    NAME:         ClassVar[Final[str]] = "PyFS"
    TLM_OUT_HOST: ClassVar[Final[str]] = "127.0.0.1"
    TLM_OUT_PORT: ClassVar[Final[int]] = 5010
    CMD_IN_HOST:  ClassVar[Final[str]] = "0.0.0.0"
    CMD_IN_PORT:  ClassVar[Final[int]] = 5020