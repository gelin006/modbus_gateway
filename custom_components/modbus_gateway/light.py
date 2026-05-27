"""Platform for Modbus Gateway lights."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ModbusHub
from .const import CONF_DATA_POINTS, CONF_DP_NAME, DOMAIN
from .entity import ModbusGatewayEntity
from .modbus_hub import ModbusDataPoint

_LOGGER = logging.getLogger(__name__)

# Default mapping:
#  address = on/off (coil or register)
#  address+1 = brightness (0-255)
#  address+2 = color_temp (optional)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Modbus Gateway lights."""
    hub: ModbusHub = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for unique_id, dp in hub.data_points.items():
        if dp.entity_type == "light":
            entities.append(ModbusGatewayLight(hub, dp))

    if entities:
        async_add_entities(entities)


class ModbusGatewayLight(ModbusGatewayEntity, LightEntity):
    """Representation of a Modbus Gateway light."""

    def __init__(self, hub: ModbusHub, data_point: ModbusDataPoint) -> None:
        """Initialize the light."""
        super().__init__(hub, data_point)
        self._attr_is_on = False
        self._attr_brightness = None
        self._attr_color_temp = None
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def _process_updated_value(self, value: Any) -> None:
        """Process value - treat as brightness for now."""
        if isinstance(value, bool):
            self._attr_is_on = value
        elif value is not None:
            self._attr_is_on = int(value) > 0
            self._attr_brightness = min(255, int(value))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)

        if brightness is not None:
            self._attr_brightness = brightness
            value = brightness
        else:
            value = 255

        success = await self._hub.async_write_data(self._data_point, value)
        if success:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        success = await self._hub.async_write_data(self._data_point, 0)
        if success:
            self._attr_is_on = False
            self._attr_brightness = 0
            self.async_write_ha_state()
