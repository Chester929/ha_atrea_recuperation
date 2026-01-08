# Troubleshooting

This page lists common problems and how to diagnose or resolve them.

## No entities appear after install

- Confirm integration is added to `configuration.yaml` and Home Assistant was restarted.
- Check Home Assistant logs (Configuration → Logs or Supervisor System Logs) for lines containing `ha_atrea_recuperation`.
- Ensure `modbus_hub` (if used) references a valid HA Modbus integration name from `configuration.yaml`.
- If using pymodbus fallback, ensure `modbus_host`/`modbus_port` are set and `pymodbus` is installed.

## Modbus read/write errors

- Verify network connectivity to the device:
  - Ping the device IP
  - Test with a Modbus tool such as `modpoll` or a simple pymodbus script
- Ensure the Modbus unit id (`unit`) matches the device (often 1).
- Confirm whether the device expects 1-based or 0-based addressing and adjust `registers` override if necessary.
- If using HA Modbus hub, ensure the hub is correctly configured and working (other Modbus entities using the hub should also work).

## pymodbus fallback not working

- Verify the `pymodbus` package is installed in the Python environment running Home Assistant (`pymodbus>=2.5.0`).
- Confirm `modbus_host` and `modbus_port` are reachable from the HA host.
- Check HA logs for pymodbus connection exceptions.

## Incorrect temperature values (wrong scale or offset)

- Device stores temperature as integer tenths of °C (scale 10). If values appear 10x too large or too small, validate the register used and the configured `scale`. Override via `registers` mapping if needed.
- Some devices use alternative encodings (float32). If your device uses float registers, open an issue or request float decoding support and provide register addresses.

## Logging and debugging

Add integration-level debug logging:

```yaml
logger:
  default: info
  logs:
    custom_components.ha_atrea_recuperation: debug
```

Restart HA and watch logs for details about register read/writes, HA Modbus hub usage, and pymodbus fallback attempts.

## Device-specific quirks

- Some devices require a pause between consecutive Modbus requests; the hub polls many registers — if your device is slow, increase `poll_interval`.
- If a read of a multi-register value returns unexpected bytes, the device may use a different word or byte ordering. Report the register pair and observed values and the integration can be extended to support configurable endianness.

If you are stuck, gather:
- HA logs (with debug as above)
- The `modbus:` configuration (if used)
- The integration config from `configuration.yaml`
- A sample of register values (tools like `modpoll` or `pymodbus` help)

Open an issue in the repository including these details and I can help debug.