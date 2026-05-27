"""Constants for the Modbus Gateway integration."""

DOMAIN = "modbus_gateway"
DOMAIN_TITLE = "Modbus Gateway"

# Configuration keys - Connection
CONF_HOST = "host"
CONF_PORT = "port"
CONF_TYPE = "type"  # tcp, serial_rtu, serial_ascii
CONF_BAUDRATE = "baudrate"
CONF_PARITY = "parity"
CONF_STOP_BITS = "stop_bits"
CONF_DATA_BITS = "data_bits"
CONF_SERIAL_PORT = "serial_port"
CONF_SLAVE_ID = "slave_id"
CONF_TIMEOUT = "timeout"
CONF_RETRIES = "retries"
CONF_RETRY_ON_EMPTY = "retry_on_empty"
CONF_DELAY = "delay"
CONF_CLOSE_COMM_ON_ERROR = "close_comm_on_error"

# Configuration keys - Data Point
CONF_DATA_POINTS = "data_points"
CONF_DP_NAME = "name"
CONF_DP_SLAVE = "slave"
CONF_DP_ADDRESS = "address"
CONF_DP_COUNT = "count"
CONF_DP_FUNCTION_CODE = "function_code"
CONF_DP_DATA_TYPE = "data_type"
CONF_DP_WRITE_TYPE = "write_type"  # read_only, read_write, write_only
CONF_DP_ENTITY_TYPE = "entity_type"  # sensor, switch, light, climate, cover, binary_sensor, number, button, select
CONF_DP_SCALE = "scale"
CONF_DP_OFFSET = "offset"
CONF_DP_UNIT = "unit_of_measurement"
CONF_DP_PRECISION = "precision"
CONF_DP_CUSTOM_STRUCT = "custom_struct"
CONF_DP_INPUT_TYPE = "input_type"  # holding, input, coil, discrete
CONF_DP_STEP = "step"
CONF_DP_MIN_VALUE = "min_value"
CONF_DP_MAX_VALUE = "max_value"
CONF_DP_OPTIONS = "options"
CONF_DP_BUTTON_PAYLOAD = "button_payload"
CONF_DP_BUTTON_PAYLOAD_TYPE = "button_payload_type"  # hex, raw, decimal
CONF_DP_SCAN_INTERVAL = "scan_interval"

# Connection types
TYPE_TCP = "tcp"
TYPE_SERIAL_RTU = "serial_rtu"
TYPE_SERIAL_ASCII = "serial_ascii"

# Serial defaults
DEFAULT_BAUDRATE = 9600
DEFAULT_PARITY = "N"
DEFAULT_STOP_BITS = 1
DEFAULT_DATA_BITS = 8
DEFAULT_SERIAL_PORT = "/dev/ttyUSB0"
DEFAULT_TIMEOUT = 5
DEFAULT_RETRIES = 3
DEFAULT_DELAY = 0
DEFAULT_SCAN_INTERVAL = 30

# TCP defaults
DEFAULT_HOST = "192.168.1.100"
DEFAULT_PORT = 502

# Slave defaults
DEFAULT_SLAVE_ID = 1

# Data types
DATA_TYPE_INT16 = "int16"
DATA_TYPE_UINT16 = "uint16"
DATA_TYPE_INT32 = "int32"
DATA_TYPE_UINT32 = "uint32"
DATA_TYPE_FLOAT32 = "float32"
DATA_TYPE_INT64 = "int64"
DATA_TYPE_UINT64 = "uint64"
DATA_TYPE_STRING = "string"
DATA_TYPE_CUSTOM = "custom"

DATA_TYPES = [
    DATA_TYPE_UINT16,
    DATA_TYPE_INT16,
    DATA_TYPE_UINT32,
    DATA_TYPE_INT32,
    DATA_TYPE_FLOAT32,
    DATA_TYPE_INT64,
    DATA_TYPE_UINT64,
    DATA_TYPE_STRING,
    DATA_TYPE_CUSTOM,
]

# Function codes
FC_READ_COILS = 1
FC_READ_DISCRETE_INPUTS = 2
FC_READ_HOLDING_REGISTERS = 3
FC_READ_INPUT_REGISTERS = 4
FC_WRITE_SINGLE_COIL = 5
FC_WRITE_SINGLE_REGISTER = 6
FC_WRITE_MULTIPLE_COILS = 15
FC_WRITE_MULTIPLE_REGISTERS = 16

# Entity platform mapping
PLATFORM_SENSOR = "sensor"
PLATFORM_BINARY_SENSOR = "binary_sensor"
PLATFORM_SWITCH = "switch"
PLATFORM_LIGHT = "light"
PLATFORM_CLIMATE = "climate"
PLATFORM_COVER = "cover"
PLATFORM_NUMBER = "number"
PLATFORM_BUTTON = "button"
PLATFORM_SELECT = "select"

ENTITY_PLATFORMS = [
    PLATFORM_SENSOR,
    PLATFORM_BINARY_SENSOR,
    PLATFORM_SWITCH,
    PLATFORM_LIGHT,
    PLATFORM_CLIMATE,
    PLATFORM_COVER,
    PLATFORM_NUMBER,
    PLATFORM_BUTTON,
    PLATFORM_SELECT,
]

# Write type
WRITE_READ_ONLY = "read_only"
WRITE_READ_WRITE = "read_write"
WRITE_WRITE_ONLY = "write_only"

# Input type mapping to function codes
INPUT_TYPE_HOLDING = "holding"
INPUT_TYPE_INPUT = "input"
INPUT_TYPE_COIL = "coil"
INPUT_TYPE_DISCRETE = "discrete"

# Entity type default input type mapping
ENTITY_INPUT_TYPE_MAP = {
    PLATFORM_SENSOR: INPUT_TYPE_HOLDING,
    PLATFORM_BINARY_SENSOR: INPUT_TYPE_DISCRETE,
    PLATFORM_SWITCH: INPUT_TYPE_COIL,
    PLATFORM_LIGHT: INPUT_TYPE_HOLDING,
    PLATFORM_CLIMATE: INPUT_TYPE_HOLDING,
    PLATFORM_COVER: INPUT_TYPE_HOLDING,
    PLATFORM_NUMBER: INPUT_TYPE_HOLDING,
    PLATFORM_BUTTON: INPUT_TYPE_HOLDING,
    PLATFORM_SELECT: INPUT_TYPE_HOLDING,
}

# Button payload type
BUTTON_PAYLOAD_HEX = "hex"
BUTTON_PAYLOAD_RAW = "raw"
BUTTON_PAYLOAD_DECIMAL = "decimal"

# Storage
STORAGE_KEY = "modbus_gateway_data_points"
STORAGE_VERSION = 1
