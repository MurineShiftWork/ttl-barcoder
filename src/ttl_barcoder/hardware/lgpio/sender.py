"""lgpio backend: chardev-based GPIO, daemon-free, works on Raspberry Pi 4 and 5.

Mirrors the pigpio backend's public interface (:class:`LgpioBarcodeSender`,
:class:`LgpioConnection`, :func:`send_barcode_sequence`) so it is a drop-in alternative.
Unlike pigpio there is no daemon and no wave layer, so a barcode is emitted by driving
the line directly (``gpio_write``) and holding each segment for its duration with a
monotonic busy-wait - accurate to well under the default barcode tolerance for the
millisecond-scale segments used here, and with no background daemon to configure.

``lgpio`` is the maintained successor to ``pigpio``: it is pip-installable and, being
chardev-based, is compatible with the Raspberry Pi 5 (RP1) where ``pigpio`` is not. Pass
``gpiochip=4`` on the Pi 5 (its GPIO lives on gpiochip4); the default ``0`` suits Pi 4.
"""

from __future__ import annotations

import time
from typing import Any

try:
    import lgpio

    LGPIO_AVAILABLE = True
except ImportError:
    lgpio = None
    LGPIO_AVAILABLE = False

_INSTALL_HINT = "lgpio not available. Install with: pip install ttl-barcoder[lgpio]"


class LgpioBarcodeSender:
    """Prepares barcode pulses for lgpio without managing the connection."""

    def __init__(self, pin: int = 18):
        if not LGPIO_AVAILABLE:
            raise ImportError(_INSTALL_HINT)
        self.pin = pin

    def prepare_pulses(
        self, timing_sequence: list[tuple[bool, float]]
    ) -> list[tuple[int, int]]:
        """Map ``(level, duration_ms)`` pairs to ``(level_int, duration_us)``."""
        return [
            (1 if level else 0, int(duration_ms * 1000))
            for level, duration_ms in timing_sequence
        ]


class LgpioConnection:
    """Opens a gpiochip output line and transmits barcode sequences (daemon-free)."""

    def __init__(self, pin: int = 18, gpiochip: int = 0):
        if not LGPIO_AVAILABLE:
            raise ImportError(_INSTALL_HINT)
        self.pin = pin
        self.gpiochip = gpiochip
        self.handle: Any = None
        self.connected = False
        self.sender = LgpioBarcodeSender(pin)

    def connect(self) -> bool:
        """Open the gpiochip and claim the pin as an output (starting low)."""
        try:
            self.handle = lgpio.gpiochip_open(self.gpiochip)
            lgpio.gpio_claim_output(self.handle, self.pin, 0)
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to open gpiochip {self.gpiochip}: {e}")
            self.connected = False
            return False

    def send_sequence(self, timing_sequence: list[tuple[bool, float]]) -> bool:
        """Drive the pin through the sequence, blocking until complete; leave it low."""
        if not self.connected and not self.connect():
            return False
        try:
            perf = time.perf_counter
            for level, duration_us in self.sender.prepare_pulses(timing_sequence):
                lgpio.gpio_write(self.handle, self.pin, level)
                end = perf() + duration_us / 1_000_000
                while perf() < end:  # busy-wait: sub-ms accurate, no daemon
                    pass
            lgpio.gpio_write(self.handle, self.pin, 0)
            return True
        except Exception as e:
            print(f"Failed to send sequence: {e}")
            return False

    def disconnect(self):
        """Drive the pin low and close the gpiochip handle."""
        if self.handle is not None:
            try:
                lgpio.gpio_write(self.handle, self.pin, 0)
                lgpio.gpiochip_close(self.handle)
            except Exception:
                pass
            self.handle = None
            self.connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


def send_barcode_sequence(
    timing_sequence: list[tuple[bool, float]], pin: int = 18, gpiochip: int = 0
) -> bool:
    """Send a timing sequence via lgpio (convenience wrapper around LgpioConnection)."""
    with LgpioConnection(pin, gpiochip) as gpio:
        return gpio.send_sequence(timing_sequence)
