from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

SENSOR_TYPES = {
    "battery": {
        "name": "Battery Voltage",
        "unit": "V",
        "icon": "mdi:car-battery",
        "key": "volt",
        "transform": lambda x: round(int(x) / 10, 1)
    },
    "temperature": {
        "name": "Vehicle Temperature",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "key": "temp",
        "transform": lambda x: float(x)
    },
    "mileage": {
        "name": "Vehicle Mileage",
        "unit": "km",
        "icon": "mdi:counter",
        "key": "mileage",
        "transform": lambda x: int(x)
    },
    "speed": {
        "name": "Vehicle Speed",
        "unit": "km/h",
        "icon": "mdi:speedometer",
        "key": "speed",
        "transform": lambda x: int(x)
    },
    "gps_online": {
        "name": "GPS Online",
        "unit": None,
        "icon": "mdi:crosshairs-gps",
        "key": "gpsol",
        "transform": lambda x: "📍 Connected" if x == "1" else "❌ Offline"
    },
    "gsm_status": {
        "name": "GSM Signal",
        "unit": None,
        "icon": "mdi:signal",
        "key": "gsmol",
        "transform": lambda x: "📶 OK" if x == "1" else "❌ No Signal"
    },
    "air_conditioning": {
        "name": "Air Conditioning",
        "unit": None,
        "icon": "mdi:fan",
        "key": "vcl_air",
        "transform": lambda x: "💨 On" if str(x) == "1" else ("🌙 Off" if str(x) == "0" else "❓ Unknown")
    },
    "engine": {
        "name": "Engine Status",
        "unit": None,
        "icon": "mdi:engine",
        "key": "vcl_eng",
        "transform": lambda x: "🟢 On" if str(x) == "1" else ("🔴 Off" if str(x) == "0" else "❓ Unknown")
    },
    "trunk_status": {
        "name": "Trunk Status",
        "unit": None,
        "icon": "mdi:car-back",
        "key": "dor_trk",
        "transform": lambda x: "🔓 Open" if str(x) == "1" else ("🔒 Closed" if str(x) == "0" else "❓ Unknown")
    }
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        EvoStartSensor(coordinator, sensor_id, sensor_cfg)
        for sensor_id, sensor_cfg in SENSOR_TYPES.items()
    ]
    async_add_entities(entities)  # ✅ sans await

class EvoStartSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, sensor_id, sensor_cfg):
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._cfg = sensor_cfg
        self._attr_name = f"EVO-START {sensor_cfg['name']}"
        self._attr_unique_id = f"evo_start_{sensor_id}"
        self._attr_icon = sensor_cfg["icon"]
        self._attr_native_unit_of_measurement = sensor_cfg["unit"]

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        try:
            key = self._cfg["key"]
            if key in self.coordinator.data.get("flags", {}):
                raw_value = self.coordinator.data["flags"].get(key)
            else:
                raw_value = self.coordinator.data["lloc"].get(key)
            return self._cfg["transform"](raw_value)
        except Exception as e:
            _LOGGER.debug("❌ Sensor %s failed: %s", self._sensor_id, e)
            return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "evo_start_vehicle")},
            "name": self.coordinator.data.get("carinfo", {}).get("cname", "EVO-START Vehicle"),
            "manufacturer": "Fortin",
            "model": "EVO-START",
            "entry_type": "service",
        }
