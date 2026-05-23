"""
Bpod Hardware Implementation

StateMachine integration for Bpod barcode generation with clean separation
between state preparation and execution.
"""

from .sender import BARCODE_FIRST_STATE_NAME, BpodBarcodeSender, inject_barcode_states

__all__ = ["BARCODE_FIRST_STATE_NAME", "BpodBarcodeSender", "inject_barcode_states"]
