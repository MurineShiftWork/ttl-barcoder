from typing import NamedTuple


class TimingSegment(NamedTuple):
    """Single timing segment in a barcode sequence."""

    level: bool  # Signal level (True=HIGH, False=LOW)
    duration_ms: float  # Duration in milliseconds


class TimingEncoder:
    """Encode barcode bits into timing sequences for hardware drivers."""

    def __init__(self, bit_duration_ms: float = 35.0, init_duration_ms: float = 10.0):
        self.bit_duration_ms = bit_duration_ms
        self.init_duration_ms = init_duration_ms
        self.init_sequence_ms = 3 * init_duration_ms

    def encode_timing_sequence(self, bits: list[bool]) -> list[TimingSegment]:
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

        for bit in bits:
            sequence.append(TimingSegment(bit, self.bit_duration_ms))

        # End initialization: LOW-HIGH-LOW
        sequence.append(TimingSegment(False, self.init_duration_ms))
        sequence.append(TimingSegment(True, self.init_duration_ms))
        sequence.append(TimingSegment(False, self.init_duration_ms))

        return sequence

    def encode_state_durations(self, bits: list[bool]) -> list[float]:
        return [seg.duration_ms for seg in self.encode_timing_sequence(bits)]

    def encode_level_durations(self, bits: list[bool]) -> list[tuple[bool, float]]:
        return [
            (seg.level, seg.duration_ms) for seg in self.encode_timing_sequence(bits)
        ]

    def get_total_duration(self, num_bits: int) -> float:
        return 2 * self.init_sequence_ms + num_bits * self.bit_duration_ms

    @property
    def info(self) -> dict:
        return {
            "bit_duration_ms": self.bit_duration_ms,
            "init_duration_ms": self.init_duration_ms,
            "init_sequence_ms": self.init_sequence_ms,
        }
