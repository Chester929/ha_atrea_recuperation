# HA Atrea Recuperation - Home Assistant integration (HACS ready)

This integration exposes Atrea DUPLEX device registers via Modbus and maps them to Home Assistant entities.

What it provides
- climate.* : Climate entity (target temperature + simplified HVAC mapping)
- select.* : Operation mode select (writes integer to holding register 1001)
- fan.* : Percentage-based fan control (writes to holding register 1004)
- number.* : Writable number entities (e.g., target temperature -> holding 1002)
- sensor.* : Sensors for input and holding registers (temperatures, flows, counters, serial)
- button.* : Buttons for coil actions (7001, 8000, 8001, 8002)

Design choices
- The integration is YAML-configured and prefers reusing Home Assistant's Modbus integration hub.
- If a HA Modbus hub is not available, the integration falls back to a direct Modbus TCP client using `pymodbus`.
- Register numbers are used exactly as shown in the device document. If your device requires 0-based addressing, change the register numbers in config or code.
- Temperatures are scaled by 10 (device stores tenths of °C). Flows are scaled by 10 (device stores 0.1 m³/h).
- Multi-register values (e.g., motohours) are combined as 32-bit little-word (low register first, then high register).
- Serial number is decoded from registers 3000..3008 as ASCII characters.

Requirements
- Home Assistant (recent)
- If you want the pymodbus fallback enabled, `pymodbus>=2.5.0` is required (listed in manifest). HACS or Home Assistant will install it when the integration is installed.

Installation
1. Push this repository to GitHub (repo name: `ha_atrea_recuperation`).
2. Install via HACS (add custom repository -> category: Integration) or copy the `ha_atrea_recuperation` folder into `custom_components/`.
3. Configure the official HA Modbus integration in `configuration.yaml` (recommended) and set `modbus_hub: <name>` in the integration config so the integration reuses the HA Modbus hub.
4. If you don't have the HA Modbus integration, the integration will attempt direct Modbus TCP using `modbus_host`/`modbus_port` from the config and `pymodbus`.

Example configuration (configuration.yaml)

modbus:
  name: modbus_atrea
  type: tcp
  host: 192.168.1.50
  port: 502
  timeout: 5

ha_atrea_recuperation:
  name: "Atrea Buštěhrad RD1"
  # Preferred: reuse HA Modbus hub:
  modbus_hub: modbus_atrea

  # Fallback (used only if modbus_hub is not set or not found):
  modbus_host: 192.168.1.50
  modbus_port: 502

  unit: 1
  poll_interval: 10

  # Optional: override default HVAC labels (English defaults are used otherwise)
  hvac_mode_labels:
    0: "Off"
    1: "Auto"
    2: "Ventilation"
    3: "Circulation with ventilation"
    4: "Circulation"
    5: "Night precooling"
    6: "Balancing"
    7: "Overpressure"
    8: "Undefined"
