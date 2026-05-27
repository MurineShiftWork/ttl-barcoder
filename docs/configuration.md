# Configuration

## BarcodeConfig

`BarcodeConfig` is a Pydantic v2 model. All fields are validated on construction.

```python
from ttl_barcoder.core import BarcodeConfig, TTLType, TimestampPrecision

config = BarcodeConfig(
    ttl_type=TTLType.timestamp,                        # or TTLType.random
    barcode_bits=37,                                   # 16–64 bits
    timestamp_precision=TimestampPrecision.milliseconds,  # s / ms / us
    bit_duration_ms=35.0,
    init_duration_ms=10.0,
    tolerance=0.25,
)
```

### Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `ttl_type` | `TTLType` | `timestamp` | Barcode value source: `timestamp` or `random` |
| `barcode_bits` | `int` | `37` | Number of data bits (16–64) |
| `timestamp_precision` | `TimestampPrecision` | `milliseconds` | Time resolution for timestamp barcodes |
| `bit_duration_ms` | `float` | `35.0` | Duration of each data bit in ms |
| `init_duration_ms` | `float` | `10.0` | Duration of the preamble pulse in ms |
| `tolerance` | `float` | `0.25` | Fractional timing tolerance for decoding (0–1) |

### TTLType

- `TTLType.timestamp` — encodes Unix time quantised to the configured precision
- `TTLType.random` — draws from a numpy RNG; value is a random integer in `[0, 2^barcode_bits)`

### TimestampPrecision

- `TimestampPrecision.seconds` — 1 s resolution
- `TimestampPrecision.milliseconds` — 1 ms resolution (default)
- `TimestampPrecision.microseconds` — 1 µs resolution

## Presets

Presets cover common hardware setups. Load with `get_preset`:

```python
from ttl_barcoder.core import get_preset

config = get_preset("conservative")
barcoder = BarcodeTTL(config)
```

| Preset | Bits | Precision | Bit duration | TX duration | Coverage |
|---|---|---|---|---|---|
| `default` | 37 | ms | 35 ms | ~1355 ms | 4.4 yr |
| `high_speed` | 32 | ms | 25 ms | ~848 ms | 49 days |
| `conservative` | 37 | ms | 50 ms | ~1940 ms | 4.4 yr |
| `high_precision` | 42 | µs | 50 ms | ~2190 ms | 51 days |
| `random` | 32 | — | 35 ms | ~1148 ms | — |

**TX duration** = total transmission time including preamble.
**Coverage** = time range before timestamp wraps (timestamp barcodes only).

## Choosing a preset

- **Default**: general-purpose; suitable for most neuroscience rigs with ~1 s alignment tolerance.
- **Conservative**: slower bit rate; use when hardware timing jitter is high (>10 ms).
- **High speed**: shorter total duration; use when inter-trial intervals are short.
- **High precision**: microsecond timestamps; use when sub-millisecond alignment is needed and hardware supports it.
- **Random**: non-temporal ID; use when you want trial identity rather than wall-clock alignment.
