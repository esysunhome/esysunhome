from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EsyAppApiClient, EsyAppApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class EsyAppCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetch ESY device data for all configured devices."""

    def __init__(self, hass: HomeAssistant, client: EsyAppApiClient, devices: list[dict[str, str]]) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.devices = devices
        self.sns = [device["sn"] for device in devices]
        self.polling_enabled = True

    def device_id_for_sn(self, sn: str) -> str | None:
        for device in self.devices:
            if device["sn"] == sn:
                return device.get("device_id")
        return None

    def mode_options_for_sn(self, sn: str) -> dict[str, int | str]:
        device = self.data.get(sn, {}) if self.data else {}
        options = device.get("_mode_options")
        if isinstance(options, dict) and options:
            return options
        return {
            "Regular Mode": 1,
            "Emergency Mode": 2,
            "Electricity Sell Mode": 3,
        }

    def set_polling_enabled(self, enabled: bool) -> None:
        self.polling_enabled = enabled

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        if not self.polling_enabled and self.data is not None:
            return self.data

        data: dict[str, dict[str, Any]] = {}
        for device in self.devices:
            sn = device["sn"]
            device_id = device.get("device_id")
            try:
                merged = await self.client.get_device_data(sn)
                merged["sn"] = sn
                if device_id:
                    merged["deviceId"] = device_id
                    try:
                        merged.update(await self.client.get_device_detail(device_id))
                    except EsyAppApiError as err:
                        _LOGGER.warning("Failed to fetch ESY detail for %s: %s", sn, err)
                    try:
                        patterns = await self.client.get_mode_patterns(device_id)
                        merged["_mode_patterns"] = _extract_pattern_records(patterns)
                        merged["_mode_options"] = _build_mode_options(merged["_mode_patterns"])
                    except EsyAppApiError as err:
                        _LOGGER.warning("Failed to fetch ESY pattern modes for %s: %s", sn, err)
                data[sn] = merged
            except EsyAppApiError as err:
                raise UpdateFailed(f"Failed to update ESY device {sn}: {err}") from err
        return data


def _extract_pattern_records(payload: Any) -> list[dict[str, Any]]:
    """Return pattern records from common /lsypattern/page response shapes."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("records", "list", "rows", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    nested = payload.get("data")
    if isinstance(nested, dict):
        return _extract_pattern_records(nested)
    if isinstance(nested, list):
        return [item for item in nested if isinstance(item, dict)]
    return []


def _build_mode_options(records: list[dict[str, Any]]) -> dict[str, int | str]:
    options: dict[str, int | str] = {}
    for record in records:
        code = _first_present(record, ("code", "modeCode", "patternCode", "value", "id"))
        name = _first_present(record, ("name", "patternName", "modeName", "title", "label", "description", "desc"))
        if code is None or name is None:
            continue
        options[str(name)] = code
    return options


def _first_present(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None
