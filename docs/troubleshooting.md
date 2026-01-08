# Troubleshooting

This page lists common problems, their causes, and how to diagnose or resolve them.

## No Entities Appear After Install

**Symptoms**: After installation and restart, no entities are visible in Home Assistant.

**Possible Causes & Solutions**:

1. **Configuration not added**
   - Verify `ha_atrea_recuperation:` section exists in `configuration.yaml`
   - Check YAML syntax (proper indentation, no tabs)
   - Run **Configuration** → **Server Controls** → **Check Configuration**

2. **Home Assistant not restarted**
   - The integration requires a full restart to load
   - Restart via **Settings** → **System** → **Restart** or restart the container/service

3. **Modbus hub reference incorrect**
   - If using `modbus_hub`, ensure the name matches exactly with your `modbus:` configuration
   - Check `modbus:` section has `name:` parameter matching your `modbus_hub` value
   - Example: If `modbus_hub: my_atrea`, ensure `modbus:` section has `- name: my_atrea`

4. **Pymodbus not installed (fallback mode)**
   - If not using `modbus_hub`, integration needs pymodbus
   - HACS installations should auto-install dependencies
   - Manual installations: `pip install pymodbus>=2.5.0` in HA environment

5. **Integration failed to load**
   - Check Home Assistant logs: **Settings** → **System** → **Logs**
   - Search for "ha_atrea_recuperation"
   - Look for error messages during startup

**Diagnostic Steps**:

1. Check configuration validation:
   ```bash
   ha core check
   ```

2. Review logs after restart:
   ```bash
   tail -f /config/home-assistant.log | grep ha_atrea
   ```

3. Verify integration is loaded:
   - Go to **Developer Tools** → **States**
   - Filter by your configured name (e.g., "atrea")
   - Should see climate, fan, select, sensors, etc.

## Modbus Read/Write Errors

**Symptoms**: Logs show Modbus connection errors, timeout errors, or register read failures. Entities show "Unavailable".

**Common Error Messages**:
- "Modbus connection failed"
- "Timeout waiting for response"
- "No response received"
- "Invalid Modbus response"

**Possible Causes & Solutions**:

1. **Network connectivity issues**
   - Ping the device IP: `ping <device_ip>`
   - Verify device is powered on and connected to network
   - Check firewall rules (Modbus TCP uses port 502)
   - Ensure Home Assistant can reach device (same VLAN, no network isolation)

2. **Wrong Modbus unit ID**
   - Most Atrea devices use unit ID 1 (default)
   - Verify your device's unit ID in device settings
   - Update `unit:` parameter in configuration if needed

3. **Device requires 0-based addressing**
   - Some Modbus devices use 0-based addressing (register 1001 → address 1000)
   - Atrea devices typically use 1-based addressing (as configured in this integration)
   - If your device differs, you may need to modify `const.py` register addresses

4. **Too aggressive polling**
   - Device may be slow to respond
   - Increase `poll_interval` (e.g., from 10 to 20 seconds)
   - Some devices need delay between consecutive requests

5. **HA Modbus hub misconfigured**
   - If using `modbus_hub`, verify the hub works with other Modbus integrations
   - Check `timeout:` setting in `modbus:` configuration (increase if needed)
   - Try adding `delay:` parameter to modbus config (e.g., `delay: 1`)

**Diagnostic Steps**:

1. Test connection with modbus tool:
   ```bash
   # Using modpoll (if installed)
   modpoll -m tcp -a 1 -r 1104 -c 1 <device_ip>
   
   # Should return indoor temperature register value
   ```

2. Enable debug logging (see section below)

3. Try fallback mode (direct connection):
   - Temporarily comment out `modbus_hub:`
   - Add `modbus_host:` and `modbus_port:` directly
   - Restart and check if connection works

## Pymodbus Fallback Not Working

**Symptoms**: Configuration uses `modbus_host` but connection still fails.

**Possible Causes & Solutions**:

1. **Pymodbus not installed**
   - Verify: `pip list | grep pymodbus` in HA environment
   - Install: `pip install pymodbus>=2.5.0`
   - For HA OS/Supervised: Use HACS (auto-installs dependencies)

2. **Host/port unreachable**
   - Verify `modbus_host` is correct IP address
   - Verify `modbus_port` (default 502)
   - Check network connectivity: `ping <modbus_host>`
   - Ensure port 502 is open (firewall, network ACLs)

3. **Device authentication required**
   - Some Modbus devices require authentication
   - Current implementation doesn't support authentication
   - May need to disable authentication in device settings

**Diagnostic Steps**:

1. Test with simple pymodbus script:
   ```python
   from pymodbus.client.sync import ModbusTcpClient
   
   client = ModbusTcpClient('<device_ip>', port=502)
   client.connect()
   result = client.read_input_registers(1104, 1, unit=1)
   print(result.registers)
   client.close()
   ```

2. Check Home Assistant logs for pymodbus import errors
3. Verify manifest.json includes pymodbus dependency

## Incorrect Temperature Values

**Symptoms**: Temperature sensors show values that are 10x too large, too small, or completely wrong.

**Possible Causes & Solutions**:

1. **Scaling factor mismatch**
   - Atrea devices store temperature as integer × 10 (e.g., 23.5°C → 235)
   - Integration divides by 10 automatically
   - If your device uses different scaling, you may see wrong values
   - Check raw register value vs displayed value in logs (debug mode)

2. **Wrong register mapping**
   - Verify register addresses in `const.py` match your device documentation
   - Different Atrea models may use different register layouts
   - Example: Some devices may use register 1500 instead of 1104 for indoor temp

3. **Float32 encoding**
   - Some devices store temperatures as IEEE 754 float32 (2 registers)
   - Current implementation expects scaled integers
   - Float32 support would require code modification

**Diagnostic Steps**:

1. Enable debug logging to see raw register values
2. Compare raw values with device display
3. Calculate expected scaling: `device_display = raw_value / scale`
4. If scale is wrong, modify `const.py` for affected registers

**Workaround**:
For quick fix, you can use HA Template sensor to adjust scaling:

```yaml
sensor:
  - platform: template
    sensors:
      adjusted_temp:
        value_template: "{{ states('sensor.atrea_villa_b_indoor_temperature') | float * 0.1 }}"
        unit_of_measurement: "°C"
```

## Entity Shows "Unavailable"

**Symptoms**: Some or all entities show "Unavailable" status.

**Possible Causes & Solutions**:

1. **Modbus communication failure** (see Modbus errors section above)

2. **Coordinator not updating**
   - Check if `poll_interval` is set correctly
   - Verify hub's `async_update` method is being called
   - Check logs for coordinator errors

3. **Register read failures**
   - Specific register may not exist on your device model
   - Enable debug logging to see which registers fail
   - Remove unsupported registers from `const.py` if needed

4. **Device offline or restarting**
   - Verify device is powered on
   - Check if device is in boot/update mode
   - Wait for device to fully start

## Entities Don't Update / Stale Data

**Symptoms**: Entity values never change or update very slowly.

**Possible Causes & Solutions**:

1. **Poll interval too long**
   - Default is 10 seconds
   - Reduce `poll_interval` for faster updates (minimum 5 seconds recommended)

2. **Coordinator not polling**
   - Check logs for coordinator update errors
   - Verify `poll_interval` configuration is valid integer

3. **Device caching values**
   - Some devices update registers only periodically
   - This is device behavior, not integration issue
   - Faster polling won't help if device doesn't update registers

## Button Press Not Working

**Symptoms**: Pressing reset buttons doesn't trigger expected action.

**Possible Causes & Solutions**:

1. **Coil pulse too short**
   - Default pulse is 500ms
   - Some devices may need longer pulse
   - Modify `write_coil_pulse` in `hub.py` to increase duration

2. **Wrong coil address**
   - Verify coil addresses in `const.py` match your device
   - Consult device documentation for correct coil addresses

3. **Coil write permission**
   - Some coils may be read-only or protected
   - Check device settings/manual

## Logging and Debugging

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.ha_atrea_recuperation: debug
    pymodbus: debug  # Optional: see low-level Modbus communication
```

Restart Home Assistant.

### View Logs

**Via UI**:
- **Settings** → **System** → **Logs**
- Search for "ha_atrea_recuperation"

**Via Command Line**:
```bash
# Tail logs in real-time
tail -f /config/home-assistant.log | grep -i atrea

# Filter for errors only
grep -i "error\|exception\|traceback" /config/home-assistant.log | grep -i atrea

# View coordinator updates
tail -f /config/home-assistant.log | grep "coordinator"
```

**Via Docker**:
```bash
docker logs -f homeassistant 2>&1 | grep atrea
```

### Useful Log Messages

When debug logging is enabled, you'll see:

- Hub initialization: Modbus connection method selected
- Register reads: Which registers were read and their values
- Coordinator updates: When polling occurs
- Entity updates: When entities receive new data
- Modbus errors: Connection failures, timeouts, invalid responses
- Write operations: When settings are changed (mode, temperature, fan speed)

Example debug output:
```
DEBUG - HaAtreaModbusHub initialized with HA Modbus hub: modbus_atrea
DEBUG - Reading input register 1104: value=235 (scaled: 23.5)
DEBUG - Coordinator update completed, 45 registers cached
DEBUG - Writing holding register 1002, value=220 (22.0°C)
```

## Device-Specific Quirks

### Slow Devices

Some Atrea units respond slowly to Modbus requests:
- Increase `poll_interval` to 15-30 seconds
- Add `delay:` to `modbus:` config (e.g., `delay: 1`)
- Reduce number of sensors if possible

### Different Register Layout

If your Atrea model uses different registers:
1. Consult your device's Modbus register map
2. Edit `custom_components/ha_atrea_recuperation/const.py`
3. Update `INPUT_REGISTERS` and `HOLDING_REGISTERS` dictionaries
4. Restart Home Assistant

### Float32 Temperature Values

If your device uses float32 encoding (uncommon):
- Current integration doesn't support float32
- Open GitHub issue with device model and register documentation
- Workaround: Use template sensors to convert values

### Multiple Recuperation Units

Current limitation: One integration instance per Home Assistant installation.

**Workarounds**:
- Run multiple HA instances (different machines/containers)
- Use HA Modbus integration directly for second unit
- Open GitHub issue to request multi-instance support

## Getting Diagnostic Information

When opening a GitHub issue, please provide:

1. **Home Assistant Version**: 
   ```
   Settings → About → Version
   ```

2. **Integration Version**:
   ```yaml
   # From manifest.json or HACS
   Version: 1.0.6
   ```

3. **Configuration** (sanitized):
   ```yaml
   ha_atrea_recuperation:
     name: "Atrea"
     modbus_hub: my_hub
     # ...
   ```

4. **Debug Logs**:
   - Enable debug logging
   - Reproduce issue
   - Capture 50-100 lines of logs around the error
   - Include startup logs showing hub initialization

5. **Device Information**:
   - Atrea model (e.g., "DUPLEX 390")
   - Firmware version (if known)
   - Network setup (direct Ethernet, WiFi bridge, etc.)

6. **Steps to Reproduce**:
   - Exact steps to trigger the issue
   - Expected vs actual behavior
   - Screenshots if UI-related

## Still Stuck?

If none of the above helps:

1. **Search existing issues**: https://github.com/Chester929/ha_atrea_recuperation/issues
2. **Open new issue**: https://github.com/Chester929/ha_atrea_recuperation/issues/new
3. **Provide diagnostic info** as listed above
4. **Be patient**: Maintainer will respond when available

For general Home Assistant questions (not specific to this integration):
- Home Assistant Community: https://community.home-assistant.io/
- Home Assistant Discord: https://discord.gg/home-assistant