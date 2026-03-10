"""
Bpod Hardware Implementation

StateMachine integration for Bpod barcode generation with clean separation
between state preparation and execution.
"""

from .sender import BpodBarcodeSender, BpodConnection

__all__ = ["BpodBarcodeSender", "BpodConnection"]
