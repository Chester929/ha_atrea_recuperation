# Entities and Register Mapping

This integration creates multiple entities based on the device register tables. Below are the main entities and the registers they map to.

Important: register numbers are the device register numbers from the document (not zero-based offsets). Use `registers` config overrides if your device differs.

## Climate

Entity: climate.<name>

- current_temperature — Input register 1104 (value /10 → °C)
- target_temperature — Holding register 1002 (value /10 → °C) — writable by climate.set_temperature or number.set_value
- hvac_mode — Mapped heuristically from device mode register 1001 (device integer → HA HVAC modes)

## Operation Mode (Select)

Entity: select.<name>_operation_mode

- Reads/writes holding register 1001
- Options: labels for indices 0..8 (default English labels)
- This select writes the integer mode index to the device (use for precise control)

Default labels (English)
- 0: Off
- 1: Auto
- 2: Ventilation
- 3: Circulation with ventilation
- 4: Circulation
- 5: Night precooling
- 6: Balancing
- 7: Overpressure
- 8: Undefined

Override via `hvac_mode_labels` in configuration.

## Fan

Entity: fan.<name>_fan

- Maps to holding register 1004 (percentage 0–100)
- Writes to device to set fan power

## Number (Target Temperature)

Entity: number.<name>_target_temperature

- Maps to holding register 1002
- Writes an integer value scaled by 10 (value = temperature * 10)

## Sensors

Sensors are created for Input and selected Holding registers. Example sensors:

- sensor.<name>_outdoor_temperature — input 1101 (value /10 °C)
- sensor.<name>_supply_temperature — input 1102 (value /10 °C)
- sensor.<name>_extract_temperature — input 1103 (value /10 °C)
- sensor.<name>_indoor_temperature — input 1104 (value /10 °C)
- sensor.<name>_supply_fan_percent — input 1107 (%)
- sensor.<name>_supply_flow_m3h — input 1109 (value /10 m³/h)
- sensor.<name>_serial_number — combined registers 3000..3008 decoded to ASCII string (single sensor)
- sensor.<name>_m1_hours — combined 3200 (low) + 3201 (high) → 32-bit hours value

## Buttons (Coils)

Buttons call coil pulses (True -> wait -> False):

- button.<name>_reset_states — coil 8000
- button.<name>_reset_filters — coil 8001
- button.<name>_reset_uv — coil 8002
- button.<name>_example_function — coil 7001 (example)

## Optional Binary Sensors

If `expose_discrete_inputs: true`, binary_sensors can be created for discrete input addresses from your device spec (not enabled by default).

## Entity IDs

Entity IDs are generated using the integration `name` (lowercased, spaces replaced with underscores) as a prefix. Examples after installing with name "Atrea Buštěhrad RD1":

- climate.atrea_villa_b
- select.atrea_villa_b_operation_mode
- fan.atrea_villa_b_fan
- number.atrea_villa_b_target_temperature
- sensor.atrea_villa_b_indoor_temperature
- button.atrea_villa_b_reset_filters

You can customize entity_id in Home Assistant via the UI (Device / Entity settings) after the entities appear.