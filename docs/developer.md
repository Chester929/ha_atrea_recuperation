# Developer notes

This page describes the internal architecture, coding guidance and how to extend the integration.

## Architecture Overview

Since version 1.0.6, the integration uses Home Assistant's platform-based architecture with `async_setup_platform` for all entity types. This provides better reliability and follows Home Assistant best practices.

### Component Initialization Flow

1. **`__init__.py:async_setup()`** - Main entry point
   - Reads YAML configuration from `configuration.yaml`
   - Creates `HaAtreaModbusHub` instance
   - Creates `DataUpdateCoordinator` with hub's `async_update` method
   - Performs initial coordinator refresh
   - Stores hub, coordinator, name, and config in `hass.data[DOMAIN]`
   - Loads all platforms using `discovery.async_load_platform`

2. **Platform Loading** - For each platform (climate, sensor, fan, select, number, button):
   - `discovery.async_load_platform` triggers platform discovery
   - Platform's `async_setup_platform` is called
   - Platform retrieves hub and coordinator from `hass.data[DOMAIN]`
   - Platform creates entities and calls `async_add_entities`

3. **Entity Updates**:
   - Coordinator polls hub at configured interval
   - Hub reads registers via Modbus (HA integration or pymodbus)
   - Coordinator notifies all CoordinatorEntity instances
   - Entities update their state from coordinator data

## Project layout

```
.
├─ hacs.json              # HACS metadata
├─ mkdocs.yml             # Documentation configuration
├─ VERSION                # Current version (1.1.0)
├─ requirements.txt       # Python dependencies
├─ scripts/               # Helper scripts
│  ├─ bump_version.sh    # Version bumping utility
│  └─ pre_release_checks.sh  # Pre-release validation
├─ custom_components/ha_atrea_recuperation/
│  ├── manifest.json      # Integration metadata and dependencies
│  ├── __init__.py        # Main integration setup, coordinator creation
│  ├── const.py           # Register definitions (INPUT_REGISTERS, HOLDING_REGISTERS, COILS)
│  ├── hub.py             # Modbus I/O hub with HA/pymodbus support
│  ├── climate.py         # Climate platform (async_setup_platform)
│  ├── sensor.py          # Sensor platform (async_setup_platform)
│  ├── fan.py             # Fan platform (async_setup_platform)
│  ├── select.py          # Select platform (async_setup_platform)
│  ├── number.py          # Number platform (async_setup_platform)
│  └── button.py          # Button platform (async_setup_platform)
└─ docs/                  # MkDocs documentation
   ├─ index.md
   ├─ installation.md
   ├─ configuration.md
   ├─ entities.md
   ├─ troubleshooting.md
   ├─ developer.md
   └─ changelog.md
```

## Key Components

### Hub (`hub.py`)

**Class**: `HaAtreaModbusHub`

Responsibilities:
- Manage Modbus I/O (read input/holding registers, write holdings, pulse coils)
- Prefer Home Assistant Modbus hub when configured (`modbus_hub` parameter)
- Fall back to pymodbus `ModbusTcpClient` if enabled and HA Modbus not available
- Poll device registers on interval and cache values in dictionary
- Provide methods: `async_update()`, `read_input()`, `read_holding()`, `write_holding()`, `write_coil_pulse()`
- Cache register values for entity access

### Coordinator (`__init__.py`)

**Class**: `DataUpdateCoordinator`

- Created in `async_setup` with hub's `async_update` as the update method
- Polls at interval specified by `poll_interval` configuration
- Stores cached register values in `coordinator.data` (dictionary)
- Automatically notifies all subscribed CoordinatorEntity instances

### Platform Files

Each platform implements the required `async_setup_platform` function:

```python
async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the [platform] platform."""
    # Retrieve shared resources from hass.data
    hub = hass.data[DOMAIN]["hub"]
    coordinator = hass.data[DOMAIN]["coordinator"]
    name = hass.data[DOMAIN]["name"]
    
    # Create entities
    entities = [...]
    
    # Register entities
    async_add_entities(entities)
```

**Entity Base Class Pattern**:
All entities extend `CoordinatorEntity` for automatic updates:

```python
class MyEntity(CoordinatorEntity, EntityType):
    def __init__(self, coordinator, hub, name, ...):
        super().__init__(coordinator)
        self._hub = hub
        self._name = name
        # ...
    
    @property
    def some_property(self):
        # Access cached data from coordinator
        value = self.coordinator.data.get(register_address)
        return process_value(value)
```

## Adding New Sensors / Registers

1. **Add register metadata to `const.py`**:

```python
INPUT_REGISTERS = {
    1234: {"name": "New Sensor", "scale": 10, "unit": "°C"},
    # ...
}
```

2. **Sensor is automatically created** by `sensor.py` which iterates over all INPUT_REGISTERS and HOLDING_REGISTERS

3. **For custom decoding** (e.g., multi-register values):
   - Modify `sensor.py` to add special-case entity
   - Or extend `HaAtreaSensor` class with custom value property

## Multi-register values

Current implementation supports:

- **32-bit counters**: Low word at address N, high word at N+1 → combined as `low + (high << 16)`
- **Serial number**: Sequential registers (3000-3008) with ASCII integer codes → decoded to string
- **Scaled values**: Single register divided by scale factor (e.g., temperature ÷ 10)

For float32 or other formats, implement custom decoding in the sensor entity class.

## Adding New Platforms

To add a new entity platform (e.g., `binary_sensor`):

1. Create `custom_components/ha_atrea_recuperation/binary_sensor.py`
2. Implement `async_setup_platform` function
3. Create entity classes extending `CoordinatorEntity` and `BinarySensorEntity`
4. Add platform to the list in `__init__.py:async_setup`:

```python
for platform in ("climate", "sensor", "select", "fan", "number", "button", "binary_sensor"):
    hass.async_create_task(
        discovery.async_load_platform(hass, platform, DOMAIN, {}, config)
    )
```

5. Update `hacs.json` domains list

## Testing

### Integration Testing

Test with actual hardware or Modbus simulator:

1. Set up test Home Assistant instance
2. Configure integration with debug logging:
   ```yaml
   logger:
     logs:
       custom_components.ha_atrea_recuperation: debug
   ```
3. Verify all entities appear and update correctly
4. Test all services (climate, fan, select, number, button)
5. Check logs for errors or warnings

### Unit Testing

Currently focused on integration testing. For unit tests:

- Mock `hub.get_cached(register)` and `coordinator.data`
- Verify entity properties return expected values
- Test write operations call hub methods correctly

### Modbus Simulator

For development without hardware, use `pymodbus` simulator:

```python
from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock

# Set up data store with test values
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0]*100),
    co=ModbusSequentialDataBlock(0, [0]*100),
    hr=ModbusSequentialDataBlock(0, [0]*10000),
    ir=ModbusSequentialDataBlock(0, [0]*10000)
)
context = ModbusServerContext(slaves=store, single=True)

# Start simulator on port 5020
StartTcpServer(context, address=("0.0.0.0", 5020))
```

## Coding Style

Follow Home Assistant integration best practices:

- **Async everywhere**: Use `async def` for all I/O operations
- **Non-blocking I/O**: Move blocking pymodbus calls to executor if needed
- **Coordinator pattern**: Use DataUpdateCoordinator for polling
- **CoordinatorEntity**: Extend for automatic update handling
- **Type hints**: Use Python type annotations
- **Logging**: Use module logger, appropriate levels (debug, info, warning, error)
- **Entity naming stability**: Keep entity IDs stable to avoid registry churn
- **Unique IDs**: Provide `unique_id` for all entities

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test thoroughly (integration testing with device)
5. Run pre-release checks: `bash scripts/pre_release_checks.sh`
6. Commit with clear messages
7. Push and open a pull request

### Pull Request Guidelines

- Describe the problem being solved
- Explain the solution approach
- List testing performed (device model, HA version)
- Update documentation if adding features
- Update `manifest.json` if dependencies change
- Add entry to `docs/changelog.md`

## Release Process & HACS

1. Update `VERSION` file with new semantic version (e.g., `1.2.0`)
2. Update `custom_components/ha_atrea_recuperation/manifest.json` version
3. Add release notes to `docs/changelog.md`
4. Run `bash scripts/bump_version.sh` to sync versions
5. Commit changes: `git commit -m "Bump version to 1.2.0"`
6. Tag release: `git tag v1.2.0`
7. Push with tags: `git push && git push --tags`
8. Create GitHub release from tag with changelog

HACS will automatically detect updates if:
- Repository has `hacs.json` (✓)
- Repository has `manifest.json` in integration folder (✓)
- Releases are properly tagged

## Extending the Integration

### Adding Config Flow (UI Configuration)

Currently YAML-only. To add UI configuration:

1. Create `config_flow.py` implementing `ConfigFlow`
2. Add translations in `translations/en.json`
3. Update `manifest.json` to add `"config_flow": true`
4. Implement `async_step_user` for UI flow
5. Store config in `ConfigEntry` instead of YAML
6. Refactor `async_setup` to `async_setup_entry`

### Adding Services

To expose custom services:

1. Define service schema in `__init__.py`
2. Register service with `hass.services.async_register`
3. Implement service handler
4. Add service documentation to `services.yaml`
5. Update README and docs with service examples

### Float32 Register Support

To support float32 registers:

1. Add float decoding in `hub.py`:
   ```python
   import struct
   
   def decode_float32(low_word, high_word):
       bytes_val = struct.pack('>HH', high_word, low_word)
       return struct.unpack('>f', bytes_val)[0]
   ```
2. Add configuration for float registers in `const.py`
3. Update sensor to use float decoder for specified registers

## Need Help?

For questions about implementation:

- Check existing code for patterns
- Review Home Assistant developer docs: https://developers.home-assistant.io/
- Open an issue or discussion on GitHub
- Reference similar integrations for examples

For feature requests:
- Open an issue describing the use case
- Provide device register documentation if adding new registers
- Test with your device and share findings