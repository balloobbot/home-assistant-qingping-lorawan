[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=balloobbot&repository=home-assistant-qingping-lorawan&category=integration)

# Qingping LoRaWAN

Use the Qingping CO₂, temperature, and humidity LoRaWAN monitor sold by RAKwireless
with Home Assistant. Requires Home Assistant 2026.11.0b0 or newer, including
2026.11 beta releases.

## Install

1. Open the HACS link above and download the integration.
2. Restart Home Assistant.
3. Configure The Things Network or The Things Stack integration.
4. Register the monitor using **RAKwireless > Qingping CO2 & Temp & RH Monitor**
   from the TTN device catalog.
5. Open **Settings > Devices & services** and configure the discovered
   **Qingping LoRaWAN** integration. You can also select it under **Add integration**.

To install manually, copy `custom_components/qingping_lorawan` into your Home
Assistant `config/custom_components` directory and restart.

## Readings

The integration creates temperature, humidity, CO₂, and battery percentage
sensors. Battery is a diagnostic entity enabled by default. Its value comes from
the LoRaWAN status report when available, otherwise from the monitor's payload.

Real-time reports and history batches are supported. The newest sample updates
the entities; older samples do not overwrite it. History batches are not imported
into Home Assistant's recorder as historical states. Readings remain unknown
until the monitor sends a supported report.

This integration matches the TTN catalog identity `rakwireless/qingping-co2-t-h`.
It has no ChirpStack catalog mapping. Qingping Bluetooth and Wi-Fi monitors use
different protocols. Additional application-level payload encryption is not
supported; normal LoRaWAN transport encryption is handled by the network server.

## Development

The device library is bundled under `custom_components/qingping_lorawan/_vendor`.
Tests use the real-time and history examples from the manufacturer's protocol
manual, including their checksums. Physical-device testing is still needed.

```sh
uv sync --group dev
uv run python script/prepare_tests.py
uv run pytest --disable-socket --allow-unix-socket
uv run ruff check .
uv run ruff format --check .
```

CI tests both the pinned Home Assistant revision and current `dev`.
When reporting a decoding issue, include the model, firmware, uplink FPort,
payload, and expected reading. Do not include API keys or device keys.

Protocol reference: [Qingping Indoor CO₂ Monitoring Solution manual](https://downloads.rakwireless.com/IoT-Marketplace/Qingping/Indoor%20CO2%20Monitoring%20Solution/Qingping%20Indoor%20CO2%20Monitoring%20Solution%20User%20Manual.pdf).
Catalog identity: [TTN Qingping entry](https://github.com/TheThingsNetwork/lorawan-devices/blob/master/vendor/rakwireless/qingping-co2-t-h.yaml).
Brand images are bundled from [Home Assistant Brands](https://github.com/home-assistant/brands/tree/master/core_integrations/qingping).
