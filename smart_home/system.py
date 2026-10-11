"""HomeSystem: ties simulator, devices, automation, alerts and storage together."""
from __future__ import annotations

import random
import time
import uuid
from collections import deque
from datetime import datetime, timedelta

import pandas as pd

from .automation import RULES, evaluate_alerts, run_automation
from .config import BASE_LOAD_W, DEFAULT_SETTINGS, MANUAL_OVERRIDE_MIN, MODES, ROOMS
from .database import Database
from .devices import Device, default_devices
from .environment import Environment


class HomeSystem:
    def __init__(self, db: Database | None = None, warmup_steps: int = 24, seed: int | None = None):
        self.rng = random.Random(seed)
        self.run_id = uuid.uuid4().hex[:8]
        self.db = db or Database()
        self.devices: dict[str, Device] = {d.id: d for d in default_devices()}
        self.settings = dict(DEFAULT_SETTINGS)
        self.rules_enabled = {r.key: True for r in RULES}
        self.automation_enabled = True
        self.mode = "Home"
        now = datetime.now().replace(second=0, microsecond=0)
        self.sim_time = now - timedelta(minutes=5 * warmup_steps)
        self.env = Environment(self.rng)
        self.history: deque = deque(maxlen=300)
        self.events: deque = deque(maxlen=200)
        self.active_alerts: dict[str, dict] = {}
        self.last_motion = {room: self.sim_time for room in ROOMS}
        self.energy_kwh = 0.0
        self.total_power = BASE_LOAD_W
        self.last_wall_tick = 0.0
        self.log("System", "Smart home system started", "info")
        for _ in range(warmup_steps):          # pre-fill charts with a couple of hours of data
            self.tick(5)

    # --------------------------------------------------------------- device API
    def devices_of(self, dtype: str) -> list[Device]:
        return [d for d in self.devices.values() if d.type == dtype]

    def devices_in(self, room: str) -> list[Device]:
        return [d for d in self.devices.values() if d.room == room]

    def manual_active(self, dev: Device) -> bool:
        return dev.manual_until is not None and self.sim_time < dev.manual_until

    def room_power(self, room: str) -> float:
        return sum(d.power_w() for d in self.devices_in(room))

    def set_device(self, dev_id: str, on: bool | None = None, value: float | None = None) -> None:
        """Manual (user) change. Automation will leave this device alone for a while."""
        dev = self.devices[dev_id]
        parts = []
        if on is not None and on != dev.on:
            dev.on = on
            parts.append(f"turned {dev.state_label.upper()}" if dev.type in ("lock", "camera")
                         else f"turned {'ON' if on else 'OFF'}")
        if value is not None and value != dev.value:
            dev.value = value
            parts.append(f"set to {self._fmt_value(dev)}")
        if parts:
            dev.manual_until = self.sim_time + timedelta(minutes=MANUAL_OVERRIDE_MIN)
            self.log("Manual", f"{dev.room} · {dev.name} {' and '.join(parts)} by user", "info")

    def auto_set(self, dev: Device, on: bool | None = None, value: float | None = None, reason: str = "") -> None:
        """Change made by an automation rule."""
        if on is not None:
            dev.on = on
        if value is not None:
            dev.value = value
        state = dev.state_label.upper()
        self.log("Automation", f"{dev.room} · {dev.name} → {state}: {reason}", "info")

    @staticmethod
    def _fmt_value(dev: Device) -> str:
        if dev.type == "light":
            return f"{dev.value:.0f}% brightness"
        if dev.type == "fan":
            return {1: "Low", 2: "Medium", 3: "High"}.get(int(dev.value), str(dev.value)) + " speed"
        if dev.type == "ac":
            return f"{dev.value:.1f} °C"
        return str(dev.value)

    def bulk(self, action: str) -> None:
        if action == "lights_off":
            for d in self.devices_of("light"):
                self.set_device(d.id, on=False)
        elif action == "lock":
            self.set_device("front_lock", on=True)
        elif action == "all_off":
            for d in self.devices.values():
                if d.type not in ("lock", "camera"):
                    self.set_device(d.id, on=False)

    # ------------------------------------------------------------ mode / events
    def set_mode(self, mode: str) -> None:
        if mode in MODES and mode != self.mode:
            old, self.mode = self.mode, mode
            self.log("System", f"Home mode changed: {old} → {mode}", "info")

    def trigger(self, scenario: str) -> str:
        """Inject a test scenario. Returns a short message for the UI."""
        t = self.sim_time
        if scenario == "heat_wave":
            self.env.heat_wave_until = t + timedelta(hours=3)
            self.log("Scenario", "Heat wave started (+6 °C outdoors for 3 h)", "warning")
            return "Heat wave started"
        if scenario == "pollution":
            self.env.pollution_until = t + timedelta(hours=2)
            self.log("Scenario", "Air pollution spike started (2 h)", "warning")
            return "Pollution spike started"
        if scenario == "dry":
            self.env.dry_until = t + timedelta(hours=3)
            self.log("Scenario", "Dry spell started (3 h)", "warning")
            return "Dry spell started"
        if scenario == "intruder":
            if self.mode != "Away":
                return "Switch to Away mode first"
            self.env.intruder_until = t + timedelta(minutes=30)
            self.log("Scenario", "Simulated intruder at the entrance", "critical")
            return "Intruder simulated"
        return "Unknown scenario"

    def log(self, category: str, message: str, level: str = "info") -> None:
        self.events.appendleft({"time": self.sim_time, "category": category, "level": level, "message": message})
        self.db.log_event(self.run_id, self.sim_time, category, level, message)

    # --------------------------------------------------------------------- tick
    def tick(self, minutes: int = 10) -> None:
        self.sim_time += timedelta(minutes=minutes)
        self.env.step(self, minutes)
        for room, state in self.env.rooms.items():
            if state.motion:
                self.last_motion[room] = self.sim_time
        if self.automation_enabled:
            run_automation(self)
        self.total_power = BASE_LOAD_W + sum(d.power_w() for d in self.devices.values())
        self.energy_kwh += self.total_power * minutes / 60 / 1000
        self._update_alerts()
        snap = self.snapshot()
        self.history.append(snap)
        self.db.log_snapshot(self.run_id, snap)
        self.last_wall_tick = time.time()

    def _update_alerts(self) -> None:
        current = evaluate_alerts(self)
        for key, alert in current.items():
            if key not in self.active_alerts:
                self.log("Alert", alert["message"], alert["level"])
        for key, alert in self.active_alerts.items():
            if key not in current:
                self.log("Alert", f"Resolved: {alert['message']}", "info")
        self.active_alerts = current

    def snapshot(self) -> dict:
        return {
            "time": self.sim_time,
            "mode": self.mode,
            "power": self.total_power,
            "energy_kwh": self.energy_kwh,
            "outdoor_temp": self.env.outdoor_temp,
            "rooms": {
                room: {
                    "temperature": s.temperature,
                    "humidity": s.humidity,
                    "aqi": s.aqi,
                    "lux": s.lux,
                    "motion": s.motion,
                    "power": self.room_power(room),
                }
                for room, s in self.env.rooms.items()
            },
        }

    # ---------------------------------------------------------------- analytics
    def room_history(self, room: str) -> pd.DataFrame:
        rows = [{"time": s["time"], **s["rooms"][room]} for s in self.history]
        return pd.DataFrame(rows)

    def power_history(self) -> pd.DataFrame:
        return pd.DataFrame([{"time": s["time"], "power": s["power"]} for s in self.history])
