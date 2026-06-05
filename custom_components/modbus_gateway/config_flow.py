"""Config flow for Modbus Gateway integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.storage import Store

from .const import (
    CONF_BAUDRATE,
    CONF_CLOSE_COMM_ON_ERROR,
    CONF_DATA_BITS,
    CONF_DATA_POINTS,
    CONF_DELAY,
    CONF_DP_ADDRESS,
    CONF_DP_BUTTON_PAYLOAD,
    CONF_DP_BUTTON_PAYLOAD_TYPE,
    CONF_DP_COUNT,
    CONF_DP_CUSTOM_STRUCT,
    CONF_DP_DATA_TYPE,
    CONF_DP_ENTITY_TYPE,
    CONF_DP_FUNCTION_CODE,
    CONF_DP_INPUT_TYPE,
    CONF_DP_MAX_VALUE,
    CONF_DP_MIN_VALUE,
    CONF_DP_NAME,
    CONF_DP_OPTIONS,
    CONF_DP_OFFSET,
    CONF_DP_PRECISION,
    CONF_DP_SCALE,
    CONF_DP_SCAN_INTERVAL,
    CONF_DP_SLAVE,
    CONF_DP_STEP,
    CONF_DP_UNIT,
    CONF_DP_WRITE_TYPE,
    CONF_HOST,
    CONF_PARITY,
    CONF_PORT,
    CONF_RETRIES,
    CONF_RETRY_ON_EMPTY,
    CONF_SERIAL_PORT,
    CONF_SLAVE_ID,
    CONF_STOP_BITS,
    CONF_TIMEOUT,
    CONF_TYPE,
    DATA_TYPES,
    DATA_TYPE_CUSTOM,
    DOMAIN,
    ENTITY_PLATFORMS,
    INPUT_TYPE_COIL,
    INPUT_TYPE_DISCRETE,
    INPUT_TYPE_HOLDING,
    INPUT_TYPE_INPUT,
    STORAGE_KEY,
    STORAGE_VERSION,
    TYPE_SERIAL_ASCII,
    TYPE_SERIAL_RTU,
    TYPE_TCP,
    WRITE_READ_ONLY,
    WRITE_READ_WRITE,
    WRITE_WRITE_ONLY,
    BUTTON_PAYLOAD_HEX,
    BUTTON_PAYLOAD_RAW,
    BUTTON_PAYLOAD_DECIMAL,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_SLAVE_ID,
    DEFAULT_BAUDRATE,
    DEFAULT_PARITY,
    DEFAULT_STOP_BITS,
    DEFAULT_DATA_BITS,
    DEFAULT_SERIAL_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_RETRIES,
    DEFAULT_DELAY,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# --- Connection type step schema ---
CONNECTION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TYPE, default=TYPE_TCP): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    TYPE_TCP,
                    TYPE_SERIAL_RTU,
                    TYPE_SERIAL_ASCII,
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="connection_type",
            )
        ),
    }
)

# --- TCP Schema ---
TCP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="Modbus Device"): str,
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
        vol.Optional(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): vol.Coerce(int),
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.Coerce(int),
        vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): vol.Coerce(int),
        vol.Optional(CONF_RETRY_ON_EMPTY, default=False): bool,
        vol.Optional(CONF_DELAY, default=DEFAULT_DELAY): vol.Coerce(float),
        vol.Optional(CONF_CLOSE_COMM_ON_ERROR, default=False): bool,
    }
)

# --- Serial Schema ---
SERIAL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="Modbus Device"): str,
        vol.Required(CONF_SERIAL_PORT, default=DEFAULT_SERIAL_PORT): str,
        vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): vol.All(
            vol.Coerce(int),
            vol.In([1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]),
        ),
        vol.Optional(CONF_PARITY, default=DEFAULT_PARITY): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=["N", "E", "O", "M", "S"],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(CONF_STOP_BITS, default=DEFAULT_STOP_BITS): vol.All(
            vol.Coerce(int), vol.In([1, 2])
        ),
        vol.Optional(CONF_DATA_BITS, default=DEFAULT_DATA_BITS): vol.All(
            vol.Coerce(int), vol.In([5, 6, 7, 8])
        ),
        vol.Optional(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): vol.Coerce(int),
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.Coerce(int),
        vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): vol.Coerce(int),
        vol.Optional(CONF_RETRY_ON_EMPTY, default=False): bool,
        vol.Optional(CONF_DELAY, default=DEFAULT_DELAY): vol.Coerce(float),
        vol.Optional(CONF_CLOSE_COMM_ON_ERROR, default=False): bool,
    }
)

# --- Data point schema (add/edit a single point) ---
def _ensure_options_str(value: Any) -> str:
    """Convert options to string format for the form.

    Handles both list (deprecated storage format) and str.
    """
    if isinstance(value, list):
        return ",".join(value)
    if isinstance(value, str):
        return value
    return ""


def _build_data_point_schema(defaults: dict[str, Any] | None = None) -> dict:
    """Build schema for a data point."""
    d = defaults or {}

    schema = {
        vol.Required(CONF_DP_NAME, default=d.get(CONF_DP_NAME, "")): str,
        vol.Required(CONF_DP_ADDRESS, default=d.get(CONF_DP_ADDRESS, 0)): vol.Coerce(int),
        vol.Optional(CONF_DP_COUNT, default=d.get(CONF_DP_COUNT, 1)): vol.Coerce(int),
        vol.Optional(CONF_DP_SLAVE, default=d.get(CONF_DP_SLAVE, DEFAULT_SLAVE_ID)): vol.Coerce(int),
        vol.Optional(
            CONF_DP_ENTITY_TYPE, default=d.get(CONF_DP_ENTITY_TYPE, "sensor")
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=ENTITY_PLATFORMS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(
            CONF_DP_INPUT_TYPE, default=d.get(CONF_DP_INPUT_TYPE, INPUT_TYPE_HOLDING)
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    INPUT_TYPE_HOLDING,
                    INPUT_TYPE_INPUT,
                    INPUT_TYPE_COIL,
                    INPUT_TYPE_DISCRETE,
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(
            CONF_DP_FUNCTION_CODE, default=d.get(CONF_DP_FUNCTION_CODE, 3)
        ): vol.All(
            vol.Coerce(int),
            vol.In([1, 2, 3, 4, 5, 6, 15, 16]),
        ),
        vol.Optional(
            CONF_DP_DATA_TYPE, default=d.get(CONF_DP_DATA_TYPE, "uint16")
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=DATA_TYPES,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(
            CONF_DP_CUSTOM_STRUCT,
            default=d.get(CONF_DP_CUSTOM_STRUCT, ""),
        ): str,
        vol.Optional(
            CONF_DP_WRITE_TYPE, default=d.get(CONF_DP_WRITE_TYPE, WRITE_READ_WRITE)
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    WRITE_READ_ONLY,
                    WRITE_READ_WRITE,
                    WRITE_WRITE_ONLY,
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(
            CONF_DP_SCALE, default=d.get(CONF_DP_SCALE, 1.0)
        ): vol.Coerce(float),
        vol.Optional(
            CONF_DP_OFFSET, default=d.get(CONF_DP_OFFSET, 0.0)
        ): vol.Coerce(float),
        vol.Optional(
            CONF_DP_PRECISION, default=d.get(CONF_DP_PRECISION, 0)
        ): vol.Coerce(int),
        vol.Optional(
            CONF_DP_UNIT, default=d.get(CONF_DP_UNIT, "")
        ): str,
        vol.Optional(
            CONF_DP_SCAN_INTERVAL, default=d.get(CONF_DP_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        ): vol.Coerce(int),
        vol.Optional(CONF_DP_STEP, default=d.get(CONF_DP_STEP, None)): vol.Any(
            None, vol.Coerce(float)
        ),
        vol.Optional(CONF_DP_MIN_VALUE, default=d.get(CONF_DP_MIN_VALUE, None)): vol.Any(
            None, vol.Coerce(float)
        ),
        vol.Optional(CONF_DP_MAX_VALUE, default=d.get(CONF_DP_MAX_VALUE, None)): vol.Any(
            None, vol.Coerce(float)
        ),
        vol.Optional(
            CONF_DP_OPTIONS,
            default=_ensure_options_str(d.get(CONF_DP_OPTIONS, "")),
        ): str,
        # Button payload fields (for non-standard protocol / raw command)
        vol.Optional(
            CONF_DP_BUTTON_PAYLOAD, default=d.get(CONF_DP_BUTTON_PAYLOAD, "")
        ): str,
        vol.Optional(
            CONF_DP_BUTTON_PAYLOAD_TYPE,
            default=d.get(CONF_DP_BUTTON_PAYLOAD_TYPE, BUTTON_PAYLOAD_HEX),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    BUTTON_PAYLOAD_HEX,
                    BUTTON_PAYLOAD_RAW,
                    BUTTON_PAYLOAD_DECIMAL,
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    }
    return schema


DATA_POINT_SCHEMA = vol.Schema(_build_data_point_schema(None))


def _get_field_description(entity_type: str) -> str:
    """Get a human-readable description for an entity type."""
    descriptions = {
        "sensor": "只读传感器值",
        "binary_sensor": "二进制开关状态 (0/1)",
        "switch": "可控制的开关",
        "light": "灯光控制 (亮度/色温)",
        "climate": "空调/温控设备",
        "cover": "窗帘/卷帘/遮阳设备",
        "number": "数值输入滑块",
        "button": "自定义按钮 (非标准协议)",
        "select": "下拉选择器",
    }
    return descriptions.get(entity_type, entity_type)


class ModbusGatewayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Modbus Gateway."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._connection_config: dict[str, Any] = {}
        # We store data points in a list for UI management
        self._data_points: list[dict[str, Any]] = []
        self._editing_point_index: int | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: Choose connection type."""
        errors = {}

        if user_input is not None:
            self._connection_config[CONF_TYPE] = user_input[CONF_TYPE]
            conn_type = user_input[CONF_TYPE]

            if conn_type == TYPE_TCP:
                return await self.async_step_tcp()
            else:
                return await self.async_step_serial()

        return self.async_show_form(
            step_id="user",
            data_schema=CONNECTION_SCHEMA,
            errors=errors,
            description_placeholders={
                "step_desc": "选择 Modbus 连接类型"
            },
        )

    async def async_step_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2a: Configure TCP connection."""
        errors = {}

        if user_input is not None:
            self._connection_config.update(user_input)
            return self._create_entry()

        return self.async_show_form(
            step_id="tcp",
            data_schema=TCP_SCHEMA,
            errors=errors,
            description_placeholders={
                "step_desc": "配置 Modbus TCP 连接参数"
            },
        )

    async def async_step_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2b: Configure Serial/RTU connection."""
        errors = {}

        if user_input is not None:
            self._connection_config.update(user_input)
            return self._create_entry()

        return self.async_show_form(
            step_id="serial",
            data_schema=SERIAL_SCHEMA,
            errors=errors,
            description_placeholders={
                "step_desc": "配置 Modbus 串口连接参数 (波特率、校验方式等)"
            },
        )

    def _create_entry(self) -> FlowResult:
        """Create the config entry with connection config (data points added via options)."""
        conn_type = self._connection_config.get(CONF_TYPE, TYPE_TCP)
        if conn_type == TYPE_TCP:
            unique_id = f"modbus_{conn_type}_{self._connection_config.get(CONF_HOST)}_{self._connection_config.get(CONF_PORT)}"
        else:
            unique_id = f"modbus_{conn_type}_{self._connection_config.get(CONF_SERIAL_PORT)}"

        self._async_abort_entries_match(unique_id)

        entry_data = dict(self._connection_config)
        entry_data[CONF_DATA_POINTS] = []

        return self.async_create_entry(
            title=self._connection_config.get(CONF_NAME, "Modbus Device"),
            data=entry_data,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return ModbusGatewayOptionsFlow(config_entry)


class ModbusGatewayOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Modbus Gateway."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self._data_points: list[dict[str, Any]] = []
        self._editing_point_index: int | None = None
        _LOGGER.debug("ModbusGatewayOptionsFlow initialized for entry: %s", config_entry.title)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options - start with data points."""
        try:
            # Read from entry.options (written by OptionsFlow), then fallback to data (ConfigFlow)
            existing = (
                self.config_entry.options.get(CONF_DATA_POINTS, []) or
                self.config_entry.data.get(CONF_DATA_POINTS, [])
            )
            self._data_points = list(existing)
        except Exception as err:
            _LOGGER.exception("OptionsFlow init failed: %s", err)
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema({}),
                errors={"base": "unknown"},
                description_placeholders={
                    "points": f"初始化失败: {err}",
                    "count": "0",
                },
            )
        return await self.async_step_manage_points()

    async def async_step_manage_points(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage data points in options."""
        try:
            if user_input is not None:
                action = user_input.get("action", "finish")

                if action == "add":
                    return await self.async_step_add_point()
                elif action == "finish":
                    # Save and create entry
                    new_data = dict(self.config_entry.data)
                    new_data[CONF_DATA_POINTS] = self._data_points
                    return self.async_create_entry(title="", data=new_data)

            points_summary = []
            for i, dp in enumerate(self._data_points):
                entity_type = dp.get(CONF_DP_ENTITY_TYPE, "sensor")
                _desc = _get_field_description(entity_type)  # noqa: F841
                points_summary.append(
                    f"  {i+1}. [{entity_type.upper()}] {dp.get(CONF_DP_NAME, '?')} "
                    f"(地址={dp.get(CONF_DP_ADDRESS, 0)})"
                )

            points_text = "\n".join(points_summary) if points_summary else "  (暂无)"

            return self.async_show_form(
                step_id="manage_points",
                data_schema=vol.Schema(
                    {
                        vol.Required("action", default="add"): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=["add", "finish"],
                                mode=selector.SelectSelectorMode.LIST,
                                translation_key="manage_points_action",
                            )
                        ),
                    }
                ),
                description_placeholders={
                    "points": points_text,
                    "count": str(len(self._data_points)),
                },
            )
        except Exception as err:
            _LOGGER.exception("OptionsFlow manage_points failed: %s", err)
            return self.async_show_form(
                step_id="manage_points",
                data_schema=vol.Schema({}),
                errors={"base": "unknown"},
                description_placeholders={
                    "points": f"加载失败: {err}",
                    "count": "0",
                },
            )

    async def async_step_add_point(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new data point in options."""
        try:
            if user_input is not None:
                name = user_input.get(CONF_DP_NAME, "").strip()
                if not name:
                    return self.async_show_form(
                        step_id="add_point",
                        data_schema=vol.Schema(_build_data_point_schema()),
                        errors={"base": "name_required"},
                    )

                options_str = user_input.get(CONF_DP_OPTIONS, "")
                user_input[CONF_DP_OPTIONS] = (
                    [o.strip() for o in options_str.split(",") if o.strip()]
                    if options_str
                    else None
                )
                if user_input.get(CONF_DP_CUSTOM_STRUCT) == "":
                    user_input[CONF_DP_CUSTOM_STRUCT] = None
                if user_input.get(CONF_DP_UNIT) == "":
                    user_input[CONF_DP_UNIT] = None
                if not user_input.get(CONF_DP_BUTTON_PAYLOAD):
                    user_input[CONF_DP_BUTTON_PAYLOAD] = None

                self._data_points.append(dict(user_input))
                return await self.async_step_manage_points()

            return self.async_show_form(
                step_id="add_point",
                data_schema=vol.Schema(_build_data_point_schema()),
            )
        except Exception as err:
            _LOGGER.exception("OptionsFlow add_point failed: %s", err)
            return self.async_show_form(
                step_id="add_point",
                data_schema=vol.Schema({}),
                errors={"base": "unknown"},
            )
