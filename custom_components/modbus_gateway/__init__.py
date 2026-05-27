"""Modbus Gateway integration for Home Assistant."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.storage import Store

from .const import (
    CONF_DATA_POINTS,
    CONF_TYPE,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .modbus_hub import ModbusHub

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.LIGHT,
    Platform.CLIMATE,
    Platform.COVER,
    Platform.NUMBER,
    Platform.BUTTON,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Modbus Gateway from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Create the Modbus hub
    hub = ModbusHub(hass, entry.entry_id, entry.data)
    hass.data[DOMAIN][entry.entry_id] = hub

    # Load stored data points
    store = Store[dict[str, Any]](
        hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry.entry_id}"
    )
    stored_data = await store.async_load()

    if stored_data and "data_points" in stored_data:
        from .modbus_hub import ModbusDataPoint

        for dp_config in stored_data["data_points"]:
            dp = ModbusDataPoint.from_config(dp_config)
            if dp.unique_id:
                hub.data_points[dp.unique_id] = dp

    # Connect to the Modbus device
    if not await hub.async_connect():
        _LOGGER.warning(
            "Could not connect to Modbus device %s. Entities will retry automatically.",
            hub.name,
        )

    # Register the device in device registry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=hub.name,
        manufacturer="Modbus Gateway",
        model=f"Modbus {entry.data.get(CONF_TYPE, 'TCP').replace('_', ' ').title()}",
        sw_version="1.0.0",
    )

    # Forward setup to all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for config changes
    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hub: ModbusHub = hass.data[DOMAIN][entry.entry_id]
    await hub.async_disconnect()

    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        return True

    return False


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle config entry update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    # Clean up stored data
    store = Store[dict[str, Any]](
        hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry.entry_id}"
    )
    await store.async_remove()
