#!/usr/bin/env python3
"""
Example: Bpod loopback test

Demonstrates Bpod StateMachine integration with loopback testing
on the same device (BNC1 out -> BNC1 in).
"""

from ttl_barcoder.core import BarcodeConfig, BarcodeTTL


def main():
    print("TTL Barcoder - Bpod Loopback Example")
    print("=" * 45)

    try:
        from pybpod import StateMachine

        from ttl_barcoder.hardware.bpod import BpodBarcodeSender, inject_barcode_states
    except ImportError as e:
        print(f"Bpod not available: {e}")
        print("Install with: pip install pybpod")
        return

    # Configuration for demo
    config = BarcodeConfig(
        barcode_bits=32,  # Shorter for demo
        bit_duration_ms=50.0,  # Slower for visualization
        init_duration_ms=15.0,
    )

    print(f"Using config: {config}")

    # Create barcode system
    barcoder = BarcodeTTL(config)

    # Get barcode sequence
    test_barcode = 12345
    timing_sequence = barcoder.get_sequence(test_barcode)

    print(f"\nGenerated sequence for barcode {test_barcode}:")
    print(f"  {len(timing_sequence)} segments")
    print(f"  Total duration: {config.total_duration_ms:.0f}ms")

    # Create StateMachine
    sma = StateMachine()

    # Initial state
    sma.add_state(
        state_name="start",
        state_timer=1.0,
        state_change_conditions={"Tup": "send_barcode"},
        output_actions=[],
    )

    # Method 1: Direct injection (recommended)
    print("\nMethod 1: Direct injection")
    sender = BpodBarcodeSender()
    sender.inject_states(
        sma=sma,
        timing_sequence=timing_sequence,
        bnc_channel="BNC1",
        first_state_name="send_barcode",
        last_state_name="listen_barcode",
    )

    # Listen for barcode return
    sma.add_state(
        state_name="listen_barcode",
        state_timer=config.total_duration_ms / 1000.0 + 0.5,  # Give extra time
        state_change_conditions={"BNC1High": "detected", "Tup": "timeout"},
        output_actions=[],
    )

    # Detection states
    sma.add_state(
        state_name="detected",
        state_timer=0.1,
        state_change_conditions={"Tup": "success"},
        output_actions=[("LED", 255)],  # Success indicator
    )

    sma.add_state(
        state_name="timeout",
        state_timer=0.1,
        state_change_conditions={"Tup": "exit"},
        output_actions=[],
    )

    sma.add_state(
        state_name="success",
        state_timer=2.0,
        state_change_conditions={"Tup": "exit"},
        output_actions={"LED": 255},
    )

    print(f"Created StateMachine with {len(sma.state_names)} states")
    print("State sequence:", " -> ".join(sma.state_names))

    # Method 2: Convenience function
    print("\nMethod 2: Convenience function")
    sma2 = StateMachine()
    sma2.add_state(
        state_name="start",
        state_timer=1.0,
        state_change_conditions={"Tup": "barcode"},
        output_actions=[],
    )

    inject_barcode_states(
        sma=sma2,
        timing_sequence=timing_sequence,
        bnc_channel="BNC1",
        first_state_name="barcode",
        last_state_name="end",
    )

    sma2.add_state(
        state_name="end",
        state_timer=0.1,
        state_change_conditions={"Tup": "exit"},
        output_actions=[],
    )
    print(f"Method 2 StateMachine: {len(sma2.state_names)} states")

    # Connection and execution (commented for safety)
    print("\nTo run on actual Bpod device:")
    print("1. Connect Bpod at /dev/ttyACM0")
    print("2. Wire BNC1 output to BNC1 input (loopback)")
    print("3. Uncomment execution code below")

    """
    # Uncomment to run on actual device
    class BpodConnection:
        def __init__(self, device_path):
            self.bpod = BpodBase(device_path)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.bpod.close()

        def run(self, sma):
            self.bpod.send_state_machine(sma)
            self.bpod.run_state_machine(sma)

    try:
        with BpodConnection("/dev/ttyACM0") as bpod:
            print("Connected to Bpod, running state machine...")
            bpod.run(sma)
            print("StateMachine completed successfully!")
    except Exception as e:
        print(f"Bpod execution failed: {e}")
    """

    print("\nBpod loopback example completed!")


if __name__ == "__main__":
    main()
