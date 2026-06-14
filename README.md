# TTL Barcoder

[![PyPI](https://img.shields.io/pypi/v/ttl-barcoder.svg)](https://pypi.org/project/ttl-barcoder)

Generate and decode binary barcodes over TTL signals to synchronize multiple data acquisition systems.

**[→ Full documentation](https://murineshiftwork.github.io/ttl-barcoder)**
Barcodes encode a timestamp or random value as a sequence of timed HIGH/LOW pulses, transmittable over any digital output.


## Quick Start

```python
from ttl_barcoder.core import BarcodeTTL, BarcodeConfig, TTLType, TimestampPrecision

# Timestamp barcode (default) — encodes current time at ms precision
barcoder = BarcodeTTL()
sequence = barcoder.get_sequence()   # [(level: bool, duration_ms: float), ...]

# Random barcode
config = BarcodeConfig(ttl_type=TTLType.random, barcode_bits=32)
barcoder = BarcodeTTL(config)
sequence = barcoder.get_sequence()
```

### Bpod
```python
from ttl_barcoder.core import BarcodeTTL
from ttl_barcoder.hardware.bpod import inject_barcode_states

barcoder = BarcodeTTL()
sequence = barcoder.get_sequence()
inject_barcode_states(sma, sequence, bnc_channel='BNC1', first_state_name='send_sync', last_state_name='next')
```

### Raspberry Pi GPIO
```python
from ttl_barcoder.hardware.pigpio import send_barcode_sequence

send_barcode_sequence(barcoder.get_sequence(), pin=18)
```


## Installation

```bash
pip install ttl-barcoder          # core only
pip install ttl-barcoder[bpod]    # + Bpod
pip install ttl-barcoder[pigpio]  # + Raspberry Pi GPIO
```


## Configuration

`BarcodeConfig` is a Pydantic model — all fields are validated on construction.

```python
from ttl_barcoder.core import BarcodeConfig, TTLType, TimestampPrecision

config = BarcodeConfig(
    ttl_type=TTLType.timestamp,            # or TTLType.random
    barcode_bits=37,                        # 16–64 bits
    timestamp_precision=TimestampPrecision.milliseconds,  # s / ms / us
    bit_duration_ms=35.0,
    init_duration_ms=10.0,
    tolerance=0.25,
)
```

**Presets**: `default`, `high_speed`, `conservative`, `high_precision`, `random`

```python
from ttl_barcoder.core import get_preset
config = get_preset("conservative")
```

| Preset           | Bits | Precision | Bit duration | TX duration | Coverage |
|------------------|------|-----------|--------------|-------------|----------|
| `default`        | 37   | ms        | 35 ms        | 1355 ms     | 4.4 yr   |
| `high_speed`     | 32   | ms        | 25 ms        | 848 ms      | 49 days  |
| `conservative`   | 37   | ms        | 50 ms        | 1940 ms     | 4.4 yr   |
| `high_precision` | 42   | us        | 50 ms        | 2190 ms     | 51 days  |


## Architecture

```
ttl_barcoder/
├── core/
│   ├── config.py        # BarcodeConfig (Pydantic), TTLType, TimestampPrecision
│   ├── generator.py     # TTLGenerator ABC → TimestampGenerator / RandomGenerator
│   ├── encoder.py       # bits → (level, duration_ms) timing sequence
│   ├── decoder.py       # edge timestamps → barcode value
│   └── barcode_ttl.py   # BarcodeTTL — main interface combining the above
└── hardware/
    ├── bpod/            # Bpod StateMachine integration
    └── pigpio/          # Raspberry Pi GPIO via pigpio
```

- The generator is selected via a factory (`create_generator(config)`) based on `TTLType`.
- `TimestampGenerator` quantizes Unix time at the configured precision
- `RandomGenerator` draws from a numpy RNG. Both share the same `encode_bits` / `max_value` interface on the `TTLGenerator` base class.


## Examples

- `examples/dry_simulation.py` — full walkthrough, no hardware needed
- `examples/bpod_loopback.py` — Bpod StateMachine with loopback test
- `examples/pigpio_send.py` — Raspberry Pi GPIO transmission


## Contributing

1. Fork and create a feature branch
2. Add tests for new functionality
3. Run `pytest`
4. Submit a pull request


## Acknowledgments

- Based on barcode synchronization from University of Colorado ONE Core
- Inspired by Open Ephys protocols
- Built for the neuroscience and scientific DAQ community


## License & sources

This software is released under the **[BSD 3-Clause License](LICENSE)**.
