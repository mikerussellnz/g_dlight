"""Google Dlight light platform."""

import logging
from typing import Any, override

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_DEVICE_CODE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a Google Dlight light."""
    async_add_entities([GoogleDlightLight(entry)])


class GoogleDlightLight(LightEntity):
    """Representation of a Google Dlight light."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS, ColorMode.COLOR_TEMP}
    _attr_min_color_temp_kelvin = 2700
    _attr_max_color_temp_kelvin = 6500

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the light."""
        self._attr_unique_id = entry.unique_id
        self._attr_device_code = entry.data[CONF_DEVICE_CODE]
        self._attr_is_on = False
        self._attr_brightness = 255
        self._attr_color_temp_kelvin = 4000
        self._attr_color_mode = ColorMode.BRIGHTNESS

    @property
    @override
    def is_on(self) -> bool:
        """Return whether the light is on."""
        return self._attr_is_on

    @property
    @override
    def brightness(self) -> int:
        """Return the current brightness."""
        return self._attr_brightness

    @property
    @override
    def color_mode(self) -> ColorMode:
        """Return the current color mode."""
        return self._attr_color_mode

    @property
    @override
    def color_temp_kelvin(self) -> int:
        """Return the current color temperature."""
        return self._attr_color_temp_kelvin

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on and apply requested settings."""
        self._attr_is_on = True
        if (brightness := kwargs.get(ATTR_BRIGHTNESS)) is not None:
            self._attr_brightness = brightness
            self._attr_color_mode = ColorMode.BRIGHTNESS
        if (color_temp := kwargs.get(ATTR_COLOR_TEMP_KELVIN)) is not None:
            self._attr_color_temp_kelvin = color_temp
            self._attr_color_mode = ColorMode.COLOR_TEMP
        await self._async_send_command("turn_on", kwargs)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        self._attr_is_on = False
        await self._async_send_command("turn_off", kwargs)
        self.async_write_ha_state()

    async def _async_send_command(self, command: str, data: dict[str, Any]) -> None:
        """Placeholder for the Google Dlight network request."""
        _LOGGER.debug(
            "Google Dlight command placeholder: code=%s command=%s data=%s",
            self._attr_device_code,
            command,
            data,
        )
