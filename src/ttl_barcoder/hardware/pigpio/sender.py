import time
from typing import Any

try:
    import pigpio

    PIGPIO_AVAILABLE = True
except ImportError:
    pigpio = None
    PIGPIO_AVAILABLE = False


class PigpioBarcodeSender:
    """Prepares barcode pulses for pigpio without managing the connection."""

    def __init__(self, pin: int = 18):
        if not PIGPIO_AVAILABLE:
            raise ImportError("pigpio not available. Install with: pip install pigpio")
        self.pin = pin

    def prepare_pulses(self, timing_sequence: list[tuple[bool, float]]) -> list[Any]:
        """Convert (level, duration_ms) pairs to pigpio pulse objects."""
        pulses = []
        pin_mask = 1 << self.pin
        for level, duration_ms in timing_sequence:
            duration_us = int(duration_ms * 1000)
            if level:
                pulses.append(pigpio.pulse(pin_mask, 0, duration_us))
            else:
                pulses.append(pigpio.pulse(0, pin_mask, duration_us))
        return pulses

    def prepare_wave(self, timing_sequence: list[tuple[bool, float]]) -> int:
        raise NotImplementedError("Use PigpioConnection.prepare_wave() instead")


class PigpioConnection:
    """Manages pigpio daemon connection and wave transmission."""

    def __init__(self, pin: int = 18, host: str = "localhost", port: int = 8888):
        if not PIGPIO_AVAILABLE:
            raise ImportError("pigpio not available. Install with: pip install pigpio")
        self.pin = pin
        self.host = host
        self.port = port
        self.pi: Any = None
        self.connected = False
        self.sender = PigpioBarcodeSender(pin)

    def connect(self) -> bool:
        try:
            self.pi = pigpio.pi(self.host, self.port)
            if not self.pi.connected:
                return False
            self.pi.set_mode(self.pin, pigpio.OUTPUT)
            self.pi.wave_tx_stop()
            self.pi.wave_clear()
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to pigpio daemon: {e}")
            self.connected = False
            return False

    def send_sequence(self, timing_sequence: list[tuple[bool, float]]) -> bool:
        """Send timing sequence via GPIO wave, blocking until complete."""
        if not self.connected and not self.connect():
            return False
        try:
            self.pi.wave_tx_stop()
            self.pi.wave_clear()
            pulses = self.sender.prepare_pulses(timing_sequence)
            self.pi.wave_add_generic(pulses)
            wid = self.pi.wave_create()
            if wid >= 0:
                self.pi.wave_send_once(wid)
                while self.pi.wave_tx_busy():
                    time.sleep(0.001)
                self.pi.wave_delete(wid)
                return True
            else:
                print("Failed to create pigpio wave")
                return False
        except Exception as e:
            print(f"Failed to send sequence: {e}")
            return False

    def disconnect(self):
        if self.pi is not None:
            try:
                self.pi.wave_tx_stop()
                self.pi.wave_clear()
                self.pi.stop()
            except Exception:
                pass
            self.pi = None
            self.connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


def send_barcode_sequence(
    timing_sequence: list[tuple[bool, float]], pin: int = 18
) -> bool:
    """Send a timing sequence via GPIO (convenience wrapper around PigpioConnection)."""
    with PigpioConnection(pin) as gpio:
        return gpio.send_sequence(timing_sequence)
