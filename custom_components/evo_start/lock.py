import asyncio

from homeassistant.components.lock import LockEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.lock import LockEntityFeature
from .const import DOMAIN

LOCK_FLAGS = {
    "vcl_lok": {
        "name": "Central Lock",
        "icon": "mdi:lock",
        "inverted": True,
        "actionable": True  # ✅ Central Lock is fully actionable (lock + unlock)
    }
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    
    # Create locks for each vehicle
    for vehicle_id in coordinator.get_all_vehicle_ids():
        vehicle_data = coordinator.get_vehicle_data(vehicle_id)
        vehicle_name = vehicle_data.get("carinfo", {}).get("cname", f"Vehicle {vehicle_id}")
        
        for flag_id, flag_cfg in LOCK_FLAGS.items():
            entities.append(EvoStartLock(coordinator, vehicle_id, flag_id, flag_cfg, vehicle_name))
    
    async_add_entities(entities)

class EvoStartLock(CoordinatorEntity, LockEntity):
    def __init__(self, coordinator, vehicle_id, flag_id, flag_cfg, vehicle_name):
        super().__init__(coordinator)
        self._vehicle_id = vehicle_id
        self._flag_id = flag_id
        self._cfg = flag_cfg
        self._vehicle_name = vehicle_name
        self._attr_name = f"EVO-START {vehicle_name} {flag_cfg['name']}"
        self._attr_unique_id = f"evo_start_{vehicle_id}_{flag_id}"
        self._attr_icon = flag_cfg["icon"]
        self._attr_should_poll = False

    @property
    def is_locked(self):
        vehicle_flags = self.coordinator.get_vehicle_flags(self._vehicle_id)
        if not vehicle_flags:
            return None
            
        bit = str(vehicle_flags.get(self._flag_id))
        if bit not in ("0", "1"):
            return None

        inverted = self._cfg.get("inverted", False)
        return bit == ("0" if inverted else "1")

    async def async_lock(self, **kwargs):
        """Lock the vehicle remotely."""
        if self._flag_id == "vcl_lok" and self._cfg.get("actionable", False):
            await self.coordinator.async_remote_lock(self._vehicle_id)
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs):
        """Unlock the vehicle remotely."""
        if self._flag_id == "vcl_lok" and self._cfg.get("actionable", False):
            await self.coordinator.async_remote_unlock(self._vehicle_id)
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()

    @property
    def available(self):
        """The lock is always available for Central Lock."""
        return True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"evo_start_vehicle_{self._vehicle_id}")},
            "name": self._vehicle_name,
            "manufacturer": "Fortin",
            "model": "EVO-START",
            "entry_type": "service",
        }
