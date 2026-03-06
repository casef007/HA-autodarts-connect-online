"""Die Autodarts Connect Online Integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AutodartsCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Initialisiert die Integration vor den Entries."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setzt ein über die UI konfiguriertes Board auf."""
    coord = AutodartsCoordinator(
        hass, 
        entry.data["email"], 
        entry.data["password"], 
        entry.data["board_id"]
    )
    
    await coord.async_config_entry_first_refresh()
    await coord.async_start()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coord
    
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Entlädt ein Board sauber aus Home Assistant."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    
    if unload_ok:
        coord = hass.data[DOMAIN].pop(entry.entry_id)
        await coord.async_stop()
        
    return unload_ok