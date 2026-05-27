"""Platform for Modbus Gateway select entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ModbusHub
from .const import CONF_DATA_POINTS, CONF_DP_NAME, CONF_DP_OPTIONS, DOMAIN
from .entity import ModbusGatewayEntity
from .modbus_hub import ModbusDataPoint

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Modbus Gateway select entities."""
    hub: ModbusHub = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for unique_id, dp in hub.data_points.items():
        if dp.entity_type == "select" and dp.options:
            entities.append(ModbusGatewaySelect(hub, dp))

    if entities:
        async_add_entities(entities)


class ModbusGatewaySelect(ModbusGatewayEntity, SelectEntity):
    """Representation of a Modbus Gateway select."""

    def __init__(self, hub: ModbusHub, data_point: ModbusDataPoint) -> None:
        """Initialize."""
        super().__init__(hub, data_point)
        self._attr_options = data_point.options or []
        self._attr_current_option = None

    def _process_updated_value(self, value: Any) -> None:
        """Process the select value."""
        if value is None:
            return
        idx = int(value)
        if 0 <= idx < len(self._attr_options):
            self._attr_current_option = self._attr_options[idx]
        elif str(value) in self._attr_options:
            self._attr_current_option = str(value)

    async def async_select_option(self, option: str) -> None:
        """Write the selected option index to Modbus."""
        if option in self._attr_options:
            idx = self._attr_options.index(option)
            success = await self._hub.async_write_data(self._data_point, idx)
            if success:
                self._attr_current_option = option
                self.async_write_ha_state()
