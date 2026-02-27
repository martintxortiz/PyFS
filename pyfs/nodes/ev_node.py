from pyfs.common.fs_mid import Mid
from pyfs.core.fs_node import FSNode


# event node in construction
class EventNode(FSNode):
    name = "ev"
    enabled = False


    def on_init(self) -> None:
        self.sub(Mid.EVENT_CMD, self._on_event)

    def _on_event(self):
        pass