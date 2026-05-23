from typing import NamedTuple


class TimingSegment(NamedTuple):
    """Single timing segment in a barcode sequence."""

    level: bool  # Signal level (True=HIGH, False=LOW)
    duration_ms: float  # Duration in milliseconds


class TimingEncoder:
    """Encode barcode bits into timing sequences for hardware drivers."""

    def __init__(self, bit_duration_ms: float = 35.0, init_duration_ms: float = 10.0):
        """
        Initialize timing encoder.

        Args:
            bit_duration_ms: Duration of each data bit
            init_duration_ms: Duration of initialization pulses
        """
        self.bit_duration_ms = bit_duration_ms
        self.init_duration_ms = init_duration_ms

        # Calculate total timing
        self.init_sequence_ms = 3 * init_duration_ms  # LOW-HIGH-LOW

    def encode_timing_sequence(self, bits: list[bool]) -> list[TimingSegment]:
        """
        Convert bit array to complete timing sequence with init wrappers.

        Args:
            bits: List of bits (LSB first)

        Returns:
            List of TimingSegment objects
        """
        sequence = []

        # Start initialization: HIGH-LOW-HIGH
        # Must start HIGH (not LOW) so the first edge always fires even when
        # the BNC output is at LOW idle between trials. Starting LOW would
        # suppress the first edge, leaving only 1 init gap visible to the
        # decoder and causing init validation to fail for ~50% of barcodes
        # (those where bit[0]=0, which produce no edge at t=30ms).
        sequence.append(TimingSegment(True, self.init_duration_ms))
        sequence.append(TimingSegment(False, self.init_duration_ms))
        sequence.append(TimingSegment(True, self.init_duration_ms))

        # Data bits
        for bit in bits:
            sequence.append(TimingSegment(bit, self.bit_duration_ms))

        # End initialization: LOW-HIGH-LOW
        sequence.append(TimingSegment(False, self.init_duration_ms))
        sequence.append(TimingSegment(True, self.init_duration_ms))
        sequence.append(TimingSegment(False, self.init_duration_ms))

        return sequence

    def encode_state_durations(self, bits: list[bool]) -> list[float]:
        """
        Convert bits to list of state durations (for simple hardware).

        Args:
            bits: List of bits

        Returns:
            List of durations in milliseconds
        """
        sequence = self.encode_timing_sequence(bits)
        return [seg.duration_ms for seg in sequence]

    def encode_level_durations(self, bits: list[bool]) -> list[tuple[bool, float]]:
        """
        Convert bits to (level, duration) pairs.

        Args:
            bits: List of bits

        Returns:
            List of (level, duration_ms) tuples
        """
        sequence = self.encode_timing_sequence(bits)
        return [(seg.level, seg.duration_ms) for seg in sequence]

    def get_total_duration(self, num_bits: int) -> float:
        """
        Calculate total duration for a barcode sequence.

        Args:
            num_bits: Number of data bits

        Returns:
            Total duration in milliseconds
        """
        init_time = 2 * self.init_sequence_ms  # Start + end
        data_time = num_bits * self.bit_duration_ms
        return init_time + data_time

    @property
    def info(self) -> dict:
        """Information about timing configuration."""
        return {
            "bit_duration_ms": self.bit_duration_ms,
            "init_duration_ms": self.init_duration_ms,
            "init_sequence_ms": self.init_sequence_ms,
        }
