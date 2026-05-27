"""Platform for Modbus Gateway switches."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ModbusHub
from .const import CONF_DATA_POINTS, CONF_DP_NAME, DOMAIN, INPUT_TYPE_COIL
from .entity import ModbusGatewayEntity
from .modbus_hub import ModbusDataPoint

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Modbus Gateway switches."""
    hub: ModbusHub = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for unique_id, dp in hub.data_points.items():
        if dp.entity_type == "switch":
            entities.append(ModbusGatewaySwitch(hub, dp))

    if entities:
        async_add_entities(entities)


class ModbusGatewaySwitch(ModbusGatewayEntity, SwitchEntity):
    """Representation of a Modbus Gateway switch."""

    def __init__(self, hub: ModbusHub, data_point: ModbusDataPoint) -> None:
        """Initialize."""
        super().__init__(hub, data_point)
        self._attr_is_on = None

    def _process_updated_value(self, value: Any) -> None:
        """Process a switch value."""
        if isinstance(value, bool):
            self._attr_is_on = value
        elif isinstance(value, (int, float)):
            self._attr_is_on = bool(value)
        else:
            self._attr_is_on = None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        success = await self._hub.async_write_data(self._data_point, 1)
        if success:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        success = await self._hub.async_write_data(self._data_point, 0)
        if success:
            self._attr_is_on = False
            self.async_write_ha_state()
