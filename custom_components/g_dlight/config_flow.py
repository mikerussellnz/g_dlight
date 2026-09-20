"""Config flow for the Google Dlight integration."""

import logging

import probatio

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import CONF_DEVICE_CODE, CONF_SERVICE_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_DEVICE_CODE): str,
    }
)


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Google Dlight."""

    VERSION = 1

    _discovered_host: str | None = None
    _discovered_service_name: str | None = None

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_CODE])
            self._abort_if_unique_id_configured()
            data = dict(user_input)
            if self._discovered_service_name:
                data[CONF_SERVICE_NAME] = self._discovered_service_name
            return self.async_create_entry(title="Google Dlight", data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle mDNS discovery."""
        if any(
            entry.data.get(CONF_SERVICE_NAME) == discovery_info.name
            for entry in self.hass.config_entries.async_entries(DOMAIN)
        ):
            return self.async_abort(reason="already_configured")

        _LOGGER.debug(
            "Discovered Google Dlight service: name=%s, host=%s, port=%s, properties=%s",
            discovery_info.name,
            discovery_info.host,
            discovery_info.port,
            discovery_info.properties,
        )
        self._discovered_host = discovery_info.host
        self._discovered_service_name = discovery_info.name
        return await self.async_step_user()
