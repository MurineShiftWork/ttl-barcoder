"""
Main BarcodeTTL class - One-liner interface for barcode sequences

Combines generator, encoder, and decoder with clean configuration interface.
"""

from typing import List, Optional, Tuple

from .config import BarcodeConfig
from .decoder import BarcodeDecoder
from .encoder import TimingEncoder
from .generator import BarcodeGenerator


class BarcodeTTL:
    """
    Main interface for TTL barcode generation and decoding.

    Provides clean one-liner methods for getting barcode sequences
    ready for hardware transmission.
    """

    def __init__(self, config: Optional[BarcodeConfig] = None):
        """
        Initialize BarcodeTTL with configuration.

        Args:
            config: BarcodeConfig object (None = default configuration)
        """
        self.config = config or BarcodeConfig.default()

        # Initialize components
        self.generator = BarcodeGenerator(self.config.barcode_bits, self.config.time_precision_ms)
        self.encoder = TimingEncoder(self.config.bit_duration_ms, self.config.init_duration_ms)
        self.decoder = BarcodeDecoder(
            self.config.barcode_bits,
            self.config.bit_duration_ms,
            self.config.init_duration_ms,
            self.config.tolerance,
        )

    def get_sequence(self, barcode: Optional[int] = None) -> List[Tuple[bool, float]]:
        """
        One-liner: Get timing sequence ready for hardware transmission.

        Args:
            barcode: Specific barcode value (None = current timestamp)

        Returns:
            List of (level, duration_ms) tuples for hardware modules

        Example:
            >>> barcoder = BarcodeTTL()
            >>> sequence = barcoder.get_sequence()  # Current timestamp
            >>> sequence = barcoder.get_sequence(12345)  # Specific barcode
        """
        # Generate barcode if not provided
        if barcode is None:
            barcode = self.generator.generate_timestamp_barcode()

        # Encode to bits
        bits = self.generator.encode_bits(barcode)

        # Convert to timing sequence
        return self.encoder.encode_level_durations(bits)

    def get_sequence_from_timestamp(self, timestamp: float) -> List[Tuple[bool, float]]:
        """
        Get timing sequence from specific timestamp.

        Args:
            timestamp: Unix timestamp in seconds

        Returns:
            Timing sequence for the timestamp
        """
        barcode = self.generator.generate_timestamp_barcode(timestamp)
        return self.get_sequence(barcode)

    def get_multiple_sequences(
        self, count: int = 1, interval_s: float = 5.0, start_timestamp: Optional[float] = None
    ) -> List[List[Tuple[bool, float]]]:
        """
        Generate multiple barcode sequences with intervals.

        Args:
            count: Number of sequences
            interval_s: Time interval between sequences
            start_timestamp: Starting timestamp (None = current time)

        Returns:
            List of timing sequences
        """
        barcodes = self.generator.generate_sequence(start_timestamp, count, interval_s)
        return [self.get_sequence(barcode) for barcode in barcodes]

    def decode_edges(
        self, edge_timestamps: List[float], edge_levels: List[bool]
    ) -> Optional[Tuple[float, int]]:
        """
        Decode barcode from edge timestamps.

        Args:
            edge_timestamps: Edge times in seconds
            edge_levels: Edge levels (True=rising, False=falling)

        Returns:
            (timestamp, barcode_value) or None if decode fails
        """
        return self.decoder.decode_edges(edge_timestamps, edge_levels)

    def recover_timestamp(
        self, barcode_value: int, reference_time: Optional[float] = None
    ) -> float:
        """
        Recover original timestamp from barcode value.

        Args:
            barcode_value: Decoded barcode
            reference_time: Reference for wraparound resolution

        Returns:
            Recovered timestamp in seconds
        """
        return self.generator.recover_timestamp(barcode_value, reference_time)

    @classmethod
    def default_config(cls) -> BarcodeConfig:
        """Get default configuration."""
        return BarcodeConfig.default()

    @property
    def info(self) -> dict:
        """Get comprehensive information about this configuration."""
        return {
            "config": self.config.info(),
            "generator": self.generator.info,
            "encoder": self.encoder.info,
        }

    def __str__(self) -> str:
        """Human-readable summary."""
        return f"BarcodeTTL({self.config})"
