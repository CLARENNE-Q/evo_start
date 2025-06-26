import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

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
    },
    "door_lock_status": {
        "name": "Door Lock Status",
        "unit": None,
        "icon": "mdi:lock",
        "key": "vcl_lok",
        "transform": lambda x: "🔒 Locked" if str(x) == "1" else ("🔓 Unlocked" if str(x) == "0" else "❓ Unknown")
    },
    "hood_status": {
        "name": "Hood Status",
        "unit": None,
        "icon": "mdi:car-hood",
        "key": "dor_frn",
        "transform": lambda x: "🔓 Open" if str(x) == "1" else ("🔒 Closed" if str(x) == "0" else "❓ Unknown")
    },
    "left_front_door": {
        "name": "Left Front Door",
        "unit": None,
        "icon": "mdi:car-door",
        "key": "dor_lf",
        "transform": lambda x: "🔓 Open" if str(x) == "1" else ("🔒 Closed" if str(x) == "0" else "❓ Unknown")
    },
    "right_front_door": {
        "name": "Right Front Door",
        "unit": None,
        "icon": "mdi:car-door",
        "key": "dor_rf",
        "transform": lambda x: "🔓 Open" if str(x) == "1" else ("🔒 Closed" if str(x) == "0" else "❓ Unknown")
    },
    "left_rear_door": {
        "name": "Left Rear Door",
        "unit": None,
        "icon": "mdi:car-door",
        "key": "dor_lb",
        "transform": lambda x: "🔓 Open" if str(x) == "1" else ("🔒 Closed" if str(x) == "0" else "❓ Unknown")
    },
    "right_rear_door": {
        "name": "Right Rear Door",
        "unit": None,
        "icon": "mdi:car-door",
        "key": "dor_rb",
        "transform": lambda x: "🔓 Open" if str(x) == "1" else ("🔒 Closed" if str(x) == "0" else "❓ Unknown")
    }
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    
    # Create sensors for each vehicle
    for vehicle_id in coordinator.get_all_vehicle_ids():
        vehicle_data = coordinator.get_vehicle_data(vehicle_id)
        vehicle_name = vehicle_data.get("carinfo", {}).get("cname", f"Vehicle {vehicle_id}")
        
        for sensor_id, sensor_cfg in SENSOR_TYPES.items():
            entities.append(EvoStartSensor(coordinator, vehicle_id, sensor_id, sensor_cfg, vehicle_name))
    
    async_add_entities(entities)

class EvoStartSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, vehicle_id, sensor_id, sensor_cfg, vehicle_name):
        super().__init__(coordinator)
        self._vehicle_id = vehicle_id
        self._sensor_id = sensor_id
        self._cfg = sensor_cfg
        self._vehicle_name = vehicle_name
        self._attr_name = f"EVO-START {vehicle_name} {sensor_cfg['name']}"
        self._attr_unique_id = f"evo_start_{vehicle_id}_{sensor_id}"
        self._attr_icon = sensor_cfg["icon"]
        self._attr_native_unit_of_measurement = sensor_cfg["unit"]

    @property
    def native_value(self):
        vehicle_data = self.coordinator.get_vehicle_data(self._vehicle_id)
        vehicle_flags = self.coordinator.get_vehicle_flags(self._vehicle_id)
        
        if not vehicle_data or not vehicle_flags:
            return None
        try:
            key = self._cfg["key"]
            if key in vehicle_flags:
                raw_value = vehicle_flags.get(key)
            else:
                raw_value = vehicle_data["lloc"].get(key)
            return self._cfg["transform"](raw_value)
        except Exception as e:
            return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"evo_start_vehicle_{self._vehicle_id}")},
            "name": self._vehicle_name,
            "manufacturer": "Fortin",
            "model": "EVO-START",
            "entry_type": "service",
        }
