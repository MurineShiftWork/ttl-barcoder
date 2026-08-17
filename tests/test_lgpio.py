"""lgpio backend tests: no lgpio or GPIO hardware required (the module is mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ttl_barcoder.hardware.lgpio import (
    LgpioBarcodeSender,
    LgpioConnection,
    send_barcode_sequence,
)

_MOD = "ttl_barcoder.hardware.lgpio.sender"


def _available():
    """Patch the sender module so lgpio 'is installed'; returns (ctx, fake_lgpio)."""
    fake = MagicMock()
    return patch.multiple(_MOD, lgpio=fake, LGPIO_AVAILABLE=True), fake


# --- availability guard ---
def test_raises_when_lgpio_not_installed():
    # lgpio is not installed in the test env, so both entry points must fail loudly.
    with pytest.raises(ImportError, match="lgpio"):
        LgpioBarcodeSender(pin=18)
    with pytest.raises(ImportError, match="lgpio"):
        LgpioConnection(pin=18)


# --- sequence preparation ---
def test_prepare_pulses_converts_ms_to_us_and_level():
    ctx, _ = _available()
    with ctx:
        s = LgpioBarcodeSender(pin=25)
        assert s.prepare_pulses([(True, 10.0), (False, 20.0), (True, 1.5)]) == [
            (1, 10000),
            (0, 20000),
            (1, 1500),
        ]


# --- connection lifecycle ---
def test_connect_opens_chip_and_claims_output():
    ctx, fake = _available()
    with ctx:
        fake.gpiochip_open.return_value = 7
        conn = LgpioConnection(pin=18, gpiochip=4)  # gpiochip=4 == Raspberry Pi 5
        assert conn.connect() is True
        fake.gpiochip_open.assert_called_once_with(4)
        fake.gpio_claim_output.assert_called_once_with(7, 18, 0)


def test_send_sequence_writes_each_level_then_leaves_low():
    ctx, fake = _available()
    with ctx:
        fake.gpiochip_open.return_value = 7
        conn = LgpioConnection(pin=18)
        assert conn.send_sequence([(True, 0.001), (False, 0.001)]) is True
        # one write per segment, plus a final low; all on (handle=7, pin=18)
        writes = fake.gpio_write.call_args_list
        assert [c.args for c in writes] == [(7, 18, 1), (7, 18, 0), (7, 18, 0)]


def test_context_manager_opens_and_closes():
    ctx, fake = _available()
    with ctx:
        fake.gpiochip_open.return_value = 7
        with LgpioConnection(pin=18) as conn:
            assert conn.connected is True
        fake.gpiochip_close.assert_called_once_with(7)


def test_connect_failure_returns_false_and_short_circuits_send():
    ctx, fake = _available()
    with ctx:
        fake.gpiochip_open.side_effect = OSError("no such gpiochip")
        conn = LgpioConnection(pin=18)
        assert conn.connect() is False
        assert conn.send_sequence([(True, 0.001)]) is False


def test_send_barcode_sequence_convenience_wrapper():
    ctx, fake = _available()
    with ctx:
        fake.gpiochip_open.return_value = 7
        assert send_barcode_sequence([(True, 0.001)], pin=18, gpiochip=0) is True
        fake.gpiochip_close.assert_called_once_with(7)  # wrapper cleans up
