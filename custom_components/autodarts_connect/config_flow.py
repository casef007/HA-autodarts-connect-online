"""Config Flow für Autodarts Connect Online."""
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

DATA_SCHEMA = vol.Schema({
    vol.Required("email"): str,
    vol.Required("password"): str,
    vol.Required("board_id"): str,
})

class AutodartsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # FIX: Check ob die Board ID schon existiert (Duplicate Protection)
            await self.async_set_unique_id(user_input["board_id"])
            self._abort_if_unique_id_configured()
            
            # Simple Validation
            if not user_input["email"] or not user_input["password"]:
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(
                    title=f"Board {user_input['board_id'][:8]}",
                    data=user_input
                )

        return self.async_show_form(
            step_id="user", 
            data_schema=DATA_SCHEMA, 
            errors=errors
        )