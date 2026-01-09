# HA Atrea Recuperation

[![HACS](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/badge/version-1.0.11-blue.svg)](https://github.com/Chester929/ha_atrea_recuperation/releases)

Home Assistant integration for Atrea DUPLEX recuperation (heat recovery / ventilation) units via Modbus TCP. This custom component provides comprehensive control and monitoring of your Atrea recuperation system directly from Home Assistant.

## Features

- **Multi-Device Support**: Configure multiple recuperation units with unique Modbus hubs or TCP connections
- **Device Registry Integration**: All devices appear in Home Assistant's device list with proper grouping
- **Climate Control**: Full thermostat functionality with target temperature control and HVAC mode mapping
- **Operation Modes**: Select entity for precise device mode control (Off, Auto, Ventilation, Circulation, etc.)
- **Fan Control**: Percentage-based fan speed control
- **Comprehensive Sensors**: Temperature readings, airflow measurements, fan power, operating hours, and more
- **Device Information**: Automatic detection of device model and software version from Modbus registers
- **Reset Actions**: Button entities for filter reset, UV lamp reset, and state reset
- **Platform-Based Architecture**: Uses Home Assistant's `async_setup_platform` for reliable entity registration
- **Flexible Modbus Integration**: Can use Home Assistant's Modbus integration or standalone pymodbus fallback
- **HACS Ready**: Easy installation and updates via Home Assistant Community Store

## Status and Compatibility

- **Current Version**: 1.0.11
- **Minimum Home Assistant Version**: 2021.12.0
- **Integration Type**: YAML-configured custom component
- **IoT Class**: Local Polling
- **Supported Platforms**: Climate, Sensor, Fan, Select, Number, Button

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → **⋮** (top-right menu) → **Custom repositories**
3. Add repository URL: `https://github.com/Chester929/ha_atrea_recuperation`
4. Set category to **Integration**
5. Click **Add**
6. Find "HA Atrea Recuperation" in HACS and click **Download**
7. Restart Home Assistant

### Option 2: Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/ha_atrea_recuperation/` folder into your Home Assistant `config/custom_components/` directory
3. The path should be: `config/custom_components/ha_atrea_recuperation/`
4. Restart Home Assistant

**Note**: After installation, you must configure the integration in `configuration.yaml` (see Configuration section below).

## Configuration

This integration is configured via YAML in your `configuration.yaml` file. It supports two Modbus connection methods:

1. **Recommended**: Reuse Home Assistant's Modbus integration
2. **Fallback**: Direct connection using pymodbus

### Basic Configuration Example

```yaml
# Configure Home Assistant's Modbus integration (recommended)
modbus:
  - name: modbus_atrea
    type: tcp
    host: 192.168.1.50
    port: 502
    timeout: 5

# Configure HA Atrea Recuperation integration
ha_atrea_recuperation:
  name: "Atrea Villa"
  modbus_hub: modbus_atrea    # Reference to the Modbus hub above
  unit: 1                      # Modbus slave/unit ID
  poll_interval: 10            # Polling interval in seconds
```

### Advanced Configuration Example

```yaml
ha_atrea_recuperation:
  name: "Atrea Villa"
  modbus_hub: modbus_atrea
  unit: 1
  poll_interval: 10

  # Optional: Custom operation mode labels (default: English)
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
```

### Multiple Devices Configuration

You can configure multiple recuperation units by providing a list of device configurations. Each device will appear as a separate device in Home Assistant with all its entities grouped together.

#### Multiple devices with shared Modbus hub:

```yaml
# Configure Home Assistant's Modbus integration (recommended)
modbus:
  - name: modbus_atrea
    type: tcp
    host: 192.168.1.50
    port: 502
    timeout: 5

# Configure multiple HA Atrea Recuperation devices
ha_atrea_recuperation:
  - name: "Atrea Ground Floor"
    modbus_hub: modbus_atrea
    unit: 1
    poll_interval: 10

  - name: "Atrea First Floor"
    modbus_hub: modbus_atrea
    unit: 2
    poll_interval: 10
```

#### Multiple devices with separate Modbus hubs:

```yaml
# Configure multiple Modbus hubs in Home Assistant
modbus:
  - name: modbus_atrea_building_a
    type: tcp
    host: 192.168.1.50
    port: 502
    timeout: 5

  - name: modbus_atrea_building_b
    type: tcp
    host: 192.168.1.51
    port: 502
    timeout: 5

# Each device uses its own Modbus hub
ha_atrea_recuperation:
  - name: "Atrea Building A"
    modbus_hub: modbus_atrea_building_a
    unit: 1
    poll_interval: 10

  - name: "Atrea Building B"
    modbus_hub: modbus_atrea_building_b
    unit: 1
    poll_interval: 10
```

#### Multiple devices with separate TCP connections:

```yaml
ha_atrea_recuperation:
  - name: "Atrea Building A"
    modbus_host: 192.168.1.50
    modbus_port: 502
    unit: 1
    poll_interval: 10

  - name: "Atrea Building B"
    modbus_host: 192.168.1.51
    modbus_port: 502
    unit: 1
    poll_interval: 10
```

#### Mixed configuration (hub + direct TCP):

```yaml
modbus:
  - name: modbus_atrea_main
    type: tcp
    host: 192.168.1.50
    port: 502
    timeout: 5

ha_atrea_recuperation:
  - name: "Atrea Main Building"
    modbus_hub: modbus_atrea_main
    unit: 1
    poll_interval: 10

  - name: "Atrea Remote Site"
    modbus_host: 192.168.2.100
    modbus_port: 502
    unit: 1
    poll_interval: 15
```

### Fallback Configuration (without HA Modbus integration)

```yaml
ha_atrea_recuperation:
  name: "Atrea Villa"
  modbus_host: 192.168.1.50   # Direct IP address
  modbus_port: 502             # Modbus TCP port
  unit: 1
  poll_interval: 10
```

### Configuration Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `name` | string | Yes | - | Friendly name used as prefix for all entities |
| `modbus_hub` | string | No* | - | Name of existing Home Assistant Modbus hub |
| `modbus_host` | string | No* | - | IP address for pymodbus fallback |
| `modbus_port` | integer | No | 502 | Modbus TCP port for fallback |
| `unit` | integer | No | 1 | Modbus slave/unit ID |
| `poll_interval` | integer | No | 10 | Register polling interval in seconds |
| `hvac_mode_labels` | mapping | No | Default English | Custom labels for operation modes 0-8 |

*Either `modbus_hub` or `modbus_host` must be provided.

## Device Registry Integration

All configured recuperation units appear as devices in Home Assistant's device registry. Each device groups all its entities (climate, sensors, fan, select, number, buttons) for easy management.

### Device Information

Each device displays the following information in Home Assistant:
- **Name**: The configured device name
- **Manufacturer**: Atrea
- **Model**: Automatically detected from Modbus registers (3009-3019) or defaults to "DUPLEX Recuperation"
- **Software Version**: Automatically detected from Modbus registers (3100-3103)
- **Serial Number**: Read from Modbus registers (3000-3008)
- **Identifiers**: Uses serial number or device name for unique identification

### Device Benefits

- **Organized Entity View**: All entities for a device are grouped together
- **Device Actions**: Perform actions on all entities of a device at once
- **Diagnostics**: View device status and information in one place
- **Automation**: Easier to create automations targeting specific devices

## Platform-Based Architecture

This integration was refactored in PR #2 to use Home Assistant's platform-based architecture with `async_setup_platform` for reliable entity registration. The integration loads the following platforms:

- **Climate** (`climate.py`): Thermostat control with temperature management
- **Sensor** (`sensor.py`): All input and holding register sensors
- **Select** (`select.py`): Operation mode selector
- **Fan** (`fan.py`): Fan speed control
- **Number** (`number.py`): Target temperature number entity
- **Button** (`button.py`): Coil pulse buttons for reset actions

Each platform is loaded via Home Assistant's discovery mechanism and registers entities using `async_setup_platform`, ensuring proper initialization and coordinator integration.

## Entities and Platforms

### Climate Entity

**Entity ID**: `climate.<name>`

The climate entity provides thermostat-style control for Atrea DUPLEX recuperation units. These devices support temperature control through integrated preheaters and reheaters, making the climate entity highly relevant for:

- **Temperature Control**: Set desired supply air temperature
- **Heating Modes**: Utilize integrated electric or water-based heaters
- **Seasonal Operation**: Automatic bypass for cooling in summer
- **Night Cooling**: Precooling mode for energy efficiency

Features:
- Current temperature from input register 1104
- Target temperature (read/write) from holding register 1002
- HVAC modes mapped from device operation mode
- Supports `climate.set_temperature` service

### Select Entity (Operation Mode)

**Entity ID**: `select.<name>_operation_mode`

Controls device operation mode via holding register 1001:

- **Options**: 0=Off, 1=Auto, 2=Ventilation, 3=Circulation with ventilation, 4=Circulation, 5=Night precooling, 6=Balancing, 7=Overpressure, 8=Undefined
- Writes integer mode directly to device
- Provides precise control beyond Climate HVAC modes

### Fan Entity

**Entity ID**: `fan.<name>_fan`

- Controls fan power percentage (0-100%)
- Maps to holding register 1004
- Supports `fan.turn_on`, `fan.turn_off`, `fan.set_percentage`

### Number Entity (Target Temperature)

**Entity ID**: `number.<name>_target_temperature`

- Direct control of target temperature
- Maps to holding register 1002
- Range: -30°C to 90°C
- Alternative to climate thermostat control

### Sensor Entities

Automatically created sensors include:

**Temperature Sensors** (scaled by 10, unit: °C):
- `sensor.<name>_outdoor_temperature` - Input 1101
- `sensor.<name>_supply_temperature` - Input 1102
- `sensor.<name>_extract_temperature` - Input 1103
- `sensor.<name>_indoor_temperature` - Input 1104
- `sensor.<name>_return_temperature` - Input 1105

**Airflow Sensors** (scaled by 0.1, unit: m³/h):
- `sensor.<name>_supply_flow` - Input 1109
- `sensor.<name>_extract_flow` - Input 1110
- `sensor.<name>_fresh_air_flow` - Input 1111

**Fan Power Sensors** (unit: %):
- `sensor.<name>_supply_fan_power` - Input 1107
- `sensor.<name>_extract_fan_power` - Input 1108

**Operating Hours** (32-bit counters, unit: hours):
- `sensor.<name>_m1_hours` - Combined from inputs 3200+3201
- `sensor.<name>_m2_hours` - Combined from inputs 3202+3203
- `sensor.<name>_uv_hours` - Combined from inputs 3204+3205

**Device Information**:
- `sensor.<name>_serial_number` - Decoded from inputs 3000-3008

### Button Entities

Reset action buttons (pulse coils):

- `button.<name>_reset_states` - Coil 8000
- `button.<name>_reset_filters` - Coil 8001
- `button.<name>_reset_uv` - Coil 8002
- `button.<name>_example_function` - Coil 7001

### Entity Naming Convention

Entity IDs are automatically generated from the configured `name`:
- Lowercase conversion
- Spaces replaced with underscores
- Platform prefix added (climate, sensor, fan, etc.)

**Example**: If `name: "Atrea Villa B"`, entities will be:
- `climate.atrea_villa_b`
- `sensor.atrea_villa_b_indoor_temperature`
- `fan.atrea_villa_b_fan`
- etc.

## Services

This integration uses standard Home Assistant services for the entity platforms:

### Climate Services
- `climate.set_temperature` - Set target temperature
- `climate.set_hvac_mode` - Set HVAC mode
- `climate.turn_on` / `climate.turn_off`

### Fan Services
- `fan.turn_on` / `fan.turn_off`
- `fan.set_percentage` - Set fan speed (0-100%)

### Select Services
- `select.select_option` - Change operation mode

### Number Services
- `number.set_value` - Set target temperature value

### Button Services
- `button.press` - Trigger reset action

## Troubleshooting & Diagnostics

### No Entities Appear

1. Verify integration is in `configuration.yaml`
2. Check that Home Assistant was restarted after installation
3. Review Home Assistant logs for errors
4. Ensure `modbus_hub` references a valid Modbus integration
5. Check network connectivity to device

### Enabling Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.ha_atrea_recuperation: debug
```

Restart Home Assistant and check logs in **Configuration** → **Logs** or via command line:

```bash
tail -f /config/home-assistant.log | grep ha_atrea_recuperation
```

### Common Issues

**Wrong temperature values**: Temperatures are stored as integers divided by 10. If values appear incorrect, verify register mapping.

**Modbus connection errors**: 
- Verify IP address and port
- Check Modbus unit ID (typically 1)
- Test connectivity with tools like `modpoll` or `pymodbus`
- Ensure no firewall blocking port 502

**pymodbus not found**: 
- For HACS installations, dependencies install automatically
- For manual installations, run: `pip install pymodbus>=2.5.0` in HA environment

### Getting Help

If you encounter issues:

1. Enable debug logging (see above)
2. Collect relevant logs
3. Note your configuration (sanitize IP addresses)
4. Open an issue at: https://github.com/Chester929/ha_atrea_recuperation/issues

Include:
- Home Assistant version
- Integration version
- Configuration snippet
- Debug logs showing the error
- Device model/firmware version (if known)

## Development

### Code Layout

```
custom_components/ha_atrea_recuperation/
├── manifest.json          # Integration metadata and dependencies
├── __init__.py           # Main integration setup, coordinator creation
├── const.py              # Register definitions and constants
├── hub.py                # Modbus I/O hub with HA/pymodbus support
├── climate.py            # Climate platform (async_setup_platform)
├── sensor.py             # Sensor platform (async_setup_platform)
├── fan.py                # Fan platform (async_setup_platform)
├── select.py             # Select platform (async_setup_platform)
├── number.py             # Number platform (async_setup_platform)
└── button.py             # Button platform (async_setup_platform)
```

### Key Files

- **`manifest.json`**: Integration metadata, version (1.0.6), dependencies (pymodbus>=2.5.0), IoT class
- **`__init__.py`**: YAML setup entry point, coordinator creation, platform discovery
- **`hub.py`**: HaAtreaModbusHub class managing register reads/writes and caching
- **`const.py`**: INPUT_REGISTERS, HOLDING_REGISTERS, COILS definitions
- **Platform files**: Each implements `async_setup_platform` for entity registration

### How to Contribute

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with your device
5. Run pre-release checks: `scripts/pre_release_checks.sh`
6. Open a pull request with:
   - Description of changes
   - Testing performed
   - Any new dependencies

### Running Tests

Currently, the integration focuses on integration testing with actual hardware. For development:

1. Set up a test Home Assistant instance
2. Configure debug logging
3. Test with real Atrea device or Modbus simulator
4. Verify all entity states and services

### Documentation

Full documentation is available in the `docs/` folder:

- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [Entity & Register Mapping](docs/entities.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Developer Notes](docs/developer.md)
- [Changelog](docs/changelog.md)

To view docs locally:

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

Then open http://127.0.0.1:8000

## Changelog

### Recent Changes

**v1.0.6** (Current)
- Platform-based architecture using `async_setup_platform` (PR #2)
- Improved entity registration reliability
- Better coordinator integration
- Enhanced Modbus hub compatibility

**v1.0.5**
- Code cleanup and linting improvements

**v1.0.1-1.0.4**
- Initial HACS-ready releases
- Climate, sensor, fan, select, number, and button platforms
- Serial number decoding
- 32-bit operating hours support
- Documentation framework

For detailed changelog, see [docs/changelog.md](docs/changelog.md).

## License

This project does not currently include a license file. Please contact the maintainer if you wish to use or contribute to this project.

## Maintainer

**Chester929** ([@Chester929](https://github.com/Chester929))

For issues, feature requests, or questions:
- **Issues**: https://github.com/Chester929/ha_atrea_recuperation/issues
- **Discussions**: https://github.com/Chester929/ha_atrea_recuperation/discussions

## Acknowledgments

- Built for Home Assistant and the Atrea DUPLEX recuperation system
- Uses pymodbus for Modbus TCP communication
- Platform architecture follows Home Assistant integration best practices