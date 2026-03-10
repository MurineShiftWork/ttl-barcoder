"""
Bpod Hardware Implementation

StateMachine integration for Bpod barcode generation with clean separation
between state preparation and execution.
"""

from .sender import BpodBarcodeSender, add_barcode_sma_states

__all__ = ["BpodBarcodeSender", "add_barcode_sma_states"]
