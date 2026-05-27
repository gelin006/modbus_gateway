"""Platform for Modbus Gateway number entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
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
    """Set up Modbus Gateway number entities."""
    hub: ModbusHub = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for unique_id, dp in hub.data_points.items():
        if dp.entity_type == "number":
            entities.append(ModbusGatewayNumber(hub, dp))

    if entities:
        async_add_entities(entities)


class ModbusGatewayNumber(ModbusGatewayEntity, NumberEntity):
    """Representation of a Modbus Gateway number entity."""

    def __init__(self, hub: ModbusHub, data_point: ModbusDataPoint) -> None:
        """Initialize."""
        super().__init__(hub, data_point)
        self._attr_native_value = 0
        self._attr_native_min_value = data_point.min_value or 0
        self._attr_native_max_value = data_point.max_value or 1000
        self._attr_native_step = data_point.step or 1
        self._attr_native_unit_of_measurement = data_point.unit
        self._attr_mode = NumberMode.BOX

    def _process_updated_value(self, value: Any) -> None:
        """Process number value."""
        if isinstance(value, (int, float)):
            self._attr_native_value = float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        success = await self._hub.async_write_data(self._data_point, value)
        if success:
            self._attr_native_value = value
            self.async_write_ha_state()
