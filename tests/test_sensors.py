"""Tests for Qingping entities."""

from dataclasses import replace
from datetime import UTC, datetime

from homeassistant.components.lorawan.websocket_api import _snapshot
from homeassistant.const import EntityCategory
from homeassistant.helpers import entity_registry as er
from lorawan_connection import StatusEvent, UplinkEvent
import pytest


@pytest.mark.usefixtures("connection_entry")
async def test_sensors(hass, config_entry, mock_connection, descriptor) -> None:
    """Expose measurements, battery, and the LoRaWAN device link."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    mock_connection.emit(
        UplinkEvent(
            descriptor=descriptor,
            received_at=datetime.now(UTC),
            f_port=1,
            data=bytes.fromhex("014115015c7788b62fc29a01aa4e312e302e3043fe"),
        )
    )
    await hass.async_block_till_done()
    for key, value in {
        "temperature": "26.4",
        "humidity": "66.6",
        "carbon_dioxide": "426",
        "battery": "78",
    }.items():
        assert hass.states.get(f"sensor.garden_{key}").state == value
    battery = er.async_get(hass).async_get("sensor.garden_battery")
    assert battery.entity_category is EntityCategory.DIAGNOSTIC
    assert battery.disabled_by is None
    metadata = next(
        row
        for row in _snapshot(hass)["devices"]
        if row["dev_eui"] == descriptor.dev_eui
    )
    assert metadata["device_id"] == battery.device_id
    status = StatusEvent(
        descriptor=descriptor,
        received_at=datetime.now(UTC),
        battery_level=0,
        battery_level_unavailable=False,
    )
    mock_connection.emit(status)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.garden_battery").state == "0"
    mock_connection.emit(replace(status, battery_level_unavailable=True))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.garden_battery").state == "78"
    await hass.config_entries.async_unload(config_entry.entry_id)
