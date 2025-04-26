from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

# Tous les labels humains
FLAG_LABELS = {
    "lig_smal": "Small lights",
    "lig_big": "Headlights",
    "dor_frn": "Hood",
    "dor_rb": "Right back door",
    "dor_rf": "Right front door",
    "dor_lb": "Left rear door",
    "dor_lf": "Left front door",
    "vcl_on2": "Relay 2",
    "vcl_on1": "Relay 1",
    "wnd_top": "Sunroof",
    "wnd_rb": "Right back window",
    "wnd_rf": "Right front window",
    "wnd_lb": "Left rear window",
    "vcl_anit": "Anti-theft",
    "vcl_repair": "Car repair",
    "vcl_air": "Air Conditioner",
    "brk_fot": "Foot brake",
    "brk_han": "Handbrake",
    "gps_cls": "GPS short circuit",
    "gps_opn": "GPS open circuit",
    "gps_loc": "GPS position",
    "gps_power": "GPS power",
    "alm_tpms": "Tire pressure",
    "alm_bat": "Low voltage",
    "alm_belt_m": "Seat belt",
    "alm_acc": "Illegal ignition",
    "alm_dor": "Illegal door opening",
    "alm_vib": "Vibration",
    "alm_ultrasonic": "Ultrasound",
    "alm_dor_open": "Door not closed after locking"
}

# Définition des catégories
OPEN_FLAGS = {
    "lig_smal", "lig_big",
    "dor_frn", "dor_rb", "dor_rf", "dor_lb", "dor_lf",
    "vcl_on2", "vcl_on1",
    "wnd_top", "wnd_rb", "wnd_rf", "wnd_lb",
    "vcl_anit", "vcl_repair", "vcl_air",
    "brk_fot", "brk_han",
    "gps_cls", "gps_opn", "gps_loc", "gps_power"
}

ALERT_FLAGS = {
    "alm_tpms", "alm_bat", "alm_belt_m", "alm_acc",
    "alm_dor", "alm_vib", "alm_ultrasonic", "alm_dor_open"
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entity = EvoStartDeviceTracker(coordinator)
    async_add_entities([entity])

class EvoStartDeviceTracker(CoordinatorEntity, TrackerEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "evo_start_vehicle_tracker"
        self._attr_name = "EVO-START Vehicle"
        self._attr_icon = "mdi:car"
        self._attr_source_type = SourceType.GPS

    @property
    def latitude(self):
        return float(self.coordinator.data["lloc"].get("lat"))

    @property
    def longitude(self):
        return float(self.coordinator.data["lloc"].get("lng"))

    @property
    def extra_state_attributes(self):
        flags = self.coordinator.data.get("flags", {})
        attributes = {}
        for key, value in flags.items():
            if value not in ("0", "1"):
                continue
            label = FLAG_LABELS.get(key, key)

            if key in OPEN_FLAGS:
                state = "🔴 open" if value == "1" else "🟢 close"
            elif key in ALERT_FLAGS:
                state = "⚠️ alert" if value == "1" else "✅ normal"
            else:
                # Par défaut open/close
                state = "🔴 open" if value == "1" else "🟢 close"

            attributes[label] = state
        return attributes

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "evo_start_vehicle")},
            "name": self.coordinator.data.get("carinfo", {}).get("cname", "EVO-START Vehicle"),
            "manufacturer": "Fortin",
            "model": "EVO-START",
            "entry_type": "service",
        }
