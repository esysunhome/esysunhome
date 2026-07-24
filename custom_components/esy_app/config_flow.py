from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EsyAppApiClient, EsyAppApiError
from .const import (
    CONF_BASE_URL,
    CONF_DEVICES,
    CONF_DEVICE_SNS,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_SHOW_POWER_PAGE,
    CONF_USERNAME,
    DEFAULT_NAME,
    DOMAIN,
)


class EsyAppConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an ESY App config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._name = DEFAULT_NAME
        self._base_url = ""
        self._username = ""
        self._password = ""
        self._token = ""
        self._show_power_page = True
        self._client: EsyAppApiClient | None = None
        self._devices: list[dict[str, str]] = []

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            self._name = user_input.get(CONF_NAME) or DEFAULT_NAME
            self._base_url = user_input[CONF_BASE_URL].rstrip("/")
            self._username = user_input[CONF_USERNAME].strip()
            self._password = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            self._client = EsyAppApiClient(
                session,
                self._base_url,
                username=self._username,
                password=self._password,
            )
            try:
                self._token = await self._client.login()
                raw_devices = await self._client.get_devices()
                self._devices = _parse_device_records(raw_devices)
                if not self._devices:
                    errors["base"] = "no_devices"
                return await self.async_step_device()
            except EsyAppApiError:
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_BASE_URL, default="https://your-api.example.com"): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_device(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_sn = user_input["device"]
            self._show_power_page = user_input.get(CONF_SHOW_POWER_PAGE, True)
            for device in self._devices:
                if device["sn"] == selected_sn:
                    return await self._create_entry(device)
            errors["base"] = "device_not_found"

        options = {device["sn"]: _device_label(device) for device in self._devices}
        default_device = self._devices[0]["sn"] if self._devices else None
        schema = {
            vol.Required("device", default=default_device): vol.In(options),
            vol.Optional(CONF_SHOW_POWER_PAGE, default=self._show_power_page): bool,
        }
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def _create_entry(self, device: dict[str, str]):
        devices = [device]
        unique_devices = ",".join(f"{item['sn']}:{item.get('device_id', '')}" for item in devices)
        await self.async_set_unique_id(f"{DOMAIN}:{self._base_url}:{self._username}:{unique_devices}")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"{self._name} ({device['sn']})",
            data={
                CONF_NAME: self._name,
                CONF_BASE_URL: self._base_url,
                CONF_USERNAME: self._username,
                CONF_PASSWORD: self._password,
                CONF_TOKEN: self._token,
                CONF_DEVICES: devices,
                CONF_DEVICE_SNS: [device["sn"]],
                CONF_SHOW_POWER_PAGE: self._show_power_page,
            },
        )


def _parse_device_records(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    devices: list[dict[str, str]] = []
    seen: set[str] = set()
    for record in records:
        sn = _first_present(record, ("sn", "deviceSn", "deviceSN", "serialNumber", "serialNo", "deviceCode"))
        if not sn:
            continue
        sn = str(sn)
        if sn in seen:
            continue
        seen.add(sn)
        device_id = _first_present(record, ("id", "deviceId", "device_id"))
        name = _first_present(record, ("name", "deviceName", "alias", "plantName"))
        device = {"sn": sn}
        if device_id:
            device["device_id"] = str(device_id)
        if name:
            device["name"] = str(name)
        devices.append(device)
    return devices


def _first_present(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _device_label(device: dict[str, str]) -> str:
    name = device.get("name")
    device_id = device.get("device_id")
    if name and device_id:
        return f"{name} ({device['sn']} / {device_id})"
    if name:
        return f"{name} ({device['sn']})"
    if device_id:
        return f"{device['sn']} ({device_id})"
    return device["sn"]
