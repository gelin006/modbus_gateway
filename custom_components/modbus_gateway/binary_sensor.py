"""Platform for Modbus Gateway binary sensors."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ModbusHub
from .const import CONF_DATA_POINTS, CONF_DP_NAME, DOMAIN, WRITE_READ_ONLY
from .entity import ModbusGatewayEntity
from .modbus_hub import ModbusDataPoint

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Modbus Gateway binary sensors."""
    hub: ModbusHub = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for unique_id, dp in hub.data_points.items():
        if dp.entity_type == "binary_sensor":
            entities.append(ModbusGatewayBinarySensor(hub, dp))

    if entities:
        async_add_entities(entities)


class ModbusGatewayBinarySensor(ModbusGatewayEntity, BinarySensorEntity):
    """Representation of a Modbus Gateway binary sensor."""

    def __init__(self, hub: ModbusHub, data_point: ModbusDataPoint) -> None:
        """Initialize."""
        super().__init__(hub, data_point)
        self._attr_is_on = None
        self._attr_device_class = BinarySensorDeviceClass.POWER

    def _process_updated_value(self, value):
        """Process a binary value."""
        if isinstance(value, bool):
            self._attr_is_on = value
        elif isinstance(value, (int, float)):
            self._attr_is_on = bool(value)
        else:
            self._attr_is_on = None
