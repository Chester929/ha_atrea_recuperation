# Configuration

ha_atrea_recuperation is YAML-configured (configuration.yaml). It supports reusing Home Assistant's official Modbus hub or using a pymodbus fallback.

Example configuration (complete)

```yaml
modbus:
  name: modbus_atrea
  type: tcp
  host: 192.168.1.50
  port: 502
  timeout: 5

ha_atrea_recuperation:
  name: "Atrea Vila B"
  modbus_hub: modbus_atrea           # Recommended: reuse HA Modbus hub

  # Fallback (only used if modbus_hub is not set or not available):
  # modbus_host: 192.168.1.50
  # modbus_port: 502

  unit: 1                            # Modbus unit id (slave)
  poll_interval: 10                  # polling interval in seconds

  enable_pymodbus_fallback: true     # allow pymodbus fallback when HA Modbus is not available

  # Optional register overrides (only include keys you want to change)
  registers:
    current_temp_input: 1104
    target_temp_holding: 1002
    hvac_mode_holding: 1001
    fan_power_holding: 1004

  # Override operation mode labels (Select entity options)
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

  expose_discrete_inputs: false      # default: false
  create_all_sensors: true           # default: true
  log_level: info                    # optional
```

Configuration options explained

- name (string): Friendly integration/device name used as prefix for entity names.
- modbus_hub (string): Name of an existing Home Assistant Modbus hub (recommended). If present the integration uses the HA Modbus hub for all reads/writes.
- modbus_host (string) / modbus_port (int): Fallback TCP host and port used by pymodbus when `modbus_hub` is not set or not found.
- unit (int): Modbus unit id (commonly 1).
- poll_interval (int): Polling interval in seconds for the hub to read registers.
- enable_pymodbus_fallback (bool): When true, the integration will use pymodbus TCP to read/write registers if no HA Modbus hub is available.
- registers (mapping): Override default register numbers. Keys correspond to friendly names in the integration (see Entities / code).
- hvac_mode_labels (mapping int->string): Labels for the Select entity options for device operation modes (indices 0..8).
- expose_discrete_inputs (bool): If true, create binary_sensors for discrete inputs (disabled by default).
- create_all_sensors (bool): If true, the integration creates sensors for all documented Input/Holding registers. You can set to false to create only the main sensors.
- log_level (string): Optional; allow integration-specific log level setting (e.g., debug, info).

Notes
- Register numbers are used as-is (document values like 1001, 1104, 3200). If your device requires 0-based addressing, override the registers or adjust the code.
- The integration decodes:
  - Temperatures: divide by 10 → °C
  - Flows: divide by 10 → m³/h
  - 32-bit counters (motohours): combine low + (high << 16)
  - Serial number: registers 3000..3008 converted from integer ASCII codes into a string

Editing register mapping
- To change any register mapping, add entries under `registers:` in the config and restart HA. Only include the mappings you wish to override.

Example: disable auto sensor creation and only create the climate + fan + target number

```yaml
ha_atrea_recuperation:
  name: "Atrea RD1"
  modbus_hub: modbus_atrea
  create_all_sensors: false
```