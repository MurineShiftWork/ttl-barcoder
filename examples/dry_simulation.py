#!/usr/bin/env python3
"""
Example: Dry simulation - No hardware required

Shows core functionality and configuration options without any hardware dependencies.
"""

from ttl_barcoder.core import BarcodeTTL, BarcodeConfig, get_preset


def main():
    print("TTL Barcoder - Dry Simulation Example")
    print("=" * 45)
    
    # 1. Basic configuration
    print("\n1. Basic Configuration:")
    config = BarcodeConfig.default()
    print(f"Default config: {config}")
    print(f"Config info: {config.info()}")
    
    # 2. Create BarcodeTTL instance
    barcoder = BarcodeTTL(config)
    print(f"\nBarcoder: {barcoder}")
    
    # 3. One-liner sequence generation
    print("\n2. One-liner Sequence Generation:")
    sequence = barcoder.get_sequence()  # Current timestamp
    print(f"Generated sequence: {len(sequence)} segments")
    
    # Show first few segments
    print("First 5 segments:")
    for i, (level, duration) in enumerate(sequence[:5]):
        level_str = "HIGH" if level else "LOW"
        print(f"  {i}: {level_str} for {duration:.1f}ms")
    
    # 4. Specific barcode
    print("\n3. Specific Barcode:")
    specific_sequence = barcoder.get_sequence(12345)
    print(f"Barcode 12345 sequence: {len(specific_sequence)} segments")
    
    # 5. Multiple sequences
    print("\n4. Multiple Sequences:")
    multi_sequences = barcoder.get_multiple_sequences(count=3, interval_s=1.0)
    print(f"Generated {len(multi_sequences)} sequences")
    
    # 6. Test different configurations
    print("\n5. Configuration Presets:")
    for preset_name in ["high_speed", "conservative", "high_precision"]:
        preset_config = get_preset(preset_name)
        preset_barcoder = BarcodeTTL(preset_config)
        preset_sequence = preset_barcoder.get_sequence()
        
        print(f"{preset_name:15s}: {len(preset_sequence)} segments, "
              f"{preset_config.total_duration_ms:.0f}ms total")
    
    # 7. Simulate decode test
    print("\n6. Decode Simulation:")
    # Simulate perfect edge detection
    test_sequence = barcoder.get_sequence(99999)
    simulated_edges = simulate_perfect_edges(test_sequence)
    
    decoded = barcoder.decode_edges(*simulated_edges)
    if decoded:
        timestamp, barcode_value = decoded
        print(f"Simulated decode successful: barcode = {barcode_value}")
    else:
        print("Simulated decode failed")
    
    print("\nDry simulation completed!")


def simulate_perfect_edges(timing_sequence):
    """Convert timing sequence to perfect edge timestamps for testing."""
    edge_times = []
    edge_levels = []
    
    current_time = 0.0
    current_level = False  # Start LOW
    
    for target_level, duration_ms in timing_sequence:
        if target_level != current_level:
            # Level change - record edge
            edge_times.append(current_time)
            edge_levels.append(target_level)
            current_level = target_level
        
        current_time += duration_ms / 1000.0  # Convert to seconds
    
    return edge_times, edge_levels


if __name__ == "__main__":
    main()
