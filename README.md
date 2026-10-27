# 🏠 Home Pulse — Smart Home Monitoring & Automation System

A **Streamlit-based Smart Home Monitoring and Automation System** that simulates real-time environmental monitoring, smart device control, security alerts, rule-based automation, and energy analytics — without requiring any physical IoT hardware.

Home Pulse provides an interactive dashboard to monitor home conditions, control simulated smart devices, detect unusual activities, and automate everyday tasks using predefined rules.

## 📸 Screenshots

### 🏠 Main Dashboard

<img width="1892" height="891" alt="Screenshot 2026-10-26 205040" src="https://github.com/user-attachments/assets/8da5d65d-3ea8-484c-9909-7a6a17ae7be1" />

<img width="1887" height="887" alt="Screenshot 2026-10-26 205103" src="https://github.com/user-attachments/assets/2c1a2138-2822-4451-8aef-236b7d2085eb" />

<img width="1881" height="890" alt="Screenshot 2026-10-26 205118" src="https://github.com/user-attachments/assets/2da561f7-be79-4371-94ff-954c12bffa46" />

---

### 🔌 Devices

<img width="1890" height="902" alt="Screenshot 2026-10-26 205948" src="https://github.com/user-attachments/assets/dded120a-a523-4911-bf96-0ce96de57dab" />

<img width="1895" height="900" alt="Screenshot 2026-10-26 210011" src="https://github.com/user-attachments/assets/57b5af95-bb16-4608-af80-e213240d26b2" />

<img width="1907" height="887" alt="Screenshot 2026-10-26 210040" src="https://github.com/user-attachments/assets/2eb64fd0-8122-4f7b-a5d1-f96514cf6b33" />

---

### ⚙️ Automation 

<img width="1902" height="895" alt="Screenshot 2026-10-26 210400" src="https://github.com/user-attachments/assets/671ccf29-5c29-491e-a581-10ea5503dd10" />

<img width="1887" height="902" alt="Screenshot 2026-10-26 210428" src="https://github.com/user-attachments/assets/8318a198-5163-4e63-8142-8e04666cdcf4" />

<img width="1875" height="897" alt="Screenshot 2026-10-26 210450" src="https://github.com/user-attachments/assets/ddfeb363-eda6-4689-8924-13d438490883" />

<img width="1887" height="908" alt="Screenshot 2026-10-26 210507" src="https://github.com/user-attachments/assets/3b7aa71d-efc2-4f46-9141-fef41056e463" />

---

### 📊 Analytics 

<img width="1886" height="892" alt="Screenshot 2026-10-26 210904" src="https://github.com/user-attachments/assets/41d449ee-280a-4849-9527-4a39eba4c15d" />

<img width="1887" height="892" alt="Screenshot 2026-10-26 210925" src="https://github.com/user-attachments/assets/59b1c81b-82dc-4f91-b484-055b36692007" />

<img width="1877" height="873" alt="Screenshot 2026-10-26 211015" src="https://github.com/user-attachments/assets/83507d83-bbaf-4db0-9da0-d477330bd36a" />

---

### 📋 Event Log

<img width="1897" height="902" alt="Screenshot 2026-10-26 211135" src="https://github.com/user-attachments/assets/9f955059-fed1-4272-8676-c5bd39dc417c" />

---

## ✨ Features 

### 🌡️ Environmental Monitoring
- Monitor temperature and humidity levels.
- Track air quality and light intensity.
- Simulate motion detection across different rooms.
- View changing sensor readings through simulated real-time updates.
- Visualize environmental data using interactive charts and gauges.

### 💡 Smart Device Control
- Control simulated lights, fans, air conditioners, and air purifiers.
- Manage humidifiers and other supported smart devices.
- Simulate door lock and security camera controls.
- Adjust brightness, fan speed, and AC temperature settings.
- Observe how device interactions affect environmental readings.

### ⚙️ Rule-Based Automation
- Automate devices using predefined conditions and actions.
- Support Home, Away, and Sleep operating modes.
- Simulate motion-based lighting and smart cooling.
- Trigger air-quality and humidity control actions.
- Apply mode-specific automation rules to improve comfort, safety, and energy efficiency.

### 🚨 Security Monitoring & Alerts
- Generate alerts for simulated security events.
- Monitor motion activity and door-lock status.
- Simulate suspicious or unusual home scenarios.
- Display relevant alerts and system events.
- Maintain an event history for reviewing previous activities.

### 📊 Analytics & Energy Management
- Visualize historical sensor readings.
- Track simulated electricity consumption.
- Monitor device activity and energy usage.
- Review alerts and automation events over time.
- Export supported data to CSV for further analysis.

### 🗄️ Data Storage
- Use SQLite to store supported application data.
- Maintain event history and relevant monitoring records.
- Support persistent storage between application sessions where implemented.

### 🧪 Testing
- Use pytest for automated testing.
- Validate supported application features and core functionality.
- Run tests locally to check for regressions.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic and simulation |
| Streamlit | Interactive web dashboard |
| Plotly | Interactive charts and visualizations |
| pandas | Data processing and analysis |
| SQLite | Local database storage |
| pytest | Automated testing |

---

## 🏗️ System Overview

Home Pulse follows a simulation-based architecture:

1. **Sensor Simulator:** Generates environmental readings such as temperature, humidity, air quality, light, and motion.
2. **Monitoring Dashboard:** Displays room conditions, sensor values, and device states.
3. **Device Controller:** Processes user interactions with simulated smart devices.
4. **Automation Engine:** Evaluates predefined rules and triggers supported actions.
5. **Alert System:** Displays security-related events and automation alerts.
6. **Data Layer:** Uses SQLite and application data processing to maintain supported records and history.
7. **Analytics Module:** Visualizes trends and energy usage and provides CSV export functionality.

**Workflow:**

`Sensor Simulation → Dashboard → Rule Engine → Device Actions → Alerts & History → Analytics`

---

## 🚀 Getting Started

### 📋 Prerequisites

Make sure you have the following installed:

- Python 3.10 or a compatible version supported by the project dependencies
- Git
- A modern web browser

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Soumya-CSE/Home-Pulse.git
cd Home-Pulse
```

### 2️⃣ Create a Virtual Environment

```bash
python -m venv .venv
```

### 3️⃣ Activate the Virtual Environment

**Windows — PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows — Command Prompt**

```cmd
.venv\Scripts\activate.bat
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

### 4️⃣ Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5️⃣ Run the Application

```bash
streamlit run app.py
```

Open the following address in your browser:

**http://localhost:8501**

The dashboard will start locally, allowing you to explore the simulated smart home environment.

---

## 🧪 Running Tests

Run the test suite from the project root:

```bash
python -m pytest -q tests
```

This command executes the tests inside the `tests` directory and displays a summary of the results.

---

## 🎮 How to Use

1. Launch the application using Streamlit.
2. Explore the dashboard to view the simulated home environment.
3. Monitor room conditions, including temperature, humidity, air quality, and light.
4. Use the device controls to change the state of supported smart devices.
5. Select an appropriate operating mode: Home, Away, or Sleep.
6. Observe automation actions and generated alerts.
7. Review environmental trends, event history, and energy analytics.
8. Export supported records to CSV for further analysis.

*Available controls and displayed information depend on the implemented application features.*

---

## 🔐 Security & Privacy

- Designed as a local, hardware-free simulation.
- Does not require a physical smart home installation.
- Uses simulated environmental and device data.
- Stores supported records locally using SQLite.
- Intended for educational demonstrations rather than production home security.

**Note:** This project demonstrates simulated security monitoring. It should not be considered a replacement for real alarms, surveillance systems, or certified home security devices.

---

## 🎯 Project Goals

The main goals of Home Pulse are to:

- Demonstrate smart home monitoring and IoT concepts.
- Build an interactive dashboard using Python and Streamlit.
- Implement rule-based automation for common household scenarios.
- Explore security event monitoring and alert generation.
- Analyze environmental conditions and simulated energy consumption.
- Practice data visualization, database integration, and software testing.

---

## 🔮 Future Enhancements

Potential improvements include:

- Integration with real IoT sensors and microcontrollers.
- MQTT-based communication with smart devices.
- Machine learning for occupancy prediction and anomaly detection.
- Advanced energy optimization and usage forecasting.
- User authentication and role-based access control.
- Notifications through email or messaging services.
- Additional automation rules and customizable scenarios.
- Docker-based deployment and continuous integration.

---

## 👨‍💻 Author

**Soumya Kanti Hazra**

- GitHub: [Soumya-CSE](https://github.com/Soumya-CSE)
- Project Repository: [Home Pulse](https://github.com/Soumya-CSE/Home-Pulse)

---

## ⭐ Support

If you find this project interesting or useful, consider giving the repository a **star ⭐** on GitHub!

*Built with Python, Streamlit, and a passion for smart home technology.*
