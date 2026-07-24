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


SENSOR_NAMES: dict[str, str] = {
    "device_status": "Device Status",
    "online_status": "Grid Connected",
    "battery_status": "Battery Status",
    "switch_status": "Battery Active",
    "operation_status": "Operation Status",
    "fault_code": "Fault Code",
    "mode_code": "Base Operating Mode Code",
    "mode_description": "Base Operating Mode",
    "energy_flow_switch": "Energy Flow Switch",
    "battery_soc": "Battery State of Charge",
    "pv_power": "PV Power",
    "load_power": "Load Power",
    "grid_power": "Grid Power",
    "output_power": "Output Power",
    "grid_import_power": "Grid Import Power",
    "grid_export_power": "Grid Export Power",
    "grid_voltage_l1": "Grid Voltage L1",
    "grid_voltage_l2": "Grid Voltage L2",
    "grid_voltage_l3": "Grid Voltage L3",
    "grid_current_l1": "Grid Current L1",
    "grid_current_l2": "Grid Current L2",
    "grid_current_l3": "Grid Current L3",
    "grid_frequency": "Grid Frequency",
    "daily_generation": "Daily Generation",
    "daily_pv_generation": "Daily PV Generation",
    "daily_grid_import": "Daily Grid Import",
    "daily_grid_export": "Daily Grid Export",
    "total_generation": "Total Generation",
    "total_grid_import": "Total Grid Import",
    "total_grid_export": "Total Grid Export",
    "total_consumption": "Total Consumption",
}

STATE_VALUE_MAP: dict[str, str] = {
    "\u672a\u77e5": "Unknown",
    "\u5173\u95ed": "Off",
    "\u5f00\u542f": "On",
    "\u5f00": "On",
    "\u5173": "Off",
    "\u6b63\u5e38": "Normal",
    "\u79bb\u7ebf": "Offline",
    "\u5728\u7ebf": "Online",
    "\u6545\u969c": "Fault",
    "\u9519\u8bef": "Error",
    "\u5f85\u673a": "Standby",
    "\u8fd0\u884c": "Run",
    "\u5145\u7535": "Charging",
    "\u653e\u7535": "Discharging",
}

STATUS_VALUE_MAPS: dict[str, dict[Any, str]] = {
    "device_status": {0: "Normal", 1: "Maintenance", 2: "Offline", 3: "Error", "0": "Normal", "1": "Maintenance", "2": "Offline", "3": "Error"},
    "online_status": {0: "Disconnected", 1: "Connected", "0": "Disconnected", "1": "Connected"},
    "battery_status": {0: "Standby", 1: "Charging", 2: "Discharging", "0": "Standby", "1": "Charging", "2": "Discharging"},
    "switch_status": {0: "Off", 1: "On", "0": "Off", "1": "On"},
    "energy_flow_switch": {0: "Off", 1: "On", "0": "Off", "1": "On"},
}
SENSOR_DESCRIPTIONS: tuple[EsySensorEntityDescription, ...] = (
    EsySensorEntityDescription(key="device_status", json_key="status"),
    EsySensorEntityDescription(key="online_status", json_key="onlineStatus"),
    EsySensorEntityDescription(key="battery_status", json_key="batteryStatus"),
    EsySensorEntityDescription(key="switch_status", json_key="switchStatus"),
    EsySensorEntityDescription(key="operation_status", json_key="operationStatus"),
    EsySensorEntityDescription(key="fault_code", json_key="faultCode"),
    EsySensorEntityDescription(key="mode_code", json_key="code"),
    EsySensorEntityDescription(key="mode_description", json_key="code"),
    EsySensorEntityDescription(key="energy_flow_switch", json_key="energyFlowSwitch"),
    EsySensorEntityDescription(key="battery_soc", json_key="batteryLevel", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="pv_power", json_key="pvPower", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="load_power", json_key="loadElec", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_power", json_key="activePowerTotal", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="output_power", json_key="outputPower", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_import_power", json_key="gridImportPower", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_export_power", json_key="gridExportPower", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_voltage_l1", json_key="gridVoltageL1", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_voltage_l2", json_key="gridVoltageL2", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_voltage_l3", json_key="gridVoltageL3", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_current_l1", json_key="gridCurrentL1", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_current_l2", json_key="gridCurrentL2", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_current_l3", json_key="gridCurrentL3", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="grid_frequency", json_key="gridFrequency", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT),
    EsySensorEntityDescription(key="daily_generation", json_key="dailyEnergyYield", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    EsySensorEntityDescription(key="daily_pv_generation", json_key="todayPvElec", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    EsySensorEntityDescription(key="daily_grid_import", json_key="todayBuyElec", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    EsySensorEntityDescription(key="daily_grid_export", json_key="todaySellElec", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    EsySensorEntityDescription(key="total_generation", json_key="totalEnergyYield", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    EsySensorEntityDescription(key="total_grid_import", json_key="gridImportEnergyTotal", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    EsySensorEntityDescription(key="total_grid_export", json_key="gridExportEnergyTotal", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    EsySensorEntityDescription(key="total_consumption", json_key="totalConsume", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
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
        self._attr_name = SENSOR_NAMES.get(description.key, description.key.replace("_", " ").title())
        self._attr_unique_id = f"{DOMAIN}_{sn}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, sn)},
            "name": f"ESY {sn}",
            "manufacturer": "ESY",
        }

    @property
    def native_value(self) -> Any:
        device = self.coordinator.data.get(self.sn, {}) if self.coordinator.data else {}
        value = device.get(self.entity_description.json_key)

        if self.entity_description.key == "mode_description":
            mode_options = self.coordinator.mode_options_for_sn(self.sn)
            reverse = {str(code): name for name, code in mode_options.items()}
            return reverse.get(str(value), value)

        status_map = STATUS_VALUE_MAPS.get(self.entity_description.key)
        if status_map is not None:
            return status_map.get(value, status_map.get(str(value), value))

        if isinstance(value, str):
            return STATE_VALUE_MAP.get(value, value)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        device = self.coordinator.data.get(self.sn, {}) if self.coordinator.data else {}
        if self.entity_description.key not in {"device_status", "online_status", "operation_status", "fault_code", "mode_code", "energy_flow_switch"}:
            return {"sn": self.sn}
        return {"sn": self.sn, "raw": device}

