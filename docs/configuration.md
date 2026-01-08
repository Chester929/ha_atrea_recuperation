# Configuration

ha_atrea_recuperation is YAML-configured via `configuration.yaml`. The integration supports two Modbus connection methods:

1. **Recommended**: Reuse Home Assistant's official Modbus integration
2. **Fallback**: Use pymodbus for direct TCP connection

## Example configuration (complete)

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
  name: "Atrea Villa B"
  modbus_hub: modbus_atrea           # Recommended: reuse HA Modbus hub
  unit: 1                             # Modbus unit id (slave)
  poll_interval: 10                   # polling interval in seconds

  # Optional: override operation mode labels (Select entity options)
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

## Fallback configuration (without HA Modbus integration)

If you don't use Home Assistant's Modbus integration, you can configure direct connection:

```yaml
ha_atrea_recuperation:
  name: "Atrea Villa B"
  modbus_host: 192.168.1.50          # Direct IP address
  modbus_port: 502                    # Modbus TCP port
  unit: 1
  poll_interval: 10
```

**Note**: The integration will automatically use pymodbus if `modbus_hub` is not provided or not found.

## Configuration options explained

### Required Options

- **`name`** (string): Friendly integration/device name used as prefix for all entity names. This will appear in entity IDs (lowercased with underscores).

### Modbus Connection (choose one method)

**Method 1 (Recommended)**: Use Home Assistant Modbus integration
- **`modbus_hub`** (string): Name of an existing Home Assistant Modbus hub from your `modbus:` configuration. When specified, the integration uses the HA Modbus hub for all register reads/writes.

**Method 2**: Direct pymodbus connection
- **`modbus_host`** (string): IP address or hostname of the Atrea device
- **`modbus_port`** (integer, default: 502): Modbus TCP port

*Note*: Either `modbus_hub` OR `modbus_host` must be provided.

### Optional Settings

- **`unit`** (integer, default: 1): Modbus slave/unit ID. Most Atrea devices use unit ID 1.

- **`poll_interval`** (integer, default: 10): Polling interval in seconds. The integration reads all registers at this interval. Increase if your device is slow or network is unreliable. Decrease for faster updates (minimum recommended: 5 seconds).

- **`hvac_mode_labels`** (mapping): Custom labels for the operation mode Select entity. Maps mode indices (0-8) to string labels. Default is English labels. Use this to translate or customize mode names.

## Platform Configuration

The integration automatically creates entities for all platforms based on the code:

- **Climate**: Single climate entity for thermostat control
- **Sensor**: All registers defined in `const.py` (INPUT_REGISTERS and HOLDING_REGISTERS)
- **Fan**: Single fan entity for percentage control
- **Select**: Single select entity for operation mode
- **Number**: Single number entity for target temperature
- **Button**: One button per coil defined in `const.py` (reset actions)

No additional platform configuration is required. All entities are created automatically.

## Register Decoding

The integration automatically decodes register values:

- **Temperatures**: Register value ÷ 10 → °C
- **Airflows**: Register value ÷ 10 → m³/h  
- **Percentages**: Register value as-is → %
- **32-bit counters** (operating hours): Combines two consecutive registers (low + high×65536) → hours
- **Serial number**: Converts registers 3000-3008 from integer ASCII codes → string

## Advanced: Custom Register Mapping

Currently, register addresses are defined in `custom_components/ha_atrea_recuperation/const.py`. To modify register mappings:

1. Edit the `const.py` file (requires manual file modification)
2. Update `INPUT_REGISTERS`, `HOLDING_REGISTERS`, or `COILS` dictionaries
3. Restart Home Assistant

Example `const.py` modification for new sensor:

```python
INPUT_REGISTERS = {
    # ... existing registers ...
    1999: {"name": "My Custom Sensor", "scale": 10, "unit": "°C"},
}
```

**Note**: Future versions may support register overrides via YAML configuration.

## Example Configurations for Different Scenarios

### Scenario 1: Single Atrea unit with HA Modbus

```yaml
modbus:
  - name: atrea_modbus
    type: tcp
    host: 192.168.1.100
    port: 502
    timeout: 5
    delay: 0

ha_atrea_recuperation:
  name: "Atrea"
  modbus_hub: atrea_modbus
  unit: 1
  poll_interval: 10
```

### Scenario 2: Multiple Atrea units (different IPs)

```yaml
modbus:
  - name: atrea_unit1
    type: tcp
    host: 192.168.1.100
    port: 502
  - name: atrea_unit2
    type: tcp
    host: 192.168.1.101
    port: 502

# Note: Currently only one instance supported per HA installation
# Use the first unit
ha_atrea_recuperation:
  name: "Atrea Unit 1"
  modbus_hub: atrea_unit1
  unit: 1
  poll_interval: 10
```

**Limitation**: The current implementation supports only one integration instance. For multiple units, you would need to install separate HA instances or wait for multi-instance support in future versions.

### Scenario 3: Fast polling with custom labels

```yaml
modbus:
  - name: atrea_modbus
    type: tcp
    host: 192.168.1.50
    port: 502

ha_atrea_recuperation:
  name: "Atrea RD5"
  modbus_hub: atrea_modbus
  unit: 1
  poll_interval: 5      # Poll every 5 seconds for faster updates
  
  hvac_mode_labels:
    0: "Vypnuto"
    1: "Automaticky"
    2: "Větrání"
    3: "Cirkulace s větráním"
    4: "Cirkulace"
    5: "Noční předchlazení"
    6: "Balancování"
    7: "Přetlak"
    8: "Nedefinováno"
```

## Validation

After adding configuration:

1. Check Home Assistant configuration: **Configuration** → **Server Controls** → **Check Configuration**
2. Review logs for any errors
3. Restart Home Assistant
4. Check that entities appear in **Developer Tools** → **States**
5. Filter by your configured `name` (e.g., search for "atrea" if name is "Atrea Villa B")

Expected entities (if name is "Atrea Villa B"):
- `climate.atrea_villa_b`
- `fan.atrea_villa_b_fan`
- `select.atrea_villa_b_operation_mode`
- `number.atrea_villa_b_target_temperature`
- `sensor.atrea_villa_b_*` (multiple temperature, flow, and counter sensors)
- `button.atrea_villa_b_*` (reset buttons)

## Troubleshooting Configuration

**Configuration not loading**: 
- Verify YAML syntax (indentation must be consistent, use spaces not tabs)
- Check `configuration.yaml` has `ha_atrea_recuperation:` section
- Review Home Assistant logs after restart

**Modbus connection errors**:
- If using `modbus_hub`, ensure the hub name matches your `modbus:` configuration exactly
- If using `modbus_host`, verify IP address is correct and device is reachable
- Check that pymodbus is installed (should be automatic with HACS)

**Entities not appearing**:
- Check that Home Assistant was restarted after adding configuration
- Review logs for errors: `grep ha_atrea_recuperation home-assistant.log`
- Verify Modbus connection is working (check HA Modbus integration if used)

For more troubleshooting, see [Troubleshooting](troubleshooting.md).