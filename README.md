[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-%23FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/clarenneq)

# 🧩 EVO-START – Home Assistant Custom Integration

Custom integration for vehicles equipped with the **Fortin EVO-START** system, allowing vehicle status to be monitored in Home Assistant.

---

## 🚗 Features

- 🔐 Track **central lock** and **trunk** status
- 🚗 Monitor **engine**, **air conditioning**, and **ACC** status
- 📍 GPS position as a `device_tracker`
- � **Multi-vehicle support** - All vehicles under your account are automatically detected
- �🔋 Built-in sensors:
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

**Note**: With multi-vehicle support, each vehicle creates its own set of entities. The vehicle name from your EVO-START account is included in entity names to distinguish between vehicles.

### 🔐 `lock.`

| Entity                                    | Description                |
|-------------------------------------------|----------------------------|
| `lock.evo_start_{vehicle_name}_central_lock` | Central lock (actionable)   |

### 🛎️ `button.`

| Entity                                     | Description                 |
|--------------------------------------------|------------------------------|
| `button.evo_start_{vehicle_name}_remote_start`  | Start the vehicle remotely  |
| `button.evo_start_{vehicle_name}_remote_stop`   | Stop the vehicle remotely   |

### 🌡️ `sensor.`

| Entity                                            | Description                          |
|---------------------------------------------------|--------------------------------------|
| `sensor.evo_start_{vehicle_name}_battery_voltage`      | Battery voltage (in volts)           |
| `sensor.evo_start_{vehicle_name}_vehicle_temperature`  | Engine temperature                   |
| `sensor.evo_start_{vehicle_name}_vehicle_mileage`      | Total mileage (in kilometers)        |
| `sensor.evo_start_{vehicle_name}_vehicle_speed`        | Current vehicle speed (in km/h)      |
| `sensor.evo_start_{vehicle_name}_gsm_signal`            | GSM network signal status            |
| `sensor.evo_start_{vehicle_name}_gps_online`            | GPS online connection status         |
| `sensor.evo_start_{vehicle_name}_engine_status`         | Engine running status (On/Off)       |
| `sensor.evo_start_{vehicle_name}_trunk_status`          | Trunk open/closed status             |
| `sensor.evo_start_{vehicle_name}_door_lock_status`      | Door lock status (Locked/Unlocked)   |
| `sensor.evo_start_{vehicle_name}_hood_status`           | Hood open/closed status              |
| `sensor.evo_start_{vehicle_name}_left_front_door`       | Left front door open/closed status   |
| `sensor.evo_start_{vehicle_name}_right_front_door`      | Right front door open/closed status  |
| `sensor.evo_start_{vehicle_name}_left_rear_door`        | Left rear door open/closed status    |
| `sensor.evo_start_{vehicle_name}_right_rear_door`       | Right rear door open/closed status   |

### 📍 `device_tracker.`

| Entity                                       | Description                                                           |
|----------------------------------------------|-----------------------------------------------------------------------|
| `device_tracker.evo_start_{vehicle_name}` | GPS position (latitude/longitude) with all flags (doors, lights, etc.) in attributes |


---

## 🧠 Technical Notes

- The `coordinator` handles data retrieval via the **Evo Start** app API.
- Data is refreshed every **60 seconds**.
- Authentication uses a **SHA-1** password hash.
- All binary flags (`VST`) are decoded, interpreted, and displayed in the attributes of the `device_tracker`.
- **Multi-vehicle support**: All vehicles associated with your account are automatically discovered and configured.
- Each vehicle gets its own device in Home Assistant with separate entities for complete control.

---

## 📸 To Come

- [x] Multi-vehicle support ✅ **COMPLETED**

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
