# Hardware Integration

## Bpod

The Bpod integration injects barcode timing states into a pybpodapi `StateMachine`.
The barcode is transmitted as a series of BNC output states; the last injected
state chains to whatever state you specify as `last_state_name`.

### Installation

```bash
pip install ttl-barcoder[bpod]
```

### Usage

```python
from ttl_barcoder.core import BarcodeTTL
from ttl_barcoder.hardware.bpod import inject_barcode_states

barcoder = BarcodeTTL()
barcoder.prepare()

inject_barcode_states(
    sma,                            # pybpodapi StateMachine
    barcoder.get_sequence(),
    bnc_channel="BNC1",             # Bpod BNC output channel
    first_state_name="barcode_start",
    last_state_name="next_trial",   # state to enter after barcode finishes
)
```

### State naming

`inject_barcode_states` adds one state per barcode bit plus preamble and
trailer states. The `first_state_name` is the entry point: set this as the
`state_change_conditions` target from your preceding state. The sequence
chains internally and exits to `last_state_name` when complete.

### Channel

Pass any BNC output channel supported by your Bpod model, e.g. `"BNC1"` or
`"BNC2"`. The same channel must be wired to the recording system input.

---

## Raspberry Pi GPIO (pigpio)

!!! note "lgpio migration planned"
    The current implementation uses `pigpio`. Support for `lgpio` (compatible
    with Raspberry Pi 5 and newer kernels) is planned: see the
    [GitHub issue tracker](https://github.com/murineshiftwork/ttl-barcoder/issues).

### Installation

```bash
pip install ttl-barcoder[pigpio]
```

`pigpio` requires the pigpio daemon to be running on the Pi:

```bash
sudo pigpiod
```

### Usage

```python
from ttl_barcoder.core import BarcodeTTL
from ttl_barcoder.hardware.pigpio import send_barcode_sequence

barcoder = BarcodeTTL()
barcoder.prepare()
send_barcode_sequence(barcoder.get_sequence(), pin=18)
```

`pin` is the BCM GPIO pin number. The function is blocking: it returns after
the full sequence has been transmitted.

### Timing accuracy

`pigpio` provides hardware-timed waveforms with ~1 µs jitter, well within the
default 25 % tolerance. Ensure the pigpio daemon is started with sufficient
priority (`sudo pigpiod -t 0`) on loaded systems.

---

## Custom hardware

For any hardware not listed above, consume the timing sequence directly:

```python
sequence = barcoder.get_sequence()
# sequence: list of (level: bool, duration_ms: float)

for level, duration_ms in sequence:
    your_output.set(level)
    time.sleep(duration_ms / 1000.0)
```

The sequence is hardware-agnostic: any output that can switch a digital line
and hold it for a specified duration can transmit a barcode.
