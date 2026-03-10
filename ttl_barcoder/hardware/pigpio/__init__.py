"""
Pigpio Hardware Implementation

Raspberry Pi GPIO integration for direct barcode transmission with clean
separation between pulse preparation and GPIO execution.
"""

from .sender import PigpioBarcodeSender, PigpioConnection

__all__ = ["PigpioBarcodeSender", "PigpioConnection"]
