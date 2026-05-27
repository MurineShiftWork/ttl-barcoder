# TTL Barcoder

[![PyPI](https://img.shields.io/pypi/v/ttl-barcoder.svg)](https://pypi.org/project/ttl-barcoder)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Generate and decode binary barcodes over TTL signals to synchronize multiple data acquisition systems.
Barcodes encode a timestamp or random value as a sequence of timed HIGH/LOW pulses,
transmittable over any digital output.

## Key features

- Timestamp barcodes: encode Unix time at second, millisecond, or microsecond precision
- Random barcodes: 16–64 bit random values from a seeded numpy RNG
- Hardware-agnostic core: timing sequences are plain Python lists — no hardware dependency
- Bpod integration: inject barcode states directly into a pybpodapi `StateMachine`
- Raspberry Pi GPIO: send sequences over any GPIO pin via `pigpio`
- Decoder: recover barcode value from edge timestamps with configurable tolerance
- Validated configuration: Pydantic v2 `BarcodeConfig` with presets for common setups

## Quick start

```python
from ttl_barcoder.core import BarcodeTTL, BarcodeConfig, TTLType

# Timestamp barcode (default) — encodes current time at ms precision
barcoder = BarcodeTTL()
barcoder.prepare()                            # generates value + timing sequence
sequence = barcoder.get_sequence()            # [(level: bool, duration_ms: float), ...]

# Random barcode
config = BarcodeConfig(ttl_type=TTLType.random, barcode_bits=32)
barcoder = BarcodeTTL(config)
barcoder.prepare()
sequence = barcoder.get_sequence()
```

→ [Getting Started](getting_started.md) for installation and a step-by-step walkthrough.

→ [Configuration](configuration.md) for `BarcodeConfig` options and presets.

→ [Hardware](hardware.md) for Bpod and Raspberry Pi GPIO integration.
