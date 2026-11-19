"""Stream decoding: barcodes found by their configured lengths, not by silences."""

from __future__ import annotations

import random

import pytest

from ttl_barcoder import BarcodeConfig, BarcodeTTL
from ttl_barcoder.core.decoder import drop_short_pulses


def _stream(ttl: BarcodeTTL, values, starts):
    """Edges of several barcodes on one idle-low line, starting at ``starts``."""
    times, levels = [], []
    level = False
    for value, t in zip(values, starts, strict=True):
        for target, ms in ttl.get_sequence(value):
            if target != level:
                times.append(t)
                levels.append(target)
                level = target
            t += ms / 1000.0
    return times, levels


@pytest.mark.parametrize(("bit", "init"), [(35.0, 10.0), (100.0, 100.0)])
def test_every_value_decodes_including_long_runs(bit, init):
    ttl = BarcodeTTL(BarcodeConfig(bit_duration_ms=bit, init_duration_ms=init))
    rng = random.Random(0)
    values = [0, 2**37 - 1, 1, 2**36, 0b1111111111 << 13]
    values += [rng.getrandbits(37) for _ in range(100)]
    gap = ttl.config.total_duration_ms / 1000.0 + 0.2
    times, levels = _stream(ttl, values, [i * gap for i in range(len(values))])
    found = ttl.find_barcodes(times, levels)
    assert [b.value for b in found] == values
    assert [round(b.start_s, 6) for b in found] == [
        round(i * gap, 6) for i in range(len(values))
    ]
    assert all(
        b.end_s - b.start_s == pytest.approx(ttl.config.total_duration_ms / 1000)
        for b in found
    )


def test_pulses_outside_barcodes_are_not_decoded():
    ttl = BarcodeTTL(BarcodeConfig(bit_duration_ms=100.0, init_duration_ms=100.0))
    times, levels = _stream(ttl, [12345], [10.0])
    # trial pulses before and after (0.5 s and 50 ms wide)
    times = [1.0, 1.5, 2.0, 2.05, *times, 30.0, 30.5]
    levels = [True, False, True, False, *levels, True, False]
    assert ttl.decode_stream(times, levels) == [(10.0, 12345)]


def test_zero_length_pulses_are_dropped_in_either_order():
    ttl = BarcodeTTL()
    times, levels = _stream(ttl, [987654321], [5.0])
    noisy_t, noisy_l = [], []
    for t, level in zip(times, levels, strict=True):
        noisy_t += [t]
        noisy_l += [level]
        mid = t + 0.002
        # an off/on (or on/off) pair at one timestamp, as from a shared port
        noisy_t += [mid, mid]
        noisy_l += [not level, level] if level else [level, not level]
    assert ttl.decode_stream(noisy_t, noisy_l) == [(5.0, 987654321)]


def test_drop_short_pulses_keeps_the_prior_level():
    t, lv = drop_short_pulses(
        [0.0, 1.0, 1.0005, 2.0], [True, False, True, False], min_width_s=0.001
    )
    assert (t, lv) == ([0.0, 2.0], [True, False])


def test_frame_rate_line_starts_at_the_first_high_frame():
    cfg = BarcodeConfig(bit_duration_ms=100.0, init_duration_ms=100.0)
    ttl = BarcodeTTL(cfg)
    times, levels = _stream(ttl, [2**35 + 77], [3.0])
    fps = 60.0
    frames = [3.0 + k / fps - 0.5 for k in range(int(6 * fps))]

    def level(at):
        cur = False
        for t, lv in zip(times, levels, strict=True):
            if t <= at:
                cur = lv
        return cur

    sampled = [level(f) for f in frames]
    edge_t = [f for i, f in enumerate(frames) if i and sampled[i] != sampled[i - 1]]
    edge_l = [s for i, s in enumerate(sampled) if i and s != sampled[i - 1]]
    (found,) = ttl.find_barcodes(edge_t, edge_l, sample_interval_s=1 / fps)
    assert found.value == 2**35 + 77
    # half an interval before the first high frame: within half a frame of the edge
    assert abs(found.start_s - 3.0) <= 0.5 / fps


def test_short_init_skips_framing_at_frame_rate():
    ttl = BarcodeTTL()  # 10 ms init pulses: not visible at 60 fps
    times, levels = _stream(ttl, [4242], [1.0])
    # the camera sees the three init segments as one high run from the start
    data = [(t, lv) for t, lv in zip(times, levels, strict=True) if t >= 1.03]
    edge_t = [1.0, *[t for t, _ in data]]
    edge_l = [True, *[lv for _, lv in data]]
    assert ttl.decode_stream(edge_t, edge_l) == []  # framing check fails
    ((start, value),) = ttl.decode_stream(edge_t, edge_l, sample_interval_s=1 / 60)
    assert value == 4242
    assert start == pytest.approx(1.0 - 0.5 / 60)
