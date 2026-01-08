# HA Atrea Recuperation

HA Atrea Recuperation integrates Atrea DUPLEX recuperation units with Home Assistant using Modbus (Modbus TCP). The integration exposes thermostat functionality + device-specific controls and telemetry:

- Climate entity (target temperature, simplified HVAC mapping)
- Select entity for device operation mode (writes integer to holding register 1001)
- Fan entity (percentage control, writes to holding register 1004)
- Number entity for target temperature (holding 1002)
- Sensors for temperatures, flows, counters, and serial number decoding
- Buttons that pulse coils (reset actions)
- Optional pymodbus fallback if Home Assistant Modbus hub is not used

This documentation explains installation (HACS or manual), configuration options, entities created, troubleshooting tips and developer notes.

Quick links
- Installation: Installation
- Configuration options: Configuration
- Entities and register mapping: Entities
- Troubleshooting tips and logs: Troubleshooting
- Developer notes and architecture: Developer