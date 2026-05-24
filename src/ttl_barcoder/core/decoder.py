import numpy as np


class BarcodeDecoder:
    """Decode edge timestamps back to barcode values."""

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
        # Require ≥1 init-duration gap (not 2): BNC idle-LOW + old encoder starting LOW
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
