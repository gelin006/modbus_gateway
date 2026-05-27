"""Platform for Modbus Gateway climate (thermostat/AC)."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ModbusHub
from .const import CONF_DATA_POINTS, CONF_DP_NAME, DOMAIN
from .entity import ModbusGatewayEntity
from .modbus_hub import ModbusDataPoint

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Modbus Gateway climate entities."""
    hub: ModbusHub = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for unique_id, dp in hub.data_points.items():
        if dp.entity_type == "climate":
            entities.append(ModbusGatewayClimate(hub, dp))

    if entities:
        async_add_entities(entities)


class ModbusGatewayClimate(ModbusGatewayEntity, ClimateEntity):
    """Representation of a Modbus Gateway climate device."""

    def __init__(self, hub: ModbusHub, data_point: ModbusDataPoint) -> None:
        """Initialize."""
        super().__init__(hub, data_point)
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO]
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_target_temperature = 25.0
        self._attr_current_temperature = None
        self._attr_max_temp = data_point.max_value or 35.0
        self._attr_min_temp = data_point.min_value or 16.0
        self._attr_target_temperature_step = data_point.step or 1.0
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
        )

    def _process_updated_value(self, value: Any) -> None:
        """Process the temperature value."""
        if isinstance(value, (int, float)):
            self._attr_current_temperature = float(value)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        mode_map = {
            HVACMode.OFF: 0,
            HVACMode.HEAT: 1,
            HVACMode.COOL: 2,
            HVACMode.AUTO: 3,
        }
        write_value = mode_map.get(hvac_mode, 0)
        success = await self._hub.async_write_data(self._data_point, write_value)
        if success:
            self._attr_hvac_mode = hvac_mode
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            success = await self._hub.async_write_data(
                self._data_point, int(temperature * 10)  # multiply by 10 for precision
            )
            if success:
                self._attr_target_temperature = temperature
                self.async_write_ha_state()
