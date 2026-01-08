# Entities and Register Mapping

This integration creates multiple entities based on the device register tables defined in `const.py`. Below are the main entities and the registers they map to.

**Important**: Register numbers are the device register numbers from the Atrea documentation (not zero-based offsets). All registers are accessed as-is (e.g., register 1001 is accessed as address 1001).

## Platform Overview

The integration creates entities across six platforms:

1. **Climate** - Thermostat control
2. **Select** - Operation mode selection
3. **Fan** - Fan speed control
4. **Number** - Target temperature control
5. **Sensor** - Temperature, flow, and status monitoring
6. **Button** - Reset action triggers

## Climate Entity

**Entity ID**: `climate.<name>` (e.g., `climate.atrea_villa_b`)

**Purpose**: Provides thermostat functionality with temperature control and simplified HVAC mode mapping.

**Registers**:
- **Current temperature**: Input register 1104 (Indoor temperature, scaled ÷10 → °C)
- **Target temperature**: Holding register 1002 (read/write, scaled ÷10 → °C)
- **HVAC mode**: Derived from holding register 1001 (device operation mode)

**Supported HVAC Modes**:
The climate entity maps device modes (0-8) to Home Assistant HVAC modes heuristically:
- `OFF` - Device mode 0
- `AUTO` - Device mode 1
- `FAN_ONLY` - Device modes 2, 3
- `HEAT` - Other modes (4-8)

**Services**:
- `climate.set_temperature` - Set target temperature
- `climate.set_hvac_mode` - Change HVAC mode
- `climate.turn_on` / `climate.turn_off`

**Attributes**:
- `current_temperature` - Current indoor temperature
- `temperature` - Target temperature setpoint
- `hvac_mode` - Current HVAC mode
- `hvac_modes` - List of available HVAC modes

## Select Entity (Operation Mode)

**Entity ID**: `select.<name>_operation_mode` (e.g., `select.atrea_villa_b_operation_mode`)

**Purpose**: Provides precise device operation mode control with all available modes.

**Register**: Holding register 1001 (read/write, integer 0-8)

**Options** (default English labels):
- `0` - Off
- `1` - Auto
- `2` - Ventilation
- `3` - Circulation with ventilation
- `4` - Circulation
- `5` - Night precooling
- `6` - Balancing
- `7` - Overpressure
- `8` - Undefined

**Customization**: Override labels via `hvac_mode_labels` in configuration.

**Services**:
- `select.select_option` - Change operation mode by label

**Use Case**: Use this for precise mode control when Climate HVAC modes are too simplified.

## Fan Entity

**Entity ID**: `fan.<name>_fan` (e.g., `fan.atrea_villa_b_fan`)

**Purpose**: Controls fan speed as a percentage.

**Register**: Holding register 1004 (read/write, percentage 0-100)

**Services**:
- `fan.turn_on` - Turn fan on (restores last percentage or sets to 100%)
- `fan.turn_off` - Turn fan off (sets to 0%)
- `fan.set_percentage` - Set fan speed percentage (0-100)

**Attributes**:
- `percentage` - Current fan speed percentage
- `is_on` - Fan on/off state (true if percentage > 0)

## Number Entity (Target Temperature)

**Entity ID**: `number.<name>_target_temperature` (e.g., `number.atrea_villa_b_target_temperature`)

**Purpose**: Direct numeric control of target temperature (alternative to Climate entity).

**Register**: Holding register 1002 (read/write, scaled ÷10 → °C)

**Range**: -30°C to 90°C (configurable in code)

**Services**:
- `number.set_value` - Set target temperature value

**Attributes**:
- `value` - Current target temperature
- `min_value` - Minimum temperature (-30°C)
- `max_value` - Maximum temperature (90°C)
- `unit_of_measurement` - °C

## Sensor Entities

Sensors are automatically created for all registers defined in `INPUT_REGISTERS` and `HOLDING_REGISTERS` in `const.py`. Below are the key sensors:

### Temperature Sensors

All temperature sensors are scaled by dividing register value by 10.

| Entity ID | Register | Description | Unit |
|-----------|----------|-------------|------|
| `sensor.<name>_outdoor_temperature` | Input 1101 | Outdoor air temperature | °C |
| `sensor.<name>_supply_temperature` | Input 1102 | Supply air temperature (after heat recovery) | °C |
| `sensor.<name>_extract_temperature` | Input 1103 | Extract air temperature (from house) | °C |
| `sensor.<name>_indoor_temperature` | Input 1104 | Indoor/room temperature | °C |
| `sensor.<name>_return_temperature` | Input 1105 | Return air temperature | °C |

### Airflow Sensors

Airflow sensors are scaled by dividing register value by 10.

| Entity ID | Register | Description | Unit |
|-----------|----------|-------------|------|
| `sensor.<name>_supply_flow` | Input 1109 | Supply airflow rate | m³/h |
| `sensor.<name>_extract_flow` | Input 1110 | Extract airflow rate | m³/h |
| `sensor.<name>_fresh_air_flow` | Input 1111 | Fresh air flow rate | m³/h |

### Fan Power Sensors

| Entity ID | Register | Description | Unit |
|-----------|----------|-------------|------|
| `sensor.<name>_supply_fan_power` | Input 1107 | Supply fan power | % |
| `sensor.<name>_extract_fan_power` | Input 1108 | Extract fan power | % |

### Operating Hours (32-bit Counters)

These sensors combine two consecutive 16-bit registers into a 32-bit hour counter using the formula: `low + (high << 16)`.

| Entity ID | Registers | Description | Unit |
|-----------|-----------|-------------|------|
| `sensor.<name>_m1_hours` | Input 3200 (low), 3201 (high) | Motor 1 operating hours | h |
| `sensor.<name>_m2_hours` | Input 3202 (low), 3203 (high) | Motor 2 operating hours | h |
| `sensor.<name>_uv_hours` | Input 3204 (low), 3205 (high) | UV lamp operating hours | h |

### Device Information

| Entity ID | Registers | Description |
|-----------|-----------|-------------|
| `sensor.<name>_serial_number` | Input 3000-3008 | Device serial number (decoded from ASCII codes) |

### Additional Sensors

The integration also creates sensors for:
- Mode values from input/holding registers
- Desired power and flow values
- Zone selection
- Trigger states (inputs 7103, 7104, 7105)
- Active calendar and scene (holdings 3189, 3190)

**Complete list**: See `const.py` for all `INPUT_REGISTERS` and `HOLDING_REGISTERS` definitions.

## Button Entities

Buttons trigger coil pulse operations (writes True, waits 500ms, writes False).

| Entity ID | Coil | Description |
|-----------|------|-------------|
| `button.<name>_example_function` | 7001 | Example function trigger |
| `button.<name>_reset_states` | 8000 | Reset device states |
| `button.<name>_reset_filters` | 8001 | Reset filter counter/alarm |
| `button.<name>_reset_uv` | 8002 | Reset UV lamp counter/alarm |

**Services**:
- `button.press` - Trigger the button action

**Use Cases**:
- Reset filter timer after filter replacement
- Reset UV lamp timer after replacement
- Clear device error states

## Entity Naming Convention

Entity IDs are automatically generated from the configured `name` parameter:

1. Convert to lowercase
2. Replace spaces with underscores
3. Add entity type and descriptive suffix

**Examples** with `name: "Atrea Villa B"`:

| Entity Type | Entity ID |
|-------------|-----------|
| Climate | `climate.atrea_villa_b` |
| Select | `select.atrea_villa_b_operation_mode` |
| Fan | `fan.atrea_villa_b_fan` |
| Number | `number.atrea_villa_b_target_temperature` |
| Sensor (temp) | `sensor.atrea_villa_b_indoor_temperature` |
| Sensor (flow) | `sensor.atrea_villa_b_supply_flow` |
| Sensor (hours) | `sensor.atrea_villa_b_m1_hours` |
| Button | `button.atrea_villa_b_reset_filters` |

**Customization**: You can rename entity IDs in Home Assistant UI via **Settings** → **Devices & Services** → select entity → **Settings icon** → change Entity ID.

## Understanding Register Types

### Input Registers (Read-Only)
- Read from device, cannot be written
- Contain sensor values, status information
- Examples: temperatures, flows, counters
- Address range in Atrea devices: typically 1000-7999

### Holding Registers (Read/Write)
- Can be read and written
- Used for control and setpoints
- Examples: target temperature, mode, fan power
- Address range in Atrea devices: typically 1000-3999

### Coils (Write for Pulse)
- Single-bit values (on/off)
- Used for momentary actions (buttons)
- Integration pulses them (on → wait → off)
- Address range in Atrea devices: typically 7000-8999

## Data Update Flow

1. **Coordinator polls** at `poll_interval` (default 10 seconds)
2. **Hub reads** all input and holding registers via Modbus
3. **Data cached** in `coordinator.data` as a dictionary `{register: value}`
4. **Entities notified** via CoordinatorEntity mechanism
5. **Entities update** their state by reading from cached data
6. **Home Assistant displays** updated entity states

This polling architecture ensures:
- Efficient batch reading of all registers
- Consistent data across all entities
- Reduced Modbus traffic
- Automatic recovery from communication errors

## Troubleshooting Entity Issues

**Entities not appearing**:
- Check Home Assistant logs for errors
- Verify Modbus connection is working
- Ensure `name` is configured correctly
- Restart Home Assistant after configuration changes

**Wrong values displayed**:
- Verify register scaling in `const.py`
- Check that your device uses same register mapping
- Enable debug logging to see raw register values

**Entities show "Unavailable"**:
- Check Modbus connection (network, IP, port)
- Verify device is powered on and responding
- Review logs for Modbus read errors
- Check `poll_interval` isn't too aggressive

For detailed troubleshooting, see [Troubleshooting](troubleshooting.md).