from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EsyAppCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: EsyAppCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EsyApiPollingSwitch(coordinator, sn) for sn in coordinator.sns])


class EsyApiPollingSwitch(CoordinatorEntity[EsyAppCoordinator], SwitchEntity):
    _attr_has_entity_name = True
    _attr_translation_key = None
    _attr_name = "API Polling"
    _attr_icon = "mdi:reload"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: EsyAppCoordinator, sn: str) -> None:
        super().__init__(coordinator)
        self.sn = sn
        self._attr_unique_id = f"{DOMAIN}_{sn}_api_polling"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, sn)},
            "name": f"ESY {sn}",
            "manufacturer": "ESY",
        }

    @property
    def is_on(self) -> bool:
        return self.coordinator.polling_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.coordinator.set_polling_enabled(True)
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.set_polling_enabled(False)
        self.async_write_ha_state()
