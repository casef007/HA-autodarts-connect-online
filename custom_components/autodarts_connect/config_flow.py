"""Config flow für Autodarts Connect Online."""
import logging
import voluptuous as vol
import aiohttp
from homeassistant import config_entries
from .const import DOMAIN, URL_CREDENTIALS, URL_TOKEN

_LOGGER = logging.getLogger(__name__)

class AutodartsConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Behandelt den Config Flow für Autodarts Connect Online."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            valid = await self._test_credentials(user_input["email"], user_input["password"])
            if valid:
                return self.async_create_entry(title=f"Board {user_input['board_id']}", data=user_input)
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("email"): str,
                vol.Required("password"): str,
                vol.Required("board_id"): str,
            }),
            errors=errors
        )

    async def _test_credentials(self, email, password):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(URL_CREDENTIALS, timeout=10) as resp:
                    if resp.status != 200: return False
                    creds = await resp.json()
                    c_id, c_sec = creds.get("client_id"), creds.get("client_secret")

                data = {"client_id": c_id, "client_secret": c_sec, "grant_type": "password", "username": email, "password": password}
                async with session.post(URL_TOKEN, data=data, ssl=False, timeout=10) as token_resp:
                    return token_resp.status == 200
        except Exception:
            return False