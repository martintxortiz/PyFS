from pyfs.common.mid import Mid
from pyfs.core.node import FSNode


class TestNode(FSNode):
    def __init__(self, bus):
        super().__init__("tlm", bus)
        self.bus.subscribe(self.name, Mid.SCHEDULE_NODE_1HZ, self.tick)
        self.count = 0

    def tick(self, msg):
        self.count += 1
        self.bus.publish(Mid.TELEMETRY_MSG_ID, {"count": self.count})

class TestNode2(FSNode):
    def __init__(self, bus):
        super().__init__("gnc", bus)
        self.bus.subscribe(self.name,Mid.TELEMETRY_MSG_ID, self._on_telemetry)
        self.bus.subscribe(self.name,Mid.SCHEDULE_NODE_10HZ, self._on_10hz)

    def _on_telemetry(self, tlm):
        print(tlm)

    def _on_10hz(self, tlm):
        print("test")


