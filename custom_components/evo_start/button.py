import asyncio
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

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
        _LOGGER.info(f"🔘 Button pressed: {self._cfg['action']} for vehicle {self._vehicle_id}")
        
        try:
            if self._cfg["action"] == "start":
                _LOGGER.info(f"🚗 Attempting remote start for vehicle {self._vehicle_id}")
                result = await self.coordinator.async_remote_start(self._vehicle_id)
                if result:
                    _LOGGER.info(f"✅ Remote start command sent successfully for vehicle {self._vehicle_id}")
                else:
                    _LOGGER.error(f"❌ Remote start command failed for vehicle {self._vehicle_id}")
                    
            elif self._cfg["action"] == "stop":
                _LOGGER.info(f"🛑 Attempting remote stop for vehicle {self._vehicle_id}")
                result = await self.coordinator.async_remote_stop(self._vehicle_id)
                if result:
                    _LOGGER.info(f"✅ Remote stop command sent successfully for vehicle {self._vehicle_id}")
                else:
                    _LOGGER.error(f"❌ Remote stop command failed for vehicle {self._vehicle_id}")
            
            # Wait a moment then refresh data to get updated status
            await asyncio.sleep(3)
            await self.coordinator.async_request_refresh()
            
        except Exception as e:
            _LOGGER.exception(f"❌ Exception during {self._cfg['action']} action for vehicle {self._vehicle_id}: {e}")

    @property
    def available(self) -> bool:
        """Only show start/stop based on engine status."""
        vehicle_flags = self.coordinator.get_vehicle_flags(self._vehicle_id)
        
        # If no flags available, still allow the button to be available
        # The user might want to try the action even if status is unknown
        if not vehicle_flags:
            _LOGGER.debug(f"🟡 No vehicle flags available for {self._vehicle_id}, allowing button")
            return True

        engine_flag = vehicle_flags.get("vcl_eng")
        _LOGGER.debug(f"🔧 Engine flag for vehicle {self._vehicle_id}: {engine_flag}")
        
        # If engine status is unknown, allow both buttons to be available
        if engine_flag is None:
            _LOGGER.debug(f"🟡 Engine status unknown for {self._vehicle_id}, allowing button")
            return True

        engine_on = str(engine_flag) == "1"
        _LOGGER.debug(f"🚗 Engine status for vehicle {self._vehicle_id}: {'ON' if engine_on else 'OFF'}")

        if self._cfg["action"] == "start":
            available = not engine_on  # show start button if engine is OFF
            _LOGGER.debug(f"🔘 Start button available for {self._vehicle_id}: {available}")
            return available
        elif self._cfg["action"] == "stop":
            available = engine_on  # show stop button if engine is ON
            _LOGGER.debug(f"🔘 Stop button available for {self._vehicle_id}: {available}")
            return available

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
