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
            # 1. Leerzeichen am Anfang/Ende entfernen (Strip)
            user_input["email"] = user_input["email"].strip()
            user_input["password"] = user_input["password"].strip()
            user_input["board_id"] = user_input["board_id"].strip()

            # Check ob die Board ID schon existiert (Duplicate Protection)
            await self.async_set_unique_id(user_input["board_id"])
            self._abort_if_unique_id_configured()
            
            # 2. Simple Validation jetzt inkl. board_id
            if not user_input["email"] or not user_input["password"] or not user_input["board_id"]:
                errors["base"] = "incomplete_input"
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