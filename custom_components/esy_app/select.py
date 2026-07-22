from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EsyAppCoordinator

FALLBACK_MODE_LABELS = {
    1: "Regular Mode",
    2: "Emergency Mode",
    3: "Electricity Sell Mode",
    "1": "Regular Mode",
    "2": "Emergency Mode",
    "3": "Electricity Sell Mode",
    4: "Emergency Mode",
    "4": "Emergency Mode",
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: EsyAppCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [EsyRunModeSelect(coordinator, sn) for sn in coordinator.sns if coordinator.device_id_for_sn(sn)]
    async_add_entities(entities)


class EsyRunModeSelect(CoordinatorEntity[EsyAppCoordinator], SelectEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "run_mode"
    _attr_icon = "mdi:battery-sync-outline"

    def __init__(self, coordinator: EsyAppCoordinator, sn: str) -> None:
        super().__init__(coordinator)
        self.sn = sn
        self._attr_unique_id = f"{DOMAIN}_{sn}_run_mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, sn)},
            "name": f"ESY {sn}",
            "manufacturer": "ESY",
        }

    @property
    def options(self) -> list[str]:
        return list(self.coordinator.mode_options_for_sn(self.sn))

    @property
    def current_option(self) -> str | None:
        device = self.coordinator.data.get(self.sn, {}) if self.coordinator.data else {}
        mode_options = self.coordinator.mode_options_for_sn(self.sn)
        reverse = {value: label for label, value in mode_options.items()}
        reverse.update({str(value): label for label, value in mode_options.items()})

        for key in ("code", "systemRunMode", "mode", "runMode", "modeCode", "patternCode"):
            mode_code = device.get(key)
            if mode_code in reverse:
                return reverse[mode_code]
            if str(mode_code) in reverse:
                return reverse[str(mode_code)]
            if mode_code in FALLBACK_MODE_LABELS:
                return FALLBACK_MODE_LABELS[mode_code]
        return None

    async def async_select_option(self, option: str) -> None:
        device_id = self.coordinator.device_id_for_sn(self.sn)
        if not device_id:
            raise HomeAssistantError("Device id is required to switch operating mode")

        mode_options = self.coordinator.mode_options_for_sn(self.sn)
        mode_code = mode_options.get(option)
        if mode_code is None:
            raise HomeAssistantError(f"Unsupported operating mode: {option}")

        await self.coordinator.client.set_base_mode(device_id, mode_code)
        await self.coordinator.async_request_refresh()
