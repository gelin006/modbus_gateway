"""Platform for Modbus Gateway select entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ModbusHub
from .const import DOMAIN
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


# Options format: comma-separated "label=value" pairs
# e.g. "停止=0,低速=2,中速=4,高速=8"
# Or plain labels: "停止,低速,中速,高速" (index-based)


def parse_select_options(options_str: str) -> tuple[list[str], dict[str, int]]:
    """Parse the options string into labels list and label->value mapping.

    Supports two formats:
      - "label=value,label=value" (custom values)
      - "label,label,label" (index-based: 0, 1, 2...)
    """
    labels: list[str] = []
    values: dict[str, int] = {}
    parts = [p.strip() for p in options_str.split(",") if p.strip()]

    if not parts:
        return labels, values

    # Detect format: if any part contains "=", treat as mapping
    has_mapping = any("=" in p for p in parts)

    if has_mapping:
        for part in parts:
            if "=" in part:
                label, raw_val = part.split("=", 1)
                label = label.strip()
                try:
                    val = int(raw_val.strip())
                except ValueError:
                    _LOGGER.warning("Invalid select value: %s, using index", raw_val)
                    val = len(labels)
                labels.append(label)
                values[label] = val
            else:
                # Fallback for parts without "=": use index
                labels.append(part)
                values[part] = len(labels) - 1
    else:
        # Plain labels: index-based mapping
        for i, label in enumerate(parts):
            labels.append(label)
            values[label] = i

    return labels, values


class ModbusGatewaySelect(ModbusGatewayEntity, SelectEntity):
    """Representation of a Modbus Gateway select."""

    def __init__(self, hub: ModbusHub, data_point: ModbusDataPoint) -> None:
        """Initialize."""
        super().__init__(hub, data_point)
        self._label_to_value: dict[str, int] = {}
        self._value_to_label: dict[int, str] = {}

        # Parse options
        options_str = ", ".join(data_point.options) if data_point.options else ""
        labels, label_to_val = parse_select_options(options_str)

        self._attr_options = labels
        self._label_to_value = label_to_val
        self._value_to_label = {v: k for k, v in label_to_val.items()}
        self._attr_current_option = None

        _LOGGER.debug(
            "Select %s: labels=%s, mapping=%s",
            data_point.name,
            labels,
            label_to_val,
        )

    def _process_updated_value(self, value: Any) -> None:
        """Process the select value."""
        if value is None:
            return
        try:
            raw = int(value)
        except (ValueError, TypeError):
            raw = value

        # Try to find matching label by value
        if isinstance(raw, int) and raw in self._value_to_label:
            self._attr_current_option = self._value_to_label[raw]
        elif str(raw) in self._attr_options:
            # Direct label match (e.g. from manual input)
            self._attr_current_option = str(raw)
        else:
            # Fallback: use as index
            if isinstance(raw, int) and 0 <= raw < len(self._attr_options):
                self._attr_current_option = self._attr_options[raw]
            _LOGGER.debug(
                "Select %s: raw value %s not found in mapping, options=%s, values=%s",
                self._data_point.name,
                raw,
                self._attr_options,
                self._value_to_label,
            )

    async def async_select_option(self, option: str) -> None:
        """Write the selected option to Modbus."""
        if option not in self._attr_options:
            _LOGGER.warning("Select %s: option %s not in options", self._data_point.name, option)
            return

        value = self._label_to_value.get(option, 0)
        _LOGGER.debug("Select %s: writing %s -> value %d", self._data_point.name, option, value)
        success = await self._hub.async_write_data(self._data_point, value)
        if success:
            self._attr_current_option = option
            self.async_write_ha_state()
