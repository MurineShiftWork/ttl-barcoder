"""Tests for BarcodeDecoder: roundtrip and edge-case handling."""

from __future__ import annotations

import pytest

from ttl_barcoder.core.config import TimestampPrecision
from ttl_barcoder.core.decoder import BarcodeDecoder
from ttl_barcoder.core.encoder import TimingEncoder
from ttl_barcoder.core.generator import TimestampGenerator


def _simulate_edges(
    timing_sequence: list[tuple[bool, float]],
) -> tuple[list[float], list[bool]]:
    """Convert (level, duration_ms) sequence to perfect edge timestamps."""
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


def _encode_value(value: int, bits: int = 37) -> tuple[list[float], list[bool]]:
    gen = TimestampGenerator(
        barcode_bits=bits, precision=TimestampPrecision.milliseconds
    )
    enc = TimingEncoder()
    seq = enc.encode_level_durations(gen.encode_bits(value))
    return _simulate_edges(seq)


class TestDecodeRoundtrip:
    @pytest.mark.parametrize("value", [0, 1, 99999, 2**20 - 1, 2**36])
    def test_known_values_roundtrip(self, value: int) -> None:
        dec = BarcodeDecoder()
        edge_times, edge_levels = _encode_value(value)
        result = dec.decode_edges(edge_times, edge_levels)
        assert result is not None
        _, decoded = result
        assert decoded == value % (2**37)

    def test_returns_start_time(self) -> None:
        dec = BarcodeDecoder()
        edge_times, edge_levels = _encode_value(42)
        result = dec.decode_edges(edge_times, edge_levels)
        assert result is not None
        start_time, _ = result
        assert start_time == pytest.approx(edge_times[0])


class TestDecodeEdgeCases:
    def test_too_few_edges_returns_none(self) -> None:
        dec = BarcodeDecoder()
        assert (
            dec.decode_edges(
                [0.0, 0.01, 0.02, 0.03, 0.04], [True, False, True, False, True]
            )
            is None
        )

    def test_empty_input_returns_none(self) -> None:
        dec = BarcodeDecoder()
        assert dec.decode_edges([], []) is None

    def test_bad_init_timing_returns_none(self) -> None:
        dec = BarcodeDecoder(init_duration_ms=10.0, tolerance=0.25)
        # Gaps of 1ms (far below init_duration_ms tolerance window)
        edge_times = [i * 0.001 for i in range(10)]
        edge_levels = [bool(i % 2) for i in range(10)]
        assert dec.decode_edges(edge_times, edge_levels) is None


class TestDecodeWithJitter:
    def test_small_jitter_still_decodes(self) -> None:
        import random

        random.seed(42)
        dec = BarcodeDecoder(tolerance=0.25)
        edge_times, edge_levels = _encode_value(12345)
        jitter = [t + random.uniform(-0.002, 0.002) for t in edge_times]
        result = dec.decode_edges(jitter, edge_levels)
        assert result is not None
        assert result[1] == 12345
