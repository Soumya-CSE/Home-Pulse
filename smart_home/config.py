"""Static configuration for the Smart Home Monitoring & Automation System."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "smart_home.db"

ROOMS = ["Living Room", "Bedroom", "Kitchen", "Bathroom"]
ROOM_ICONS = {"Living Room": "🛋️", "Bedroom": "🛏️", "Kitchen": "🍳", "Bathroom": "🚿"}

MODES = ["Home", "Away", "Sleep"]
MODE_ICONS = {"Home": "🏠", "Away": "🚪", "Sleep": "🌙"}

TYPE_ICONS = {
    "light": "💡",
    "fan": "🌀",
    "ac": "❄️",
    "purifier": "🌫️",
    "humidifier": "💧",
    "lock": "🔒",
    "camera": "📷",
}

BASE_LOAD_W = 90            # fridge, router, standby loads (always on)
MANUAL_OVERRIDE_MIN = 60    # simulated minutes automation leaves a hand-operated device alone

# Tunable automation / alert thresholds (editable from the dashboard)
DEFAULT_SETTINGS = {
    "cooling_on_temp": 29.0,
    "cooling_target": 24.0,
    "cooling_hysteresis": 0.5,
    "light_lux_threshold": 150,
    "light_off_delay_min": 15,
    "aqi_on": 100,
    "aqi_off": 60,
    "humidity_low": 45,
    "humidity_high": 65,
    "night_start_hour": 23,
    "night_end_hour": 5,
    "alert_temp_high": 34.0,
    "alert_aqi_high": 150,
    "alert_humidity_high": 85,
    "alert_power_high": 2500,
}

# (key, label, min, max, step, group) - min/max/step share the type of the default
SETTINGS_SPEC = [
    ("cooling_on_temp", "Turn AC on above (°C)", 24.0, 38.0, 0.5, "Climate"),
    ("cooling_target", "AC target temperature (°C)", 18.0, 28.0, 0.5, "Climate"),
    ("cooling_hysteresis", "AC switch-off margin (°C)", 0.1, 2.0, 0.1, "Climate"),
    ("light_lux_threshold", "Room is 'dark' below (lux)", 20, 500, 10, "Lighting"),
    ("light_off_delay_min", "Lights off after no motion (min)", 5, 60, 5, "Lighting"),
    ("aqi_on", "Purifier on above (AQI)", 50, 200, 5, "Air quality"),
    ("aqi_off", "Purifier off below (AQI)", 20, 100, 5, "Air quality"),
    ("humidity_low", "Humidifier on below (%)", 25, 60, 1, "Humidity"),
    ("humidity_high", "Humidifier off above (%)", 50, 80, 1, "Humidity"),
    ("night_start_hour", "Night security starts (hour)", 18, 23, 1, "Security"),
    ("night_end_hour", "Night security ends (hour)", 3, 9, 1, "Security"),
    ("alert_temp_high", "Alert: temperature above (°C)", 28.0, 45.0, 0.5, "Alerts"),
    ("alert_aqi_high", "Alert: AQI above", 80, 300, 10, "Alerts"),
    ("alert_humidity_high", "Alert: humidity above (%)", 65, 95, 1, "Alerts"),
    ("alert_power_high", "Alert: total power above (W)", 500, 6000, 100, "Alerts"),
]
