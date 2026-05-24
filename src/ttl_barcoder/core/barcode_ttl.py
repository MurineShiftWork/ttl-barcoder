from __future__ import annotations

from ttl_barcoder.core.config import BarcodeConfig, TTLType
from ttl_barcoder.core.decoder import BarcodeDecoder
from ttl_barcoder.core.encoder import TimingEncoder
from ttl_barcoder.core.generator import (
    TimestampGenerator,
    TTLGenerator,
    create_generator,
)


class BarcodeTTL:
    """Main interface for TTL barcode generation and decoding."""

    def __init__(self, config: BarcodeConfig | None = None) -> None:
        self.config = config or BarcodeConfig.default()
        self.generator: TTLGenerator = create_generator(self.config)
        self.encoder = TimingEncoder(
            bit_duration_ms=self.config.bit_duration_ms,
            init_duration_ms=self.config.init_duration_ms,
        )
        self.decoder = BarcodeDecoder(
            barcode_bits=self.config.barcode_bits,
            bit_duration_ms=self.config.bit_duration_ms,
            init_duration_ms=self.config.init_duration_ms,
            tolerance=self.config.tolerance,
        )

    def prepare(self) -> tuple[int, float, list[tuple[bool, float]]]:
        """Capture wall time and return (barcode_value, wall_time, timing_sequence).

        Wall time is captured before generate() so it matches the encoded timestamp.
        """
        import time

        wall_time = time.time()
        barcode_value = self.generator.generate(timestamp=wall_time)
        timing_sequence = self.get_sequence(barcode=barcode_value)
        return barcode_value, wall_time, timing_sequence

    def get_sequence(self, barcode: int | None = None) -> list[tuple[bool, float]]:
        """Return (level, duration_ms) timing sequence for hardware transmission."""
        if barcode is None:
            barcode = self.generator.generate()
        bits = self.generator.encode_bits(barcode)
        return self.encoder.encode_level_durations(bits)

    def get_sequence_from_timestamp(self, timestamp: float) -> list[tuple[bool, float]]:
        """Get timing sequence from a specific Unix timestamp (timestamp TTL only)."""
        if self.config.ttl_type != TTLType.timestamp:
            raise ValueError("get_sequence_from_timestamp requires TTLType.timestamp")
        assert isinstance(self.generator, TimestampGenerator)
        barcode = self.generator.generate(timestamp=timestamp)
        return self.get_sequence(barcode=barcode)

    def get_multiple_sequences(
        self,
        count: int = 1,
        interval_s: float = 5.0,
        start_timestamp: float | None = None,
    ) -> list[list[tuple[bool, float]]]:
        if self.config.ttl_type == TTLType.timestamp:
            assert isinstance(self.generator, TimestampGenerator)
            barcodes = self.generator.generate_sequence(
                count=count, interval_s=interval_s, start_timestamp=start_timestamp
            )
        else:
            barcodes = [self.generator.generate() for _ in range(count)]
        return [self.get_sequence(b) for b in barcodes]

    def decode_edges(
        self, edge_timestamps: list[float], edge_levels: list[bool]
    ) -> tuple[float, int] | None:
        """Decode edge timestamps to (timestamp, barcode_value) or None."""
        return self.decoder.decode_edges(
            edge_timestamps=edge_timestamps, edge_levels=edge_levels
        )

    def recover_timestamp(
        self, barcode_value: int, reference_time: float | None = None
    ) -> float:
        """Recover original timestamp from barcode value with wraparound handling."""
        if self.config.ttl_type != TTLType.timestamp:
            raise ValueError("recover_timestamp requires TTLType.timestamp")
        assert isinstance(self.generator, TimestampGenerator)
        return self.generator.recover_timestamp(
            barcode_value=barcode_value, reference_time=reference_time
        )

    @classmethod
    def default_config(cls) -> BarcodeConfig:
        return BarcodeConfig.default()

    @property
    def info(self) -> dict:
        return {
            "config": self.config.info(),
            "generator": self.generator.info,
            "encoder": self.encoder.info,
        }

    def __str__(self) -> str:
        return f"BarcodeTTL({self.config})"
