"""
Barcode Configuration with Pydantic Integration

Centralized parameter management with type validation and model support.
"""

from dataclasses import dataclass
from typing import Any, Dict

try:
    from pydantic import BaseModel, Field, field_validator

    PYDANTIC_AVAILABLE = True
except ImportError:
    BaseModel = object
    Field = lambda **kwargs: None
    validator = lambda *args, **kwargs: lambda f: f
    PYDANTIC_AVAILABLE = False


# Pydantic model for type validation
class BarcodeConfigModel(BaseModel):
    """Pydantic model for barcode configuration with validation."""

    barcode_bits: int = Field(
        default=37, ge=16, le=64, description="Number of bits in barcode (16-64)"
    )
    time_precision_ms: float = Field(
        default=10.0, gt=0, le=1000, description="Timestamp precision in ms"
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

    @field_validator("bit_duration_ms")
    def bit_duration_must_be_reasonable(cls, v, values):
        if "tolerance" in values:
            min_safe = 10.0 / values["tolerance"]  # 10ms jitter safety
            if v < min_safe:
                raise ValueError(
                    f"bit_duration_ms should be ≥{min_safe:.1f}ms for reliable decoding"
                )
        return v

    class Config:
        validate_assignment = True
        extra = "forbid"


@dataclass
class BarcodeConfig:
    """
    Centralized configuration for barcode generation and encoding.

    Supports both individual parameters and Pydantic model integration
    for type validation and IDE support.
    """

    # Core parameters
    barcode_bits: int = 37
    time_precision_ms: float = 10.0
    bit_duration_ms: float = 35.0
    init_duration_ms: float = 10.0
    tolerance: float = 0.25

    @classmethod
    def default(cls) -> "BarcodeConfig":
        """Create default configuration."""
        return cls()

    @classmethod
    def from_model(cls, model: BarcodeConfigModel) -> "BarcodeConfig":
        """
        Create configuration from Pydantic model.

        Args:
            model: Validated BarcodeConfigModel instance

        Returns:
            BarcodeConfig with validated parameters
        """
        if not PYDANTIC_AVAILABLE:
            raise ImportError("Pydantic not available. Install with: pip install pydantic")

        return cls(
            barcode_bits=model.barcode_bits,
            time_precision_ms=model.time_precision_ms,
            bit_duration_ms=model.bit_duration_ms,
            init_duration_ms=model.init_duration_ms,
            tolerance=model.tolerance,
        )

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "BarcodeConfig":
        """
        Create configuration from dictionary with validation.

        Args:
            config_dict: Dictionary of configuration parameters

        Returns:
            Validated BarcodeConfig
        """
        if PYDANTIC_AVAILABLE:
            model = BarcodeConfigModel(**config_dict)
            return cls.from_model(model)
        else:
            # Basic validation without Pydantic
            return cls(**config_dict)

    def to_model(self) -> BarcodeConfigModel:
        """Convert to Pydantic model for validation."""
        if not PYDANTIC_AVAILABLE:
            raise ImportError("Pydantic not available. Install with: pip install pydantic")

        return BarcodeConfigModel(
            barcode_bits=self.barcode_bits,
            time_precision_ms=self.time_precision_ms,
            bit_duration_ms=self.bit_duration_ms,
            init_duration_ms=self.init_duration_ms,
            tolerance=self.tolerance,
        )

    def validate(self) -> bool:
        """Validate configuration parameters."""
        if PYDANTIC_AVAILABLE:
            try:
                self.to_model()
                return True
            except Exception:
                return False
        else:
            # Basic validation
            return (
                16 <= self.barcode_bits <= 64
                and self.time_precision_ms > 0
                and self.bit_duration_ms > 0
                and self.init_duration_ms > 0
                and 0.05 <= self.tolerance <= 0.5
            )

    @property
    def coverage_years(self) -> float:
        """Calculate coverage in years for this configuration."""
        time_units_per_second = 1000.0 / self.time_precision_ms
        max_time_units = 2**self.barcode_bits
        coverage_seconds = max_time_units / time_units_per_second
        return coverage_seconds / (365.25 * 24 * 3600)

    @property
    def total_duration_ms(self) -> float:
        """Calculate total barcode duration in milliseconds."""
        init_time = 6 * self.init_duration_ms  # 2 × (LOW-HIGH-LOW)
        data_time = self.barcode_bits * self.bit_duration_ms
        return init_time + data_time

    @property
    def safety_ratio(self) -> float:
        """Calculate safety ratio (bit_duration vs tolerance window)."""
        tolerance_window = self.bit_duration_ms * self.tolerance
        return self.bit_duration_ms / (2 * tolerance_window)

    def info(self) -> Dict[str, Any]:
        """Get configuration summary as dictionary."""
        return {
            "barcode_bits": self.barcode_bits,
            "time_precision_ms": self.time_precision_ms,
            "bit_duration_ms": self.bit_duration_ms,
            "init_duration_ms": self.init_duration_ms,
            "tolerance": self.tolerance,
            "coverage_years": self.coverage_years,
            "total_duration_ms": self.total_duration_ms,
            "safety_ratio": self.safety_ratio,
            "is_valid": self.validate(),
        }

    def __str__(self) -> str:
        """Human-readable configuration summary."""
        return (
            f"BarcodeConfig({self.barcode_bits}-bit, "
            f"{self.time_precision_ms}ms precision, "
            f"{self.bit_duration_ms}ms bits, "
            f"{self.coverage_years:.1f} year coverage, "
            f"{self.total_duration_ms:.0f}ms duration)"
        )


# Preset configurations
PRESETS = {
    "default": BarcodeConfig(),
    "high_speed": BarcodeConfig(
        barcode_bits=32, time_precision_ms=100.0, bit_duration_ms=25.0, init_duration_ms=8.0
    ),
    "high_precision": BarcodeConfig(
        barcode_bits=42, time_precision_ms=1.0, bit_duration_ms=50.0, init_duration_ms=15.0
    ),
    "conservative": BarcodeConfig(
        barcode_bits=37,
        time_precision_ms=10.0,
        bit_duration_ms=50.0,
        init_duration_ms=15.0,
        tolerance=0.20,
    ),
}


def get_preset(name: str) -> BarcodeConfig:
    """Get a preset configuration by name."""
    if name not in PRESETS:
        available = list(PRESETS.keys())
        raise ValueError(f"Unknown preset '{name}'. Available: {available}")
    return PRESETS[name]
