from importlib.metadata import PackageNotFoundError, version

from ttl_barcoder.core import (
    BarcodeConfig,
    BarcodeDecoder,
    BarcodeTTL,
    RandomGenerator,
    TimestampGenerator,
    TimestampPrecision,
    TimingEncoder,
    TTLGenerator,
    TTLType,
    create_generator,
    get_preset,
)

try:
    __version__ = version("ttl-barcoder")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "BarcodeConfig",
    "BarcodeDecoder",
    "BarcodeTTL",
    "RandomGenerator",
    "TimestampGenerator",
    "TimestampPrecision",
    "TimingEncoder",
    "TTLGenerator",
    "TTLType",
    "create_generator",
    "get_preset",
]
