from dataclasses import dataclass

from pyfs.common.fs_mid import Mid
from pyfs.core.fs_message import FSMessage
from pyfs.core.fs_node import FSNode


@dataclass(frozen=True, slots=True)
class FSTlmPayload:
    altitude: int


class DataGenerator(FSNode):
    name = "dg"

    def on_init(self) -> None:
        self.sub(Mid.SCH_WAKEUP_1HZ, self._tick)
        self.count = 0

    def _tick(self, message: FSMessage) -> None:
        self.count += 1
        payload = FSTlmPayload(altitude=self.count)
        self.bus.pub(Mid.TLM_MESSAGE_MID, FSMessage(Mid.TLM_MESSAGE_MID, payload=payload))


class CommandReceiver(FSNode):
    name = "cr"
    enabled = False

    def on_init(self) -> None:
        self.sub(Mid.SCH_WAKEUP_1HZ, self._tick)

    def _tick(self, message: FSMessage) -> None:
        pass


class CommandReceiver2(FSNode):
    name = "cr2"
    enabled = False

    def on_init(self) -> None:
        self.sub(Mid.SCH_WAKEUP_1HZ, self._tick)

    def _tick(self, message: FSMessage) -> None:
        self.log.info("1")