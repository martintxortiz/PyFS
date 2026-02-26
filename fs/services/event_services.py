class EventServices:
    # app_registry:   dict[int, AppData]    # app_id → data
    name_index:     dict[str, int]           # app_name → app_id
    # local_event_log: RingBuffer[EventPacket] # bounded, maxlen = LOG_MAX (20)
    message_count:  int
    next_app_id:    int

    def __init__(self):
        pass