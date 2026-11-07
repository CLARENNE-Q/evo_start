[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-%23FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/clarenneq)

# 🧩 EVO-START – Home Assistant Custom Integration# EVO-START Integration for Home Assistant

Custom component for Home Assistant to monitor and control vehicles equipped with **Fortin EVO-START LTE** telematics systems.

## Features

- **Sensors:**
  - 🔋 Battery Voltage (`sensor.battery`)
  - 🌡️ Cabin Temperature (`sensor.temperature`)
  - 🚗 Speed (`sensor.speed`)
  - 🔢 Persistent Virtual Odometer (`sensor.mileage` - accumulative from API trips)
  - 📍 Daily Distance (`sensor.distance_aujourdhui`)
  - 📅 Monthly Distance (`sensor.distance_ce_mois`)
  - ⏱️ Last Trip Metrics (Distance and Top Speed)
  - 🚪 Status flags (Doors, Trunk, Hood, Engine, Lock, GSM & GPS connection)
- **Controls:**
  - 🔒 Central Lock / Unlock door actuators (`lock.verrouillage_centralise`)
  - 🔑 Remote Engine Start & Remote Engine Stop (`button.demarrer_le_moteur`, `button.arreter_le_moteur`) with safety interlocks (prevent start when hood is open or engine is already running)
- **Geolocation:**
  - 🛰️ GPS Tracker (`device_tracker.position_gps`) with anti-drift filtering (eliminates (0.0, 0.0) coordinates) and dynamic accuracy reporting.

## Installation

### Via HACS (Recommended)
1. In Home Assistant, open **HACS** > **Integrations**.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Enter your repository URL, select category **Integration**, and click **Add**.
4. Download the integration and restart Home Assistant.

### Manual Installation
1. Copy the `custom_components/evo_start` folder into your Home Assistant `/config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings** > **Devices & Services** > **Add Integration** and search for **EVO-START**.
4. Enter your EVO-START mobile application email and password.

## Security Improvements
- Strict TLS/SSL verification on API endpoints.
- SHA-1 password hashing in-memory; credentials masked in configuration flow.
- Session token reuse with automatic renewal on expiration.
- Prevents concurrent actuator commands through async locks.
