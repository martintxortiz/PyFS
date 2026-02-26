import logging
import threading
import time
from dataclasses import dataclass

from fs.common.constants import Status
from fs.common.singleton import Singleton

_SUBSEC_PER_SEC: int = 65_536  # 2^16

# Sane bounds for ground-uploadable fields
_MAX_LEAP_SECONDS: int   = 128
_MAX_STCF_ABS:     float = 1e9


@dataclass(slots=True, frozen=True)
class FSTime:
    seconds:    int
    subseconds: int
    tai:        float
    utc:        float


class TimeServices(Singleton):
    _log: logging.Logger = logging.getLogger("fs.ts")

    def __init__(
            self,
            *,
            stcf:         float = 0.0,
            leap_seconds: int   = 18,
            met_offset:   float = 0.0,
    ) -> None:
        assert isinstance(stcf, (int, float)),          "stcf must be numeric"
        assert isinstance(leap_seconds, int),            "leap_seconds must be int"
        assert 0 <= leap_seconds <= _MAX_LEAP_SECONDS,   "leap_seconds out of range"
        assert isinstance(met_offset, (int, float)),     "met_offset must be numeric"

        self._lock: threading.RLock = threading.RLock()

        # Monotonic reference — set ONCE at init, never mutated afterwards
        self._boot_wall: float = time.monotonic()

        self._met_offset:   float = float(met_offset)
        self._stcf:         float = float(stcf)
        self._leap_seconds: int   = leap_seconds

        # Telemetry command counters (housekeeping packet)
        self._cmd_count:     int = 0
        self._cmd_err_count: int = 0

        self._log.info(
            "TS initialised, (stcf=%.6f, leap_seconds=%d, met_offset=%.3f)",
            self._stcf, self._leap_seconds, self._met_offset,
        )


    def get_time(self) -> FSTime:
        """
        Return the current spacecraft time as an immutable :class:`FSTime`.

        MET  = (monotonic_now − boot_wall) + met_offset
        TAI  = MET + STCF
        UTC  = TAI − leap_seconds
        """
        with self._lock:
            met = self._raw_met()
            tai = met + self._stcf
            utc = tai - self._leap_seconds
            return FSTime(
                seconds    = int(met),
                subseconds = int((met % 1.0) * _SUBSEC_PER_SEC),
                tai        = tai,
                utc        = utc,
            )

    def met_seconds(self) -> float:
        """
        Return MET as a high-resolution float (whole seconds + fraction).

        Equivalent to ``CFE_TIME_GetMETseconds()`` plus the subsecond
        fraction, expressed as a single ``float``.
        """
        with self._lock:
            return self._raw_met()

    def set_stcf(self, value: float) -> Status:
        """
        Unconditionally replace the STCF  (CFE_TIME_SetSTCF, CC 10).

        Used by ground to correlate MET to a known absolute epoch after
        receiving a time-at-tone message.
        """
        if not isinstance(value, (int, float)):
            self._cmd_err_count += 1
            self._log.error("set_stcf: expected numeric, got %s", type(value).__name__)
            return Status.ERR_INVALID_ARGUMENT

        value = float(value)
        if abs(value) > _MAX_STCF_ABS:
            self._cmd_err_count += 1
            self._log.error("set_stcf: value %.3f exceeds sanity limit", value)
            return Status.ERR_INVALID_PARAM

        with self._lock:
            old = self._stcf
            self._stcf = value
            self._cmd_count += 1

        self._log.info("STCF  %.6f → %.6f", old, value)
        return Status.SUCCESS

    def add_stcf_adjustment(self, delta: float) -> Status:
        """
        Apply a positive one-shot STCF correction  (CFE_TIME_AddSTCFAdjustment, CC 12).

        Use when the spacecraft clock is running slow and needs advancing.
        ``delta`` must be a non-negative number of seconds.
        """
        return self._apply_stcf_delta(delta, sign=+1, tag="ADD_STCF_ADJUSTMENT")

    def sub_stcf_adjustment(self, delta: float) -> Status:
        """
        Apply a negative one-shot STCF correction  (CFE_TIME_SubSTCFAdjustment, CC 13).

        Use when the spacecraft clock is running fast and needs retarding.
        ``delta`` must be a non-negative number of seconds.
        """
        return self._apply_stcf_delta(delta, sign=-1, tag="SUB_STCF_ADJUSTMENT")

    def set_leap_seconds(self, value: int) -> Status:
        """
        Update the GPS–UTC leap-second offset  (CFE_TIME_SetLeapSeconds, CC 11).

        Per cFE spec: *"The Leap Seconds value will always be a positive number."*
        The current real-world value is 18 (as of 2024).
        """
        if not isinstance(value, int):
            self._cmd_err_count += 1
            self._log.error(
                "set_leap_seconds: expected int, got %s", type(value).__name__
            )
            return Status.ERR_INVALID_ARGUMENT

        if not (0 <= value <= _MAX_LEAP_SECONDS):
            self._cmd_err_count += 1
            self._log.error(
                "set_leap_seconds: value %d out of valid range [0, %d]",
                value, _MAX_LEAP_SECONDS,
            )
            return Status.ERR_INVALID_PARAM

        with self._lock:
            old = self._leap_seconds
            self._leap_seconds = value
            self._cmd_count += 1

        self._log.info("Leap seconds  %d → %d", old, value)
        return Status.SUCCESS

    @property
    def cmd_count(self) -> int:
        """Total accepted command count (housekeeping telemetry field)."""
        with self._lock:
            return self._cmd_count

    @property
    def cmd_err_count(self) -> int:
        """Total rejected command count (housekeeping telemetry field)."""
        with self._lock:
            return self._cmd_err_count

    @property
    def hk_tlm(self) -> dict:
        """
        Housekeeping telemetry snapshot  (CFE_TIME_HousekeepingTlm_t).

        Publish this dict on the Software Bus at 1 Hz or pack it directly
        into a CCSDS telemetry packet.
        """
        t = self.get_time()
        with self._lock:
            return {
                "cmd_count":      self._cmd_count,
                "cmd_err_count":  self._cmd_err_count,
                "leap_seconds":   self._leap_seconds,
                "stcf":           self._stcf,
                "met_seconds":    t.seconds,
                "met_subseconds": t.subseconds,
                "tai":            t.tai,
                "utc":            t.utc,
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _raw_met(self) -> float:
        """
        Compute raw MET float.

        **Must be called while holding** ``self._lock``.
        Kept as a private helper so ``get_time()`` and ``met_seconds()``
        share the same arithmetic without duplicating it.
        """
        return (time.monotonic() - self._boot_wall) + self._met_offset

    def _apply_stcf_delta(self, delta: float, sign: int, tag: str) -> Status:
        """
        Shared implementation for :meth:`add_stcf_adjustment` and
        :meth:`sub_stcf_adjustment`.

        Parameters
        ----------
        delta:
            Non-negative correction magnitude in seconds.
        sign:
            ``+1`` to advance STCF, ``-1`` to retard it.
        tag:
            Command name used in log messages.
        """
        if not isinstance(delta, (int, float)):
            self._cmd_err_count += 1
            self._log.error("%s: expected numeric delta, got %s", tag, type(delta).__name__)
            return Status.ERR_INVALID_ARGUMENT

        delta = float(delta)
        if delta < 0.0:
            self._cmd_err_count += 1
            self._log.error("%s: delta must be non-negative, got %.9f", tag, delta)
            return Status.ERR_INVALID_PARAM

        with self._lock:
            self._stcf += sign * delta
            self._cmd_count += 1

        self._log.info("%s  Δ=%.9f s  → new STCF=%.6f", tag, delta, self._stcf)
        return Status.SUCCESS
