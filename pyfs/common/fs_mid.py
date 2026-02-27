"""Message ID registry — all MIDs used on the software bus."""

from enum import IntEnum


class Mid(IntEnum):
    """Unique integer identifiers for every message routed on the bus."""

    TEST_MID             = 0x1001

    SCH_WAKEUP_1HZ       = 0x0801
    SCH_WAKEUP_10HZ      = 0x0802
    SCH_WAKEUP_50HZ      = 0x0803

    TLM_MESSAGE_MID      = 0x0804
    CMD_GS_HEARTBEAT_MID = 0x0805
