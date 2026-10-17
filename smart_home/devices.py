"""Simulated smart devices."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Device:
    id: str
    name: str
    room: str
    type: str                      # light | fan | ac | purifier | humidifier | lock | camera
    on: bool = False               # for a lock, on == locked; for a camera, on == recording
    value: float = 0.0             # light brightness %, fan speed 1-3, AC set-point °C
    manual_until: Optional[datetime] = None   # automation backs off until this (sim time)

    @property
    def state_label(self) -> str:
        if self.type == "lock":
            return "Locked" if self.on else "Unlocked"
        if self.type == "camera":
            return "Recording" if self.on else "Off"
        return "On" if self.on else "Off"

    def power_w(self) -> float:
        """Instantaneous electrical draw in watts."""
        if self.type == "lock":
            return 1.0
        if not self.on:
            return 0.0
        if self.type == "light":
            return 12.0 * self.value / 100.0
        if self.type == "fan":
            return 20.0 * self.value
        if self.type == "ac":
            return 1100.0
        if self.type == "purifier":
            return 45.0
        if self.type == "humidifier":
            return 30.0
        if self.type == "camera":
            return 6.0
        return 0.0


def default_devices() -> list[Device]:
    return [
        # Living room
        Device("lr_light", "Ceiling Light", "Living Room", "light", False, 80),
        Device("lr_fan", "Ceiling Fan", "Living Room", "fan", False, 2),
        Device("lr_ac", "Air Conditioner", "Living Room", "ac", False, 24),
        Device("lr_purifier", "Air Purifier", "Living Room", "purifier", False),
        Device("front_lock", "Front Door Lock", "Living Room", "lock", True),
        Device("front_cam", "Entrance Camera", "Living Room", "camera", False),
        # Bedroom
        Device("br_light", "Bedside Light", "Bedroom", "light", False, 60),
        Device("br_fan", "Ceiling Fan", "Bedroom", "fan", False, 1),
        Device("br_ac", "Air Conditioner", "Bedroom", "ac", False, 24),
        Device("br_humidifier", "Humidifier", "Bedroom", "humidifier", False),
        Device("br_purifier", "Air Purifier", "Bedroom", "purifier", False),
        # Kitchen
        Device("kt_light", "Kitchen Light", "Kitchen", "light", False, 100),
        Device("kt_fan", "Exhaust Fan", "Kitchen", "fan", False, 2),
        # Bathroom
        Device("ba_light", "Bathroom Light", "Bathroom", "light", False, 80),
        Device("ba_fan", "Exhaust Fan", "Bathroom", "fan", False, 2),
    ]
