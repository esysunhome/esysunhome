from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import frontend, websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EsyAppApiClient
from .const import (
    CONF_BASE_URL,
    CONF_DEVICES,
    CONF_DEVICE_SNS,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USERNAME,
    DOMAIN,
)
from .coordinator import EsyAppCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SELECT, Platform.SWITCH]
CARD_URL = "/esy_app_static/esy-power-chart-card.js"
STATIC_PATH = Path(__file__).parent / "www"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = EsyAppApiClient(
        session,
        entry.data[CONF_BASE_URL],
        entry.data.get(CONF_TOKEN),
        entry.data.get(CONF_USERNAME),
        entry.data.get(CONF_PASSWORD),
    )
    devices = entry.data.get(CONF_DEVICES) or [{"sn": sn} for sn in entry.data[CONF_DEVICE_SNS]]
    coordinator = EsyAppCoordinator(hass, client, devices)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _register_static_path(hass)
    _register_websocket_api(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def _register_static_path(hass: HomeAssistant) -> None:
    if hass.data.setdefault(DOMAIN, {}).get("static_registered"):
        return
    hass.http.register_static_path("/esy_app_static", str(STATIC_PATH), cache_headers=False)
    hass.data[DOMAIN]["static_registered"] = True


def _register_websocket_api(hass: HomeAssistant) -> None:
    if hass.data.setdefault(DOMAIN, {}).get("websocket_registered"):
        return
    websocket_api.async_register_command(hass, websocket_power_data)
    hass.data[DOMAIN]["websocket_registered"] = True


@websocket_api.websocket_command(
    {
        vol.Required("type"): "esy_app/power_data",
        vol.Optional("entry_id"): str,
        vol.Required("device_id"): str,
        vol.Required("date"): str,
    }
)
@websocket_api.async_response
async def websocket_power_data(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Return daily power curve data for the custom Lovelace card."""
    date = msg["date"]
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        connection.send_error(msg["id"], "invalid_date", "date must be YYYY-MM-DD")
        return

    coordinator = _coordinator_for_message(hass, msg)
    if coordinator is None:
        connection.send_error(msg["id"], "entry_not_found", "ESY App config entry was not found")
        return

    try:
        rows = await coordinator.client.get_power_data(msg["device_id"], date)
    except Exception as err:  # noqa: BLE001 - send concise error to frontend
        connection.send_error(msg["id"], "request_failed", str(err))
        return

    connection.send_result(msg["id"], {"date": date, "rows": rows})


def _coordinator_for_message(hass: HomeAssistant, msg: dict[str, Any]) -> EsyAppCoordinator | None:
    domain_data = hass.data.get(DOMAIN, {})
    entry_id = msg.get("entry_id")
    if entry_id:
        coordinator = domain_data.get(entry_id)
        return coordinator if isinstance(coordinator, EsyAppCoordinator) else None
    for value in domain_data.values():
        if isinstance(value, EsyAppCoordinator):
            return value
    return None

