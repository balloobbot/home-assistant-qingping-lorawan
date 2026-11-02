"""Qingping sensors."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from homeassistant.components.lorawan import LoRaWANEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import QingpingConfigEntry
from ._vendor.qingping_lorawan import CO2Monitor
from .coordinator import QingpingCoordinator

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class QingpingSensorDescription(SensorEntityDescription):
    """Select a monitor measurement."""

    value_fn: Callable[[CO2Monitor], float | None]


DESCRIPTIONS = (
    QingpingSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.temperature,
    ),
    QingpingSensorDescription(
        key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.humidity,
    ),
    QingpingSensorDescription(
        key="carbon_dioxide",
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.carbon_dioxide,
    ),
    QingpingSensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: (
            battery
            if (battery := device.battery_level) is not None
            else device.battery_percentage
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: QingpingConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Qingping sensors."""

    @callback
    def added(coordinator: QingpingCoordinator) -> None:
        async_add_entities(
            QingpingSensor(coordinator, description) for description in DESCRIPTIONS
        )

    entry.async_on_unload(entry.runtime_data.subscribe_coordinator_added(added))


class QingpingSensor(LoRaWANEntity[CO2Monitor], SensorEntity):
    """Represent a Qingping measurement."""

    coordinator: QingpingCoordinator
    entity_description: QingpingSensorDescription

    @property
    @override
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info

    @property
    @override
    def native_value(self) -> float | None:
        return self.entity_description.value_fn(self.device)
