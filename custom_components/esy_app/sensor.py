from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfEnergy, UnitOfFrequency, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EsyAppCoordinator


@dataclass(frozen=True, kw_only=True)
class EsySensorEntityDescription(SensorEntityDescription):
    json_key: str


SENSOR_DESCRIPTIONS: tuple[EsySensorEntityDescription, ...] = (
    # Grid and energy basics
    EsySensorEntityDescription(key="device_status", json_key="status", translation_key="device_status"),
    EsySensorEntityDescription(key="online_status", json_key="onlineStatus", translation_key="online_status"),
    EsySensorEntityDescription(key="battery_status", json_key="batteryStatus", translation_key="battery_status"),
    EsySensorEntityDescription(key="switch_status", json_key="switchStatus", translation_key="switch_status"),
    EsySensorEntityDescription(key="operation_status", json_key="operationStatus", translation_key="operation_status"),
    EsySensorEntityDescription(key="fault_code", json_key="faultCode", translation_key="fault_code"),
    EsySensorEntityDescription(key="mode_code", json_key="modeCode", translation_key="mode_code"),
    EsySensorEntityDescription(key="mode_description", json_key="modeDesc", translation_key="mode_description"),
    EsySensorEntityDescription(key="energy_flow_switch", json_key="energyFlowSwitch", translation_key="energy_flow_switch"),

    # Grid and energy basics
    EsySensorEntityDescription(key="battery_soc", json_key="batteryLevel", translation_key="battery_soc", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="soc_lower_limit", json_key="socLowerLimit", translation_key="soc_lower_limit", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),

    # Grid and energy basics
    EsySensorEntityDescription(key="pv_power", json_key="pvPower", translation_key="pv_power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="load_power", json_key="loadElec", translation_key="load_power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_import_power", json_key="gridImportPower", translation_key="grid_import_power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_export_power", json_key="gridExportPower", translation_key="grid_export_power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="output_power", json_key="outputPower", translation_key="output_power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="active_power_total", json_key="activePowerTotal", translation_key="active_power_total", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),

    # Grid and energy basics
    EsySensorEntityDescription(key="grid_voltage_l1", json_key="gridVoltageL1", translation_key="grid_voltage_l1", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_voltage_l2", json_key="gridVoltageL2", translation_key="grid_voltage_l2", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_voltage_l3", json_key="gridVoltageL3", translation_key="grid_voltage_l3", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_current_l1", json_key="gridCurrentL1", translation_key="grid_current_l1", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_current_l2", json_key="gridCurrentL2", translation_key="grid_current_l2", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_current_l3", json_key="gridCurrentL3", translation_key="grid_current_l3", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_frequency", json_key="gridFrequency", translation_key="grid_frequency", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="daily_energy_yield", json_key="dailyEnergyYield", translation_key="daily_energy_yield", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    EsySensorEntityDescription(key="total_energy_yield", json_key="totalEnergyYield", translation_key="total_energy_yield", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    EsySensorEntityDescription(key="grid_import_energy_total", json_key="gridImportEnergyTotal", translation_key="grid_import_energy_total", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    EsySensorEntityDescription(key="grid_export_energy_total", json_key="gridExportEnergyTotal", translation_key="grid_export_energy_total", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: EsyAppCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[EsyDeviceSensor] = []
    for sn in coordinator.sns:
        for description in SENSOR_DESCRIPTIONS:
            entities.append(EsyDeviceSensor(coordinator, sn, description))
    async_add_entities(entities)


class EsyDeviceSensor(CoordinatorEntity[EsyAppCoordinator], SensorEntity):
    entity_description: EsySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: EsyAppCoordinator, sn: str, description: EsySensorEntityDescription) -> None:
        super().__init__(coordinator)
        self.sn = sn
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{sn}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, sn)},
            "name": f"ESY {sn}",
            "manufacturer": "ESY",
        }

    @property
    def native_value(self) -> Any:
        device = self.coordinator.data.get(self.sn, {}) if self.coordinator.data else {}
        return device.get(self.entity_description.json_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        device = self.coordinator.data.get(self.sn, {}) if self.coordinator.data else {}
        if self.entity_description.key not in {"device_status", "online_status", "operation_status", "fault_code", "mode_code", "energy_flow_switch"}:
            return {"sn": self.sn}
        return {"sn": self.sn, "raw": device}

