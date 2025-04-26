from homeassistant.components.lock import LockEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

LOCK_FLAGS = {
    "vcl_lok": {
        "name": "Central Lock",
        "icon": "mdi:lock",
        "inverted": True
    },
    "dor_trk": {
        "name": "Trunk",
        "icon": "mdi:car-back",
        "inverted": True
    }
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        EvoStartLock(coordinator, flag_id, flag_cfg)
        for flag_id, flag_cfg in LOCK_FLAGS.items()
    ]
    async_add_entities(entities)  # ✅ sans await

class EvoStartLock(CoordinatorEntity, LockEntity):
    def __init__(self, coordinator, flag_id, flag_cfg):
        super().__init__(coordinator)
        self._flag_id = flag_id
        self._cfg = flag_cfg
        self._attr_name = f"EVO-START {flag_cfg['name']}"
        self._attr_unique_id = f"evo_start_{flag_id}"
        self._attr_icon = flag_cfg["icon"]
        self._attr_should_poll = False

        # 🔐 UI : LOCK/UNLOCK seulement pour Central Lock
        if flag_id == "vcl_lok":
            self._attr_supported_features = 1  # peut être remplacé par LockEntityFeature.LOCK or UNLOCK si besoin
        else:
            self._attr_supported_features = 0  # lecture seule

    @property
    def is_locked(self):
        if not self.coordinator.data:
            return None
        flags = self.coordinator.data.get("flags", {})
        bit = str(flags.get(self._flag_id))  # 🔐 force string pour éviter bool vs str
        if bit not in ("0", "1"):
            return None

        inverted = self._cfg.get("inverted", False)
        return bit == ("0" if inverted else "1")

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "evo_start_vehicle")},
            "name": self.coordinator.data.get("carinfo", {}).get("cname", "EVO-START Vehicle"),
            "manufacturer": "Fortin",
            "model": "EVO-START",
            "entry_type": "service",
        }
