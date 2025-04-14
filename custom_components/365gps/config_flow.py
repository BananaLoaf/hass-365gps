import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import _365GPSDataUpdateCoordinator
from .api import _365GPSAPI


LOGGER = logging.getLogger(DOMAIN)


class GPSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict = None) -> dict:
        if user_input is not None:
            errors = await self.try_login(user_input)
            if not errors:
                return self.async_create_entry(
                    title=f"Account {user_input[CONF_USERNAME][:5]}**********",
                    data=user_input,
                )
        else:
            errors = {}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                # vol.Optional(IS_DEMO_KEY, default=False): cv.boolean,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def try_login(self, user_input: dict):
        errors = {}
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]

        try:
            api = _365GPSAPI(
                username=username,
                password=password,
                hass=self.hass,
            )

        except Exception as e:
            errors["base"] = str(e)
            LOGGER.error(e)

        return errors
