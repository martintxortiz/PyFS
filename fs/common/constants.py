import enum
from enum import IntEnum


class SubsystemId(IntEnum):
    EVS  = 0x08  # Event Services
    ES   = 0x09  # Executive Services
    SB   = 0x0A  # Software Bus
    TIME = 0x0B  # Time Services
    TBL  = 0x0C  # Table Services
    FS   = 0x0D  # File Services


class Status(IntEnum):
    # Success codes
    SUCCESS = 0

    # General error codes
    ERR_INVALID_POINTER = -1
    ERR_INVALID_ARGUMENT = -2
    ERR_INVALID_MSG_ID = -3
    ERR_INVALID_PIPE_ID = -4
    ERR_INVALID_PARAM = -5

    # Resource errors
    ERR_NO_RESOURCE = -10
    ERR_RESOURCE_EXISTS = -11
    ERR_RESOURCE_NOT_FOUND = -12
    ERR_RESOURCE_IN_USE = -13

    # Service errors
    ERR_SERVICE_NOT_INITIALIZED = -20
    ERR_SERVICE_ALREADY_INITIALIZED = -21
    ERR_SERVICE_DISABLED = -22

    # Buffer/Queue errors
    ERR_QUEUE_FULL = -30
    ERR_QUEUE_EMPTY = -31
    ERR_BUFFER_FULL = -32
    ERR_BUFFER_EMPTY = -33

    # App errors
    ERR_APP_LOAD_FAILED = -40
    ERR_APP_START_FAILED = -41
    ERR_APP_STOP_FAILED = -42
    ERR_APP_NOT_FOUND = -43

    # Timeout error
    ERR_TIMEOUT = -50

    # Table errors
    ERR_TABLE_NOT_FOUND = -60
    ERR_TABLE_INVALID = -61
    ERR_TABLE_VALIDATION_FAILED = -62

    # Event errors
    ERR_EVENT_FILTERED = -70
    ERR_EVENT_UNREGISTERED = -71