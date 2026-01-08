# Developer notes

This page describes the internal architecture, coding guidance and how to extend the integration.

## Project layout

```
.
├─ hacs.json
├─ mkdocs.yml
├─ custom_components/ha_atrea_recuperation/
│  ├─ manifest.json
│  ├─ __init__.py
│  ├─ hub.py
│  ├─ climate.py
│  ├─ select.py
│  ├─ fan.py
│  ├─ sensor.py
│  ├─ number.py
│  ├─ button.py
│  └─ README.md
└─ docs/
   ├─ index.md
   ├─ installation.md
   ├─ configuration.md
   ├─ entities.md
   ├─ troubleshooting.md
   └─ developer.md
```

## Hub responsibilities

- Manage Modbus I/O (read/write/pulse)
- Prefer HA Modbus hub when configured
- Fall back to pymodbus if enabled and HA Modbus hub is not available
- Poll device registers on an interval and cache values
- Notify subscribed entities (simple callback list) when cache is updated

Key file: `hub.py`.

## Adding new sensors / registers

- Add register metadata to `__init__.py` (INPUT_REGISTERS / HOLDING_REGISTERS mappings).
- Create new entity in `__init__.py` entity list or implement dynamic creation based on mapping.
- Ensure sensor class reads from `hub.get_cached(register)` and applies scale/decoding.

## Multi-register values

- The current implementation expects:
  - 32-bit counters: low word at address N, high word at N+1 → combined as low + (high << 16).
  - Serial chars: sequential registers with ASCII integer codes combined into a string.
- For float32, implement configurable decoding with endianness options.

## Testing

- Unit tests: mock `hub.get_cached` and verify entity properties.
- Integration tests: run a local pymodbus TCP simulator or use device in test network.
- Logging: use `custom_components.ha_atrea_recuperation` logger at DEBUG level.

## Coding style

- Follow Home Assistant integration best practices: async entrypoints, non-blocking I/O (move blocking pymodbus calls to executor).
- Provide `manifest.json` with required dependencies and iot_class.
- Keep entity names stable to avoid entity registry churn.

## Contributing

- Fork the repo → create a branch → open PR.
- If you add new register mappings or translations, update documentation (docs/) and `manifest.json` if dependencies change.

## Release & HACS

- Tag releases with semver (e.g., v1.0.0).
- HACS detects updates if repository includes `hacs.json` and `manifest.json`.
- For a HACS release, create a GitHub release and optionally attach a changelog.

If you need help implementing features (UI config_flow, binary_sensor auto-generation, float32 decoding), open an issue or request a PR and I can assist.