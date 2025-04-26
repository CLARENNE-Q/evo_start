from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import EvoStartCoordinator

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the EVO-START component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EVO-START from a config entry."""
    email = entry.data["email"]
    password = entry.data["password"]

    coordinator = EvoStartCoordinator(hass, email, password)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Charger les plateformes
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, ["sensor", "lock", "device_tracker", "button"])
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload EVO-START entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, ["sensor", "lock", "device_tracker", "button"]):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
