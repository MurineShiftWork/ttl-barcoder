# TTL Barcoder

A modular Python package for generating and decoding binary barcodes via TTL signals, designed for synchronizing multiple data acquisition systems in scientific applications.

## 🎯 Key Features

- **Clean Architecture**: Separate core logic from hardware implementations
- **One-liner Interface**: `sequence = barcoder.get_sequence()`
- **Pydantic Validation**: Type-checked configuration with IDE support
- **Multiple Hardware**: Bpod StateMachine, Raspberry Pi GPIO, extensible
- **Configurable Timing**: 37-bit default (40 years @ 10ms precision, 1.36s duration)
- **Robust Decoding**: Handles timing jitter and missing edges

## 🚀 Quick Start

### Basic Usage (No Hardware)
```python
from ttl_barcoder.core import BarcodeTTL, BarcodeConfig

# Create configured barcode system
config = BarcodeConfig(barcode_bits=37, bit_duration_ms=35.0)
barcoder = BarcodeTTL(config)

# One-liner: get timing sequence
sequence = barcoder.get_sequence()  # Current timestamp
sequence = barcoder.get_sequence(12345)  # Specific barcode

# Returns: [(bool, float), ...] - (level, duration_ms) pairs
```

### Bpod Integration
```python
from pybpod import StateMachine
from ttl_barcoder.core import BarcodeTTL
from ttl_barcoder.hardware.bpod import add_barcode_sma_states

barcoder = BarcodeTTL()
sma = StateMachine()

# Add your states...
sma.add_state('trial_start', timer=1.0, next='send_sync')

# One line to inject barcode states
sequence = barcoder.get_sequence()
add_barcode_sma_states(sma, sequence, 'send_sync', 'stimulus_on', 'BNC1')

# Continue with your protocol...
sma.add_state('stimulus_on', ...)
```

### Raspberry Pi GPIO
```python
from ttl_barcoder.core import BarcodeTTL
from ttl_barcoder.hardware.pigpio import send_barcode_sequence

barcoder = BarcodeTTL()
sequence = barcoder.get_sequence()

# One-liner GPIO transmission
success = send_barcode_sequence(sequence, pin=18)
```

## 📦 Installation

### Core Package (encoding/decoding only)
```bash
pip install ttl-barcoder
```

### With Hardware Support
```bash
# Bpod support
pip install ttl-barcoder[bpod]

# Raspberry Pi GPIO
pip install ttl-barcoder[pigpio]

# Pydantic validation
pip install ttl-barcoder[validation]

# Everything
pip install ttl-barcoder[all]
```

## 🏗️ Architecture

```
ttl_barcoder/
├── core/                   # Pure logic, hardware-agnostic
│   ├── config.py          # BarcodeConfig + Pydantic integration
│   ├── generator.py       # Timestamp → barcode conversion
│   ├── encoder.py         # Bits → timing sequences  
│   ├── decoder.py         # Edge timestamps → barcodes
│   └── barcode_ttl.py     # Main BarcodeTTL interface
└── hardware/               # Device-specific implementations
    ├── bpod/              # Bpod StateMachine integration
    └── pigpio/            # Raspberry Pi GPIO via pigpio
```

## ⚙️ Configuration

### Method 1: Individual Parameters
```python
from ttl_barcoder.core import BarcodeConfig

config = BarcodeConfig(
    barcode_bits=37,          # 40 years coverage @ 10ms precision
    time_precision_ms=10.0,   # 10ms timestamp resolution
    bit_duration_ms=35.0,     # 35ms per bit (safe for 10ms jitter)
    init_duration_ms=10.0,    # 10ms initialization pulses
    tolerance=0.25            # 25% decoding tolerance
)
```

### Method 2: Pydantic Model (with validation)
```python
from ttl_barcoder.core import BarcodeConfig, BarcodeConfigModel

# Type-checked model
model = BarcodeConfigModel(
    barcode_bits=37,
    bit_duration_ms=35.0
)

config = BarcodeConfig.from_model(model)
```

### Method 3: Presets
```python
from ttl_barcoder.core import get_preset

config = get_preset("default")        # 37-bit, balanced
config = get_preset("high_speed")     # 32-bit, 848ms duration  
config = get_preset("conservative")   # 37-bit, 50ms bits, extra safe
```

## 🎛️ Hardware Integration

### Bpod StateMachine
```python
# Method 1: Prepare states separately
from ttl_barcoder.hardware.bpod import BpodBarcodeSender

sender = BpodBarcodeSender()
states = sender.prepare_states(sequence, 'start', 'end', 'BNC1')
# states = [{'state_name': ..., 'state_timer': ...}, ...]

# Method 2: Direct injection
sender.inject_states(sma, sequence, 'start', 'end', 'BNC1')

# Method 3: Convenience function  
add_barcode_sma_states(sma, sequence, 'start', 'end', 'BNC1')
```

### Raspberry Pi GPIO
```python
# Method 1: One-liner
from ttl_barcoder.hardware.pigpio import send_barcode_sequence
send_barcode_sequence(sequence, pin=18)

# Method 2: Connection management
from ttl_barcoder.hardware.pigpio import PigpioConnection

with PigpioConnection(pin=18) as gpio:
    success = gpio.send_sequence(sequence)

# Method 3: Pulse preparation (for integration)
from ttl_barcoder.hardware.pigpio import PigpioBarcodeSender

sender = PigpioBarcodeSender(pin=18)
pulses = sender.prepare_pulses(sequence)  # Raw pigpio pulses
```

## 📊 Performance & Coverage

| Configuration | Bits | Duration | Coverage | Use Case |
|---------------|------|----------|----------|----------|
| `default` | 37 | 1355ms | 40 years | Balanced performance |
| `high_speed` | 32 | 848ms | 13 years | Fast transmission |
| `conservative` | 37 | 1940ms | 40 years | Maximum reliability |
| `high_precision` | 42 | 2190ms | 139 years | Long-term studies |

**Timing Safety**: 35ms bits with 25% tolerance = ±8.75ms window, safe for 10ms system jitter.

## 🔧 Examples

See `examples/` directory:
- `dry_simulation.py`: Core functionality without hardware
- `bpod_loopback.py`: Bpod StateMachine with loopback test  
- `pigpio_send.py`: Raspberry Pi GPIO transmission

## 🧪 Hardware Setup

### Bpod Setup
1. Connect Bpod device (e.g., `/dev/ttyACM0`)
2. Configure BNC outputs in your StateMachine
3. Optional: Wire loopback for testing (BNC1 out → BNC1 in)

### Raspberry Pi Setup
1. Enable pigpio daemon: `sudo systemctl enable pigpio`
2. Connect TTL output to GPIO pin (default: pin 18)
3. Connect ground reference between Pi and target systems
4. Verify with oscilloscope or logic analyzer

## 🔍 API Reference

### Core Classes

**`BarcodeTTL(config)`** - Main interface
- `get_sequence(barcode=None)` → timing sequence
- `decode_edges(timestamps, levels)` → barcode value
- `get_multiple_sequences(count, interval)` → multiple sequences

**`BarcodeConfig`** - Configuration management
- `BarcodeConfig.default()` → default settings
- `BarcodeConfig.from_model(model)` → from Pydantic
- `get_preset(name)` → preset configurations

### Hardware Modules

**Bpod**: `ttl_barcoder.hardware.bpod`
- `add_barcode_sma_states()` → inject into StateMachine
- `BpodBarcodeSender.prepare_states()` → state definitions
- `BpodConnection(device_path)` → device management

**Pigpio**: `ttl_barcoder.hardware.pigpio`  
- `send_barcode_sequence()` → one-liner transmission
- `PigpioBarcodeSender.prepare_pulses()` → pulse objects
- `PigpioConnection(pin)` → GPIO management

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Run tests: `pytest`
5. Submit pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on barcode synchronization from University of Colorado ONE Core
- Inspired by Open Ephys protocols
- Built for the neuroscience and scientific DAQ community

---

**Ready to synchronize your data streams? Start with a simple `pip install ttl-barcoder` and see the examples!**
