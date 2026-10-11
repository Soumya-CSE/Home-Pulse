"""Smart Home Monitoring & Automation System - Streamlit dashboard.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from smart_home.automation import RULES
from smart_home.config import (
    DEFAULT_SETTINGS,
    MODE_ICONS,
    MODES,
    ROOM_ICONS,
    ROOMS,
    SETTINGS_SPEC,
    TYPE_ICONS,
)
from smart_home.system import HomeSystem

st.set_page_config(page_title="Smart Home Monitor", page_icon="🏠", layout="wide")

LEVEL_ICONS = {"info": "🔵 info", "warning": "🟠 warning", "critical": "🔴 critical"}
FAN_LABELS = {1: "Low", 2: "Medium", 3: "High"}


# ----------------------------------------------------------------- small helpers
def show_chart(fig: go.Figure, key: str) -> None:
    try:
        st.plotly_chart(fig, width="stretch", key=key)
    except TypeError:                                   # older Streamlit
        st.plotly_chart(fig, use_container_width=True, key=key)


def show_table(df: pd.DataFrame) -> None:
    try:
        st.dataframe(df, width="stretch", hide_index=True)
    except TypeError:
        st.dataframe(df, use_container_width=True, hide_index=True)


def aqi_label(aqi: float) -> str:
    if aqi < 50:
        return "🟢 Good"
    if aqi < 100:
        return "🟡 Moderate"
    if aqi < 150:
        return "🟠 Sensitive groups"
    if aqi < 200:
        return "🔴 Unhealthy"
    return "🟣 Very unhealthy"


def gauge(value: float, title: str, unit: str, lo: float, hi: float, bands: list, key: str) -> None:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": unit, "valueformat": ".1f" if unit == " °C" else ".0f"},
            title={"text": title, "font": {"size": 15}},
            gauge={
                "axis": {"range": [lo, hi]},
                "bar": {"color": "#4c78a8"},
                "steps": [{"range": [a, b], "color": c} for a, b, c in bands],
            },
        )
    )
    fig.update_layout(height=210, margin=dict(l=25, r=25, t=55, b=10))
    show_chart(fig, key)


GREEN, AMBER, ORANGE, RED, BLUE = (
    "rgba(46,160,67,0.35)", "rgba(240,180,41,0.40)", "rgba(240,120,40,0.40)",
    "rgba(220,50,47,0.40)", "rgba(80,140,220,0.35)",
)


def prev_value(home: HomeSystem, room: str, key: str):
    if len(home.history) < 2:
        return None
    return home.history[-1]["rooms"][room][key] - home.history[-2]["rooms"][room][key]


# ---------------------------------------------------------------------- callbacks
def cb_toggle(dev_id: str) -> None:
    st.session_state.home.set_device(dev_id, on=st.session_state[f"tg_{dev_id}"])


def cb_value(dev_id: str) -> None:
    st.session_state.home.set_device(dev_id, value=st.session_state[f"val_{dev_id}"])


def cb_mode() -> None:
    st.session_state.home.set_mode(st.session_state["mode_sel"])


def cb_step() -> None:
    st.session_state.home.tick(st.session_state.get("step_min", 10))


def cb_scenario(name: str) -> None:
    st.toast(st.session_state.home.trigger(name))


def cb_bulk(action: str) -> None:
    st.session_state.home.bulk(action)


def cb_reset() -> None:
    for k in list(st.session_state.keys()):
        if k.startswith(("cfg_", "rule_", "tg_", "val_")):
            del st.session_state[k]
    st.session_state["mode_sel"] = "Home"
    st.session_state["master_auto"] = True
    st.session_state.home = HomeSystem()


def cb_clear_history() -> None:
    home = st.session_state.home
    home.db.clear(home.run_id)
    home.history.clear()
    home.events.clear()


# ---------------------------------------------------------------------------- state
if "home" not in st.session_state:
    st.session_state.home = HomeSystem()
home: HomeSystem = st.session_state.home

# ---------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("🏠 Smart Home")
    st.caption("Monitoring & automation (simulated)")

    st.session_state.setdefault("mode_sel", "Home")
    st.session_state.setdefault("master_auto", True)
    st.selectbox(
        "Home mode", MODES, key="mode_sel", on_change=cb_mode,
        format_func=lambda m: f"{MODE_ICONS[m]} {m}",
        help="Home: normal. Away: nobody in, energy saver + security. Sleep: night routine.",
    )
    home.automation_enabled = st.toggle("🤖 Automation engine", key="master_auto")

    st.divider()
    st.subheader("Simulation")
    auto_run = st.toggle("Live updates", value=True, key="auto_run")
    refresh_s = st.slider("Refresh every (seconds)", 1, 10, 3, key="refresh_s")
    step_min = st.select_slider("Simulated minutes per update", [1, 5, 10, 15, 30], value=10, key="step_min")
    st.button("⏭️ Advance one step", on_click=cb_step, key="btn_step")

    with st.expander("🧪 Scenario simulator"):
        st.caption("Inject events to watch the automation react.")
        st.button("🔥 Heat wave (3 h)", on_click=cb_scenario, args=("heat_wave",), key="sc_heat")
        st.button("🏭 Pollution spike (2 h)", on_click=cb_scenario, args=("pollution",), key="sc_poll")
        st.button("🏜️ Dry spell (3 h)", on_click=cb_scenario, args=("dry",), key="sc_dry")
        st.button("🥷 Intruder (Away mode)", on_click=cb_scenario, args=("intruder",), key="sc_intr")

    st.divider()
    c1, c2 = st.columns(2)
    c1.button("♻️ Reset", on_click=cb_reset, key="btn_reset", help="Start a fresh simulation")
    c2.button("🗑️ Clear log", on_click=cb_clear_history, key="btn_clear", help="Delete this run's stored history")
    st.caption(f"Run ID: `{home.run_id}`")


# ------------------------------------------------------------------------ renderers
def render_header(home: HomeSystem) -> None:
    prev_power = home.history[-2]["power"] if len(home.history) > 1 else home.total_power
    cols = st.columns(5)
    cols[0].metric("🕒 Simulated time", home.sim_time.strftime("%d %b, %H:%M"))
    cols[1].metric("🌤️ Outdoor", f"{home.env.outdoor_temp:.1f} °C")
    cols[2].metric("⚡ Power now", f"{home.total_power:,.0f} W", delta=f"{home.total_power - prev_power:+.0f} W",
                   delta_color="inverse")
    cols[3].metric("🔋 Energy used", f"{home.energy_kwh:.2f} kWh")
    cols[4].metric(f"{MODE_ICONS[home.mode]} Mode", home.mode,
                   delta=f"{len(home.active_alerts)} alert(s)" if home.active_alerts else "all clear",
                   delta_color="inverse" if home.active_alerts else "off")


def render_alerts(home: HomeSystem) -> None:
    if not home.active_alerts:
        st.success("✅ All systems normal - no active alerts.")
        return
    for alert in home.active_alerts.values():
        (st.error if alert["level"] == "critical" else st.warning)(alert["message"])


def render_dashboard(home: HomeSystem) -> None:
    render_alerts(home)

    st.subheader("Rooms at a glance")
    cols = st.columns(len(ROOMS))
    for col, room in zip(cols, ROOMS):
        r = home.env.rooms[room]
        active = sum(1 for d in home.devices_in(room) if d.on and d.type not in ("lock",))
        with col.container(border=True):
            st.markdown(f"**{ROOM_ICONS[room]} {room}**")
            m1, m2 = st.columns(2)
            dt_ = prev_value(home, room, "temperature")
            dh_ = prev_value(home, room, "humidity")
            m1.metric("Temp", f"{r.temperature:.1f} °C", delta=None if dt_ is None else f"{dt_:+.1f}",
                      delta_color="off")
            m2.metric("Humidity", f"{r.humidity:.0f} %", delta=None if dh_ is None else f"{dh_:+.1f}",
                      delta_color="off")
            st.caption(f"Air: {aqi_label(r.aqi)} ({r.aqi:.0f})  \n"
                       f"Light: {r.lux:.0f} lux  \n"
                       f"Motion: {'🟢 detected' if r.motion else '⚪ none'}  \n"
                       f"Devices on: {active} · {home.room_power(room):.0f} W")

    st.subheader("Room details")
    room = st.selectbox("Room", ROOMS, key="detail_room", format_func=lambda x: f"{ROOM_ICONS[x]} {x}")
    r = home.env.rooms[room]
    g = st.columns(4)
    with g[0]:
        gauge(r.temperature, "Temperature", " °C", 10, 45,
              [(10, 18, BLUE), (18, 28, GREEN), (28, 34, AMBER), (34, 45, RED)], f"g_t_{room}")
    with g[1]:
        gauge(r.humidity, "Humidity", " %", 0, 100,
              [(0, 30, AMBER), (30, 60, GREEN), (60, 80, AMBER), (80, 100, RED)], f"g_h_{room}")
    with g[2]:
        gauge(r.aqi, "Air quality (AQI)", "", 0, 300,
              [(0, 50, GREEN), (50, 100, AMBER), (100, 150, ORANGE), (150, 300, RED)], f"g_a_{room}")
    with g[3]:
        gauge(r.lux, "Light", " lx", 0, 1000, [(0, 100, BLUE), (100, 500, GREEN), (500, 1000, AMBER)],
              f"g_l_{room}")

    hist = home.room_history(room)
    if len(hist) > 1:
        c1, c2 = st.columns(2)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=hist["time"], y=hist["temperature"], name="Temperature (°C)",
                                 line=dict(color="#e45756")), secondary_y=False)
        fig.add_trace(go.Scatter(x=hist["time"], y=hist["humidity"], name="Humidity (%)",
                                 line=dict(color="#4c78a8")), secondary_y=True)
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), title="Temperature & humidity",
                          legend=dict(orientation="h", y=-0.2))
        with c1:
            show_chart(fig, f"tr_th_{room}")
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=hist["time"], y=hist["aqi"], name="AQI",
                                  line=dict(color="#72b7b2")), secondary_y=False)
        fig2.add_trace(go.Scatter(x=hist["time"], y=hist["lux"], name="Light (lux)",
                                  line=dict(color="#f2cf5b")), secondary_y=True)
        fig2.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), title="Air quality & light",
                           legend=dict(orientation="h", y=-0.2))
        with c2:
            show_chart(fig2, f"tr_al_{room}")

    ph = home.power_history()
    if len(ph) > 1:
        fig3 = px.area(ph, x="time", y="power", title="Total power draw (W)")
        fig3.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=10), xaxis_title=None, yaxis_title="W")
        show_chart(fig3, "tr_power")


def render_devices(home: HomeSystem) -> None:
    st.caption("Use the switches and sliders to control the simulated devices. A manual change pauses "
               "automation for that device for 60 simulated minutes.")
    b = st.columns(3)
    b[0].button("💡 All lights off", on_click=cb_bulk, args=("lights_off",), key="bulk_lights", width="stretch")
    b[1].button("🔒 Lock front door", on_click=cb_bulk, args=("lock",), key="bulk_lock", width="stretch")
    b[2].button("🌙 Switch everything off", on_click=cb_bulk, args=("all_off",), key="bulk_all", width="stretch")

    for room in ROOMS:
        with st.container(border=True):
            st.markdown(f"#### {ROOM_ICONS[room]} {room}")
            for dev in home.devices_in(room):
                c1, c2, c3, c4 = st.columns([2.4, 1, 3, 1.6], vertical_alignment="center")
                manual = home.manual_active(dev)
                c1.markdown(f"**{TYPE_ICONS[dev.type]} {dev.name}**")
                c1.caption("🔧 manual control" if manual else "🤖 automation")

                st.session_state[f"tg_{dev.id}"] = dev.on
                c2.toggle(dev.name, key=f"tg_{dev.id}", on_change=cb_toggle, args=(dev.id,),
                          label_visibility="collapsed")

                if dev.type == "light":
                    st.session_state[f"val_{dev.id}"] = int(dev.value)
                    c3.slider("Brightness", 10, 100, step=10, key=f"val_{dev.id}", on_change=cb_value,
                              args=(dev.id,), disabled=not dev.on, label_visibility="collapsed")
                elif dev.type == "fan":
                    st.session_state[f"val_{dev.id}"] = int(round(dev.value))
                    c3.select_slider("Speed", options=[1, 2, 3], format_func=lambda x: FAN_LABELS[x],
                                     key=f"val_{dev.id}", on_change=cb_value, args=(dev.id,),
                                     disabled=not dev.on, label_visibility="collapsed")
                elif dev.type == "ac":
                    st.session_state[f"val_{dev.id}"] = int(round(dev.value))
                    c3.slider("Set-point", 16, 30, step=1, key=f"val_{dev.id}", on_change=cb_value,
                              args=(dev.id,), disabled=not dev.on, label_visibility="collapsed")
                else:
                    c3.caption("—")
                c4.markdown(f"{dev.state_label}  \n`{dev.power_w():.0f} W`")


def render_automation(home: HomeSystem) -> None:
    st.subheader("Automation rules")
    st.caption("Rules run on every update, in the order shown. The master switch is in the sidebar.")
    if not home.automation_enabled:
        st.warning("The automation engine is switched off in the sidebar.")
    for rule in RULES:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1], vertical_alignment="center")
            c1.markdown(f"**{rule.name}**")
            c1.caption(rule.description)
            home.rules_enabled[rule.key] = c2.toggle("Enabled", value=home.rules_enabled[rule.key],
                                                     key=f"rule_{rule.key}")

    st.subheader("Thresholds")
    groups: dict[str, list] = {}
    for spec in SETTINGS_SPEC:
        groups.setdefault(spec[5], []).append(spec)
    cols = st.columns(3)
    for i, (group, specs) in enumerate(groups.items()):
        with cols[i % 3].container(border=True):
            st.markdown(f"**{group}**")
            for key, label, lo, hi, step, _ in specs:
                home.settings[key] = st.slider(label, lo, hi, value=home.settings[key], step=step,
                                               key=f"cfg_{key}")
    if st.button("Restore default thresholds", key="btn_defaults"):
        for key in DEFAULT_SETTINGS:
            st.session_state.pop(f"cfg_{key}", None)
        home.settings = dict(DEFAULT_SETTINGS)
        st.rerun()

    st.subheader("Recent automation actions")
    actions = [e for e in home.events if e["category"] == "Automation"][:12]
    if actions:
        show_table(pd.DataFrame(actions)[["time", "message"]])
    else:
        st.info("No automation actions yet.")


def render_analytics(home: HomeSystem) -> None:
    readings = home.db.readings(home.run_id)
    power = home.db.power(home.run_id)
    if readings.empty:
        st.info("No history yet - let the simulation run for a few updates.")
        return

    metrics = {"Temperature (°C)": "temperature", "Humidity (%)": "humidity",
               "Air quality (AQI)": "aqi", "Light (lux)": "lux"}
    c1, c2 = st.columns([1, 2])
    label = c1.selectbox("Metric", list(metrics), key="an_metric")
    rooms = c2.multiselect("Rooms", ROOMS, default=ROOMS, key="an_rooms")
    sub = readings[readings["room"].isin(rooms)]
    if not sub.empty:
        fig = px.line(sub, x="time", y=metrics[label], color="room", title=f"{label} over time")
        fig.update_layout(height=340, margin=dict(l=10, r=10, t=40, b=10), xaxis_title=None)
        show_chart(fig, "an_line")

    st.subheader("Energy")
    k = st.columns(3)
    k[0].metric("Average power", f"{power['power_w'].mean():,.0f} W")
    k[1].metric("Peak power", f"{power['power_w'].max():,.0f} W")
    k[2].metric("Energy used", f"{power['energy_kwh'].max():.2f} kWh")
    fig2 = px.area(power, x="time", y="power_w", color="mode", title="Power draw by home mode")
    fig2.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10), xaxis_title=None, yaxis_title="W")
    show_chart(fig2, "an_power")

    st.subheader("Room statistics")
    summary = readings.groupby("room").agg(
        temp_min=("temperature", "min"), temp_avg=("temperature", "mean"), temp_max=("temperature", "max"),
        humidity_avg=("humidity", "mean"), aqi_avg=("aqi", "mean"), aqi_max=("aqi", "max"),
        motion_pct=("motion", "mean"),
    ).round(1)
    summary["motion_pct"] = (summary["motion_pct"] * 100).round(0)
    summary = summary.rename(columns={"motion_pct": "motion_%"}).reset_index()
    show_table(summary)

    events = home.db.events(home.run_id)
    if not events.empty:
        counts = events.groupby("category").size().reset_index(name="events")
        fig3 = px.bar(counts, x="category", y="events", title="Events by category")
        fig3.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=10), xaxis_title=None)
        show_chart(fig3, "an_events")

    st.download_button("⬇️ Download readings (CSV)", readings.to_csv(index=False), "readings.csv", "text/csv",
                       key="dl_readings")


def render_logs(home: HomeSystem) -> None:
    events = home.db.events(home.run_id)
    if events.empty:
        st.info("No events logged yet.")
        return
    c1, c2 = st.columns(2)
    cats = c1.multiselect("Category", sorted(events["category"].unique()), key="log_cat")
    levels = c2.multiselect("Level", ["info", "warning", "critical"], key="log_lvl")
    if cats:
        events = events[events["category"].isin(cats)]
    if levels:
        events = events[events["level"].isin(levels)]
    shown = events.copy()
    shown["level"] = shown["level"].map(lambda x: LEVEL_ICONS.get(x, x))
    show_table(shown.head(300))
    st.download_button("⬇️ Download event log (CSV)", events.to_csv(index=False), "events.csv", "text/csv",
                       key="dl_events")


# ------------------------------------------------------------------------- main view
interval = float(refresh_s)


@st.fragment(run_every=interval if auto_run else None)
def live_view() -> None:
    h: HomeSystem = st.session_state.home
    if auto_run and time.time() - h.last_wall_tick >= interval * 0.9:
        h.tick(step_min)

    st.title("Smart Home Monitoring & Automation")
    render_header(h)
    tabs = st.tabs(["📊 Dashboard", "🔌 Devices", "⚙️ Automation", "📈 Analytics", "🧾 Event log"])
    with tabs[0]:
        render_dashboard(h)
    with tabs[1]:
        render_devices(h)
    with tabs[2]:
        render_automation(h)
    with tabs[3]:
        render_analytics(h)
    with tabs[4]:
        render_logs(h)


live_view()
