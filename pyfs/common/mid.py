"""Message-ID registry for the PyFS software bus.

Every message published on the bus carries one of these identifiers so
subscribers can filter for the traffic they care about.
"""

from __future__ import annotations

from enum import IntEnum, unique


@unique
class MID(IntEnum):
    """Unique numeric identifiers for every message type in the system.

    Ranges::

        0x0800-0x08FF  Scheduler wakeup ticks
        0x0900-0x09FF  Telemetry
        0x0A00-0x0AFF  Commands (reserved)
    """

    __slots__ = ()

    # -- Scheduler wakeup ticks ----------------------------------------
    SCH_WAKEUP_1HZ:   int = 0x0801
    SCH_WAKEUP_10HZ:  int = 0x0802
    SCH_WAKEUP_50HZ:  int = 0x0803
    SCH_WAKEUP_100HZ: int = 0x0804

    # -- Telemetry -----------------------------------------------------
    TLM_ALTITUDE:     int = 0x0901