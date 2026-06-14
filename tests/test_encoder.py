"""Tests for TimingEncoder: sequence structure and timing."""

from __future__ import annotations

import pytest

from ttl_barcoder.core.encoder import TimingEncoder


def _make_enc(bit_ms: float = 35.0, init_ms: float = 10.0) -> TimingEncoder:
    return TimingEncoder(bit_duration_ms=bit_ms, init_duration_ms=init_ms)


class TestSequenceStructure:
    def test_sequence_length(self) -> None:
        enc = _make_enc()
        bits = [True] * 37
        assert len(enc.encode_timing_sequence(bits)) == 6 + 37

    def test_starts_high(self) -> None:
        enc = _make_enc()
        seq = enc.encode_timing_sequence([False] * 8)
        assert seq[0].level is True

    def test_init_pattern_high_low_high(self) -> None:
        enc = _make_enc()
        seq = enc.encode_timing_sequence([False] * 8)
        assert seq[0].level is True
        assert seq[1].level is False
        assert seq[2].level is True

    def test_end_pattern_low_high_low(self) -> None:
        enc = _make_enc()
        seq = enc.encode_timing_sequence([False] * 8)
        assert seq[-3].level is False
        assert seq[-2].level is True
        assert seq[-1].level is False

    def test_init_segment_durations(self) -> None:
        enc = _make_enc(init_ms=10.0)
        seq = enc.encode_timing_sequence([False] * 8)
        for i in (0, 1, 2, -3, -2, -1):
            assert seq[i].duration_ms == pytest.approx(10.0)

    def test_data_segment_durations(self) -> None:
        enc = _make_enc(bit_ms=35.0)
        seq = enc.encode_timing_sequence([True, False, True])
        for seg in seq[3:-3]:
            assert seg.duration_ms == pytest.approx(35.0)

    def test_data_bits_match_input(self) -> None:
        enc = _make_enc()
        bits = [True, False, True, True, False]
        seq = enc.encode_timing_sequence(bits)
        data_segs = seq[3:-3]
        assert [s.level for s in data_segs] == bits

    def test_encode_level_durations_format(self) -> None:
        enc = _make_enc()
        result = enc.encode_level_durations([True, False])
        assert all(
            isinstance(level, bool) and isinstance(dur, float) for level, dur in result
        )

    def test_empty_bits(self) -> None:
        enc = _make_enc()
        seq = enc.encode_timing_sequence([])
        assert len(seq) == 6


class TestTotalDuration:
    def test_formula(self) -> None:
        enc = _make_enc(bit_ms=35.0, init_ms=10.0)
        assert enc.get_total_duration(37) == pytest.approx(6 * 10.0 + 37 * 35.0)

    def test_zero_bits(self) -> None:
        enc = _make_enc(bit_ms=35.0, init_ms=10.0)
        assert enc.get_total_duration(0) == pytest.approx(6 * 10.0)

    def test_custom_durations(self) -> None:
        enc = _make_enc(bit_ms=25.0, init_ms=8.0)
        assert enc.get_total_duration(32) == pytest.approx(6 * 8.0 + 32 * 25.0)
