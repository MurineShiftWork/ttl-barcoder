"""Tests for Bpod barcode injection: no pybpod installation required."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ttl_barcoder import BarcodeTTL
from ttl_barcoder.hardware.bpod import (
    BARCODE_FIRST_STATE_NAME,
    BpodBarcodeSender,
    inject_barcode_states,
)


def _make_sequence(n_bits: int = 8) -> list[tuple[bool, float]]:
    b = BarcodeTTL()
    return b.get_sequence(0)[: 6 + n_bits]


class TestInjectBarcodeStates:
    def test_add_state_called_for_each_segment(self) -> None:
        sma = MagicMock()
        seq = _make_sequence()
        inject_barcode_states(sma, seq, bnc_channel="BNC1_L")
        assert sma.add_state.call_count == len(seq)

    def test_first_state_uses_default_name(self) -> None:
        sma = MagicMock()
        seq = _make_sequence()
        inject_barcode_states(sma, seq, bnc_channel="BNC1_L")
        first_call = sma.add_state.call_args_list[0]
        assert first_call.kwargs["state_name"] == BARCODE_FIRST_STATE_NAME

    def test_custom_first_state_name(self) -> None:
        sma = MagicMock()
        seq = _make_sequence()
        inject_barcode_states(
            sma, seq, bnc_channel="BNC1_L", first_state_name="my_start"
        )
        first_call = sma.add_state.call_args_list[0]
        assert first_call.kwargs["state_name"] == "my_start"

    def test_last_state_transitions_to_last_state_name(self) -> None:
        sma = MagicMock()
        seq = _make_sequence()
        inject_barcode_states(sma, seq, bnc_channel="BNC1_L", last_state_name="done")
        last_call = sma.add_state.call_args_list[-1]
        assert last_call.kwargs["state_change_conditions"] == {"Tup": "done"}

    def test_output_actions_format(self) -> None:
        sma = MagicMock()
        seq = _make_sequence()
        inject_barcode_states(sma, seq, bnc_channel="BNC1_L")
        for c in sma.add_state.call_args_list:
            actions = c.kwargs["output_actions"]
            assert isinstance(actions, list)
            assert len(actions) == 1
            channel, value = actions[0]
            assert channel == "BNC1_L"
            assert value in (0, 1)

    def test_high_level_maps_to_one(self) -> None:
        sma = MagicMock()
        seq = [(True, 10.0)]
        inject_barcode_states(sma, seq, bnc_channel="BNC1_L")
        actions = sma.add_state.call_args_list[0].kwargs["output_actions"]
        assert actions[0][1] == 1

    def test_low_level_maps_to_zero(self) -> None:
        sma = MagicMock()
        seq = [(False, 10.0)]
        inject_barcode_states(sma, seq, bnc_channel="BNC1_L")
        actions = sma.add_state.call_args_list[0].kwargs["output_actions"]
        assert actions[0][1] == 0

    def test_state_timers_match_sequence(self) -> None:
        sma = MagicMock()
        seq = [(True, 10.0), (False, 35.0), (True, 10.0)]
        inject_barcode_states(sma, seq, bnc_channel="BNC1_L")
        for i, (_, dur_ms) in enumerate(seq):
            timer = sma.add_state.call_args_list[i].kwargs["state_timer"]
            assert timer == pytest.approx(dur_ms / 1000.0)

    def test_returns_sma(self) -> None:
        sma = MagicMock()
        result = inject_barcode_states(sma, _make_sequence(), bnc_channel="BNC1_L")
        assert result is sma


class TestBpodBarcodeSender:
    def test_inject_states_delegates(self) -> None:
        sender = BpodBarcodeSender()
        sma = MagicMock()
        seq = _make_sequence()
        result = sender.inject_states(sma, seq, bnc_channel="BNC1_L")
        assert sma.add_state.call_count == len(seq)
        assert result is sma
