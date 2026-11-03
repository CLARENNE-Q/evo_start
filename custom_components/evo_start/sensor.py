"""Plateforme de capteurs pour l'intégration EVO-START."""
import logging
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "battery": {
        "name": "Tension de la batterie",
        "unit": "V",
        "icon": "mdi:car-battery",
        "key": "volt",
        "source": "lloc",
        "transform": lambda x: round(int(x) / 10.0, 1) if x is not None else None,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "temperature": {
        "name": "Température du véhicule",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "key": "temp",
        "source": "lloc",
        "transform": lambda x: float(x) if x is not None else None,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "speed": {
        "name": "Vitesse du véhicule",
        "unit": "km/h",
        "icon": "mdi:speedometer",
        "key": "speed",
        "source": "lloc",
        "transform": lambda x: int(x) if x is not None else None,
        "device_class": SensorDeviceClass.SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "mileage": {
        "name": "Odomètre",
        "unit": "km",
        "icon": "mdi:counter",
        "key": "odometre_km",
        "source": "trips",
        "transform": lambda x: round(float(x), 1) if x is not None else 0.0,
        "device_class": SensorDeviceClass.DISTANCE,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "distance_aujourdhui": {
        "name": "Distance aujourd'hui",
        "unit": "km",
        "icon": "mdi:map-marker-distance",
        "key": "distance_jour_km",
        "source": "trips",
        "transform": lambda x: float(x) if x is not None else 0.0,
        "device_class": SensorDeviceClass.DISTANCE,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "distance_ce_mois": {
        "name": "Distance ce mois",
        "unit": "km",
        "icon": "mdi:calendar-month-outline",
        "key": "distance_mois_km",
        "source": "trips",
        "transform": lambda x: float(x) if x is not None else 0.0,
        "device_class": SensorDeviceClass.DISTANCE,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "dernier_trajet_distance": {
        "name": "Dernier trajet distance",
        "unit": "km",
        "icon": "mdi:map-marker-path",
        "key": "dernier_trajet_km",
        "source": "trips",
        "transform": lambda x: float(x) if x is not None else 0.0,
        "device_class": SensorDeviceClass.DISTANCE,
        "state_class": None,
    },
    "dernier_trajet_vitesse_max": {
        "name": "Dernier trajet vitesse max",
        "unit": "km/h",
        "icon": "mdi:speedometer",
        "key": "dernier_trajet_vitesse_max",
        "source": "trips",
        "transform": lambda x: int(x) if x is not None else 0,
        "device_class": SensorDeviceClass.SPEED,
        "state_class": None,
    },
    "engine": {
        "name": "État du moteur",
        "unit": None,
        "icon": "mdi:engine",
        "key": "vcl_eng",
        "source": "flags",
        "transform": lambda x: "En marche" if str(x) == "1" else ("Arrêté" if str(x) == "0" else "Inconnu"),
        "device_class": None,
        "state_class": None,
    },
    "trunk_status": {
        "name": "Hayon arrière",
        "unit": None,
        "icon": "mdi:car-back",
        "key": "dor_trk",
        "source": "flags",
        "transform": lambda x: "Ouvert" if str(x) == "1" else ("Fermé" if str(x) == "0" else "Inconnu"),
        "device_class": None,
        "state_class": None,
    },
    "door_lock_status": {
        "name": "État des serrures",
        "unit": None,
        "icon": "mdi:lock",
        "key": "vcl_lok",
        "source": "flags",
        "transform": lambda x: "Déverrouillé" if str(x) == "1" else ("Verrouillé" if str(x) == "0" else "Inconnu"),
        "device_class": None,
        "state_class": None,
    },
    "hood_status": {
        "name": "Capot moteur",
        "unit": None,
        "icon": "mdi:car-hood",
        "key": "dor_frn",
        "source": "flags",
        "transform": lambda x: "Ouvert" if str(x) == "1" else ("Fermé" if str(x) == "0" else "Inconnu"),
        "device_class": None,
        "state_class": None,
    },
    "left_front_door": {
        "name": "Porte avant gauche",
        "unit": None,
        "icon": "mdi:car-door",
        "key": "dor_lf",
        "source": "flags",
        "transform": lambda x: "Ouvert" if str(x) == "1" else ("Fermé" if str(x) == "0" else "Inconnu"),
        "device_class": None,
        "state_class": None,
    },
    "right_front_door": {
        "name": "Porte avant droite",
        "unit": None,
        "icon": "mdi:car-door",
        "key": "dor_rf",
        "source": "flags",
        "transform": lambda x: "Ouvert" if str(x) == "1" else ("Fermé" if str(x) == "0" else "Inconnu"),
        "device_class": None,
        "state_class": None,
    },
    "left_rear_door": {
        "name": "Porte arrière gauche",
        "unit": None,
        "icon": "mdi:car-door",
        "key": "dor_lb",
        "source": "flags",
        "transform": lambda x: "Ouvert" if str(x) == "1" else ("Fermé" if str(x) == "0" else "Inconnu"),
        "device_class": None,
        "state_class": None,
    },
    "right_rear_door": {
        "name": "Porte arrière droite",
        "unit": None,
        "icon": "mdi:car-door",
        "key": "dor_rb",
        "source": "flags",
        "transform": lambda x: "Ouvert" if str(x) == "1" else ("Fermé" if str(x) == "0" else "Inconnu"),
        "device_class": None,
        "state_class": None,
    },
    "satellite_gps": {
        "name": "Liaison satellite GPS",
        "unit": None,
        "icon": "mdi:crosshairs-gps",
        "key": "gpsol",
        "source": "lloc",
        "transform": lambda x: "Verrouillé" if str(x) == "1" else "Non synchronisé",
        "device_class": None,
        "state_class": None,
    },
    "gsm_signal": {
        "name": "Réseau cellulaire GSM",
        "unit": None,
        "icon": "mdi:signal",
        "key": "gsmol",
        "source": "lloc",
        "transform": lambda x: "Connecté" if str(x) == "1" else "Déconnecté",
        "device_class": None,
        "state_class": None,
    },
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for vehicle_id in coordinator.get_all_vehicle_ids():
        vehicle_data = coordinator.get_vehicle_data(vehicle_id) or {}
        vehicle_name = vehicle_data.get("carinfo", {}).get("cname", f"Véhicule {vehicle_id}")
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
        self._attr_name = f"{vehicle_name} {sensor_cfg['name']}"
        self._attr_unique_id = f"evo_start_{vehicle_id}_{sensor_id}"
        self._attr_icon = sensor_cfg["icon"]
        self._attr_native_unit_of_measurement = sensor_cfg["unit"]
        self._attr_device_class = sensor_cfg.get("device_class")
        self._attr_state_class = sensor_cfg.get("state_class")

    @property
    def native_value(self):
        source = self._cfg.get("source", "lloc")
        key = self._cfg["key"]
        raw = None
        try:
            if source == "trips":
                trips = self.coordinator.get_vehicle_trips(self._vehicle_id)
                raw = trips.get(key)
            elif source == "flags":
                flags = self.coordinator.get_vehicle_flags(self._vehicle_id)
                raw = flags.get(key)
            else:
                data = self.coordinator.get_vehicle_data(self._vehicle_id) or {}
                raw = data.get("lloc", {}).get(key)
            return self._cfg["transform"](raw)
        except Exception as e:
            _LOGGER.debug("Erreur extraction capteur %s: %s", self._sensor_id, e)
            return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"evo_start_vehicle_{self._vehicle_id}")},
            "name": self._vehicle_name,
            "manufacturer": "Fortin",
            "model": "EVO-START",
        }
