#!/usr/bin/env python3
"""
Example: Pigpio GPIO transmission

Demonstrates direct GPIO transmission via pigpio on Raspberry Pi.
"""

from ttl_barcoder.core import BarcodeConfig, BarcodeTTL


def main():
    print("TTL Barcoder - Pigpio GPIO Example")
    print("=" * 45)

    try:
        from ttl_barcoder.hardware.pigpio import PigpioBarcodeSender
    except ImportError as e:
        print(f"Pigpio not available: {e}")
        print("Install with: pip install pigpio")
        print("Also ensure pigpio daemon is running: sudo systemctl start pigpio")
        return

    # Configuration
    config = BarcodeConfig(barcode_bits=37, bit_duration_ms=35.0, init_duration_ms=10.0)

    print(f"Using config: {config}")

    # Create barcode system
    barcoder = BarcodeTTL(config)
    gpio_pin = 18

    print(f"\nGPIO pin: {gpio_pin}")
    print(f"Total duration per barcode: {config.total_duration_ms:.0f}ms")

    # Method 1: One-liner convenience function
    print("\n1. Convenience Function (one-liner):")
    sequence = barcoder.get_sequence()
    print(f"Generated sequence: {len(sequence)} segments")

    print("To send via GPIO (uncomment to execute):")
    print(f"success = send_barcode_sequence(sequence, pin={gpio_pin})")

    """
    # Uncomment to actually transmit
    success = send_barcode_sequence(sequence, pin=gpio_pin)
    print(f"Transmission result: {success}")
    """

    # Method 2: Detailed control
    print("\n2. Detailed Control:")

    # Prepare multiple sequences
    sequences = barcoder.get_multiple_sequences(count=3, interval_s=2.0)
    print(f"Prepared {len(sequences)} sequences")

    print("To send with detailed control:")
    print("with PigpioConnection(pin=18) as gpio:")
    print("    for i, seq in enumerate(sequences):")
    print("        print(f'Sending sequence {i+1}...')")
    print("        success = gpio.send_sequence(seq)")
    print("        time.sleep(2.0)  # Interval between barcodes")

    """
    # Uncomment to actually transmit
    try:
        with PigpioConnection(pin=gpio_pin) as gpio:
            for i, seq in enumerate(sequences):
                print(f"Sending sequence {i+1}...")
                success = gpio.send_sequence(seq)
                print(f"  Result: {success}")
                if i < len(sequences) - 1:
                    time.sleep(2.0)  # Wait between sequences
    except Exception as e:
        print(f"GPIO transmission failed: {e}")
    """

    # Method 3: Preparation only (for integration)
    print("\n3. Preparation Only (for integration):")
    sender = PigpioBarcodeSender(pin=gpio_pin)
    test_sequence = barcoder.get_sequence(42)

    try:
        pulses = sender.prepare_pulses(test_sequence)
        print(f"Prepared {len(pulses)} pigpio pulses")
        print("(Pulses ready for integration with existing pigpio code)")
    except Exception as e:
        print(f"Pulse preparation failed: {e}")

    # Timing verification
    print("\n4. Timing Verification:")
    test_barcode = 12345
    test_seq = barcoder.get_sequence(test_barcode)

    total_time = sum(duration for _, duration in test_seq)
    print(f"Barcode {test_barcode}:")
    print(f"  Calculated duration: {total_time:.1f}ms")
    print(f"  Config duration: {config.total_duration_ms:.1f}ms")
    print(f"  Match: {abs(total_time - config.total_duration_ms) < 0.1}")

    # Hardware setup reminder
    print("\nHardware Setup:")
    print("1. Ensure pigpio daemon is running: sudo systemctl start pigpio")
    print(f"2. Connect TTL output to GPIO pin {gpio_pin}")
    print("3. Connect ground reference")
    print("4. Verify with oscilloscope or logic analyzer")
    print("5. Uncomment transmission code above to execute")

    print("\nPigpio GPIO example completed!")


if __name__ == "__main__":
    main()
