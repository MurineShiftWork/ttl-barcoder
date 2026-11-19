from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Sequence


class FoundBarcode(NamedTuple):
    """One barcode located in an edge stream."""

    start_s: float  # first rising edge (init)
    end_s: float  # start_s + the configured total duration
    value: int


_INIT_LEVELS = (True, False, True)
_END_LEVELS = (False, True, False)


def drop_short_pulses(
    edge_timestamps: Sequence[float],
    edge_levels: Sequence[bool],
    min_width_s: float = 0.0,
) -> tuple[list[float], list[bool]]:
    """Edges without pulses of ``min_width_s`` or shorter, and without repeated levels.

    Digital inputs that share a port can report an off and an on edge at the same
    timestamp whenever another line on the port changes. Edges at one timestamp with
    both levels are such a pulse and are dropped together, whatever order they come
    in. With ``min_width_s`` > 0, any pulse up to that width is dropped too, so the
    line keeps the level it had before it.
    """
    grouped: list[tuple[float, bool]] = []
    i, n = 0, len(edge_timestamps)
    while i < n:
        j = i
        while j + 1 < n and edge_timestamps[j + 1] == edge_timestamps[i]:
            j += 1
        group = {bool(v) for v in edge_levels[i : j + 1]}
        if len(group) == 1:
            grouped.append((float(edge_timestamps[i]), group.pop()))
        i = j + 1

    times: list[float] = []
    levels: list[bool] = []
    for t, level in grouped:
        if levels and levels[-1] == level:
            continue
        if times and t - times[-1] <= min_width_s:
            times.pop()
            levels.pop()
            continue
        times.append(t)
        levels.append(level)
    return times, levels


class BarcodeDecoder:
    """Decode edge timestamps back to barcode values.

    Must be constructed with parameters that match the encoder that produced
    the signal. Use BarcodeConfig to keep encoder and decoder in sync.
    """

    def __init__(
        self,
        barcode_bits: int = 37,
        bit_duration_ms: float = 35.0,
        init_duration_ms: float = 10.0,
        tolerance: float = 0.25,
    ):
        self.barcode_bits = barcode_bits
        self.bit_duration_ms = bit_duration_ms
        self.init_duration_ms = init_duration_ms
        self.tolerance = tolerance

        self.init_wrapper_ms = 3 * init_duration_ms
        self.min_init = init_duration_ms * (1 - tolerance)
        self.max_init = init_duration_ms * (1 + tolerance)

    def decode_edges(
        self, edge_timestamps: list[float], edge_levels: list[bool]
    ) -> tuple[float, int] | None:
        """Decode edge timestamps to (timestamp, barcode_value) or None on failure."""
        if len(edge_timestamps) < 6:
            return None

        start_time = edge_timestamps[0]
        rel_times_ms = [(t - start_time) * 1000 for t in edge_timestamps]

        if not self._validate_init_pattern(rel_times_ms):
            return None

        data_times = rel_times_ms[2:-2]
        data_levels = edge_levels[2:-2]

        if not data_times:
            return None

        bits = self._decode_bits(data_times, data_levels)
        barcode_value = sum(bits[i] * (2**i) for i in range(len(bits)))
        return (start_time, barcode_value)

    def _validate_init_pattern(self, rel_times_ms: list[float]) -> bool:
        # Require >=1 init-duration gap (not 2): BNC idle-LOW + old encoder starting LOW
        # leaves only 1 detectable gap. HIGH-LOW-HIGH encoder fix gives 2; requiring 1
        # handles both encoder versions without breaking the fixed path.
        if len(rel_times_ms) < 4:
            return False
        time_diffs = np.diff(rel_times_ms)
        init_candidates = sum(
            1 for diff in time_diffs[:3] if self.min_init <= diff <= self.max_init
        )
        return init_candidates >= 1

    def _decode_bits(
        self, data_times: list[float], data_levels: list[bool]
    ) -> list[int]:
        """Sample each bit by majority level at the mid-point of its time slot."""
        bits = []
        current_level = False
        edge_idx = 0
        for bit in range(self.barcode_bits):
            bit_sample_time = (
                self.init_wrapper_ms
                + bit * self.bit_duration_ms
                + self.bit_duration_ms / 2
            )
            while (
                edge_idx < len(data_times) and data_times[edge_idx] <= bit_sample_time
            ):
                current_level = data_levels[edge_idx]
                edge_idx += 1
            bits.append(1 if current_level else 0)
        return bits

    @property
    def total_duration_ms(self) -> float:
        """Duration of one barcode: init and end framing plus all bits."""
        return 6 * self.init_duration_ms + self.barcode_bits * self.bit_duration_ms

    def find_barcodes(
        self,
        edge_timestamps: Sequence[float],
        edge_levels: Sequence[bool],
        *,
        min_pulse_s: float = 0.0,
        sample_interval_s: float = 0.0,
    ) -> list[FoundBarcode]:
        """Locate and decode every barcode in a continuous edge stream.

        A barcode is located by its configured lengths, not by silences around it:
        each rising edge is a candidate start, and the line level is read at the
        middle of every init, bit and end segment from there. A decoded barcode
        covers ``total_duration_ms``; the search resumes after it.

        Args:
            edge_timestamps: Edge times in seconds, ascending.
            edge_levels: Level after each edge.
            min_pulse_s: Pulses up to this width are dropped first (see
                ``drop_short_pulses``); zero-length pulses are always dropped.
            sample_interval_s: Sampling interval of the source, e.g. the frame
                interval of a camera line. When the init pulses are shorter than two
                samples they cannot be seen reliably: framing is not checked, and a
                barcode starts at the first high sample after the previous one. A
                sampled edge happened up to one interval before the sample that shows
                it, so each start is taken half an interval earlier. Bits shorter
                than about three samples do not decode reliably (at 60 fps, 35 ms bits
                decode exactly for about a quarter of frame phases, 50 ms bits always).

        Returns:
            One ``FoundBarcode`` (start, end, value) per barcode, in time order. Edges
            outside every ``[start_s, end_s]`` are not part of a barcode (trial pulses,
            other signals).
        """
        times, levels = drop_short_pulses(edge_timestamps, edge_levels, min_pulse_s)
        if not times:
            return []
        t = np.asarray(times, dtype=float)
        lv = np.asarray(levels, dtype=bool)

        init = self.init_duration_ms / 1000.0
        bit = self.bit_duration_ms / 1000.0
        n = self.barcode_bits
        check_framing = init >= 2 * sample_interval_s
        init_mid = (np.arange(3) + 0.5) * init
        bit_mid = 3 * init + (np.arange(n) + 0.5) * bit
        end_mid = 3 * init + n * bit + (np.arange(3) + 0.5) * init
        weights = np.array([1 << k for k in range(n)], dtype=object)

        def level_at(at: np.ndarray) -> np.ndarray:
            idx = np.searchsorted(t, at, side="right") - 1
            return np.where(idx >= 0, lv[np.clip(idx, 0, None)], False)

        total = self.total_duration_ms / 1000.0
        results: list[FoundBarcode] = []
        free_from = -np.inf
        for seen in t[lv]:
            start = seen - sample_interval_s / 2
            if start < free_from:
                continue
            if check_framing and (
                tuple(level_at(start + init_mid)) != _INIT_LEVELS
                or tuple(level_at(start + end_mid)) != _END_LEVELS
            ):
                continue
            bits = level_at(start + bit_mid).astype(int)
            value = int(np.dot(bits.astype(object), weights))
            results.append(FoundBarcode(float(start), float(start + total), value))
            free_from = start + total
        return results

    def decode_stream(
        self,
        edge_timestamps: Sequence[float],
        edge_levels: Sequence[bool],
        *,
        min_pulse_s: float = 0.0,
        sample_interval_s: float = 0.0,
    ) -> list[tuple[float, int]]:
        """``(start_s, value)`` of every barcode in an edge stream."""
        return [
            (b.start_s, b.value)
            for b in self.find_barcodes(
                edge_timestamps,
                edge_levels,
                min_pulse_s=min_pulse_s,
                sample_interval_s=sample_interval_s,
            )
        ]
