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
    entities = [
        EvoStartButton(coordinator, button_id, button_cfg)
        for button_id, button_cfg in BUTTON_TYPES.items()
    ]
    async_add_entities(entities)

class EvoStartButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, button_id, button_cfg):
        super().__init__(coordinator)
        self._button_id = button_id
        self._cfg = button_cfg
        self._attr_name = f"EVO-START {button_cfg['name']}"
        self._attr_unique_id = f"evo_start_{button_id}"
        self._attr_icon = button_cfg["icon"]

    async def async_press(self) -> None:
        if self._cfg["action"] == "start":
            await self.coordinator.async_remote_start()
        elif self._cfg["action"] == "stop":
            await self.coordinator.async_remote_stop()

    @property
    def available(self) -> bool:
        """Only show start/stop based on engine status."""
        if not self.coordinator.data:
            return False

        flags = self.coordinator.data.get("flags", {})
        engine_flag = flags.get("vcl_eng")
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
            "identifiers": {(DOMAIN, "evo_start_vehicle")},
            "name": self.coordinator.data.get("carinfo", {}).get("cname", "EVO-START Vehicle"),
            "manufacturer": "Fortin",
            "model": "EVO-START",
            "entry_type": "service",
        }
