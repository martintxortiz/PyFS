"""Example user nodes demonstrating the pub/sub pattern.

``TelemetryNode`` publishes altitude telemetry at 10 Hz.
``GNCNode`` subscribes to it and logs the values.
"""

from __future__ import annotations

from dataclasses import dataclass

from pyfs.common.mid import MID
from pyfs.core.bus import FSBus
from pyfs.core.message import FSMessage
from pyfs.core.node import FSNode


@dataclass(frozen=True, slots=True)
class TelemetryPayload:
    """Simple telemetry payload for demonstration."""

    altitude: float = 0.0


class TelemetryNode(FSNode):
    """Produces incrementing altitude telemetry at 10 Hz."""

    __slots__ = ("_count",)

    def __init__(self, bus: FSBus) -> None:
        self._count: int = 0
        super().__init__("tlm", bus)

    def on_init(self) -> None:
        """Subscribe to the 10 Hz wakeup tick."""
        result: bool = self._bus.subscribe(MID.SCH_WAKEUP_10HZ, self._on_wakeup)
        assert result, "failed to subscribe to SCH_WAKEUP_10HZ"

    def _on_wakeup(self, msg: FSMessage) -> None:
        """Build a ``TelemetryPayload`` and publish it on the bus."""
        assert isinstance(msg, FSMessage), "msg must be an FSMessage"

        self._count += 1
        payload: TelemetryPayload = TelemetryPayload(altitude=self._count)
        self._bus.publish(
            FSMessage(mid=MID.TLM_ALTITUDE, sender=self.name, payload=payload),
        )


class GNCNode(FSNode):
    """Consumes altitude telemetry and logs values."""

    __slots__ = ()

    def __init__(self, bus: FSBus) -> None:
        super().__init__("gnc", bus)

    def on_init(self) -> None:
        """Subscribe to altitude telemetry."""
        result: bool = self._bus.subscribe(MID.TLM_ALTITUDE, self._on_telemetry)
        assert result, "failed to subscribe to TLM_ALTITUDE"

    def _on_telemetry(self, msg: FSMessage) -> None:
        """Log received altitude."""
        assert isinstance(msg, FSMessage), "msg must be an FSMessage"
        assert isinstance(msg.payload, TelemetryPayload), "unexpected payload type"

        payload: TelemetryPayload = msg.payload
        self._log.info("altitude = %.1f", payload.altitude)