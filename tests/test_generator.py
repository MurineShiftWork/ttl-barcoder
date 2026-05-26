"""Tests for TTLGenerator subclasses and create_generator factory."""

from __future__ import annotations

import time

from ttl_barcoder import BarcodeConfig, TTLType
from ttl_barcoder.core.config import TimestampPrecision
from ttl_barcoder.core.generator import (
    RandomGenerator,
    TimestampGenerator,
    create_generator,
)


class TestTimestampGenerator:
    def _make(
        self,
        bits: int = 37,
        precision: TimestampPrecision = TimestampPrecision.milliseconds,
    ) -> TimestampGenerator:
        return TimestampGenerator(barcode_bits=bits, precision=precision)

    def test_same_timestamp_gives_same_value(self) -> None:
        gen = self._make()
        t = time.time()
        assert gen.generate(t) == gen.generate(t)

    def test_seconds_precision_quantises_to_second(self) -> None:
        gen = TimestampGenerator(barcode_bits=37, precision=TimestampPrecision.seconds)
        t = 1_000_000.5
        val = gen.generate(t)
        assert val == 1_000_000 % (2**37)

    def test_ms_precision_quantises_to_millisecond(self) -> None:
        gen = TimestampGenerator(
            barcode_bits=37, precision=TimestampPrecision.milliseconds
        )
        t = 1_000.123
        val = gen.generate(t)
        assert val == 1_000_123 % (2**37)

    def test_result_within_bounds(self) -> None:
        gen = self._make(bits=32)
        for _ in range(20):
            v = gen.generate()
            assert 0 <= v < 2**32

    def test_max_value(self) -> None:
        gen = self._make(bits=16)
        assert gen.max_value == 2**16 - 1

    def test_generate_sequence_length(self) -> None:
        gen = self._make()
        seq = gen.generate_sequence(count=5, interval_s=1.0)
        assert len(seq) == 5

    def test_generate_sequence_deterministic(self) -> None:
        gen = self._make()
        t0 = 1_000_000.0
        s1 = gen.generate_sequence(count=3, interval_s=5.0, start_timestamp=t0)
        s2 = gen.generate_sequence(count=3, interval_s=5.0, start_timestamp=t0)
        assert s1 == s2

    def test_recover_timestamp_nearby(self) -> None:
        gen = TimestampGenerator(
            barcode_bits=37, precision=TimestampPrecision.milliseconds
        )
        t = time.time()
        val = gen.generate(t)
        recovered = gen.recover_timestamp(val, reference_time=t)
        assert abs(recovered - t) < 0.01

    def test_recover_timestamp_wraparound(self) -> None:
        gen = TimestampGenerator(barcode_bits=16, precision=TimestampPrecision.seconds)
        window = 2**16
        t_actual = window + 100
        val = gen.generate(t_actual)
        reference = t_actual + 10
        recovered = gen.recover_timestamp(val, reference_time=reference)
        assert abs(recovered - t_actual) < 1.0


class TestEncodeBits:
    def test_lsb_first_value_one(self) -> None:
        gen = TimestampGenerator(barcode_bits=8, precision=TimestampPrecision.seconds)
        bits = gen.encode_bits(1)
        assert bits[0] is True
        assert all(b is False for b in bits[1:])

    def test_lsb_first_value_two(self) -> None:
        gen = TimestampGenerator(barcode_bits=8, precision=TimestampPrecision.seconds)
        bits = gen.encode_bits(2)
        assert bits[0] is False
        assert bits[1] is True

    def test_encode_bits_length(self) -> None:
        gen = TimestampGenerator(
            barcode_bits=37, precision=TimestampPrecision.milliseconds
        )
        assert len(gen.encode_bits(0)) == 37

    def test_encode_bits_wraps_at_max(self) -> None:
        gen = TimestampGenerator(barcode_bits=8, precision=TimestampPrecision.seconds)
        bits_0 = gen.encode_bits(0)
        bits_256 = gen.encode_bits(256)
        assert bits_0 == bits_256


class TestRandomGenerator:
    def test_result_within_bounds(self) -> None:
        gen = RandomGenerator(barcode_bits=32)
        for _ in range(50):
            v = gen.generate()
            assert 0 <= v < 2**32

    def test_different_calls_vary(self) -> None:
        gen = RandomGenerator(barcode_bits=32)
        values = {gen.generate() for _ in range(20)}
        assert len(values) > 1


class TestCreateGenerator:
    def test_timestamp_type_returns_timestamp_generator(self) -> None:
        cfg = BarcodeConfig(ttl_type=TTLType.timestamp)
        gen = create_generator(cfg)
        assert isinstance(gen, TimestampGenerator)

    def test_random_type_returns_random_generator(self) -> None:
        cfg = BarcodeConfig(ttl_type=TTLType.random)
        gen = create_generator(cfg)
        assert isinstance(gen, RandomGenerator)
