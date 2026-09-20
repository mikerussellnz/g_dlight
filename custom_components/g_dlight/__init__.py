"""The Google Dlight integration."""

import logging

from zeroconf import IPVersion

from homeassistant.components import zeroconf
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import DlightClient, service_name
from .const import CONF_DEVICE_CODE, CONF_SERVICE_NAME

_LOGGER = logging.getLogger(__name__)
_PLATFORMS: list[Platform] = [Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Google Dlight from a config entry."""
    device_id = entry.data[CONF_DEVICE_CODE]
    discovered_service_name = entry.data.get(CONF_SERVICE_NAME, service_name(device_id))
    aiozc = await zeroconf.async_get_async_instance(hass)
    service_info = await aiozc.async_get_service_info(
        "_ged7._tcp.local.", discovered_service_name
    )
    if service_info is None:
        _LOGGER.error("Unable to discover Google Dlight %s", device_id)
        return False

    ip_addresses = service_info.ip_addresses_by_version(IPVersion.All)
    if not ip_addresses:
        _LOGGER.error("Unable to resolve Google Dlight %s", device_id)
        return False

    entry.runtime_data = DlightClient(device_id, str(ip_addresses[0]))

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
