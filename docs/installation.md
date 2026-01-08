# Installation

This guide covers two installation methods: HACS (recommended) and manual installation.

## Prerequisites

Before installing:

1. **Home Assistant** version 2021.12.0 or newer
2. **Network access** to your Atrea device via Modbus TCP (port 502)
3. **Device IP address** and network connectivity confirmed

Optional but recommended:
- **Home Assistant Modbus integration** configured (for better reliability)

## Method 1: HACS Installation (Recommended)

HACS (Home Assistant Community Store) makes installation and updates easy.

### Step 1: Add Custom Repository

1. Open Home Assistant
2. Navigate to **HACS** (in sidebar)
3. Click **Integrations**
4. Click **⋮** (three dots in top-right corner)
5. Select **Custom repositories**
6. Add repository:
   - **Repository**: `https://github.com/Chester929/ha_atrea_recuperation`
   - **Category**: `Integration`
7. Click **Add**

### Step 2: Install Integration

1. In HACS Integrations, search for "Atrea" or "HA Atrea Recuperation"
2. Click on **HA Atrea Recuperation**
3. Click **Download** (bottom-right)
4. Select latest version
5. Click **Download**
6. Wait for download to complete

### Step 3: Restart Home Assistant

1. Go to **Settings** → **System** → **Restart**
2. Click **Restart** and wait for Home Assistant to come back online

### Step 4: Configure Integration

Since this is a YAML-configured integration, you must add configuration to `configuration.yaml`:

1. Edit your `configuration.yaml` file
2. Add configuration (see [Configuration](configuration.md) for details):

   ```yaml
   # Optional but recommended: Configure HA Modbus integration
   modbus:
     - name: modbus_atrea
       type: tcp
       host: 192.168.1.50  # Your Atrea device IP
       port: 502
       timeout: 5
   
   # Add HA Atrea Recuperation integration
   ha_atrea_recuperation:
     name: "Atrea"
     modbus_hub: modbus_atrea
     unit: 1
     poll_interval: 10
   ```

3. Save the file

### Step 5: Restart Again

1. Check configuration: **Settings** → **Server Controls** → **Check Configuration**
2. If valid, restart: **Settings** → **System** → **Restart**

### Step 6: Verify Installation

1. Go to **Developer Tools** → **States**
2. Filter by your configured name (e.g., "atrea")
3. You should see multiple entities:
   - `climate.atrea`
   - `fan.atrea_fan`
   - `select.atrea_operation_mode`
   - `sensor.atrea_*` (multiple temperature, flow sensors)
   - `button.atrea_*` (reset buttons)

## Method 2: Manual Installation

Manual installation gives you direct control over the integration files.

### Step 1: Download Integration

Download the latest release from GitHub:

**Option A: Download ZIP**
1. Visit https://github.com/Chester929/ha_atrea_recuperation
2. Click **Code** → **Download ZIP**
3. Extract the ZIP file

**Option B: Git Clone**
```bash
git clone https://github.com/Chester929/ha_atrea_recuperation.git
cd ha_atrea_recuperation
```

### Step 2: Copy Files to Home Assistant

1. Locate your Home Assistant configuration directory (where `configuration.yaml` is located)
2. Create `custom_components` folder if it doesn't exist:
   ```bash
   mkdir -p /config/custom_components
   ```

3. Copy the integration folder:
   ```bash
   cp -r custom_components/ha_atrea_recuperation /config/custom_components/
   ```

4. Verify the structure:
   ```
   /config/
   ├── configuration.yaml
   └── custom_components/
       └── ha_atrea_recuperation/
           ├── __init__.py
           ├── manifest.json
           ├── const.py
           ├── hub.py
           ├── climate.py
           ├── sensor.py
           ├── fan.py
           ├── select.py
           ├── number.py
           └── button.py
   ```

### Step 3: Install Dependencies

The integration requires `pymodbus>=2.5.0`.

**For Home Assistant OS / Container / Supervised**:
- Dependencies should install automatically from `manifest.json`
- If not, they'll be installed on first use

**For Home Assistant Core (Python venv)**:
```bash
source /srv/homeassistant/bin/activate
pip install pymodbus>=2.5.0
```

### Step 4: Configure Integration

Add configuration to `configuration.yaml` (same as HACS method above):

```yaml
modbus:
  - name: modbus_atrea
    type: tcp
    host: 192.168.1.50
    port: 502
    timeout: 5

ha_atrea_recuperation:
  name: "Atrea"
  modbus_hub: modbus_atrea
  unit: 1
  poll_interval: 10
```

### Step 5: Restart Home Assistant

Restart Home Assistant to load the integration:

```bash
# Via CLI
ha core restart

# Or use UI: Settings → System → Restart
```

### Step 6: Verify Installation

Check that entities appear (same as HACS method above).

## Configuring Modbus Connection

The integration supports two Modbus connection methods. Choose the one that fits your setup.

### Recommended: Using Home Assistant Modbus Integration

**Advantages**:
- Better reliability and error handling
- Shared connection for multiple integrations
- Built-in connection pooling

**Configuration**:
```yaml
modbus:
  - name: modbus_atrea          # Give it a name
    type: tcp
    host: 192.168.1.50           # Your Atrea device IP
    port: 502
    timeout: 5
    delay: 0                     # Optional: delay between requests (seconds)

ha_atrea_recuperation:
  name: "Atrea"
  modbus_hub: modbus_atrea      # Reference the hub name
  unit: 1
  poll_interval: 10
```

### Alternative: Direct Connection with pymodbus

**When to use**:
- You don't use HA Modbus integration
- You want simpler configuration
- You only have one Modbus device

**Configuration**:
```yaml
ha_atrea_recuperation:
  name: "Atrea"
  modbus_host: 192.168.1.50     # Direct IP address
  modbus_port: 502               # Modbus TCP port
  unit: 1
  poll_interval: 10
```

## Post-Installation Steps

### 1. Check Logs

Review logs to ensure integration loaded correctly:

```yaml
# Add to configuration.yaml for detailed logging
logger:
  default: info
  logs:
    custom_components.ha_atrea_recuperation: debug
```

Check logs:
- **UI**: Settings → System → Logs
- **CLI**: `grep ha_atrea /config/home-assistant.log`

Look for:
- ✅ "HA Atrea Recuperation integration initialized"
- ✅ "HaAtreaModbusHub initialized"
- ❌ Any error messages

### 2. Verify Entities

1. Go to **Developer Tools** → **States**
2. Search for entities with your configured name
3. Verify values are reasonable:
   - Temperatures should be in normal range (-20°C to 50°C)
   - Fan percentages should be 0-100%
   - Flows should be positive values

### 3. Test Control

Try controlling the device:

1. **Climate**: Set target temperature via climate card
2. **Fan**: Change fan speed
3. **Select**: Change operation mode
4. **Button**: Press a reset button (if safe to do so)

Verify changes are reflected on the device's display (if accessible).

### 4. Add to Dashboard

Create a dashboard card for easy access:

```yaml
type: thermostat
entity: climate.atrea
```

Or use entities card:
```yaml
type: entities
entities:
  - climate.atrea
  - fan.atrea_fan
  - select.atrea_operation_mode
  - sensor.atrea_indoor_temperature
  - sensor.atrea_supply_temperature
```

## Updating the Integration

### HACS Update

1. Go to **HACS** → **Integrations**
2. Find "HA Atrea Recuperation"
3. Click **Update** if available
4. Restart Home Assistant

### Manual Update

1. Download new version from GitHub
2. Replace files in `/config/custom_components/ha_atrea_recuperation/`
3. Restart Home Assistant

**Note**: Always check the [Changelog](changelog.md) for breaking changes before updating.

## Uninstalling

### HACS Uninstall

1. Remove configuration from `configuration.yaml`
2. Restart Home Assistant
3. Go to **HACS** → **Integrations**
4. Find "HA Atrea Recuperation"
5. Click **⋮** → **Remove**
6. Restart Home Assistant again

### Manual Uninstall

1. Remove configuration from `configuration.yaml`
2. Delete folder: `/config/custom_components/ha_atrea_recuperation/`
3. Restart Home Assistant

**Note**: Entity history will be retained unless you manually delete entities from the registry.

## Troubleshooting Installation

### Integration Doesn't Load

**Check**:
1. Files are in correct location: `/config/custom_components/ha_atrea_recuperation/`
2. `manifest.json` exists and is valid JSON
3. Home Assistant was restarted after installation
4. Configuration is in `configuration.yaml`

**Fix**:
- Review Home Assistant logs for errors
- Verify file permissions (should be readable by HA user)
- Check YAML syntax in `configuration.yaml`

### Dependencies Not Installing

**Symptoms**: `ModuleNotFoundError: No module named 'pymodbus'`

**Fix**:
- For HACS: Dependencies should install automatically
- For manual: Install manually (see Step 3 in manual installation)
- Restart Home Assistant after installing dependencies

### Entities Show "Unavailable"

**Check**:
1. Modbus connection is working (see [Troubleshooting](troubleshooting.md))
2. Device IP is correct and reachable
3. Firewall allows port 502

**Fix**:
- Enable debug logging
- Check Modbus connection with external tool (`modpoll`)
- Verify network connectivity

## Getting Help

If installation fails:

1. **Check logs**: Enable debug logging and review errors
2. **Review configuration**: Ensure YAML is valid and complete
3. **Test Modbus**: Use external tool to verify device connectivity
4. **Search issues**: https://github.com/Chester929/ha_atrea_recuperation/issues
5. **Open issue**: Provide configuration (sanitized) and logs

For detailed troubleshooting, see [Troubleshooting Guide](troubleshooting.md).