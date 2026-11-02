"""Qingping LoRaWAN devices."""

from datetime import UTC, datetime
from typing import override

from lorawan_connection import (
    Device,
    DeviceCollection,
    DeviceDescriptor,
    DeviceEvent,
    EventType,
)

__all__ = ["CO2Monitor", "QingpingDevice", "QingpingDevices"]


def _valid_crc(data: bytes) -> bool:
    crc = 0xFFFF
    for byte in data[:-2]:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc == int.from_bytes(data[-2:], "little")


class CO2Monitor(Device):
    """Qingping CO2, temperature, and humidity monitor sold by RAKwireless."""

    identifiers = {"tts": ("rakwireless", "qingping-co2-t-h")}
    model_name = "CO2 & Temp & RH Monitor"

    def __init__(self, descriptor: DeviceDescriptor) -> None:
        """Initialize readings."""
        super().__init__(descriptor)
        self.temperature: float | None = None
        self.humidity: float | None = None
        self.carbon_dioxide: int | None = None
        self.battery_percentage: int | None = None
        self.observed_at: datetime | None = None

    @override
    def handle_event(self, event: DeviceEvent) -> None:
        """Read the newest sample from a real-time or historical report."""
        if event.type != EventType.UPLINK:
            return
        data = event.data
        if len(data) < 16 or data[0:2] != b"\x01\x41" or not _valid_crc(data):
            return
        # Published examples use total length for real-time and data length for history.
        if data[2] not in (len(data), len(data) - 5):
            return
        timestamp = int.from_bytes(data[4:8], "big")
        if data[3] == 1:
            if len(data) != 21:
                return
            sample = data[8:14]
        elif data[3] == 0:
            count, remainder = divmod(len(data) - 12, 6)
            if remainder or not 1 <= count <= 5:
                return
            timestamp += (count - 1) * int.from_bytes(data[8:10], "big")
            sample = data[-8:-2]
        else:
            return
        observed_at = datetime.fromtimestamp(timestamp, UTC)
        if self.observed_at is not None and observed_at < self.observed_at:
            return
        temperature = ((sample[0] << 4 | sample[1] >> 4) - 500) / 10
        humidity = ((sample[1] & 15) << 8 | sample[2]) / 10
        if not -20 <= temperature <= 50 or not 0 <= humidity <= 100 or sample[5] > 100:
            return
        self.temperature = temperature
        self.humidity = humidity
        self.carbon_dioxide = int.from_bytes(sample[3:5], "big")
        self.battery_percentage = sample[5]
        self.observed_at = observed_at
        self.notify()


type QingpingDevice = CO2Monitor


class QingpingDevices(DeviceCollection[CO2Monitor]):
    """Collect Qingping LoRaWAN monitors."""

    DEVICES = (CO2Monitor,)
