from enum import IntEnum


class MessageID(IntEnum):
    MID_UNDEFINED = 0x0000

    # Commands
    CI_CMD_MID = 0x1880

    # Telemetry
    ES_HK_MID = 0x0800
    EVS_LONG_EVENT_MID = 0x0808
    SCH_TICK_MID = 0x0886
