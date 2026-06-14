"""Tests for BarcodeTTL: the main public interface."""

from __future__ import annotations

import pytest

from ttl_barcoder import BarcodeConfig, BarcodeTTL, TTLType


def _simulate_edges(
    timing_sequence: list[tuple[bool, float]],
) -> tuple[list[float], list[bool]]:
    edge_times: list[float] = []
    edge_levels: list[bool] = []
    t = 0.0
    current_level = False
    for target_level, duration_ms in timing_sequence:
        if target_level != current_level:
            edge_times.append(t)
            edge_levels.append(target_level)
            current_level = target_level
        t += duration_ms / 1000.0
    return edge_times, edge_levels


class TestGetSequence:
    def test_length(self) -> None:
        b = BarcodeTTL()
        assert len(b.get_sequence(0)) == 6 + b.config.barcode_bits

    def test_deterministic_for_same_value(self) -> None:
        b = BarcodeTTL()
        assert b.get_sequence(999) == b.get_sequence(999)

    def test_different_values_differ(self) -> None:
        b = BarcodeTTL()
        assert b.get_sequence(0) != b.get_sequence(1)

    def test_returns_level_duration_tuples(self) -> None:
        b = BarcodeTTL()
        for level, dur in b.get_sequence(0):
            assert isinstance(level, bool)
            assert isinstance(dur, float)


class TestDecodeEdges:
    @pytest.mark.parametrize("value", [0, 1, 42, 99999])
    def test_roundtrip(self, value: int) -> None:
        b = BarcodeTTL()
        seq = b.get_sequence(value)
        edge_times, edge_levels = _simulate_edges(seq)
        result = b.decode_edges(edge_times, edge_levels)
        assert result is not None
        assert result[1] == value

    def test_too_few_edges_returns_none(self) -> None:
        b = BarcodeTTL()
        assert b.decode_edges([0.0, 0.1, 0.2], [True, False, True]) is None


class TestPrepare:
    def test_returns_three_tuple(self) -> None:
        b = BarcodeTTL()
        result = b.prepare()
        assert len(result) == 3

    def test_barcode_value_is_int(self) -> None:
        b = BarcodeTTL()
        val, _, _ = b.prepare()
        assert isinstance(val, int)

    def test_wall_time_positive(self) -> None:
        b = BarcodeTTL()
        _, wall_time, _ = b.prepare()
        assert wall_time > 0

    def test_sequence_length(self) -> None:
        b = BarcodeTTL()
        _, _, seq = b.prepare()
        assert len(seq) == 6 + b.config.barcode_bits


class TestGetSequenceFromTimestamp:
    def test_raises_on_random_config(self) -> None:
        b = BarcodeTTL(BarcodeConfig(ttl_type=TTLType.random))
        with pytest.raises(ValueError, match="TTLType.timestamp"):
            b.get_sequence_from_timestamp(1_000_000.0)

    def test_deterministic_for_same_timestamp(self) -> None:
        b = BarcodeTTL()
        t = 1_700_000_000.0
        assert b.get_sequence_from_timestamp(t) == b.get_sequence_from_timestamp(t)


class TestRecoverTimestamp:
    def test_raises_on_random_config(self) -> None:
        b = BarcodeTTL(BarcodeConfig(ttl_type=TTLType.random))
        with pytest.raises(ValueError, match="TTLType.timestamp"):
            b.recover_timestamp(42)

    def test_recovers_nearby_timestamp(self) -> None:
        import time

        b = BarcodeTTL()
        t = time.time()
        val = b.generator.generate(t)  # type: ignore[union-attr]
        recovered = b.recover_timestamp(val, reference_time=t)
        assert abs(recovered - t) < 1.0


class TestGetMultipleSequences:
    def test_returns_n_sequences(self) -> None:
        b = BarcodeTTL()
        seqs = b.get_multiple_sequences(count=3, interval_s=5.0)
        assert len(seqs) == 3

    def test_each_sequence_correct_length(self) -> None:
        b = BarcodeTTL()
        for seq in b.get_multiple_sequences(count=3):
            assert len(seq) == 6 + b.config.barcode_bits


class TestInfo:
    def test_info_has_required_keys(self) -> None:
        b = BarcodeTTL()
        info = b.info
        assert "config" in info
        assert "generator" in info
        assert "encoder" in info
