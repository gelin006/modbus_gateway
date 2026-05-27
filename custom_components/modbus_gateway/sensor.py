"""Platform for Modbus Gateway sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ModbusHub
from .const import (
    CONF_DATA_POINTS,
    CONF_DP_NAME,
    CONF_DP_UNIT,
    CONF_DP_WRITE_TYPE,
    DOMAIN,
    WRITE_READ_ONLY,
    WRITE_READ_WRITE,
)
from .entity import ModbusGatewayEntity
from .modbus_hub import ModbusDataPoint

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Modbus Gateway sensors."""
    hub: ModbusHub = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for unique_id, dp in hub.data_points.items():
        if dp.entity_type == "sensor":
            entities.append(ModbusGatewaySensor(hub, dp))

    if entities:
        async_add_entities(entities)


class ModbusGatewaySensor(ModbusGatewayEntity, SensorEntity):
    """Representation of a Modbus Gateway sensor."""

    def __init__(
        self,
        hub: ModbusHub,
        data_point: ModbusDataPoint,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hub, data_point)
        self._attr_native_unit_of_measurement = data_point.unit
        self._attr_state_class = SensorStateClass.MEASUREMENT
        if data_point.write_type == WRITE_READ_WRITE:
            self._attr_entity_category = None
        else:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = None

    def _process_updated_value(self, value: Any) -> None:
        """Process an updated sensor value."""
        self._attr_native_value = value
