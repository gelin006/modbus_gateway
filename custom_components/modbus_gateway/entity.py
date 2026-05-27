"""Base entity for Modbus Gateway entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .modbus_hub import ModbusDataPoint, ModbusHub

_LOGGER = logging.getLogger(__name__)


class ModbusGatewayEntity(CoordinatorEntity):
    """Base entity for all Modbus Gateway entities."""

    def __init__(
        self,
        hub: ModbusHub,
        data_point: ModbusDataPoint,
    ) -> None:
        """Initialize the entity."""
        super().__init__(hub)
        self._hub = hub
        self._data_point = data_point
        self._attr_name = data_point.name

        # Unique ID
        if data_point.unique_id:
            self._attr_unique_id = data_point.unique_id
        else:
            self._attr_unique_id = (
                f"{hub.entry_id}_{data_point.entity_type}_"
                f"{data_point.slave}_{data_point.address}_{data_point.name.lower().replace(' ', '_')}"
            )

        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, hub.entry_id)},
            name=hub.name,
            manufacturer="Modbus Gateway",
            model=f"Modbus {hub.config.get('type', 'TCP').replace('_', ' ').title()}",
            sw_version="1.0.0",
        )

        # Extra state attributes
        self._attr_extra_state_attributes = {
            "modbus_slave": data_point.slave,
            "modbus_address": data_point.address,
            "modbus_count": data_point.count,
            "modbus_input_type": data_point.input_type,
            "modbus_data_type": data_point.data_type,
            "modbus_function_code": data_point.function_code,
        }

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self._hub.connected

    async def async_update(self) -> None:
        """Update the entity state from Modbus device."""
        value = await self._hub.async_read_data(self._data_point)
        if value is not None:
            self._process_updated_value(value)

    def _process_updated_value(self, value: Any) -> None:
        """Process an updated value. Override in subclasses."""
        raise NotImplementedError
