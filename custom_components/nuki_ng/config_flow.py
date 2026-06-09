from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.network import get_url
from .constants import DOMAIN
from .nuki import NukiInterface

import logging
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)


class NukiNGConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_reauth(self, user_input):
        return await self.async_step_user(user_input)

    async def find_nuki_devices(self, config: dict):
        nuki = NukiInterface(
            self.hass,
            bridge=config.get("address"),
            token=config.get("token"),
            web_token=config.get("web_token")
        )
        title = None
        use_hashed_token = False
        if nuki.token:
            hass_url = config.get("hass_url", "")
            if hass_url.lower().startswith("https://"):
                _LOGGER.error(
                    f"Bridge doesn't support HTTPS callback URLs: {hass_url}")
                return title, "https_not_supported", None, {}
            try:
                info = await nuki.bridge_info()
                use_hashed_token = info.get("bridgeType") == 1
                response = await nuki.bridge_list()
                _LOGGER.debug(f"bridge devices: {response}")
                if not response:
                    return title, "invalid_bridge_token", None, {}
                locks = {str(k): v.get("name", str(k)) for k, v in response.items()}
                title = next(iter(locks.values()))
            except Exception as err:
                _LOGGER.exception(
                    f"Failed to get list of devices from bridge: {err}")
                return title, "invalid_bridge_token", None, {}
        elif nuki.web_token:
            locks = {}
        else:
            locks = {}
        if nuki.web_token:
            try:
                response = await nuki.web_list()
                _LOGGER.debug(f"web devices: {response}")
                if not locks:
                    locks = {str(k): v.get("name", str(k)) for k, v in response.items()}
                    title = next(iter(locks.values()), None)
            except Exception as err:
                _LOGGER.exception(
                    f"Failed to get list of devices from web API: {err}")
                return title, "invalid_web_token", None, {}
        if not locks:
            return title, "invalid_bridge_token", None, {}
        return title, None, use_hashed_token, locks

    def _get_hass_url(self, hass):
        try:
            return get_url(hass)
        except Exception as err:
            _LOGGER.exception(f"Error getting HASS url: {err}")
            return ""

    async def async_step_user(self, user_input):
        errors = None
        _LOGGER.debug(f"Input: {user_input}")
        if user_input is None:
            nuki = NukiInterface(self.hass)
            bridge_address = await nuki.discover_bridge()
            hass_url = self._get_hass_url(self.hass)
            user_input = {
                "address": bridge_address,
                "hass_url": hass_url
            }
        elif not user_input.get("token") and not user_input.get("web_token"):
            errors = dict(base="no_token")
        elif user_input.get("token") and not user_input.get("address"):
            errors = dict(base="no_bridge_url")
        elif user_input.get("token") or user_input.get("web_token"):
            title, err, use_hashed_token, locks = await self.find_nuki_devices(user_input)
            if not err:
                config = {**user_input, "use_hashed": use_hashed_token}
                first_id, first_name = next(iter(locks.items()))

                await self.async_set_unique_id(first_id)
                self._abort_if_unique_id_configured()

                # Spawn discovery flows for all remaining locks immediately
                for lock_id, lock_name in list(locks.items())[1:]:
                    self.hass.async_create_task(
                        self.hass.config_entries.flow.async_init(
                            DOMAIN,
                            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
                            data={**config, "lock_id": lock_id, "lock_name": lock_name},
                        )
                    )

                return self.async_create_entry(
                    title=user_input.get("name") or first_name,
                    data={**config, "lock_id": first_id},
                )
            errors = dict(base=err)
        schema = vol.Schema({
            vol.Optional("address", default=user_input.get("address", "")): cv.string,
            vol.Optional("hass_url", default=user_input.get("hass_url", "")): cv.string,
            vol.Optional("token", default=user_input.get("token", "")): cv.string,
            vol.Optional("web_token", default=user_input.get("web_token", "")): cv.string,
            vol.Optional("name", default=user_input.get("name", "")): cv.string,
            vol.Required("update_seconds", default=user_input.get("update_seconds", 30)): vol.All(
                cv.positive_int,
                vol.Range(min=10, max=600)
            ),
        })
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_integration_discovery(self, discovery_info: dict):
        """Auto-create a config entry for a newly discovered lock."""
        lock_id = str(discovery_info["lock_id"])
        lock_name = discovery_info.get("lock_name", lock_id)

        await self.async_set_unique_id(lock_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=lock_name,
            data=discovery_info,
        )

    # def async_get_options_flow(config_entry):
    #     return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        data = self.config_entry.as_dict()["data"]
        _LOGGER.debug(f"OptionsFlowHandler: {data} {self.config_entry}")
        schema = vol.Schema({
            vol.Required("hass_url", default=data.get("hass_url")): cv.string,
            vol.Required("token", default=data.get("token")): cv.string,
            vol.Optional("web_token", default=data.get("web_token")): cv.string,
        })
        return self.async_show_form(
            step_id="options", data_schema=schema
        )
