"""Smoke tests: import and core encode/decode roundtrip without hardware."""

import pytest

from ttl_barcoder import BarcodeConfig, BarcodeTTL, TTLType, get_preset
from ttl_barcoder.core.encoder import TimingEncoder


def _simulate_edges(
    timing_sequence: list[tuple[bool, float]],
) -> tuple[list[float], list[bool]]:
    """Convert a timing sequence to perfect simulated edge timestamps."""
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


def test_top_level_imports():
    assert BarcodeTTL is not None
    assert BarcodeConfig is not None


def test_default_config():
    config = BarcodeConfig.default()
    assert config.barcode_bits == 37
    assert config.bit_duration_ms == 35.0
    assert config.total_duration_ms == pytest.approx(1355.0)


def test_preset_lookup():
    for name in ["default", "high_speed", "conservative", "high_precision", "random"]:
        cfg = get_preset(name)
        assert isinstance(cfg, BarcodeConfig)


def test_preset_unknown_raises():
    with pytest.raises(ValueError, match="Unknown preset"):
        get_preset("nonexistent")


def test_sequence_length():
    b = BarcodeTTL()
    seq = b.get_sequence(0)
    assert len(seq) == 6 + b.config.barcode_bits


def test_sequence_starts_high():
    b = BarcodeTTL()
    seq = b.get_sequence(0)
    level, _ = seq[0]
    assert level is True


def test_encoder_total_duration():
    enc = TimingEncoder(bit_duration_ms=35.0, init_duration_ms=10.0)
    assert enc.get_total_duration(37) == pytest.approx(37 * 35.0 + 6 * 10.0)


@pytest.mark.parametrize("value", [0, 1, 12345, 99999, 2**20 - 1])
def test_encode_decode_roundtrip(value):
    b = BarcodeTTL()
    seq = b.get_sequence(value)
    edge_times, edge_levels = _simulate_edges(seq)
    result = b.decode_edges(edge_times, edge_levels)
    assert result is not None, f"decode returned None for value={value}"
    _, decoded_value = result
    assert decoded_value == value


def test_decode_too_few_edges_returns_none():
    b = BarcodeTTL()
    assert b.decode_edges([0.0, 0.01, 0.02], [True, False, True]) is None


def test_random_config_roundtrip():
    config = BarcodeConfig(ttl_type=TTLType.random, barcode_bits=32)
    b = BarcodeTTL(config)
    seq = b.get_sequence(42)
    edge_times, edge_levels = _simulate_edges(seq)
    result = b.decode_edges(edge_times, edge_levels)
    assert result is not None
    assert result[1] == 42


def test_prepare_returns_consistent_value():
    b = BarcodeTTL()
    barcode_value, wall_time, seq = b.prepare()
    assert isinstance(barcode_value, int)
    assert wall_time > 0
    assert len(seq) == 6 + b.config.barcode_bits
