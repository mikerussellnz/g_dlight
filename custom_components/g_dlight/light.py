"""Google Dlight light platform."""

from datetime import timedelta
from typing import Any, override

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import DlightClient
from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=5)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a Google Dlight light."""
    async_add_entities([GoogleDlightLight(entry.runtime_data)])


class GoogleDlightLight(LightEntity):
    """Representation of a Google Dlight light."""

    _attr_has_entity_name = True
    _attr_name = "Light"
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_min_color_temp_kelvin = 2600
    _attr_max_color_temp_kelvin = 6000

    def __init__(self, client: DlightClient) -> None:
        """Initialize the light."""
        self._client = client
        self._attr_unique_id = client.device_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, client.device_id)},
            name="Google Dlight",
            manufacturer="Google",
            model="Dlight",
            serial_number=client.device_id,
        )
        self._attr_is_on = False
        self._attr_brightness = 255
        self._attr_color_temp_kelvin = 4000
        self._attr_color_mode = ColorMode.COLOR_TEMP

    async def async_update(self) -> None:
        """Fetch the current state from the device."""
        state = await self._client.async_get_state()
        self._attr_is_on = state["on"]
        self._attr_brightness = round(state["brightness"] * 255 / 100)
        self._attr_color_temp_kelvin = state["color"]["temperature"]
        self._attr_color_mode = ColorMode.COLOR_TEMP

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
            native_brightness = max(1, round(brightness * 100 / 255))
            self._attr_brightness = round(native_brightness * 255 / 100)
            await self._client.async_set_brightness(native_brightness)
        if (color_temp := kwargs.get(ATTR_COLOR_TEMP_KELVIN)) is not None:
            self._attr_color_temp_kelvin = color_temp
            self._attr_color_mode = ColorMode.COLOR_TEMP
            await self._client.async_set_color_temperature(color_temp)
        await self._client.async_turn_on()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        self._attr_is_on = False
        await self._client.async_turn_off()
        self.async_write_ha_state()
