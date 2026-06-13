# Usage

This page covers the patterns you will return to every session: encoding a
barcode, sending it over hardware, decoding from recorded edges, and handling
error cases. Installation and `BarcodeConfig` options are in
[Getting Started](getting_started.md) and [Configuration](configuration.md).

---

## Encoding a barcode

`BarcodeTTL.prepare()` is the one-stop call for the common case. It captures
wall time, generates the barcode value from that time, and returns everything
you need to log and transmit:

```python
from ttl_barcoder import BarcodeTTL

barcoder = BarcodeTTL()
barcode_value, wall_time, timing_sequence = barcoder.prepare()

# barcode_value  -- integer encoded in the TTL signal
# wall_time      -- Unix time captured before encoding (float, seconds)
# timing_sequence -- list of (level: bool, duration_ms: float)
```

Log `barcode_value` and `wall_time` to your trial table. They let you align
the recording system clock to wall time after the experiment.

If you need a sequence for a specific timestamp rather than the current time:

```python
timing_sequence = barcoder.get_sequence_from_timestamp(1_700_000_000.0)
```

This raises `ValueError` if the config uses `TTLType.random`.

---

## Generating multiple sequences up front

Pre-compute sequences for all trials before the experiment starts so that no
Python-level work occurs inside a timing-critical trial loop:

```python
sequences = barcoder.get_multiple_sequences(count=200, interval_s=5.0)

for seq in sequences:
    send(seq)          # your hardware call
    run_trial()
```

For `TTLType.timestamp` the sequences encode evenly spaced timestamps. For
`TTLType.random` each sequence encodes an independent random value.

---

## Injecting into a Bpod state machine

`inject_barcode_states` adds one state per timing segment to an existing
`StateMachine`. Call it after creating your other states, then set
`first_state_name` as the transition target from whatever state precedes the
barcode:

```python
from ttl_barcoder import BarcodeTTL
from ttl_barcoder.hardware.bpod import inject_barcode_states

barcoder = BarcodeTTL()
barcode_value, wall_time, timing_sequence = barcoder.prepare()

sma = StateMachine(bpod)

sma.add_state(
    state_name="wait_for_poke",
    state_timer=5.0,
    state_change_conditions={"Port1In": "barcode_start"},
    output_actions=[],
)

inject_barcode_states(
    sma,
    timing_sequence,
    bnc_channel="BNC1",
    first_state_name="barcode_start",
    last_state_name="stimulus",      # state to enter after barcode finishes
)

sma.add_state(
    state_name="stimulus",
    ...
)
```

The function returns `sma` so you can chain calls, but it also modifies `sma`
in-place. The barcode occupies approximately `config.total_duration_ms`
milliseconds of state machine time (around 1355 ms for the default config).

### Choosing the BNC channel

Pass the channel name as a string matching your Bpod model's output, for
example `"BNC1"` or `"BNC2"`. Wire the same channel to the digital input of
your recording system.

---

## Sending over Raspberry Pi GPIO

`send_barcode_sequence` is a convenience wrapper that opens a connection,
transmits the wave, and closes the connection:

```python
from ttl_barcoder import BarcodeTTL
from ttl_barcoder.hardware.pigpio import send_barcode_sequence

barcoder = BarcodeTTL()
_, _, timing_sequence = barcoder.prepare()

success = send_barcode_sequence(timing_sequence, pin=18)
if not success:
    print("GPIO transmission failed")
```

The call blocks until the hardware wave completes. For repeated sends within
a session, reuse a `PigpioConnection` to avoid the connect/disconnect overhead:

```python
from ttl_barcoder.hardware.pigpio import PigpioConnection

with PigpioConnection(pin=18) as gpio:
    for trial in trials:
        _, _, seq = barcoder.prepare()
        gpio.send_sequence(seq)
        run_trial(trial)
```

---

## Decoding from recorded edge timestamps

After recording, extract rising and falling edge timestamps from your TTL
channel and pass them to `decode_edges`. Timestamps must be in seconds (not
milliseconds) and edges must alternate between rising and falling:

```python
from ttl_barcoder import BarcodeTTL

barcoder = BarcodeTTL()

# edge_timestamps: list of edge times in seconds (from your recording system)
# edge_levels: corresponding level after each edge (True=HIGH, False=LOW)
result = barcoder.decode_edges(edge_timestamps, edge_levels)

if result is None:
    print("Decode failed: check edge count and init pattern")
else:
    start_time_s, barcode_value = result
    print(f"Barcode {barcode_value} detected at t={start_time_s:.3f} s")
```

`decode_edges` returns `None` when the preamble pattern is not found or there
are fewer than 6 edges. The most common causes are a truncated recording window
or a timing mismatch between the config used for encoding and decoding.

---

## Recovering wall time from a decoded value

For `TTLType.timestamp` barcodes, convert the raw integer back to a Unix
timestamp. The `reference_time` argument resolves modular wraparound; pass a
time close to when the barcode was sent:

```python
wall_time = barcoder.recover_timestamp(
    barcode_value=barcode_value,
    reference_time=recording_start_time,  # any time within coverage_years/2 of transmission
)
print(f"Barcode encoded time: {wall_time}")
```

If `reference_time` is omitted it defaults to `time.time()`, which is usually
fine for online decoding but unreliable for offline analysis of old recordings.
This method raises `ValueError` for `TTLType.random` configs.

---

## Error cases

| Symptom | Likely cause | Fix |
|---|---|---|
| `decode_edges` returns `None` | Fewer than 6 edges, or preamble gaps outside tolerance | Widen `tolerance` in config, or check wiring |
| `ValueError` from `recover_timestamp` | Config uses `TTLType.random` | Use `TTLType.timestamp` or read `barcode_value` directly |
| `ValueError` from `get_sequence_from_timestamp` | Config uses `TTLType.random` | Same as above |
| `ImportError` on `inject_barcode_states` | pybpodapi not installed | `pip install ttl-barcoder[bpod]` |
| `ImportError` on `send_barcode_sequence` | pigpio not installed | `pip install ttl-barcoder[pigpio]` |
| GPIO send returns `False` | pigpio daemon not running | `sudo pigpiod` on the Pi |
| Decoded value is wrong | Config mismatch between encoder and decoder | Use the same `BarcodeConfig` for both |

---

## Inspecting config and coverage

```python
barcoder = BarcodeTTL()
print(barcoder.config)
# BarcodeConfig(timestamp, 37-bit, ms precision, 4.4yr coverage, 35.0ms bits, 1355ms total)

print(barcoder.config.total_duration_ms)   # total TTL transmission time
print(barcoder.config.coverage_years)      # how long before timestamp wraps
print(barcoder.info)                       # full dict with generator and encoder details
```
