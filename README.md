# 🏠 Home Pulse — Smart Home Monitoring & Automation System


A Streamlit-based smart home simulation system for real-time environmental monitoring, smart device control, automated security alerts, and energy analytics — without requiring physical hardware.

## ✨ Features
- 🌡️ Environmental monitoring: Temperature, humidity, air quality, light, and motion
- 💡 Smart device control: Lights, fans, ACs, purifiers, door locks, and cameras
- ⚙️ Rule-based automation with Home, Away, and Sleep modes
- 🚨 Security alerts and scenario simulation
- 📊 Analytics, event history, and CSV export
- 🗄️ SQLite-based data storage

## 🛠️ Tech Stack
Python · Streamlit · Plotly · pandas · SQLite · pytest

## 🚀 Installation

```bash
git clone https://github.com/Soumya-CSE/Home-Pulse.git
cd Home-Pulse

python -m venv .venv
```

Activate the environment:

```powershell
# Windows
.\.venv\Scripts\Activate.ps1
```

Install dependencies and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## 🧪 Run Tests

```bash
python -m pytest -q tests
```

## 🎯 Project Goal
To demonstrate smart home monitoring, IoT concepts, rule-based automation, security monitoring, and energy management through a hardware-free simulation.

## 👨‍💻 Author
**Soumya Hazra**  
GitHub: [Soumya-CSE](https://github.com/Soumya-CSE)

⭐ If you like this project, consider giving the repository a star!s