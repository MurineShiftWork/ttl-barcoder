"""
Pigpio implementation with clean prepare/send separation

Separates pulse generation from GPIO transmission for flexibility.
"""

import time
from typing import List, Tuple, Optional, Any

try:
    import pigpio
    PIGPIO_AVAILABLE = True
except ImportError:
    pigpio = None
    PIGPIO_AVAILABLE = False


class PigpioBarcodeSender:
    """
    Prepares barcode pulses for pigpio transmission.
    
    Separated from actual GPIO communication for clean testing
    and integration flexibility.
    """
    
    def __init__(self, pin: int = 18):
        """
        Initialize pigpio barcode sender.
        
        Args:
            pin: GPIO pin number for output
        """
        if not PIGPIO_AVAILABLE:
            raise ImportError(
                "pigpio not available. Install with: pip install pigpio"
            )
        
        self.pin = pin
    
    def prepare_pulses(self, timing_sequence: List[Tuple[bool, float]]) -> List[Any]:
        """
        Prepare pigpio pulse sequence from timing data.
        
        Args:
            timing_sequence: List of (level, duration_ms) tuples
            
        Returns:
            List of pigpio pulse objects
        """
        pulses = []
        pin_mask = 1 << self.pin
        
        for level, duration_ms in timing_sequence:
            duration_us = int(duration_ms * 1000)
            
            if level:  # HIGH
                pulses.append(pigpio.pulse(pin_mask, 0, duration_us))
            else:  # LOW
                pulses.append(pigpio.pulse(0, pin_mask, duration_us))
        
        return pulses
    
    def prepare_wave(self, timing_sequence: List[Tuple[bool, float]]) -> int:
        """
        Prepare pigpio wave from timing sequence.
        
        Args:
            timing_sequence: List of (level, duration_ms) tuples
            
        Returns:
            Wave ID for transmission
        """
        # This would be implemented with a connected pigpio instance
        raise NotImplementedError("Use PigpioConnection.prepare_wave() instead")


class PigpioConnection:
    """
    Handles pigpio daemon connection and wave transmission.
    
    Separated from pulse preparation for clean testing and reuse.
    """
    
    def __init__(self, pin: int = 18, host: str = "localhost", port: int = 8888):
        """
        Initialize pigpio connection.
        
        Args:
            pin: GPIO pin number
            host: Pigpio daemon host
            port: Pigpio daemon port
        """
        if not PIGPIO_AVAILABLE:
            raise ImportError(
                "pigpio not available. Install with: pip install pigpio"
            )
        
        self.pin = pin
        self.host = host
        self.port = port
        self.pi = None
        self.connected = False
        self.sender = PigpioBarcodeSender(pin)
    
    def connect(self) -> bool:
        """
        Connect to pigpio daemon.
        
        Returns:
            True if connection successful
        """
        try:
            self.pi = pigpio.pi(self.host, self.port)
            if not self.pi.connected:
                return False
            
            # Configure pin
            self.pi.set_mode(self.pin, pigpio.OUTPUT)
            self.pi.wave_tx_stop()
            self.pi.wave_clear()
            
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to pigpio daemon: {e}")
            self.connected = False
            return False
    
    def send_sequence(self, timing_sequence: List[Tuple[bool, float]]) -> bool:
        """
        Send timing sequence via GPIO.
        
        Args:
            timing_sequence: List of (level, duration_ms) tuples
            
        Returns:
            True if successful
        """
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            # Clear any existing waves
            self.pi.wave_tx_stop()
            self.pi.wave_clear()
            
            # Prepare pulses
            pulses = self.sender.prepare_pulses(timing_sequence)
            
            # Create wave
            self.pi.wave_add_generic(pulses)
            wid = self.pi.wave_create()
            
            if wid >= 0:
                # Send wave
                self.pi.wave_send_once(wid)
                
                # Wait for completion
                while self.pi.wave_tx_busy():
                    time.sleep(0.001)
                
                # Cleanup
                self.pi.wave_delete(wid)
                return True
            else:
                print("Failed to create pigpio wave")
                return False
                
        except Exception as e:
            print(f"Failed to send sequence: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from pigpio daemon."""
        if self.pi is not None:
            try:
                self.pi.wave_tx_stop()
                self.pi.wave_clear()
                self.pi.stop()
            except:
                pass
            self.pi = None
            self.connected = False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Convenience function for simple usage
def send_barcode_sequence(timing_sequence: List[Tuple[bool, float]],
                         pin: int = 18) -> bool:
    """
    Convenience function to send barcode sequence via GPIO.
    
    Args:
        timing_sequence: List of (level, duration_ms) tuples
        pin: GPIO pin number
        
    Returns:
        True if successful
    
    Example:
        >>> from ttl_barcoder.core import BarcodeTTL
        >>> from ttl_barcoder.hardware.pigpio import send_barcode_sequence
        >>> 
        >>> barcoder = BarcodeTTL()
        >>> sequence = barcoder.get_sequence()
        >>> send_barcode_sequence(sequence, pin=18)
    """
    with PigpioConnection(pin) as gpio:
        return gpio.send_sequence(timing_sequence)
