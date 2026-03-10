"""
Barcode Decoder - Decode timing sequences back to barcode values
"""

import numpy as np
from typing import List, Tuple, Optional


class BarcodeDecoder:
    """Decode edge timestamps back to barcode values."""
    
    def __init__(self, barcode_bits: int = 37,
                 bit_duration_ms: float = 35.0,
                 init_duration_ms: float = 10.0,
                 tolerance: float = 0.25):
        """
        Initialize decoder with timing parameters.
        
        Args:
            barcode_bits: Expected number of bits
            bit_duration_ms: Expected bit duration
            init_duration_ms: Expected init duration  
            tolerance: Timing tolerance (0.25 = 25%)
        """
        self.barcode_bits = barcode_bits
        self.bit_duration_ms = bit_duration_ms
        self.init_duration_ms = init_duration_ms
        self.tolerance = tolerance
        
        # Timing windows
        self.init_wrapper_ms = 3 * init_duration_ms
        self.min_init = init_duration_ms * (1 - tolerance)
        self.max_init = init_duration_ms * (1 + tolerance)
    
    def decode_edges(self, edge_timestamps: List[float],
                    edge_levels: List[bool]) -> Optional[Tuple[float, int]]:
        """
        Decode barcode from edge timestamps.
        
        Args:
            edge_timestamps: Edge times in seconds
            edge_levels: Edge levels (True=rising, False=falling)
            
        Returns:
            (timestamp, barcode_value) or None if decode fails
        """
        if len(edge_timestamps) < 6:
            return None
        
        # Convert to relative milliseconds
        start_time = edge_timestamps[0]
        rel_times_ms = [(t - start_time) * 1000 for t in edge_timestamps]
        
        # Validate initialization pattern
        if not self._validate_init_pattern(rel_times_ms):
            return None
        
        # Extract data region
        data_times = rel_times_ms[2:-2]  # Skip init wrappers
        data_levels = edge_levels[2:-2]
        
        if not data_times:
            return None
        
        # Decode bits
        bits = self._decode_bits(data_times, data_levels)
        
        # Convert to integer
        barcode_value = sum(bits[i] * (2**i) for i in range(len(bits)))
        
        return (start_time, barcode_value)
    
    def _validate_init_pattern(self, rel_times_ms: List[float]) -> bool:
        """Check for valid initialization pattern."""
        if len(rel_times_ms) < 4:
            return False
        
        time_diffs = np.diff(rel_times_ms)
        
        # Look for initialization pulses in expected range
        init_candidates = sum(1 for diff in time_diffs[:3] 
                             if self.min_init <= diff <= self.max_init)
        
        return init_candidates >= 2
    
    def _decode_bits(self, data_times: List[float], 
                    data_levels: List[bool]) -> List[int]:
        """Decode bits by sampling at bit boundaries."""
        bits = []
        current_level = False  # Start LOW after init
        edge_idx = 0
        
        for bit in range(self.barcode_bits):
            # Sample time for this bit
            bit_sample_time = (self.init_wrapper_ms + 
                              bit * self.bit_duration_ms + 
                              self.bit_duration_ms / 2)
            
            # Update level based on edges before this sample time
            while (edge_idx < len(data_times) and 
                   data_times[edge_idx] <= bit_sample_time):
                current_level = data_levels[edge_idx]
                edge_idx += 1
            
            bits.append(1 if current_level else 0)
        
        return bits
