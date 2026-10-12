"""Unit tests for the simulation engine, automation rules and storage."""

import sys
from datetime import timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from smart_home.database import Database  # noqa: E402
from smart_home.system import HomeSystem  # noqa: E402


@pytest.fixture
def home(tmp_path):
    return HomeSystem(db=Database(tmp_path / "test.db"), warmup_steps=6, seed=42)


def test_tick_advances_time_and_records_history(home):
    before = home.sim_time
    n = len(home.history)
    home.tick(10)
    assert home.sim_time == before + timedelta(minutes=10)
    assert len(home.history) == n + 1
    assert set(home.history[-1]["rooms"]) == set(home.env.rooms)


def test_readings_stay_in_physical_bounds(home):
    for _ in range(300):
        home.tick(10)
        for r in home.env.rooms.values():
            assert 0 < r.humidity < 100
            assert 0 < r.aqi <= 400
            assert r.lux >= 0
            assert 5 < r.temperature < 60


def test_manual_control_sets_override_and_logs(home):
    home.set_device("lr_light", on=True, value=50)
    dev = home.devices["lr_light"]
    assert dev.on and dev.value == 50
    assert home.manual_active(dev)
    assert any(e["category"] == "Manual" for e in home.events)


def test_cooling_rule_turns_ac_on_when_hot_and_off_when_cool(home):
    home.set_mode("Home")
    ac = home.devices["lr_ac"]
    ac.on, ac.manual_until = False, None
    home.env.rooms["Living Room"].temperature = 36
    home.env.heat_wave_until = home.sim_time + timedelta(hours=5)
    home.tick(1)
    assert ac.on, "AC should switch on above the threshold"
    for _ in range(200):
        home.tick(10)
        if not ac.on:
            break
    # With a heat wave the AC may cycle, but it must have switched off at least once or be near target
    assert (not ac.on) or home.env.rooms["Living Room"].temperature < home.settings["cooling_on_temp"] + 1


def test_away_mode_saves_energy_and_secures_house(home):
    home.set_device("lr_light", on=True)
    home.devices["lr_light"].manual_until = None
    lock = home.devices["front_lock"]
    lock.on, lock.manual_until = False, None
    home.set_mode("Away")
    home.tick(10)
    assert lock.on, "front door must be locked in Away mode"
    assert home.devices["front_cam"].on
    assert not home.devices["lr_light"].on


def test_manual_override_beats_energy_saver(home):
    home.set_device("br_fan", on=True)
    home.set_mode("Away")
    home.tick(10)
    assert home.devices["br_fan"].on


def test_intruder_scenario_raises_critical_alert(home):
    assert home.trigger("intruder") == "Switch to Away mode first"
    home.set_mode("Away")
    assert home.trigger("intruder") == "Intruder simulated"
    seen = False
    for _ in range(6):
        home.tick(5)
        seen = seen or any(a["level"] == "critical" for a in home.active_alerts.values())
    assert seen


def test_unlocked_door_while_away_is_flagged(home):
    home.set_mode("Away")
    home.set_device("front_lock", on=False)      # manual override defeats auto-lock
    home.tick(5)
    assert "lock" in home.active_alerts


def test_rules_can_be_disabled(home):
    home.rules_enabled["energy"] = False
    home.set_device("br_fan", on=True)
    home.devices["br_fan"].manual_until = None
    home.set_mode("Away")
    home.tick(10)
    assert home.devices["br_fan"].on


def test_power_and_energy_accounting(home):
    e0 = home.energy_kwh
    home.set_device("lr_ac", on=True)
    home.tick(10)
    assert home.total_power >= 1100
    assert home.energy_kwh > e0


def test_database_roundtrip(home):
    home.tick(10)
    readings = home.db.readings(home.run_id)
    assert not readings.empty
    assert set(readings["room"]) == set(home.env.rooms)
    assert not home.db.power(home.run_id).empty
    assert not home.db.events(home.run_id).empty
    home.db.clear(home.run_id)
    assert home.db.readings(home.run_id).empty
