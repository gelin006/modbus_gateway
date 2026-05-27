"""Platform for Modbus Gateway button entities.
For non-standard protocol devices - execute raw Modbus commands."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
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
    """Set up Modbus Gateway button entities."""
    hub: ModbusHub = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for unique_id, dp in hub.data_points.items():
        if dp.entity_type == "button" and dp.button_payload:
            entities.append(ModbusGatewayButton(hub, dp))

    if entities:
        async_add_entities(entities)


class ModbusGatewayButton(ModbusGatewayEntity, ButtonEntity):
    """Representation of a Modbus Gateway button.
    Used for non-standard protocol devices - the user defines the raw data
    payload to send, similar to an IR remote button."""

    def __init__(self, hub: ModbusHub, data_point: ModbusDataPoint) -> None:
        """Initialize."""
        super().__init__(hub, data_point)

    def _process_updated_value(self, value):
        """Buttons don't have state updates from reading."""
        pass

    async def async_press(self) -> None:
        """Press the button - execute the raw Modbus command."""
        _LOGGER.debug(
            "Pressing button %s with payload: %s (type: %s)",
            self._data_point.name,
            self._data_point.button_payload,
            self._data_point.button_payload_type,
        )
        await self._hub.async_execute_button(self._data_point)
