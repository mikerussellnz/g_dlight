"""Async client for Google Dlight devices."""

import asyncio
import json
import logging
import struct
from typing import Any

_LOGGER = logging.getLogger(__name__)

COMMAND_ID = "50"
PORT = 3333
SERVICE_TYPE = "_ged7._tcp.local."
SUCCESS = "SUCCESS"


class DlightError(Exception):
    """Error communicating with a Google Dlight device."""


class DlightClient:
    """Communicate with one Google Dlight device."""

    def __init__(self, device_id: str, host: str) -> None:
        """Initialize the client."""
        self.device_id = device_id
        self.host = host

    async def async_get_state(self) -> dict[str, Any]:
        """Return the current device state."""
        response = await self._async_send_command("QUERY_DEVICE_STATES")
        return response["states"]

    async def async_turn_on(self) -> None:
        """Turn the light on."""
        await self._async_execute({"on": True})

    async def async_turn_off(self) -> None:
        """Turn the light off."""
        await self._async_execute({"on": False})

    async def async_set_brightness(self, brightness: int) -> None:
        """Set brightness on the device's native 1-100 scale."""
        await self._async_execute({"brightness": brightness})

    async def async_set_color_temperature(self, temperature: int) -> None:
        """Set color temperature in Kelvin."""
        await self._async_execute({"color": {"temperature": temperature}})

    async def _async_execute(self, command: dict[str, Any]) -> None:
        """Execute a device command."""
        await self._async_send_command("EXECUTE", command)

    async def _async_send_command(
        self, command_type: str, command: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a command and parse the length-prefixed JSON response."""
        payload = {
            "deviceId": self.device_id,
            "commandId": COMMAND_ID,
            "commandType": command_type,
        }
        if command is not None:
            payload["commands"] = [command]
        else:
            payload["commands"] = []

        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, PORT), timeout=10
        )
        try:
            writer.write(json.dumps(payload, separators=(",", ":")).encode())
            await writer.drain()
            response_header = await reader.readexactly(4)
            response_length = struct.unpack(">I", response_header)[0]
            if response_length > 5000:
                little_endian_length = struct.unpack("<I", response_header)[0]
                ascii_length = (
                    int(response_header) if response_header.isdigit() else None
                )
                if little_endian_length > 5000 and (
                    ascii_length is None or ascii_length > 5000
                ):
                    _LOGGER.error(
                        "Invalid Google Dlight response header %s (big-endian=%s, "
                        "little-endian=%s, ascii=%s)",
                        response_header.hex(),
                        response_length,
                        little_endian_length,
                        ascii_length,
                    )
                    raise DlightError(
                        "Invalid response length: "
                        f"header={response_header.hex()} "
                        f"big_endian={response_length} "
                        f"little_endian={little_endian_length} "
                        f"ascii={ascii_length}"
                    )
                if ascii_length is not None and ascii_length <= 5000:
                    response_length = ascii_length
                    _LOGGER.debug(
                        "Using ASCII Google Dlight response length %s from %s",
                        ascii_length,
                        response_header,
                    )
                else:
                    response_length = little_endian_length
                    _LOGGER.debug(
                        "Using little-endian Google Dlight response length %s from %s",
                        little_endian_length,
                        response_header.hex(),
                    )
            response = json.loads(await reader.readexactly(response_length))
        except (OSError, TimeoutError, asyncio.IncompleteReadError, ValueError) as err:
            raise DlightError(f"Failed to communicate with {self.host}") from err
        finally:
            writer.close()
            await writer.wait_closed()

        if response.get("status") != SUCCESS:
            raise DlightError("Device rejected the command")
        return response


def service_name(device_id: str) -> str:
    """Return the expected mDNS service instance name."""
    return f"{device_id}.{SERVICE_TYPE}"
