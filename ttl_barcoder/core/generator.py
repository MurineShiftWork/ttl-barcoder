"""
Barcode Generation - Creating timestamp-based barcodes with configurable precision
"""

import time
from typing import List, Optional


class BarcodeGenerator:
    """Generate barcodes with configurable timestamp precision and bit width."""

    def __init__(self, barcode_bits: int = 37, time_precision_ms: float = 10.0):
        """
        Initialize barcode generator.

        Args:
            barcode_bits: Number of bits in barcodes
            time_precision_ms: Timestamp precision in milliseconds
        """
        self.barcode_bits = barcode_bits
        self.time_precision_ms = time_precision_ms
        self.time_units_per_second = 1000.0 / time_precision_ms

        # Calculate coverage
        max_time_units = 2**barcode_bits
        self.coverage_seconds = max_time_units / self.time_units_per_second
        self.coverage_years = self.coverage_seconds / (365.25 * 24 * 3600)

    def generate_timestamp_barcode(self, timestamp: Optional[float] = None) -> int:
        """
        Generate barcode from timestamp.

        Args:
            timestamp: Time in seconds since epoch (None = current time)

        Returns:
            Integer barcode value
        """
        if timestamp is None:
            timestamp = time.time()

        # Convert to time units
        time_units = int(timestamp * self.time_units_per_second)

        # Mask to bit width
        return time_units % (2**self.barcode_bits)

    def generate_sequence(
        self, start_timestamp: Optional[float] = None, count: int = 1, interval_s: float = 5.0
    ) -> List[int]:
        """
        Generate sequence of barcodes.

        Args:
            start_timestamp: Starting timestamp (None = current time)
            count: Number of barcodes
            interval_s: Interval between barcodes in seconds

        Returns:
            List of barcode values
        """
        if start_timestamp is None:
            start_timestamp = time.time()

        barcodes = []
        for i in range(count):
            timestamp = start_timestamp + i * interval_s
            barcode = self.generate_timestamp_barcode(timestamp)
            barcodes.append(barcode)

        return barcodes

    def recover_timestamp(
        self, barcode_value: int, reference_time: Optional[float] = None
    ) -> float:
        """
        Recover timestamp from barcode (handles wraparound).

        Args:
            barcode_value: Decoded barcode value
            reference_time: Reference time for wraparound resolution

        Returns:
            Recovered timestamp in seconds
        """
        if reference_time is None:
            reference_time = time.time()

        # Convert reference to time units
        ref_units = int(reference_time * self.time_units_per_second)

        # Find the window this barcode belongs to
        window_size = 2**self.barcode_bits
        window_number = ref_units // window_size

        # Try current and adjacent windows
        candidates = []
        for w in [window_number - 1, window_number, window_number + 1]:
            candidate_units = w * window_size + barcode_value
            candidate_time = candidate_units / self.time_units_per_second
            time_diff = abs(candidate_time - reference_time)
            candidates.append((time_diff, candidate_time))

        # Return closest candidate
        _, best_time = min(candidates, key=lambda x: x[0])
        return best_time

    def encode_bits(self, barcode_value: int) -> List[bool]:
        """
        Encode barcode as bit array (LSB first).

        Args:
            barcode_value: Integer barcode

        Returns:
            List of bits (LSB first)
        """
        barcode_value = barcode_value % (2**self.barcode_bits)
        bits = []

        for i in range(self.barcode_bits):
            bit = (barcode_value >> i) & 1
            bits.append(bool(bit))

        return bits

    @property
    def max_barcode_value(self) -> int:
        """Maximum possible barcode value."""
        return (2**self.barcode_bits) - 1

    @property
    def info(self) -> dict:
        """Information about this generator configuration."""
        return {
            "barcode_bits": self.barcode_bits,
            "time_precision_ms": self.time_precision_ms,
            "coverage_years": self.coverage_years,
            "max_value": self.max_barcode_value,
        }
