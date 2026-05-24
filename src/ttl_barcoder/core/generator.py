from __future__ import annotations

import time
from abc import ABC, abstractmethod

import numpy as np

from ttl_barcoder.core.config import (
    PRECISION_UNITS_PER_SECOND,
    BarcodeConfig,
    TimestampPrecision,
    TTLType,
)


class TTLGenerator(ABC):
    """Abstract base for TTL barcode value generators."""

    def __init__(self, barcode_bits: int) -> None:
        self.barcode_bits = barcode_bits

    @abstractmethod
    def generate(self, timestamp: float | None = None) -> int:
        """Generate a barcode value."""

    def encode_bits(self, value: int) -> list[bool]:
        """Encode barcode value as bit array (LSB first)."""
        value = value % (2**self.barcode_bits)
        return [bool((value >> i) & 1) for i in range(self.barcode_bits)]

    @property
    def max_value(self) -> int:
        """Maximum possible barcode value."""
        return (2**self.barcode_bits) - 1

    @property
    def info(self) -> dict:
        return {"barcode_bits": self.barcode_bits, "max_value": self.max_value}


class TimestampGenerator(TTLGenerator):
    """Generate barcodes from Unix timestamps at configurable precision."""

    def __init__(self, barcode_bits: int, precision: TimestampPrecision) -> None:
        super().__init__(barcode_bits)
        self.precision = precision
        self._units_per_second: float = PRECISION_UNITS_PER_SECOND[precision]

    def generate(self, timestamp: float | None = None) -> int:
        """Generate barcode from timestamp (defaults to current time)."""
        if timestamp is None:
            timestamp = time.time()
        units = int(timestamp * self._units_per_second)
        return units % (2**self.barcode_bits)

    def generate_sequence(
        self,
        count: int = 1,
        interval_s: float = 5.0,
        start_timestamp: float | None = None,
    ) -> list[int]:
        """Generate a sequence of barcodes at fixed time intervals."""
        if start_timestamp is None:
            start_timestamp = time.time()
        return [self.generate(start_timestamp + i * interval_s) for i in range(count)]

    def recover_timestamp(
        self, barcode_value: int, reference_time: float | None = None
    ) -> float:
        """Recover timestamp from barcode value, resolving wraparound."""
        if reference_time is None:
            reference_time = time.time()
        ref_units = int(reference_time * self._units_per_second)
        window_size = 2**self.barcode_bits
        window_number = ref_units // window_size
        candidates = []
        for w in (window_number - 1, window_number, window_number + 1):
            candidate_units = w * window_size + barcode_value
            candidate_time = candidate_units / self._units_per_second
            candidates.append((abs(candidate_time - reference_time), candidate_time))
        return min(candidates)[1]

    @property
    def coverage_seconds(self) -> float:
        return (2**self.barcode_bits) / self._units_per_second

    @property
    def coverage_years(self) -> float:
        return self.coverage_seconds / (365.25 * 24 * 3600)

    @property
    def info(self) -> dict:
        return {
            **super().info,
            "type": "timestamp",
            "precision": self.precision.value,
            "units_per_second": self._units_per_second,
            "coverage_years": self.coverage_years,
        }


class RandomGenerator(TTLGenerator):
    """Generate random n-bit barcode values using numpy."""

    def __init__(self, barcode_bits: int) -> None:
        super().__init__(barcode_bits)
        self._rng = np.random.default_rng()

    def generate(self, timestamp: float | None = None) -> int:
        """Generate a random barcode value."""
        return int(self._rng.integers(0, 2**self.barcode_bits))

    @property
    def info(self) -> dict:
        return {**super().info, "type": "random"}


def create_generator(config: BarcodeConfig) -> TTLGenerator:
    """Create TimestampGenerator or RandomGenerator from config."""
    if config.ttl_type == TTLType.timestamp:
        return TimestampGenerator(config.barcode_bits, config.timestamp_precision)
    if config.ttl_type == TTLType.random:
        return RandomGenerator(config.barcode_bits)
    raise ValueError(f"Unknown TTL type: {config.ttl_type!r}")
