# The single unit that travels through the entire system
# Every app sends and receives only this
git 
class Message:
    mid:       int       # who is this for — the routing key
    aid:       int       # who sent this — the sender app ID
    seq:       int       # rolling counter, incremented by SB at send time
    timestamp: float     # set by SB at send time, never at construction
    func_code: int       # only meaningful for commands, 0 for telemetry
    payload:   dict      # the actual data — anything goes here


# Two logical subtypes — same class, different mid value
# mid bit 12 = 1 → command    (0x1xxx)
# mid bit 12 = 0 → telemetry  (0x0xxx)
