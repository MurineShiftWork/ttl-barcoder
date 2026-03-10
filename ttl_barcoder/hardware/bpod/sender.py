from typing import Any, Dict, List, Tuple

try:
    from pybpod import StateMachine

    BPOD_AVAILABLE = True
except ImportError:
    StateMachine = None
    BPOD_AVAILABLE = False


class BpodBarcodeSender:
    """
    Prepares barcode states for Bpod StateMachine.

    Separated from actual device communication for clean testing
    and integration with existing Bpod workflows.
    """

    def __init__(self):
        """Initialize Bpod barcode sender."""
        if not BPOD_AVAILABLE:
            raise ImportError("Bpod not available. Install with: pip install pybpod")

    def prepare_states(
        self,
        timing_sequence: List[Tuple[bool, float]],
        first_state_name: str,
        last_state_name: str,
        output_channel: str,
    ) -> List[Dict[str, Any]]:
        """
        Prepare barcode states for StateMachine injection.

        Args:
            timing_sequence: List of (level, duration_ms) tuples
            first_state_name: Entry state name
            last_state_name: Exit state name
            output_channel: Output channel ('BNC1', 'BNC2', etc.)

        Returns:
            List of state dictionaries ready for StateMachine.add_state()
        """
        states = []

        for i, (level, duration_ms) in enumerate(timing_sequence):
            # State name
            if i == 0:
                state_name = first_state_name
            else:
                state_name = f"{first_state_name}_seg_{i}"

            # Next state
            if i == len(timing_sequence) - 1:
                next_state = last_state_name
            else:
                next_state = f"{first_state_name}_seg_{i+1}"

            # Output actions
            output_actions = {}
            if level:  # HIGH
                output_actions[output_channel] = 255  # Full output
            # LOW is default (no output action needed)

            # Create state definition
            state_def = {
                "state_name": state_name,
                "state_timer": duration_ms / 1000.0,  # Convert to seconds
                "state_change_conditions": {"Tup": next_state},
                "output_actions": output_actions,
            }

            states.append(state_def)

        return states

    def inject_states(
        self,
        sma: StateMachine,
        timing_sequence: List[Tuple[bool, float]],
        first_state_name: str,
        last_state_name: str,
        output_channel: str,
    ) -> StateMachine:
        """
        Directly inject barcode states into StateMachine.

        Args:
            sma: StateMachine object to modify
            timing_sequence: List of (level, duration_ms) tuples
            first_state_name: Entry state name
            last_state_name: Exit state name
            output_channel: Output channel

        Returns:
            Modified StateMachine object
        """
        states = self.prepare_states(
            timing_sequence, first_state_name, last_state_name, output_channel
        )

        # Add states to StateMachine
        for state_def in states:
            sma.add_state(**state_def)

        return sma


def add_barcode_sma_states(
    sma: StateMachine,
    timing_sequence: List[Tuple[bool, float]],
    first_state_name: str,
    last_state_name: str,
    output_channel: str,
) -> StateMachine:
    """
    Convenience function to add barcode states to StateMachine.

    Args:
        sma: StateMachine object
        timing_sequence: List of (level, duration_ms) tuples
        first_state_name: Entry state name
        last_state_name: Exit state name
        output_channel: Output channel

    Returns:
        Modified StateMachine

    Example:
        >>> from ttl_barcoder.core import BarcodeTTL
        >>> from ttl_barcoder.hardware.bpod import add_barcode_sma_states
        >>> barcoder = BarcodeTTL()
        >>> sequence = barcoder.get_sequence()
        >>> add_barcode_sma_states(sma, sequence, "start", "end", "BNC1")
    """
    sender = BpodBarcodeSender()
    return sender.inject_states(
        sma, timing_sequence, first_state_name, last_state_name, output_channel
    )
