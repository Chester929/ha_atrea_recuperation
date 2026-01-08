"""Constants for HA Atrea Recuperation integration."""

# Input registers (read-only) with scale and unit (subset shown; hub polls a larger list)
INPUT_REGISTERS = {
    1001: {"name": "Mode (input)", "scale": 1, "unit": None},
    1002: {"name": "Desired temperature (input)", "scale": 10, "unit": "°C"},
    1101: {"name": "Outdoor temperature", "scale": 10, "unit": "°C"},
    1102: {"name": "Supply temperature", "scale": 10, "unit": "°C"},
    1103: {"name": "Extract temperature", "scale": 10, "unit": "°C"},
    1104: {"name": "Indoor temperature", "scale": 10, "unit": "°C"},
    1105: {"name": "Return temperature", "scale": 10, "unit": "°C"},
    1107: {"name": "Supply fan power", "scale": 1, "unit": "%"},
    1108: {"name": "Extract fan power", "scale": 1, "unit": "%"},
    1109: {"name": "Supply flow", "scale": 0.1, "unit": "m³/h"},
    1110: {"name": "Extract flow", "scale": 0.1, "unit": "m³/h"},
    1111: {"name": "Fresh air flow", "scale": 0.1, "unit": "m³/h"},
    # serial chars and hour counters will be decoded by the hub/sensor
    3000: {"name": "SN char 1", "scale": 1, "unit": None},
    3001: {"name": "SN char 2", "scale": 1, "unit": None},
    3002: {"name": "SN char 3", "scale": 1, "unit": None},
    3003: {"name": "SN char 4", "scale": 1, "unit": None},
    3004: {"name": "SN char 5", "scale": 1, "unit": None},
    3005: {"name": "SN char 6", "scale": 1, "unit": None},
    3006: {"name": "SN char 7", "scale": 1, "unit": None},
    3007: {"name": "SN char 8", "scale": 1, "unit": None},
    3008: {"name": "SN char 9", "scale": 1, "unit": None},
    3200: {"name": "M1 hours (low)", "scale": 1, "unit": "h"},
    3201: {"name": "M1 hours (high)", "scale": 1, "unit": None},
    3202: {"name": "M2 hours (low)", "scale": 1, "unit": "h"},
    3203: {"name": "M2 hours (high)", "scale": 1, "unit": None},
    3204: {"name": "UV hours (low)", "scale": 1, "unit": "h"},
    3205: {"name": "UV hours (high)", "scale": 1, "unit": None},
    7103: {"name": "Trigger WC+upper bath", "scale": 1, "unit": None},
    7104: {"name": "Trigger WC+lower bath", "scale": 1, "unit": None},
    7105: {"name": "Trigger technical room", "scale": 1, "unit": None},
}

# Holding registers (read/write where appropriate)
HOLDING_REGISTERS = {
    1001: {"name": "Mode (holding)", "scale": 1, "unit": None},
    1002: {"name": "Desired temperature (holding)", "scale": 10, "unit": "°C"},
    1003: {"name": "Selected zone (holding)", "scale": 1, "unit": None},
    1004: {"name": "Desired power (holding)", "scale": 1, "unit": "%"},
    1005: {"name": "Desired ventilation power", "scale": 0.1, "unit": "m³/h"},
    1006: {"name": "Desired supply power", "scale": 0.1, "unit": "m³/h"},
    1500: {"name": "Indoor temperature (holding)", "scale": 10, "unit": "°C"},
    1501: {"name": "Outdoor temperature (holding)", "scale": 10, "unit": "°C"},
    3189: {"name": "Active calendar", "scale": 1, "unit": None},
    3190: {"name": "Active scene", "scale": 1, "unit": None},
}

COILS = {
    7001: "Example function",
    8000: "reset_states",
    8001: "reset_filters",
    8002: "reset_uv",
}
