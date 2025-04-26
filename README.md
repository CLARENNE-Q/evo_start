# 🧩 EVO-START – Home Assistant Custom Integration

Custom integration for vehicles equipped with the **Fortin EVO-START** system, allowing vehicle status to be monitored in Home Assistant.

---

## 🚗 Features

- 🔐 Track **central lock** and **trunk** status
- 🚗 Monitor **engine**, **air conditioning**, and **ACC** status
- 📍 GPS position as a `device_tracker`
- 🔋 Built-in sensors:
  - Battery voltage
  - Engine temperature
  - Mileage
  - Speed
  - GSM signal strength
  - GPS online status
- 📡 Advanced VST flag decoding to extract all available flags

---

## 🛠️ Installation

### 🔁 Installation via HACS (recommended)

1. In Home Assistant, open **HACS → Integrations**.
2. Click the **three dots** (top-right) → **Custom Repositories**.
3. Add this repository URL:  
   **`https://github.com/CLARENNE-Q/evo_start`**  
   as type **Integration**.
4. Search for **EVO-START** in HACS and install it.
5. Restart Home Assistant.

### 🗂️ Manual installation

1. Download this repository as a ZIP.
2. Copy the `evo_start` folder into:  
   `config/custom_components/evo_start/`
3. Restart Home Assistant.

---

## ⚙️ Configuration

Once installed, go to **Settings → Integrations**, then:

1. Click on **"Add Integration"**
2. Search for **EVO-START**
3. Enter your **email** and **password** used in the **Evo Start** app.

---

## 🧩 Created Entities

### 🔐 `lock.`

| Entity                        | Description                     |
|-------------------------------|---------------------------------|
| `lock.evo_start_central_lock`  | Central lock (actionable)       |
| `lock.evo_start_trunk`         | Trunk (read-only)               |

### 🌡️ `sensor.`

| Entity                                | Description                     |
|--------------------------------------|---------------------------------|
| `sensor.evo_start_battery_voltage`   | Battery voltage in V            |
| `sensor.evo_start_vehicle_temperature` | Engine temperature             |
| `sensor.evo_start_vehicle_mileage`   | Total mileage in km             |
| `sensor.evo_start_vehicle_speed`     | Current speed in km/h           |
| `sensor.evo_start_gsm_signal`         | GSM signal status               |
| `sensor.evo_start_gps_online`         | GPS online status               |
| `sensor.evo_start_engine_status`      | Engine status (on/off)          |
| `sensor.evo_start_air_conditioning`   | Air conditioning status (on/off) |

### 📍 `device_tracker.`

| Entity                             | Description                        |
|------------------------------------|------------------------------------|
| `device_tracker.evo_start_vehicle` | Vehicle GPS position (latitude/longitude) + all decoded flags (doors, lights, etc.) in attributes |

---

## 🧠 Technical Notes

- The `coordinator` handles data retrieval via the **Evo Start** app API.
- Data is refreshed every **60 seconds**.
- Authentication uses a **SHA-1** password hash.
- All binary flags (`VST`) are decoded, interpreted, and displayed in the attributes of the `device_tracker`.

---

## 📸 To Come

- [ ] Support for `remote_start`, `lock`, `unlock` commands if API is confirmed
- [ ] Multi-vehicle support
- [ ] Full HACS validation (pending)

---

## 🙏 Thanks and Disclaimer

- Special thanks to the original **Evo Start** app and platform for inspiring this integration.
- This custom integration is not affiliated with, endorsed by, or officially supported by **Fortin** or **Evo Start**.
- All trademarks and copyrights are the property of their respective owners.

This project is a personal initiative, created for **educational and interoperability purposes**.  
Use at your own risk.

---

## 🧑‍💻 Author

Developed by **Quentin Clarenne**.  
Suggestions, bug reports, and contributions are welcome!
