# Getting Started

## Installation

```bash
pip install ttl-barcoder            # core only
pip install ttl-barcoder[bpod]      # + Bpod StateMachine integration
pip install ttl-barcoder[pigpio]    # + Raspberry Pi GPIO via pigpio
pip install ttl-barcoder[all]       # all extras
```

Or with uv:

```bash
uv add ttl-barcoder
uv add "ttl-barcoder[bpod]"
```

## First steps

Generate a timestamp barcode and inspect the timing sequence:

```python
from ttl_barcoder.core import BarcodeTTL

barcoder = BarcodeTTL()
barcoder.prepare()                  # generate value and compute timing sequence
sequence = barcoder.get_sequence()  # [(level: bool, duration_ms: float), ...]

print(barcoder.value)               # integer timestamp value encoded
print(len(sequence))                # number of TTL transitions
```

Each entry in `sequence` is a `(level, duration_ms)` pair: hold the output
at `level` (True = HIGH, False = LOW) for `duration_ms` milliseconds, then
move to the next entry.

## Decode from edge timestamps

After recording the TTL signal, recover the barcode value from the edge
timestamps (in milliseconds):

```python
from ttl_barcoder.core import BarcodeTTL, BarcodeConfig

config = BarcodeConfig()
barcoder = BarcodeTTL(config)

edge_times_ms = [0.0, 10.5, 45.2, ...]   # rising + falling edges in order
decoded_value = barcoder.decode(edge_times_ms)
print(decoded_value)
```

## Examples

The `examples/` directory contains:

| File | Description |
|---|---|
| `dry_simulation.py` | Full encode → decode walkthrough, no hardware needed |
| `bpod_loopback.py` | Bpod StateMachine with loopback test |
| `pigpio_send.py` | Raspberry Pi GPIO transmission |

Run the simulation example to verify the installation:

```bash
python examples/dry_simulation.py
```

## Development setup

```bash
git clone https://github.com/murineshiftwork/ttl-barcoder.git
cd ttl-barcoder
uv sync --extra dev
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
uv run pytest
```
