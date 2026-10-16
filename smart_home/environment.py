"""Physics-flavoured simulator that produces sensor readings for each room.

Temperature, humidity, air quality, light and motion all follow simple, believable
dynamics: a day/night outdoor cycle, an occupant who moves between rooms, and
devices (AC, fans, purifiers, humidifiers, lights) that push readings around.
"""
from __future__ import annotations 
import math
import random
from dataclasses import dataclass
from datetime import timedelta

from .config import ROOMS

WINDOW_FACTOR = {"Living Room": 1.0, "Bedroom": 0.8, "Kitchen": 0.9, "Bathroom": 0.25}


def approach(current: float, target: float, rate: float, dt: float) -> float:
    """Move `current` towards `target` exponentially (rate per minute, dt minutes)."""
    return current + (target - current) * (1 - math.exp(-rate * dt))


def _cooking_hours(hour: float) -> bool:
    return 7 <= hour < 9 or 12 <= hour < 14 or 19 <= hour < 21


@dataclass
class RoomState:
    temperature: float
    humidity: float
    aqi: float
    ambient_lux: float = 0.0   # daylight only
    lux: float = 0.0           # daylight + lamps
    motion: bool = False


class Environment:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.rooms = {
            room: RoomState(
                temperature=27 + rng.uniform(-1, 1),
                humidity=62 + rng.uniform(-4, 4),
                aqi=38 + rng.uniform(-8, 8),
            )
            for room in ROOMS
        }
        self.occupant: str | None = "Living Room"
        self.outdoor_temp = 28.0
        self.outdoor_humidity = 65.0
        self.outdoor_aqi = 55.0
        # Scenario timers (simulated datetimes)
        self.heat_wave_until = None
        self.pollution_until = None
        self.dry_until = None
        self.intruder_until = None
        self._natural_pollution_until = None

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _active(until, now) -> bool:
        return until is not None and now < until

    def _move_occupant(self, mode: str, hour: float, dt: float) -> None:
        if mode == "Away":
            self.occupant = None
            return
        if mode == "Sleep":
            self.occupant = "Bedroom"
            return
        if self.occupant is None:           # just came home
            self.occupant = "Living Room"
            return
        if self.rng.random() < min(1.0, dt / 25):
            if 7 <= hour < 9:
                weights = [2, 1, 3, 4]
            elif 12 <= hour < 14 or 19 <= hour < 21:
                weights = [3, 1, 5, 1]
            elif hour >= 22 or hour < 6:
                weights = [1, 6, 0.3, 1]
            else:
                weights = [5, 1, 2, 1]
            self.occupant = self.rng.choices(ROOMS, weights)[0]

    # --------------------------------------------------------------------- step
    def step(self, system, dt: float) -> None:
        rng = self.rng
        now = system.sim_time
        hour = now.hour + now.minute / 60
        mode = system.mode

        # ---- outdoor conditions
        phase = math.sin(2 * math.pi * (hour - 9) / 24)    # peaks at 15:00
        out_t = 28 + 5 * phase
        if self._active(self.heat_wave_until, now):
            out_t += 6
        self.outdoor_temp = out_t + rng.gauss(0, 0.1)

        out_h = 68 - 14 * phase
        if self._active(self.dry_until, now):
            out_h -= 35
        self.outdoor_humidity = max(10.0, out_h)

        if self._natural_pollution_until is None and rng.random() < 0.01 * dt / 10:
            self._natural_pollution_until = now + timedelta(minutes=rng.randint(60, 120))
        if self._natural_pollution_until is not None and now >= self._natural_pollution_until:
            self._natural_pollution_until = None
        out_aqi = 55.0
        if self._natural_pollution_until is not None:
            out_aqi = 140.0
        if self._active(self.pollution_until, now):
            out_aqi = 190.0
        self.outdoor_aqi = out_aqi + rng.gauss(0, 2)

        daylight = max(0.0, math.sin(math.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0.0
        intruder = self._active(self.intruder_until, now)

        self._move_occupant(mode, hour, dt)
        cooking = _cooking_hours(hour)

        # ---- per-room dynamics
        for room, s in self.rooms.items():
            devs = [d for d in system.devices.values() if d.room == room and d.on]
            lights = [d for d in devs if d.type == "light"]
            fans = [d for d in devs if d.type == "fan"]
            acs = [d for d in devs if d.type == "ac"]
            purifiers = [d for d in devs if d.type == "purifier"]
            humidifiers = [d for d in devs if d.type == "humidifier"]
            here = self.occupant == room

            # motion
            if mode == "Away":
                prob = 0.9 if (intruder and room == "Living Room") else 0.0
            elif mode == "Sleep":
                prob = 0.12 if here else 0.0
            else:
                prob = 0.85 if here else 0.02
            s.motion = rng.random() < prob

            # temperature
            target = self.outdoor_temp + 2.0
            if here:
                target += 0.8
            if room == "Kitchen" and here and cooking and mode == "Home":
                target += 3.0
            target += sum(d.value / 100 for d in lights) * 0.5
            target -= sum(0.6 * d.value for d in fans)
            s.temperature = approach(s.temperature, target, 0.004, dt)
            for ac in acs:
                s.temperature = approach(s.temperature, ac.value, 0.035, dt)
            s.temperature += rng.gauss(0, 0.05)

            # humidity
            h = approach(s.humidity, self.outdoor_humidity, 0.004, dt)
            for _ in acs:
                h = approach(h, 50, 0.012, dt)           # AC dehumidifies
            for _ in humidifiers:
                h = approach(h, 75, 0.02, dt)
            for fan in fans:
                h = approach(h, self.outdoor_humidity, 0.006 * fan.value, dt)
            if room == "Bathroom" and here and mode == "Home":
                h += rng.uniform(2, 8) * dt / 10          # shower steam
            s.humidity = min(98.0, max(15.0, h + rng.gauss(0, 0.3)))

            # air quality
            a = approach(s.aqi, self.outdoor_aqi * 0.6, 0.006, dt)
            for _ in purifiers:
                a = approach(a, 12, 0.05, dt)
            for fan in fans:
                a = approach(a, self.outdoor_aqi * 0.5, 0.004 * fan.value, dt)
            if room == "Kitchen" and here and cooking and mode == "Home":
                a += rng.uniform(8, 35) * dt / 10          # cooking fumes
            s.aqi = min(400.0, max(5.0, a + rng.gauss(0, 0.8)))

            # light
            s.ambient_lux = max(0.0, 550 * daylight * WINDOW_FACTOR[room] + rng.gauss(0, 5))
            s.lux = s.ambient_lux + sum(d.value * 4 for d in lights)
