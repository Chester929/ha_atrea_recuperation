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