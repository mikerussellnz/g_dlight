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
        command_json = json.dumps(command) if command is not None else ""
        request = (
            f'{{"deviceId":"{self.device_id}","commandId":"{COMMAND_ID}",'
            f'"commandType":"{command_type}","commands":[{command_json}]}}'
        )

        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, PORT), timeout=10
        )
        try:
            _LOGGER.debug("Sending Google Dlight request: %s", request)
            writer.write(request.encode())
            await writer.drain()
            response_header = await reader.readexactly(4)
            _LOGGER.debug(
                "Received Google Dlight response prefix: bytes=%s text=%r",
                response_header.hex(" "),
                response_header.decode(errors="replace"),
            )
            response = await self._async_read_framed_response(reader, response_header)
        except (OSError, TimeoutError, asyncio.IncompleteReadError, ValueError) as err:
            raise DlightError(f"Failed to communicate with {self.host}") from err
        finally:
            writer.close()
            await writer.wait_closed()

        if response.get("status") != SUCCESS:
            raise DlightError(f"Device rejected the command: {response}")
        return response

    async def _async_read_framed_response(
        self, reader: asyncio.StreamReader, response_header: bytes | None = None
    ) -> dict[str, Any]:
        """Read a length-prefixed JSON response."""
        response_header = response_header or await reader.readexactly(4)
        response_length = struct.unpack(">I", response_header)[0]
        if response_length > 5000:
            try:
                raw_response = response_header + await asyncio.wait_for(
                    reader.read(4096), timeout=1
                )
            except TimeoutError:
                raw_response = response_header
            _LOGGER.error(
                "Raw Google Dlight response: bytes=%s text=%r",
                raw_response.hex(" "),
                raw_response.decode(errors="replace"),
            )
            raise DlightError(
                "Invalid response length: "
                f"header={response_header.hex()} length={response_length}"
            )
        return json.loads(await reader.readexactly(response_length))


def service_name(device_id: str) -> str:
    """Return the expected mDNS service instance name."""
    return f"{device_id}.{SERVICE_TYPE}"
