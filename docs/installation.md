# Installation

Two supported installation methods are described here: HACS (recommended) and manual.

## 1) HACS (recommended)

1. On GitHub push the repository named `ha_atrea_recuperation`.
2. In Home Assistant, open HACS → Integrations → ••• (top-right) → Custom repositories.
3. Add repository URL: `https://github.com/<your-account>/ha_atrea_recuperation`  
   Category: `Integration`
4. Install "HA Atrea Recuperation" from HACS.
5. Restart Home Assistant.
6. Add configuration to your `configuration.yaml` (see Configuration).

HACS will install the integration and (if present in manifest) automatically install the `pymodbus` dependency for the fallback.

## 2) Manual installation

1. Copy the `custom_components/ha_atrea_recuperation/` folder into your Home Assistant `custom_components/` directory.
2. If you intend to use the pymodbus fallback and your HA environment does not auto-install dependencies, install `pymodbus`:
   - For Python-based installs: `pip install pymodbus>=2.5.0` in the Home Assistant environment.
   - For Home Assistant OS / supervised: prefer installation via HACS (recommended) or ensure host Python has pymodbus available.
3. Restart Home Assistant.
4. Add configuration to `configuration.yaml` (see Configuration).

## Enabling Modbus

- Recommended: configure the official Home Assistant `modbus:` integration and point `ha_atrea_recuperation` to the Modbus hub using `modbus_hub` (see Configuration).
- Fallback: if you do not use the HA Modbus integration, set `modbus_host` and `modbus_port` in `ha_atrea_recuperation` configuration so the integration can use pymodbus.

## After installation

- Restart Home Assistant.
- Check `Configuration → Devices & Services` and look for your integration.
- Monitor Home Assistant logs for modbus connection messages and any errors.