# HA Atrea Recuperation

Home Assistant custom integration to control Atrea DUPLEX recuperation units (e.g. DUPLEX 380 ECV5) over Modbus (Modbus TCP).  
This repository is HACS-ready and includes an optional pymodbus fallback so the integration can work even if you don't use Home Assistant's built-in Modbus integration.

Contents
- custom_components/ha_atrea_recuperation/ — the integration code (climate, fan, sensor, number, select, button, hub)
- hacs.json — HACS metadata
- README.md — this file (root)

What it provides
- climate entity (target temperature + simplified HVAC mapping)
- select entity (device operation mode; writes integer to holding register 1001)
- fan entity (percentage control writing to holding register 1004)
- number entity for target temperature (holding 1002)
- sensors for Input and Holding registers (temperatures, flows, counters, serial)
- buttons for coil actions (7001, 8000, 8001, 8002)
- optional pymodbus fallback (Modbus TCP) if HA Modbus hub is not configured

Requirements
- Home Assistant (a recent release — integration uses standard entity platforms)
- If you want the pymodbus fallback: pymodbus>=2.5.0 (declared in manifest). HACS/HA will install it automatically when the integration is installed via HACS.

Installation

A) Install via HACS (recommended)
1. Push this repository to GitHub under the name `ha_atrea_recuperation` (or add it as a custom repository URL in HACS).
2. In Home Assistant → HACS → Integrations → ... → Custom repositories:
   - Repository URL: `https://github.com/Chester929/ha_atrea_recuperation`
   - Category: `Integration`
3. Install "HA Atrea Recuperation" from HACS.
4. Restart Home Assistant.
5. Configure the integration (see Configuration section below).

B) Manual installation
1. Copy the folder `custom_components/ha_atrea_recuperation/` into your Home Assistant `custom_components/` directory.
2. If you want the pymodbus fallback and your HA environment does not auto-install dependencies, install pymodbus:
   - For Home Assistant OS / supervised: install via HACS (recommended) or add dependency in custom component packaging.
   - For other installs: pip install pymodbus>=2.5.0 in the Python environment running Home Assistant.
3. Restart Home Assistant.
4. Configure the integration (see Configuration section below).

Configuration

Basic flow
- Recommended: configure the official `modbus:` integration in your `configuration.yaml` and set `modbus_hub` to reuse the existing Modbus connection.
- Fallback: if no HA Modbus hub is available, the integration can use `modbus_host`/`modbus_port` and the bundled pymodbus client.

Example (complete) configuration.yaml snippet

```yaml
# --- Configure Home Assistant Modbus hub (recommended) ---
modbus:
  name: modbus_atrea
  type: tcp
  host: 192.168.1.50      # IP of your Modbus TCP gateway / device
  port: 502
  timeout: 5

# --- HA Atrea Recuperation integration ---
ha_atrea_recuperation:
  name: "Atrea Buštěhrad RD1"          # friendly integration/device name
  modbus_hub: modbus_atrea             # recommended: reuse HA Modbus hub above
  # Fallback if you don't use HA Modbus hub (pymodbus will be used):
  # modbus_host: 192.168.1.50
  # modbus_port: 502

  unit: 1                              # Modbus unit id (slave) — default: 1
  poll_interval: 10                    # polling interval in seconds (default: 10)

  # Optional: enable/disable the pymodbus fallback even if HA Modbus exists
  enable_pymodbus_fallback: true

  # Optional: override or add register mappings (only include what you need).
  # Keys are the friendly names used by the integration code; values are register numbers
  registers:
    # Example overrides (not required)
    current_temp_input: 1104
    target_temp_holding: 1002
    hvac_mode_holding: 1001
    fan_power_holding: 1004

  # Optional: override the labels for operation modes (default English labels used otherwise).
  # Use Czech labels here if you prefer Czech in the UI.
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

  # Optional fine-tuning
  expose_discrete_inputs: false        # default: false (do not create binary_sensors for DI table)
  create_all_sensors: true             # default: true (create sensors for Input/Holding registers in spec)
  log_level: info                      # optional integration-specific log level
```

Notes on configuration options
- name: friendly name used as entity name prefix.
- modbus_hub: name of the HA Modbus hub (recommended). If set and available the integration will use the hub to perform reads/writes.
- modbus_host/modbus_port: fallback TCP host/port used by pymodbus when HA Modbus hub missing.
- unit: Modbus unit ID (slave id).
- poll_interval: interval in seconds used to poll registers.
- registers: merge/override default register mapping. Only include keys you want to change.
- hvac_mode_labels: integer -> label mapping used by the Select entity for operation modes. Provide Czech labels here if you prefer Czech UI.
- enable_pymodbus_fallback: when true the integration will use pymodbus TCP client if HA Modbus hub isn't available.

Entities created (examples)
- climate.<name> (e.g. climate.ha_atrea_recuperation)  
  - current_temperature: input register 1104 (scaled /10)
  - target_temperature: holding register 1002 (scaled /10) — writable via climate service or number entity
  - hvac_modes: [off, auto, heat] mapped heuristically from device mode register (1001)
- select.<name>_operation_mode (operation mode select)  
  - Options: labels from hvac_mode_labels 0..8 — writes integer to holding 1001
- fan.<name>_fan  
  - Percentage control (writes to holding 1004)
- number.<name>_target_temperature  
  - Writes target setpoint (holding 1002) scaled by 10
- sensor.*  
  - Temperatures: 1101 (outdoor), 1102 (supply), 1103 (extract), 1104 (indoor), 1105 (return) — scale /10 → °C
  - Flows: 1109/1110/1111 — scale /10 → m³/h
  - Fan percents: 1107/1108 → %
  - Serial: sensor combining registers 3000..3008 decoded to ASCII string (single sensor)
  - Motohours: combined 32-bit from pairs 3200/3201 and 3202/3203
- button.*  
  - Buttons that pulse coils: 7001, 8000 (reset_states), 8001 (reset_filters), 8002 (reset_uv)

Entity ID examples (after install)
- climate.ha_atrea_recuperation
- select.ha_atrea_recuperation_operation_mode
- fan.ha_atrea_recuperation_fan
- number.ha_atrea_recuperation_target_temperature
- sensor.ha_atrea_recuperation_indoor_temperature
- sensor.ha_atrea_recuperation_supply_flow
- sensor.ha_atrea_recuperation_serial_number
- sensor.ha_atrea_recuperation_m1_hours
- button.ha_atrea_recuperation_reset_filters

Register addressing
- The integration uses register numbers exactly as listed in the device document (e.g., 1001, 1104, 3200). If your device requires 0-based addresses adjust numbers accordingly in the `registers` config or modify the code.

Data encoding & scaling
- Temperatures: stored as register value = temperature * 10. The integration divides by 10 to present °C.
- Flows: stored as register value = flow * 10 (0.1 m³/h units). The integration divides by 10.
- Percent values: scale 1 → %
- 32-bit counters (motohours): combined as low + (high << 16) (little-word order).
- Serial number: ASCII codes in registers 3000..3008 decoded into a single string sensor.
- Multi-register floats/other encodings: not currently supported (if your device uses float32 you can request/report which registers and endianness and we'll add support).

Pymodbus fallback behavior
- If `modbus_hub` is not set or the specified HA Modbus hub is not found, and if `enable_pymodbus_fallback: true`, the integration attempts to read/write using a direct Modbus TCP connection to `modbus_host:modbus_port` with pymodbus.
- Ensure `pymodbus>=2.5.0` is installed (HACS will install it if you install via HACS).

HACS-specific notes
- The repository includes `hacs.json` and `manifest.json` so it is recognized as an Integration by HACS.
- Add the repository as a custom repository in HACS (category Integration). HACS will show the integration and allow install/uninstall.
- After HACS install, restart Home Assistant and add the `ha_atrea_recuperation` config to `configuration.yaml`.

Troubleshooting
- No entities appear:
  - Ensure integration is added to `configuration.yaml` and Home Assistant was restarted.
  - Check HA logs (Supervisor → System logs or Configuration → Logs). Look for `ha_atrea_recuperation` or Modbus connection errors.
- Modbus errors:
  - Verify Modbus TCP endpoint with a test tool (e.g., `modpoll`, `pymodbus` script) or check HA Modbus integration settings.
  - Ensure correct unit id (slave) and register addressing base.
- pymodbus fallback not connecting:
  - Check `modbus_host`/`modbus_port` values.
  - Confirm network routing/firewall.
  - Ensure `pymodbus` installed in HA environment.
- To increase logging, in `configuration.yaml` add:
```yaml
logger:
  default: info
  logs:
    custom_components.ha_atrea_recuperation: debug
```
Then restart HA and inspect logs.

Example automations / scripts
- Set operation mode to "Ventilation" (index 2 via select):
```yaml
service: select.select_option
target:
  entity_id: select.ha_atrea_recuperation_operation_mode
data:
  option: "Ventilation"
```

- Set target temperature to 21°C:
```yaml
service: number.set_value
target:
  entity_id: number.ha_atrea_recuperation_target_temperature
data:
  value: 21.0
```

- Pulse reset filters button (coil 8001):
```yaml
service: button.press
target:
  entity_id: button.ha_atrea_recuperation_reset_filters
```

Development & file layout
- custom_components/ha_atrea_recuperation/
  - __init__.py — integration setup, entity creation
  - hub.py — Modbus I/O hub (HA Modbus preferred, pymodbus fallback)
  - climate.py — ClimateEntity wrapper
  - select.py — operation mode SelectEntity
  - fan.py — FanEntity (percentage)
  - sensor.py — generic SensorEntity (handles combined registers / serial)
  - number.py — NumberEntity (writable holding registers)
  - button.py — ButtonEntity (pulses coils)
  - manifest.json — integration metadata
- hacs.json — HACS metadata (root)
- README.md — (this file)

License & contact
- No explicit license included in this repo by default. Add a LICENSE file if you want to permit reuse (MIT recommended for Home Assistant custom integrations).
- For questions or improvements provide issues/PRs on the repository.

If you want me to:
- Generate a polished release (tag + GitHub release notes),
- Add a config_flow (UI setup) instead of YAML,
- Expose all discrete inputs as binary_sensors behind a config flag,
- Add float32 and other multi-register decoding with configurable endianness,
...tell me which and I'll update the integration code and README accordingly.