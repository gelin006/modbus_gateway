"""Platform for Modbus Gateway covers (curtains/blinds/shades)."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ModbusHub
from .const import CONF_DATA_POINTS, CONF_DP_NAME, DOMAIN
from .entity import ModbusGatewayEntity
from .modbus_hub import ModbusDataPoint

_LOGGER = logging.getLogger(__name__)

# Default mapping for cover:
# address = position (0-100%, 0=closed, 100=open)
# For coil-based covers: address = up/down (1=up/stop, 0=down)
#                         address+1 = stop


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Modbus Gateway covers."""
    hub: ModbusHub = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for unique_id, dp in hub.data_points.items():
        if dp.entity_type == "cover":
            entities.append(ModbusGatewayCover(hub, dp))

    if entities:
        async_add_entities(entities)


class ModbusGatewayCover(ModbusGatewayEntity, CoverEntity):
    """Representation of a Modbus Gateway cover."""

    def __init__(self, hub: ModbusHub, data_point: ModbusDataPoint) -> None:
        """Initialize."""
        super().__init__(hub, data_point)
        self._attr_is_closed = True
        self._attr_current_cover_position = 0
        self._attr_device_class = CoverDeviceClass.CURTAIN
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.SET_POSITION
        )

    def _process_updated_value(self, value: Any) -> None:
        """Process position value."""
        if isinstance(value, (int, float)):
            pos = int(value)
            self._attr_current_cover_position = min(100, max(0, pos))
            self._attr_is_closed = pos <= 0

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        success = await self._hub.async_write_data(self._data_point, 100)
        if success:
            self._attr_current_cover_position = 100
            self._attr_is_closed = False
            self.async_write_ha_state()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        success = await self._hub.async_write_data(self._data_point, 0)
        if success:
            self._attr_current_cover_position = 0
            self._attr_is_closed = True
            self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set cover position."""
        position = kwargs.get(ATTR_POSITION)
        if position is not None:
            success = await self._hub.async_write_data(self._data_point, int(position))
            if success:
                self._attr_current_cover_position = position
                self._attr_is_closed = position <= 0
                self.async_write_ha_state()
