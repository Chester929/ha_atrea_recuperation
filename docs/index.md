# HA Atrea Recuperation

HA Atrea Recuperation integrates Atrea DUPLEX recuperation units with Home Assistant using Modbus TCP. The integration uses a platform-based architecture (refactored in v1.0.6) with `async_setup_platform` for reliable entity registration and exposes:

- **Climate entity**: Target temperature control with simplified HVAC mode mapping
- **Select entity**: Full device operation mode control (writes integer to holding register 1001)
- **Fan entity**: Percentage-based fan power control (writes to holding register 1004)
- **Number entity**: Direct target temperature control (holding register 1002)
- **Sensors**: Temperatures, airflow rates, fan power, operating hours, and serial number decoding
- **Buttons**: Coil pulse actions for resets (filters, UV lamp, device states)
- **Flexible Modbus support**: Works with Home Assistant Modbus integration or standalone pymodbus fallback

## Platform-Based Architecture

Since version 1.0.6, the integration uses Home Assistant's platform-based architecture:

- Each entity type (climate, sensor, fan, select, number, button) is implemented as a separate platform file
- All platforms use `async_setup_platform` for proper entity registration
- A shared `DataUpdateCoordinator` manages polling and state updates
- The `HaAtreaModbusHub` handles all Modbus I/O operations
- Entities automatically inherit coordinator updates via `CoordinatorEntity`

This architecture provides:
- More reliable entity registration during startup
- Better separation of concerns
- Improved performance with coordinated polling
- Easier maintenance and extension

## Documentation Overview

This documentation explains installation (HACS or manual), configuration options, entities created, troubleshooting tips and developer notes.

Quick links
- **Installation**: Installation guide for HACS and manual methods
- **Configuration options**: Complete YAML configuration reference
- **Entities and register mapping**: Details on all entities and their Modbus registers
- **Troubleshooting tips and logs**: Common issues and debug logging
- **Developer notes and architecture**: Code layout, contributing, and extending the integration