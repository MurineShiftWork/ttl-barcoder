from typing import Any

try:
    from pybpod import StateMachine

    BPOD_AVAILABLE = True
except ImportError:
    StateMachine = None
    BPOD_AVAILABLE = False

BARCODE_FIRST_STATE_NAME = "barcode_start"


def inject_barcode_states(
    sma,
    timing_sequence: list[tuple[bool, float]],
    bnc_channel: Any,
    first_state_name: str = BARCODE_FIRST_STATE_NAME,
    last_state_name: str = "exit",
):
    """Inject barcode timing states into a pybpodapi StateMachine in-place."""
    n = len(timing_sequence)
    for i, (level, duration_ms) in enumerate(timing_sequence):
        state_name = first_state_name if i == 0 else f"{first_state_name}_seg_{i}"
        next_state = (
            last_state_name if i == n - 1 else f"{first_state_name}_seg_{i + 1}"
        )
        sma.add_state(
            state_name=state_name,
            state_timer=duration_ms / 1000.0,
            state_change_conditions={"Tup": next_state},
            output_actions=[(bnc_channel, 1 if level else 0)],
        )
    return sma


class BpodBarcodeSender:
    """Stateful wrapper around inject_barcode_states for class-based workflows."""

    def inject_states(
        self,
        sma,
        timing_sequence: list[tuple[bool, float]],
        bnc_channel: Any,
        first_state_name: str = BARCODE_FIRST_STATE_NAME,
        last_state_name: str = "exit",
    ):
        """Inject barcode states into sma; delegates to inject_barcode_states."""
        return inject_barcode_states(
            sma, timing_sequence, bnc_channel, first_state_name, last_state_name
        )
