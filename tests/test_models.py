"""Tests for Qingping's published protocol examples."""

from dataclasses import replace
from datetime import UTC, datetime

from lorawan_connection import UplinkEvent
import pytest

from custom_components.qingping_lorawan._vendor.qingping_lorawan import CO2Monitor

REALTIME = "014115015c7788b62fc29a01aa4e312e302e3043fe"
HISTORY = "014125005c7788b60005" + "2fc29a01aa4e" * 5 + "46fe"


@pytest.mark.parametrize(("payload", "offset"), [(REALTIME, 0), (HISTORY, 20)])
def test_manual_examples(descriptor, payload, offset) -> None:
    """Decode the manufacturer's complete frames, including their CRC."""
    device = CO2Monitor(descriptor)
    device.handle_event(
        UplinkEvent(
            descriptor=descriptor,
            received_at=datetime.now(UTC),
            f_port=1,
            data=bytes.fromhex(payload),
        )
    )
    assert device.temperature == 26.4
    assert device.humidity == 66.6
    assert device.carbon_dioxide == 426
    assert device.battery_percentage == 78
    assert device.observed_at == datetime.fromtimestamp(0x5C7788B6 + offset, UTC)


def test_history_order(descriptor) -> None:
    """Receiving an old history packet later does not move observations backwards."""
    device = CO2Monitor(descriptor)
    event = UplinkEvent(
        descriptor=descriptor,
        received_at=datetime.now(UTC),
        f_port=1,
        data=bytes.fromhex(HISTORY),
    )
    device.handle_event(event)
    observed_at = device.observed_at
    device.handle_event(replace(event, data=bytes.fromhex(REALTIME)))
    assert device.observed_at == observed_at


@pytest.mark.parametrize(
    "payload",
    ["", REALTIME[:-2], REALTIME + "00", REALTIME[:-4] + "0000", "0041" + REALTIME[4:]],
)
def test_bad_frame(descriptor, payload) -> None:
    """Reject incomplete or corrupt frames without publishing readings."""
    device = CO2Monitor(descriptor)
    device.handle_event(
        UplinkEvent(
            descriptor=descriptor,
            received_at=datetime.now(UTC),
            f_port=1,
            data=bytes.fromhex(payload),
        )
    )
    assert device.temperature is None
    assert device.battery_percentage is None
