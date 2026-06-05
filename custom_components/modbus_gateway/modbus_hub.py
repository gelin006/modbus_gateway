"""Modbus Hub - manages the actual Modbus connection using pymodbus."""

from __future__ import annotations

import asyncio
import logging
import struct

from pymodbus.client import (
    AsyncModbusTcpClient,
    AsyncModbusSerialClient,
)
from pymodbus.exceptions import ConnectionException, ModbusException
from pymodbus.pdu import ExceptionResponse

from homeassistant.core import HomeAssistant

from .const import (
    TYPE_TCP,
    TYPE_SERIAL_RTU,
    TYPE_SERIAL_ASCII,
    CONF_TYPE,
    CONF_HOST,
    CONF_PORT,
    CONF_SERIAL_PORT,
    CONF_BAUDRATE,
    CONF_PARITY,
    CONF_STOP_BITS,
    CONF_DATA_BITS,
    CONF_TIMEOUT,
    CONF_DP_SLAVE,
    CONF_DP_ADDRESS,
    CONF_DP_COUNT,
    CONF_DP_DATA_TYPE,
    CONF_DP_FUNCTION_CODE,
    CONF_DP_INPUT_TYPE,
    CONF_DP_WRITE_TYPE,
    CONF_DP_SCALE,
    CONF_DP_OFFSET,
    CONF_DP_PRECISION,
    CONF_DP_CUSTOM_STRUCT,
    CONF_DP_BUTTON_PAYLOAD,
    CONF_DP_BUTTON_PAYLOAD_TYPE,
    INPUT_TYPE_HOLDING,
    INPUT_TYPE_INPUT,
    INPUT_TYPE_COIL,
    INPUT_TYPE_DISCRETE,
    DATA_TYPE_INT16,
    DATA_TYPE_UINT16,
    DATA_TYPE_INT32,
    DATA_TYPE_UINT32,
    DATA_TYPE_FLOAT32,
    DATA_TYPE_INT64,
    DATA_TYPE_UINT64,
    DATA_TYPE_STRING,
    DATA_TYPE_CUSTOM,
    WRITE_READ_ONLY,
    WRITE_READ_WRITE,
    WRITE_WRITE_ONLY,
    FC_READ_COILS,
    FC_READ_DISCRETE_INPUTS,
    FC_READ_HOLDING_REGISTERS,
    FC_READ_INPUT_REGISTERS,
    FC_WRITE_SINGLE_COIL,
    FC_WRITE_SINGLE_REGISTER,
    FC_WRITE_MULTIPLE_COILS,
    FC_WRITE_MULTIPLE_REGISTERS,
    BUTTON_PAYLOAD_HEX,
    BUTTON_PAYLOAD_RAW,
    BUTTON_PAYLOAD_DECIMAL,
)

_LOGGER = logging.getLogger(__name__)


def get_input_type_for_fc(function_code: int) -> str:
    """Map function code to input type string."""
    mapping = {
        FC_READ_COILS: INPUT_TYPE_COIL,
        FC_READ_DISCRETE_INPUTS: INPUT_TYPE_DISCRETE,
        FC_READ_HOLDING_REGISTERS: INPUT_TYPE_HOLDING,
        FC_READ_INPUT_REGISTERS: INPUT_TYPE_INPUT,
    }
    return mapping.get(function_code, INPUT_TYPE_HOLDING)


class ModbusDataPoint:
    """Represents a single configured data point on a Modbus device."""

    def __init__(
        self,
        name: str,
        slave: int,
        address: int,
        count: int,
        function_code: int,
        input_type: str,
        data_type: str,
        write_type: str,
        entity_type: str,
        scale: float = 1.0,
        offset: float = 0.0,
        precision: int = 0,
        unit: str | None = None,
        custom_struct: str | None = None,
        button_payload: str | None = None,
        button_payload_type: str = BUTTON_PAYLOAD_HEX,
        scan_interval: int = 30,
        step: float | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        options: list[str] | None = None,
        unique_id: str | None = None,
    ):
        self.name = name
        self.slave = slave
        self.address = address
        self.count = count
        self.function_code = function_code
        self.input_type = input_type
        self.data_type = data_type
        self.write_type = write_type
        self.entity_type = entity_type
        self.scale = scale
        self.offset = offset
        self.precision = precision
        self.unit = unit
        self.custom_struct = custom_struct
        self.button_payload = button_payload
        self.button_payload_type = button_payload_type
        self.scan_interval = scan_interval
        self.step = step
        self.min_value = min_value
        self.max_value = max_value
        self.options = options
        self.unique_id = unique_id

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "ModbusDataPoint":
        """Create data point from configuration dict."""
        return cls(
            name=config[CONF_DP_NAME],
            slave=config.get(CONF_DP_SLAVE, 1),
            address=config[CONF_DP_ADDRESS],
            count=config.get(CONF_DP_COUNT, 1),
            function_code=config.get(CONF_DP_FUNCTION_CODE, 3),
            input_type=config.get(CONF_DP_INPUT_TYPE, INPUT_TYPE_HOLDING),
            data_type=config.get(CONF_DP_DATA_TYPE, DATA_TYPE_UINT16),
            write_type=config.get(CONF_DP_WRITE_TYPE, WRITE_READ_WRITE),
            entity_type=config.get(CONF_DP_ENTITY_TYPE, "sensor"),
            scale=config.get(CONF_DP_SCALE, 1.0),
            offset=config.get(CONF_DP_OFFSET, 0.0),
            precision=config.get(CONF_DP_PRECISION, 0),
            unit=config.get(CONF_DP_UNIT),
            custom_struct=config.get(CONF_DP_CUSTOM_STRUCT),
            button_payload=config.get(CONF_DP_BUTTON_PAYLOAD),
            button_payload_type=config.get(
                CONF_DP_BUTTON_PAYLOAD_TYPE, BUTTON_PAYLOAD_HEX
            ),
            scan_interval=config.get(CONF_DP_SCAN_INTERVAL, 30),
            step=config.get(CONF_DP_STEP),
            min_value=config.get(CONF_DP_MIN_VALUE),
            max_value=config.get(CONF_DP_MAX_VALUE),
            options=config.get(CONF_DP_OPTIONS),
            unique_id=config.get("unique_id"),
        )


class ModbusHub:
    """Manages a single Modbus connection and its associated data points."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        config: dict[str, Any],
    ) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.config = config
        self._client: AsyncModbusTcpClient | AsyncModbusSerialClient | None = None
        self._lock = asyncio.Lock()
        self._connected = False
        self.data_points: dict[str, ModbusDataPoint] = {}

    @property
    def name(self) -> str:
        """Return the hub name."""
        return self.config.get("name", "Modbus Gateway")

    @property
    def connected(self) -> bool:
        """Return connection status."""
        return self._connected

    async def async_connect(self) -> bool:
        """Establish connection to the Modbus device."""
        conn_type = self.config[CONF_TYPE]

        try:
            if conn_type == TYPE_TCP:
                self._client = AsyncModbusTcpClient(
                    host=self.config[CONF_HOST],
                    port=self.config[CONF_PORT],
                    timeout=self.config.get(CONF_TIMEOUT, 5),
                )
            elif conn_type in (TYPE_SERIAL_RTU, TYPE_SERIAL_ASCII):
                self._client = AsyncModbusSerialClient(
                    port=self.config[CONF_SERIAL_PORT],
                    baudrate=self.config.get(CONF_BAUDRATE, 9600),
                    parity=self.config.get(CONF_PARITY, "N"),
                    stopbits=self.config.get(CONF_STOP_BITS, 1),
                    bytesize=self.config.get(CONF_DATA_BITS, 8),
                    timeout=self.config.get(CONF_TIMEOUT, 5),
                )

            if self._client:
                await self._client.connect()
                self._connected = True
                _LOGGER.info("Connected to Modbus device: %s", self.name)
                return True

        except (ConnectionException, ModbusException, OSError) as err:
            _LOGGER.error("Failed to connect to Modbus device %s: %s", self.name, err)

        self._connected = False
        return False

    async def async_disconnect(self) -> None:
        """Disconnect from Modbus device."""
        if self._client:
            try:
                self._client.close()
            except Exception as err:
                _LOGGER.warning("Error disconnecting: %s", err)
            finally:
                self._client = None
                self._connected = False

    async def async_read_data(
        self, data_point: ModbusDataPoint
    ) -> Any | None:
        """Read data from a single data point.
        Auto-reconnect if connection was lost."""
        if not self._client or not self._connected:
            _LOGGER.warning("Reconnecting to Modbus device %s", self.name)
            if not await self.async_connect():
                return None

        async with self._lock:
            try:
                slave = data_point.slave
                address = data_point.address
                count = data_point.count

                if data_point.input_type == INPUT_TYPE_COIL:
                    result = await self._client.read_coils(
                        address, count, slave=slave
                    )
                elif data_point.input_type == INPUT_TYPE_DISCRETE:
                    result = await self._client.read_discrete_inputs(
                        address, count, slave=slave
                    )
                elif data_point.input_type == INPUT_TYPE_INPUT:
                    result = await self._client.read_input_registers(
                        address, count, slave=slave
                    )
                else:  # holding registers
                    result = await self._client.read_holding_registers(
                        address, count, slave=slave
                    )

                if result is None:
                    _LOGGER.warning(
                        "No response from device for %s (slave=%d, addr=%d)",
                        data_point.name,
                        slave,
                        address,
                    )
                    return None

                if isinstance(result, ExceptionResponse):
                    _LOGGER.error(
                        "Modbus exception for %s: code=%d",
                        data_point.name,
                        result.exception_code,
                    )
                    return None

                # Extract raw values
                if hasattr(result, "bits"):
                    raw_values = result.bits
                elif hasattr(result, "registers"):
                    raw_values = result.registers
                else:
                    raw_values = []

                if not raw_values:
                    return None

                value = self._decode_value(raw_values, data_point)

                if value is not None:
                    if data_point.data_type not in (
                        DATA_TYPE_STRING,
                        DATA_TYPE_CUSTOM,
                    ):
                        value = value * data_point.scale + data_point.offset
                        value = round(value, data_point.precision)

                return value

            except (ConnectionException, ModbusException, asyncio.TimeoutError) as err:
                _LOGGER.error(
                    "Error reading %s: %s",
                    data_point.name,
                    err,
                )
                return None

    async def async_write_data(
        self, data_point: ModbusDataPoint, value: Any
    ) -> bool:
        """Write data to a register or coil."""
        if not self._client or not self._connected:
            _LOGGER.warning("Not connected to Modbus device %s", self.name)
            return False

        async with self._lock:
            try:
                slave = data_point.slave
                address = data_point.address
                input_type = data_point.input_type

                if input_type == INPUT_TYPE_COIL:
                    result = await self._client.write_coil(
                        address, bool(value), slave=slave
                    )
                else:
                    # For registers, encode value to register list
                    reg_values = self._encode_value(value, data_point)
                    if len(reg_values) == 1:
                        result = await self._client.write_register(
                            address, reg_values[0], slave=slave
                        )
                    else:
                        result = await self._client.write_registers(
                            address, reg_values, slave=slave
                        )

                if isinstance(result, ExceptionResponse):
                    _LOGGER.error(
                        "Modbus exception writing %s: code=%d",
                        data_point.name,
                        result.exception_code,
                    )
                    return False

                _LOGGER.debug("Written %s=%s on %s", data_point.name, value, self.name)
                return True

            except (ConnectionException, ModbusException, asyncio.TimeoutError) as err:
                _LOGGER.error(
                    "Error writing %s=%s: %s",
                    data_point.name,
                    value,
                    err,
                )
                return False

    async def async_execute_button(self, data_point: ModbusDataPoint) -> bool:
        """Execute a raw Modbus command defined by button payload."""
        if not self._client or not self._connected:
            _LOGGER.warning("Not connected to Modbus device %s", self.name)
            return False

        payload = data_point.button_payload
        payload_type = data_point.button_payload_type

        if not payload:
            _LOGGER.warning("No payload defined for button %s", data_point.name)
            return False

        async with self._lock:
            try:
                if payload_type == BUTTON_PAYLOAD_HEX:
                    raw_bytes = bytes.fromhex(payload.replace(" ", ""))
                elif payload_type == BUTTON_PAYLOAD_RAW:
                    raw_bytes = payload.encode("latin-1")
                elif payload_type == BUTTON_PAYLOAD_DECIMAL:
                    raw_bytes = struct.pack(">H", int(payload))
                else:
                    raw_bytes = bytes.fromhex(payload.replace(" ", ""))

                # Parse the raw ADU to get function code and data
                if len(raw_bytes) < 2:
                    _LOGGER.error("Button payload too short")
                    return False

                # Extract slave, function code, and data from raw bytes
                slave_byte = raw_bytes[0]
                fc_byte = raw_bytes[1]
                data_bytes = raw_bytes[2:-2]  # exclude CRC (2 bytes)

                if fc_byte == FC_WRITE_SINGLE_COIL:
                    val = struct.unpack(">H", data_bytes[0:2])[0]
                    result = await self._client.write_coil(
                        data_point.address, bool(val), slave=slave_byte
                    )
                elif fc_byte == FC_WRITE_SINGLE_REGISTER:
                    val = struct.unpack(">H", data_bytes[0:2])[0]
                    result = await self._client.write_register(
                        data_point.address, val, slave=slave_byte
                    )
                elif fc_byte == FC_WRITE_MULTIPLE_REGISTERS:
                    # Parse: address(2) + qty(2) + byte_count(1) + regs...
                    reg_addr = struct.unpack(">H", data_bytes[0:2])[0]
                    reg_qty = struct.unpack(">H", data_bytes[2:4])[0]
                    byte_count = data_bytes[4]
                    reg_values = []
                    for i in range(reg_qty):
                        off = 5 + i * 2
                        if off + 2 <= len(data_bytes):
                            reg_values.append(
                                struct.unpack(">H", data_bytes[off : off + 2])[0]
                            )
                    result = await self._client.write_registers(
                        reg_addr, reg_values, slave=slave_byte
                    )
                elif fc_byte == FC_WRITE_MULTIPLE_COILS:
                    reg_addr = struct.unpack(">H", data_bytes[0:2])[0]
                    reg_qty = struct.unpack(">H", data_bytes[2:4])[0]
                    byte_count = data_bytes[4]
                    coil_values = []
                    for i in range(byte_count):
                        off = 5 + i
                        if off < len(data_bytes):
                            byte_val = data_bytes[off]
                            for bit in range(8):
                                idx = i * 8 + bit
                                if idx < reg_qty:
                                    coil_values.append(bool(byte_val & (1 << bit)))
                    result = await self._client.write_coils(
                        reg_addr, coil_values, slave=slave_byte
                    )
                else:
                    # For other function codes, send raw transaction
                    _LOGGER.warning("Unsupported raw function code: 0x%02x", fc_byte)
                    return False

                if isinstance(result, ExceptionResponse):
                    _LOGGER.error(
                        "Exception executing button %s: code=%d",
                        data_point.name,
                        result.exception_code,
                    )
                    return False

                _LOGGER.debug("Button %s executed successfully", data_point.name)
                return True

            except (ConnectionException, ModbusException, ValueError, struct.error) as err:
                _LOGGER.error("Error executing button %s: %s", data_point.name, err)
                return False

    def _decode_value(
        self, raw_values: list[int], data_point: ModbusDataPoint
    ) -> Any:
        """Decode raw register/coil values based on configured data type."""
        data_type = data_point.data_type

        if data_type == DATA_TYPE_UINT16:
            return raw_values[0]

        if data_type == DATA_TYPE_INT16:
            val = raw_values[0]
            return val - 65536 if val >= 32768 else val

        if data_type == DATA_TYPE_UINT32:
            if len(raw_values) >= 2:
                return (raw_values[0] << 16) | raw_values[1]
            return raw_values[0]

        if data_type == DATA_TYPE_INT32:
            if len(raw_values) >= 2:
                val = (raw_values[0] << 16) | raw_values[1]
                return val - 4294967296 if val >= 2147483648 else val
            return raw_values[0]

        if data_type == DATA_TYPE_FLOAT32:
            if len(raw_values) >= 2:
                packed = struct.pack(">HH", raw_values[0], raw_values[1])
                return struct.unpack(">f", packed)[0]
            return raw_values[0]

        if data_type == DATA_TYPE_INT64:
            if len(raw_values) >= 4:
                val = 0
                for r in raw_values[:4]:
                    val = (val << 16) | r
                return val - 18446744073709551616 if val >= 9223372036854775808 else val
            return raw_values[0]

        if data_type == DATA_TYPE_UINT64:
            if len(raw_values) >= 4:
                val = 0
                for r in raw_values[:4]:
                    val = (val << 16) | r
                return val
            return raw_values[0]

        if data_type == DATA_TYPE_STRING:
            # Each register = 2 chars (high byte, low byte)
            chars = []
            for reg in raw_values:
                high = (reg >> 8) & 0xFF
                low = reg & 0xFF
                if 32 <= high <= 126:
                    chars.append(chr(high))
                if 32 <= low <= 126:
                    chars.append(chr(low))
            return "".join(chars).strip()

        if data_type == DATA_TYPE_CUSTOM:
            # Use Python struct format string
            if data_point.custom_struct:
                try:
                    packed = struct.pack(
                        ">" + "H" * len(raw_values), *raw_values[: len(raw_values)]
                    )
                    # Count total bytes needed
                    struct_size = struct.calcsize(data_point.custom_struct)
                    if struct_size <= len(packed):
                        result = struct.unpack(
                            data_point.custom_struct, packed[:struct_size]
                        )
                        if len(result) == 1:
                            return result[0]
                        return result
                except (struct.error, TypeError) as err:
                    _LOGGER.error("Custom struct decode error: %s", err)
                    return raw_values[0]

            return raw_values[0]

        return raw_values[0]

    def _encode_value(self, value: Any, data_point: ModbusDataPoint) -> list[int]:
        """Encode a value into register values for writing."""
        data_type = data_point.data_type

        # For boolean/coil types, just return as single value
        if data_point.input_type == INPUT_TYPE_COIL:
            return [1 if value else 0]

        try:
            if data_type == DATA_TYPE_UINT16:
                return [int(value) & 0xFFFF]

            if data_type == DATA_TYPE_INT16:
                val = int(value)
                return [val & 0xFFFF]

            if data_type in (DATA_TYPE_UINT32, DATA_TYPE_INT32):
                val = int(value)
                return [(val >> 16) & 0xFFFF, val & 0xFFFF]

            if data_type == DATA_TYPE_FLOAT32:
                packed = struct.pack(">f", float(value))
                regs = struct.unpack(">HH", packed)
                return list(regs)

            if data_type in (DATA_TYPE_UINT64, DATA_TYPE_INT64):
                val = int(value)
                regs = []
                for i in range(4):
                    shift = 48 - (i * 16)
                    regs.append((val >> shift) & 0xFFFF)
                return regs

            if data_type == DATA_TYPE_STRING:
                s = str(value)
                regs = []
                i = 0
                while i < len(s):
                    high = ord(s[i]) if i < len(s) else 0
                    low = ord(s[i + 1]) if i + 1 < len(s) else 0
                    regs.append((high << 8) | low)
                    i += 2
                return regs

            if data_type == DATA_TYPE_CUSTOM:
                if data_point.custom_struct:
                    packed = struct.pack(data_point.custom_struct, value)
                    # Pad to even number of bytes (2 bytes per register)
                    if len(packed) % 2:
                        packed += b"\x00"
                    regs = []
                    for i in range(0, len(packed), 2):
                        regs.append(
                            (packed[i] << 8) | packed[i + 1]
                        )
                    return regs

        except (struct.error, ValueError, TypeError) as err:
            _LOGGER.error("Encode error for %s: %s", data_point.name, err)

        return [int(value) & 0xFFFF]
