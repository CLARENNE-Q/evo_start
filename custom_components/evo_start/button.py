import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

BUTTON_TYPES = {
    "remote_start": {
        "name": "Remote Start",
        "icon": "mdi:car-key",
        "action": "start"
    },
    "remote_stop": {
        "name": "Remote Stop",
        "icon": "mdi:car-off",
        "action": "stop"
    }
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    
    # Create buttons for each vehicle
    for vehicle_id in coordinator.get_all_vehicle_ids():
        vehicle_data = coordinator.get_vehicle_data(vehicle_id)
        vehicle_name = vehicle_data.get("carinfo", {}).get("cname", f"Vehicle {vehicle_id}")
        
        for button_id, button_cfg in BUTTON_TYPES.items():
            entities.append(EvoStartButton(coordinator, vehicle_id, button_id, button_cfg, vehicle_name))
    
    async_add_entities(entities)

class EvoStartButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, vehicle_id, button_id, button_cfg, vehicle_name):
        super().__init__(coordinator)
        self._vehicle_id = vehicle_id
        self._button_id = button_id
        self._cfg = button_cfg
        self._vehicle_name = vehicle_name
        self._attr_name = f"EVO-START {vehicle_name} {button_cfg['name']}"
        self._attr_unique_id = f"evo_start_{vehicle_id}_{button_id}"
        self._attr_icon = button_cfg["icon"]

    async def async_press(self) -> None:
        if self._cfg["action"] == "start":
            await self.coordinator.async_remote_start(self._vehicle_id)
            await asyncio.sleep(5)
            await self.coordinator.async_request_refresh()
        elif self._cfg["action"] == "stop":
            await self.coordinator.async_remote_stop(self._vehicle_id)
            await asyncio.sleep(5)
            await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Only show start/stop based on engine status."""
        vehicle_flags = self.coordinator.get_vehicle_flags(self._vehicle_id)
        if not vehicle_flags:
            return False

        engine_flag = vehicle_flags.get("vcl_eng")
        if engine_flag is None:
            return False

        engine_on = str(engine_flag) == "1"

        if self._cfg["action"] == "start":
            return not engine_on  # show start button if engine is OFF
        if self._cfg["action"] == "stop":
            return engine_on  # show stop button if engine is ON

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
