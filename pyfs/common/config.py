"""Frozen system configuration for the PyFS framework.

All configuration is declared once at import time and never mutated.
The executive reads ``SYSTEM_CONFIG`` to set up rate groups and bus limits.
"""

from __future__ import annotations

from dataclasses import dataclass

from pyfs.common.mid import MID


# -- Rate-group definition ---------------------------------------------

@dataclass(frozen=True, slots=True)
class RateGroupConfig:
    """One scheduler rate group.

    Attributes:
        mid:     The wakeup MID published every tick.
        rate_hz: Ticks per second (must be > 0).
    """

    mid: MID
    rate_hz: int

    def __post_init__(self) -> None:
        assert isinstance(self.mid, MID), "mid must be a MID enum member"
        assert self.rate_hz > 0, "rate_hz must be positive"


# -- Bus limits --------------------------------------------------------

@dataclass(frozen=True, slots=True)
class BusConfig:
    """Capacity limits for the software bus.

    Attributes:
        max_subscribers_per_mid: Upper bound on handlers per MID.
        max_mids:                Upper bound on distinct MID subscriptions.
    """

    max_subscribers_per_mid: int = 64
    max_mids: int = 512

    def __post_init__(self) -> None:
        assert self.max_subscribers_per_mid > 0, "max_subscribers_per_mid must be positive"
        assert self.max_mids > 0, "max_mids must be positive"


# -- Top-level system configuration ------------------------------------

@dataclass(frozen=True, slots=True)
class SystemConfig:
    """Immutable system-wide configuration.

    Attributes:
        rate_groups:    Tuple of rate-group definitions.
        bus:            Software-bus capacity limits.
        max_nodes:      Upper bound on registered nodes.
        minor_frame_s:  Main-loop sleep quantum in seconds.
    """

    rate_groups: tuple[RateGroupConfig, ...] = (
        RateGroupConfig(MID.SCH_WAKEUP_1HZ,   1),
        RateGroupConfig(MID.SCH_WAKEUP_10HZ,  10),
        RateGroupConfig(MID.SCH_WAKEUP_50HZ,  50),
        RateGroupConfig(MID.SCH_WAKEUP_100HZ, 100),
    )
    bus: BusConfig = BusConfig()
    max_nodes: int = 32
    minor_frame_s: float = 0.001

    def __post_init__(self) -> None:
        assert len(self.rate_groups) > 0, "at least one rate group required"
        assert self.max_nodes > 0, "max_nodes must be positive"
        assert self.minor_frame_s > 0.0, "minor_frame_s must be positive"


# -- Module-level default ----------------------------------------------

SYSTEM_CONFIG: SystemConfig = SystemConfig()
