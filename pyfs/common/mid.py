from enum import Enum
class MessageID(Enum):
    # Commands (high byte = source app)
    CI_CMD_MID       = 0x1880
    SCH_CMD_MID      = 0x18B0
    HS_CMD_MID       = 0x18A0
    # Telemetry / Events
    EVS_EVENT_MID    = 0x0801
    HS_HK_TLM_MID    = 0x0810
    SCH_HK_TLM_MID   = 0x0811
    TIME_HK_TLM_MID  = 0x0812
    HEARTBEAT_MID    = 0x0820