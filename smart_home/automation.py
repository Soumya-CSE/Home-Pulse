"""Rule-based automation engine and alert evaluation.

Each rule is a plain function `rule(system)` that inspects sensor readings and
adjusts devices through `system.auto_set(...)`. Rules respect manual overrides:
if the user touched a device recently, automation leaves it alone.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Rule:
    key: str
    name: str
    description: str


def _is_night(system) -> bool:
    s = system.settings
    hour = system.sim_time.hour
    return hour >= s["night_start_hour"] or hour < s["night_end_hour"]


# ------------------------------------------------------------------------ rules
def rule_security(system) -> None:
    lock = system.devices["front_lock"]
    cam = system.devices["front_cam"]
    night = _is_night(system)
    if (night or system.mode in ("Away", "Sleep")) and not lock.on and not system.manual_active(lock):
        system.auto_set(lock, on=True, reason="Auto-locked (night / away / sleep)")
    if (night or system.mode == "Away") and not cam.on and not system.manual_active(cam):
        system.auto_set(cam, on=True, reason="Camera recording started (night / away)")
    elif system.mode == "Home" and not night and cam.on and not system.manual_active(cam):
        system.auto_set(cam, on=False, reason="Camera stopped (someone is home)")


def rule_energy_saver(system) -> None:
    if system.mode != "Away":
        return
    for dev in system.devices.values():
        if dev.type in ("light", "fan", "ac", "humidifier", "purifier") and dev.on and not system.manual_active(dev):
            system.auto_set(dev, on=False, reason="Energy saver: nobody home")


def rule_cooling(system) -> None:
    s = system.settings
    if system.mode == "Away":
        return
    for ac in system.devices_of("ac"):
        if system.mode == "Sleep" and ac.room != "Bedroom":
            continue
        if system.manual_active(ac):
            continue
        t = system.env.rooms[ac.room].temperature
        if not ac.on and t >= s["cooling_on_temp"]:
            system.auto_set(ac, on=True, value=s["cooling_target"],
                            reason=f"Auto-cooling ON ({t:.1f} °C ≥ {s['cooling_on_temp']} °C)")
        elif ac.on and t <= ac.value + s["cooling_hysteresis"]:
            system.auto_set(ac, on=False, reason=f"Auto-cooling OFF (reached {t:.1f} °C)")


def rule_lighting(system) -> None:
    s = system.settings
    if system.mode == "Away":
        return
    for light in system.devices_of("light"):
        if system.manual_active(light):
            continue
        r = system.env.rooms[light.room]
        if system.mode == "Sleep":
            if light.on:
                system.auto_set(light, on=False, reason="Sleep mode: lights off")
            continue
        if not light.on and r.motion and r.ambient_lux < s["light_lux_threshold"]:
            system.auto_set(light, on=True, reason=f"Motion in dark room ({r.ambient_lux:.0f} lux)")
        elif light.on:
            idle = (system.sim_time - system.last_motion[light.room]).total_seconds() / 60
            if idle >= s["light_off_delay_min"]:
                system.auto_set(light, on=False, reason=f"No motion for {idle:.0f} min")
            elif r.ambient_lux >= s["light_lux_threshold"] * 1.5:
                system.auto_set(light, on=False, reason="Enough daylight")


def rule_air_quality(system) -> None:
    s = system.settings
    for p in system.devices_of("purifier"):
        if system.manual_active(p):
            continue
        aqi = system.env.rooms[p.room].aqi
        if not p.on and aqi >= s["aqi_on"]:
            system.auto_set(p, on=True, reason=f"Poor air quality (AQI {aqi:.0f})")
        elif p.on and aqi <= s["aqi_off"]:
            system.auto_set(p, on=False, reason=f"Air quality recovered (AQI {aqi:.0f})")


def rule_humidity(system) -> None:
    s = system.settings
    for h in system.devices_of("humidifier"):
        if system.manual_active(h) or system.mode == "Away":
            continue
        hum = system.env.rooms[h.room].humidity
        if not h.on and hum <= s["humidity_low"]:
            system.auto_set(h, on=True, reason=f"Air too dry ({hum:.0f}%)")
        elif h.on and hum >= s["humidity_high"]:
            system.auto_set(h, on=False, reason=f"Humidity restored ({hum:.0f}%)")


RULES: list[Rule] = [
    Rule("security", "Night & away security",
         "Locks the front door and starts the camera at night, in Away mode and in Sleep mode."),
    Rule("energy", "Energy saver (Away mode)",
         "Switches off lights, fans, AC, purifiers and humidifiers when nobody is home."),
    Rule("cooling", "Smart cooling",
         "Turns an AC on above the temperature threshold and off once the target is reached."),
    Rule("lighting", "Motion lighting",
         "Lights come on with motion in a dark room and go off after a period without motion."),
    Rule("air", "Air-quality control",
         "Runs air purifiers when the AQI rises above the threshold."),
    Rule("humidity", "Humidity control",
         "Runs the humidifier when the room air becomes too dry."),
]
_RULE_FUNCS = {
    "security": rule_security,
    "energy": rule_energy_saver,
    "cooling": rule_cooling,
    "lighting": rule_lighting,
    "air": rule_air_quality,
    "humidity": rule_humidity,
}


def run_automation(system) -> None:
    for rule in RULES:
        if system.rules_enabled.get(rule.key, True):
            _RULE_FUNCS[rule.key](system)


# ----------------------------------------------------------------------- alerts
def evaluate_alerts(system) -> dict[str, dict]:
    """Return {alert_key: {level, message}} for every condition currently active."""
    s = system.settings
    alerts: dict[str, dict] = {}
    for room, r in system.env.rooms.items():
        if r.temperature >= s["alert_temp_high"]:
            alerts[f"{room}|temp"] = {"level": "warning",
                                      "message": f"{room}: very high temperature ({r.temperature:.1f} °C)"}
        if r.aqi >= s["alert_aqi_high"]:
            alerts[f"{room}|aqi"] = {"level": "warning",
                                     "message": f"{room}: unhealthy air quality (AQI {r.aqi:.0f})"}
        if r.humidity >= s["alert_humidity_high"]:
            alerts[f"{room}|hum"] = {"level": "warning",
                                     "message": f"{room}: high humidity ({r.humidity:.0f}%) - mould risk"}
        if system.mode == "Away" and r.motion:
            alerts[f"{room}|intrusion"] = {"level": "critical",
                                           "message": f"Motion detected in {room} while away!"}
    if system.total_power >= s["alert_power_high"]:
        alerts["power"] = {"level": "warning",
                           "message": f"High power consumption ({system.total_power:,.0f} W)"}
    lock = system.devices["front_lock"]
    if system.mode in ("Away", "Sleep") and not lock.on:
        alerts["lock"] = {"level": "critical", "message": f"Front door is unlocked while in {system.mode} mode"}
    return alerts
