from __future__ import annotations

from typing import Optional

from ttl_barcoder.core.config import BarcodeConfig, TTLType
from ttl_barcoder.core.decoder import BarcodeDecoder
from ttl_barcoder.core.encoder import TimingEncoder
from ttl_barcoder.core.generator import TimestampGenerator, TTLGenerator, create_generator


class BarcodeTTL:
    """
    Main interface for TTL barcode generation and decoding.

    Provides clean one-liner methods for getting barcode sequences
    ready for hardware transmission.
    """

    def __init__(self, config: Optional[BarcodeConfig] = None) -> None:
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

    def get_sequence(self, barcode: Optional[int] = None) -> list[tuple[bool, float]]:
        """
        One-liner: get timing sequence ready for hardware transmission.

        Parameters
        ----------
        barcode : int, optional
            Specific barcode value. If None, calls generator.generate() to
            produce a fresh value (timestamp or random, per config).

        Returns
        -------
        list of (level, duration_ms) tuples
        """
        if barcode is None:
            barcode = self.generator.generate()
        bits = self.generator.encode_bits(barcode)
        return self.encoder.encode_level_durations(bits)

    def get_sequence_from_timestamp(self, timestamp: float) -> list[tuple[bool, float]]:
        """
        Get timing sequence from a specific Unix timestamp.

        Only valid for TTLType.timestamp configurations.
        """
        if self.config.ttl_type != TTLType.timestamp:
            raise ValueError("get_sequence_from_timestamp requires TTLType.timestamp")
        assert isinstance(self.generator, TimestampGenerator)
        barcode = self.generator.generate(timestamp=timestamp)
        return self.get_sequence(barcode=barcode)

    def get_multiple_sequences(
        self,
        count: int = 1,
        interval_s: float = 5.0,
        start_timestamp: Optional[float] = None,
    ) -> list[list[tuple[bool, float]]]:
        """
        Generate multiple barcode sequences.

        For timestamp TTL: sequences are spaced by interval_s.
        For random TTL: generates count independent random sequences (interval_s ignored).
        """
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
    ) -> Optional[tuple[float, int]]:
        """
        Decode barcode from edge timestamps.

        Returns (timestamp, barcode_value) or None if decode fails.
        """
        return self.decoder.decode_edges(edge_timestamps=edge_timestamps, edge_levels=edge_levels)

    def recover_timestamp(
        self, barcode_value: int, reference_time: Optional[float] = None
    ) -> float:
        """
        Recover original timestamp from barcode value (timestamp TTL only).

        Handles wraparound using reference_time.
        """
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
