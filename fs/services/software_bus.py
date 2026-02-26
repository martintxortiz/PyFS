import logging
import queue
import threading
from typing import Any


class SBPipe:
    name:       str
    owner:      str
    depth:      int
    queue:      queue.Queue
    msgs_in:    int
    drop_count: int

    def put(self, msg: Any) -> None:
        """
        try non-blocking enqueue
        if full: increment drop_count, log warning, return ERR_PIPE_FULL
        increment msgs_in
        return SUCCESS
        """

    def get(self) -> None:
        """
        block on queue with timeout
        return msg or None, never raises
        """

class SoftwareBus:
    _log = logging.getLogger("fs.sb")
    _lock:         threading.RLock

    pipes:        dict[str, SBPipe]         # name → pipe
    routing:      dict[int, list[SBPipe]]   # MID  → pipes subscribed
    msg_sent:     int
    msg_dropped:  int

    # Pipes

    def create_pipe(self, pipe_name: str, app: str, depth: int) -> SBPipe:
        """
        assert name not empty, depth within bounds
        assert pipe name not already taken
        assert total pipes under limit
        allocate SBPipe, add to pipes dict
        return SUCCESS or ERR_PIPE_LIMIT
        """


    def delete_pipe(self, pipe_name: str) -> None:
        """
        remove from pipes dict
        remove from every subscription list in routing table
        return SUCCESS or ERR_NOT_FOUND
        """

    # Subscriptions

    def subscribe(self, mid: int, pipe_name: str) -> None:
        """
        assert mid is not MID_UNDEFINED
        look up pipe, fail if not found
        look up or create subscriber list for this MID
        assert subscriber count under limit
        append pipe to list if not already there
        return SUCCESS
        """

    def unsubscribe(self, mid: int, pipe_name: str) -> None:
        """
        remove pipe from subscriber list for this MID
        return SUCCESS
        """

    # Messages

    def publish(self, message: int) -> None:
        """
        assert msg.mid is not MID_UNDEFINED
        stamp msg timestamp from TIME services   ← happens HERE not at construction
        increment msg sequence count (14-bit wrap)
        look up subscriber list for msg.mid
        if list is empty: return SUCCESS silently  ← not an error
        for each pipe in list:
            pipe.put(msg)                          ← non-blocking, drops if full
        increment msg_sent
        return SUCCESS
        """

    def receive(self, mid: int, pipe_name: str) -> None:
        """
        look up pipe by name
        call pipe.get(timeout)                     ← blocks until msg or timeout
        return msg or None
        """
