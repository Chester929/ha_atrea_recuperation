# HA Atrea Recuperation

Home Assistant integration for Atrea DUPLEX recuperation units (Modbus TCP).  
This repository is HACS-ready and includes an optional pymodbus fallback.

This README is a short entry point — full documentation lives in the docs/ folder. Please see the documentation for installation, configuration, entities and troubleshooting.

Quick links
- Documentation (full): docs/index.md
- Installation: docs/installation.md
- Configuration: docs/configuration.md
- Entities & register mapping: docs/entities.md
- Troubleshooting: docs/troubleshooting.md
- Developer notes: docs/developer.md
- Changelog: docs/changelog.md

Quick start
- Install via HACS (recommended) — see docs/installation.md
- Or copy `custom_components/ha_atrea_recuperation/` into Home Assistant `custom_components/` (manual install)
- Configure the integration in `configuration.yaml` (see docs/configuration.md)
- Restart Home Assistant and check the logs if entities do not appear

Repository layout (top-level)
- custom_components/ha_atrea_recuperation/ — integration code
- docs/ — full documentation (mkdocs)
- VERSION — current release version
- scripts/ — helper scripts (bump version, pre-release checks)
- .github/workflows/ — CI workflows for checks and releases

Viewing docs locally
- Install mkdocs and material theme, then run:
  ```
  pip install mkdocs mkdocs-material
  mkdocs serve
  ```
  Open http://127.0.0.1:8000 to view the docs.

Contributing
- Please open pull requests against this repository. Run the pre-release checks (`scripts/pre_release_checks.sh`) before submitting PRs.

License
- No license file is included by default. Add a LICENSE file if you wish to permit reuse.

For details, read the documentation in docs/.