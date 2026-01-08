## v1.0.6 — 2026-01-08

**Major refactor: Platform-based architecture (PR #2)**

This release includes a significant architectural improvement to use Home Assistant's platform-based entity registration system.

**Changes:**
- Refactored all platforms to use `async_setup_platform` instead of direct entity creation
- Improved coordinator integration for better state management
- Enhanced reliability of entity registration during Home Assistant startup
- Better separation of concerns between platforms (climate, sensor, fan, select, number, button)
- All platforms now properly use DataUpdateCoordinator for state updates
- Fixed AttributeError issues in async_setup by implementing proper platform discovery

**Technical details:**
- Integration now uses `discovery.async_load_platform` in `__init__.py` to load platforms
- Each platform file implements `async_setup_platform(hass, config, async_add_entities, discovery_info)`
- Coordinator and hub are stored in `hass.data[DOMAIN]` for platform access
- All entities extend CoordinatorEntity for automatic update handling

**User impact:**
- More reliable entity registration
- Entities should appear more consistently after HA restart
- Better performance with reduced polling overhead
- No configuration changes required — existing configurations continue to work

## v1.0.5 — 2026-01-08

- rm unnecessary files for now (8bdb53d) — Miroslav Mudrik
- Make lint happy (0a842a8) — Miroslav Mudrik

## v1.0.4 — 2026-01-08

- No user-facing changes (internal or none).


## v1.0.3 — 2026-01-08

- Fix bump ver (bca01a3) — Miroslav Mudrik
- Change rules (463f911) — Miroslav Mudrik
- Change GITHUB_TOKEN to PERSONAL_ACCESS_TOKEN (1607722) — Miroslav Mudrik
- Update readme (c4efdb4) — Miroslav Mudrik
- CLIs (de2c698) — Miroslav Mudrik
- Add versioning (f3b7683) — Miroslav Mudrik
- update readme (3279a2d) — Miroslav Mudrik



## v1.0.2 — 2026-01-08

- Change rules (463f911) — Miroslav Mudrik
- Change GITHUB_TOKEN to PERSONAL_ACCESS_TOKEN (1607722) — Miroslav Mudrik
- Update readme (c4efdb4) — Miroslav Mudrik
- CLIs (de2c698) — Miroslav Mudrik
- Add versioning (f3b7683) — Miroslav Mudrik
- update readme (3279a2d) — Miroslav Mudrik



# Changelog

All notable changes to this project are documented here.

## v1.0.1 — initial HACS-ready release
- Added HACS metadata (`hacs.json`) and mkdocs site skeleton.
- Integration created under `custom_components/ha_atrea_recuperation`.
- Hub prefers Home Assistant Modbus integration, with pymodbus fallback for Modbus TCP.
- Entities: climate, select (operation mode), fan, number (target temp), sensors, buttons (coil pulses).
- Serial number decoding and 32-bit motohours decoding implemented.
- README moved to repo root and expanded.

(For subsequent releases, tag commits and add the release notes here.)