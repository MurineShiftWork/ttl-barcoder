"""Tests for BarcodeConfig validation, properties, and presets."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ttl_barcoder import BarcodeConfig, TTLType, get_preset
from ttl_barcoder.core.config import TimestampPrecision


class TestBarcodeConfigDefaults:
    def test_default_barcode_bits(self) -> None:
        assert BarcodeConfig().barcode_bits == 37

    def test_default_bit_duration_ms(self) -> None:
        assert BarcodeConfig().bit_duration_ms == 35.0

    def test_default_init_duration_ms(self) -> None:
        assert BarcodeConfig().init_duration_ms == 10.0

    def test_default_tolerance(self) -> None:
        assert BarcodeConfig().tolerance == 0.25

    def test_default_ttl_type(self) -> None:
        assert BarcodeConfig().ttl_type == TTLType.timestamp

    def test_default_precision(self) -> None:
        assert BarcodeConfig().timestamp_precision == TimestampPrecision.milliseconds


class TestBarcodeConfigValidation:
    def test_barcode_bits_too_low(self) -> None:
        with pytest.raises(ValidationError):
            BarcodeConfig(barcode_bits=15)

    def test_barcode_bits_too_high(self) -> None:
        with pytest.raises(ValidationError):
            BarcodeConfig(barcode_bits=65)

    def test_bit_duration_zero(self) -> None:
        with pytest.raises(ValidationError):
            BarcodeConfig(bit_duration_ms=0)

    def test_bit_duration_negative(self) -> None:
        with pytest.raises(ValidationError):
            BarcodeConfig(bit_duration_ms=-1.0)

    def test_tolerance_too_low(self) -> None:
        with pytest.raises(ValidationError):
            BarcodeConfig(tolerance=0.01)

    def test_tolerance_too_high(self) -> None:
        with pytest.raises(ValidationError):
            BarcodeConfig(tolerance=0.51)

    def test_extra_field_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            BarcodeConfig.model_validate({"unknown_field": True})


class TestBarcodeConfigProperties:
    def test_total_duration_formula(self) -> None:
        cfg = BarcodeConfig(
            barcode_bits=37, bit_duration_ms=35.0, init_duration_ms=10.0
        )
        assert cfg.total_duration_ms == pytest.approx(6 * 10.0 + 37 * 35.0)

    def test_total_duration_custom(self) -> None:
        cfg = BarcodeConfig(barcode_bits=32, bit_duration_ms=25.0, init_duration_ms=8.0)
        assert cfg.total_duration_ms == pytest.approx(6 * 8.0 + 32 * 25.0)

    def test_coverage_years_timestamp(self) -> None:
        cfg = BarcodeConfig(ttl_type=TTLType.timestamp, barcode_bits=37)
        assert cfg.coverage_years is not None
        assert cfg.coverage_years > 1.0

    def test_coverage_years_seconds_precision_large(self) -> None:
        cfg = BarcodeConfig(
            ttl_type=TTLType.timestamp,
            barcode_bits=37,
            timestamp_precision=TimestampPrecision.seconds,
        )
        assert cfg.coverage_years is not None
        assert cfg.coverage_years > 1000

    def test_coverage_years_microseconds_smaller(self) -> None:
        cfg_ms = BarcodeConfig(
            ttl_type=TTLType.timestamp,
            barcode_bits=37,
            timestamp_precision=TimestampPrecision.milliseconds,
        )
        cfg_us = BarcodeConfig(
            ttl_type=TTLType.timestamp,
            barcode_bits=37,
            timestamp_precision=TimestampPrecision.microseconds,
        )
        assert cfg_us.coverage_years < cfg_ms.coverage_years  # type: ignore[operator]

    def test_coverage_years_random_is_none(self) -> None:
        cfg = BarcodeConfig(ttl_type=TTLType.random)
        assert cfg.coverage_years is None

    def test_safety_ratio_positive(self) -> None:
        assert BarcodeConfig().safety_ratio > 0

    def test_from_dict_roundtrip(self) -> None:
        cfg = BarcodeConfig(barcode_bits=32, bit_duration_ms=25.0)
        restored = BarcodeConfig.from_dict(cfg.model_dump())
        assert restored == cfg

    def test_info_has_required_keys(self) -> None:
        info = BarcodeConfig().info()
        assert "barcode_bits" in info
        assert "total_duration_ms" in info
        assert "coverage_years" in info


class TestPresets:
    @pytest.mark.parametrize(
        "name", ["default", "high_speed", "conservative", "high_precision", "random"]
    )
    def test_preset_returns_config(self, name: str) -> None:
        cfg = get_preset(name)
        assert isinstance(cfg, BarcodeConfig)

    def test_random_preset_ttl_type(self) -> None:
        assert get_preset("random").ttl_type == TTLType.random

    def test_unknown_preset_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown preset"):
            get_preset("nonexistent")
