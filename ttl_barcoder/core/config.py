"""
Barcode Configuration

Centralized parameter management with Pydantic v2 validation.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class TTLType(str, Enum):
    """Type of barcode value to generate."""

    timestamp = "timestamp"
    random = "random"


class TimestampPrecision(str, Enum):
    """Timestamp quantization precision."""

    seconds = "s"
    milliseconds = "ms"
    microseconds = "us"


# Time units per second for each precision level
PRECISION_UNITS_PER_SECOND: dict[TimestampPrecision, float] = {
    TimestampPrecision.seconds: 1.0,
    TimestampPrecision.milliseconds: 1_000.0,
    TimestampPrecision.microseconds: 1_000_000.0,
}


class BarcodeConfig(BaseModel):
    """Barcode configuration with Pydantic v2 validation."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    ttl_type: TTLType = TTLType.timestamp
    barcode_bits: int = Field(
        default=37, ge=16, le=64, description="Number of bits in barcode (16-64)"
    )
    timestamp_precision: TimestampPrecision = Field(
        default=TimestampPrecision.milliseconds,
        description="Timestamp quantization precision (s/ms/us)",
    )
    bit_duration_ms: float = Field(
        default=35.0, gt=0, le=1000, description="Duration of each bit pulse in ms"
    )
    init_duration_ms: float = Field(
        default=10.0, gt=0, le=100, description="Duration of init pulses in ms"
    )
    tolerance: float = Field(
        default=0.25, ge=0.05, le=0.5, description="Timing tolerance (0.05-0.5)"
    )

    @classmethod
    def default(cls) -> BarcodeConfig:
        """Create default configuration."""
        return cls()

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> BarcodeConfig:
        """Create configuration from dictionary."""
        return cls(**config_dict)

    @property
    def coverage_years(self) -> Optional[float]:
        """Coverage in years (timestamp TTL only)."""
        if self.ttl_type != TTLType.timestamp:
            return None
        units_per_second = PRECISION_UNITS_PER_SECOND[self.timestamp_precision]
        coverage_seconds = (2**self.barcode_bits) / units_per_second
        return coverage_seconds / (365.25 * 24 * 3600)

    @property
    def total_duration_ms(self) -> float:
        """Total barcode duration in milliseconds."""
        return 6 * self.init_duration_ms + self.barcode_bits * self.bit_duration_ms

    @property
    def safety_ratio(self) -> float:
        """Safety ratio (bit_duration vs tolerance window)."""
        return self.bit_duration_ms / (2 * self.bit_duration_ms * self.tolerance)

    def info(self) -> dict[str, Any]:
        """Configuration summary as dictionary."""
        data = self.model_dump()
        data["coverage_years"] = self.coverage_years
        data["total_duration_ms"] = self.total_duration_ms
        data["safety_ratio"] = self.safety_ratio
        return data

    def __str__(self) -> str:
        parts = [f"{self.ttl_type.value}", f"{self.barcode_bits}-bit"]
        if self.ttl_type == TTLType.timestamp:
            parts.append(f"{self.timestamp_precision.value} precision")
            if self.coverage_years is not None:
                parts.append(f"{self.coverage_years:.1f}yr coverage")
        parts += [f"{self.bit_duration_ms}ms bits", f"{self.total_duration_ms:.0f}ms total"]
        return f"BarcodeConfig({', '.join(parts)})"


# Preset configurations
PRESETS: dict[str, BarcodeConfig] = {
    "default": BarcodeConfig(),
    "high_speed": BarcodeConfig(
        barcode_bits=32,
        timestamp_precision=TimestampPrecision.milliseconds,
        bit_duration_ms=25.0,
        init_duration_ms=8.0,
    ),
    "high_precision": BarcodeConfig(
        barcode_bits=42,
        timestamp_precision=TimestampPrecision.microseconds,
        bit_duration_ms=50.0,
        init_duration_ms=15.0,
    ),
    "conservative": BarcodeConfig(
        barcode_bits=37,
        timestamp_precision=TimestampPrecision.milliseconds,
        bit_duration_ms=50.0,
        init_duration_ms=15.0,
        tolerance=0.20,
    ),
    "random": BarcodeConfig(
        ttl_type=TTLType.random,
        barcode_bits=32,
    ),
}


def get_preset(name: str) -> BarcodeConfig:
    """Get a preset configuration by name."""
    if name not in PRESETS:
        raise ValueError(f"Unknown preset '{name}'. Available: {list(PRESETS.keys())}")
    return PRESETS[name]
