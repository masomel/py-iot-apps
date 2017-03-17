"""
Support for Modbus.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/modbus/
"""
import logging
import threading

import voluptuous as vol

from homeassistant.const import (
    EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP,
    CONF_HOST, CONF_METHOD, CONF_PORT)
import homeassistant.helpers.config_validation as cv

DOMAIN = "modbus"

REQUIREMENTS = ['https://github.com/bashwork/pymodbus/archive/'
                'd7fc4f1cc975631e0a9011390e8017f64b612661.zip#pymodbus==1.2.0']

# Type of network
CONF_BAUDRATE = "baudrate"
CONF_BYTESIZE = "bytesize"
CONF_STOPBITS = "stopbits"
CONF_TYPE = "type"
CONF_PARITY = "parity"

SERIAL_SCHEMA = {
    vol.Required(CONF_BAUDRATE): cv.positive_int,
    vol.Required(CONF_BYTESIZE): vol.Any(5, 6, 7, 8),
    vol.Required(CONF_METHOD): vol.Any('rtu', 'ascii'),
    vol.Required(CONF_PORT): cv.string,
    vol.Required(CONF_PARITY): vol.Any('E', 'O', 'N'),
    vol.Required(CONF_STOPBITS): vol.Any(1, 2),
    vol.Required(CONF_TYPE): 'serial',
}

ETHERNET_SCHEMA = {
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PORT): cv.positive_int,
    vol.Required(CONF_TYPE): vol.Any('tcp', 'udp'),
}


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Any(SERIAL_SCHEMA, ETHERNET_SCHEMA)
}, extra=vol.ALLOW_EXTRA)


_LOGGER = logging.getLogger(__name__)

SERVICE_WRITE_REGISTER = "write_register"

ATTR_ADDRESS = "address"
ATTR_UNIT = "unit"
ATTR_VALUE = "value"

SERVICE_WRITE_REGISTER_SCHEMA = vol.Schema({
    vol.Required(ATTR_UNIT): cv.positive_int,
    vol.Required(ATTR_ADDRESS): cv.positive_int,
    vol.Required(ATTR_VALUE): cv.positive_int
})


HUB = None


def setup(hass, config):
    """Setup Modbus component."""
    # Modbus connection type
    # pylint: disable=global-statement, import-error
    client_type = config[DOMAIN][CONF_TYPE]

    # Connect to Modbus network
    # pylint: disable=global-statement, import-error

    if client_type == "serial":
        from pymodbus.client.sync import ModbusSerialClient as ModbusClient
        client = ModbusClient(method=config[DOMAIN][CONF_METHOD],
                              port=config[DOMAIN][CONF_PORT],
                              baudrate=config[DOMAIN][CONF_BAUDRATE],
                              stopbits=config[DOMAIN][CONF_STOPBITS],
                              bytesize=config[DOMAIN][CONF_BYTESIZE],
                              parity=config[DOMAIN][CONF_PARITY])
    elif client_type == "tcp":
        from pymodbus.client.sync import ModbusTcpClient as ModbusClient
        client = ModbusClient(host=config[DOMAIN][CONF_HOST],
                              port=config[DOMAIN][CONF_PORT])
    elif client_type == "udp":
        from pymodbus.client.sync import ModbusUdpClient as ModbusClient
        client = ModbusClient(host=config[DOMAIN][CONF_HOST],
                              port=config[DOMAIN][CONF_PORT])
    else:
        return False

    global HUB
    HUB = ModbusHub(client)

    def stop_modbus(event):
        """Stop Modbus service."""
        HUB.close()

    def start_modbus(event):
        """Start Modbus service."""
        HUB.connect()
        hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, stop_modbus)

        # Register services for modbus
        hass.services.register(DOMAIN, SERVICE_WRITE_REGISTER, write_register,
                               schema=SERVICE_WRITE_REGISTER_SCHEMA)

    def write_register(service):
        """Write modbus registers."""
        unit = int(float(service.data.get(ATTR_UNIT)))
        address = int(float(service.data.get(ATTR_ADDRESS)))
        value = service.data.get(ATTR_VALUE)
        if isinstance(value, list):
            HUB.write_registers(
                unit,
                address,
                [int(float(i)) for i in value])
        else:
            HUB.write_register(
                unit,
                address,
                int(float(value)))

    hass.bus.listen_once(EVENT_HOMEASSISTANT_START, start_modbus)

    return True


class ModbusHub(object):
    """Thread safe wrapper class for pymodbus."""

    def __init__(self, modbus_client):
        """Initialize the modbus hub."""
        self._client = modbus_client
        self._lock = threading.Lock()

    def close(self):
        """Disconnect client."""
        with self._lock:
            self._client.close()

    def connect(self):
        """Connect client."""
        with self._lock:
            self._client.connect()

    def read_coils(self, unit, address, count):
        """Read coils."""
        with self._lock:
            kwargs = {'unit': unit} if unit else {}
            return self._client.read_coils(
                address,
                count,
                **kwargs)

    def read_holding_registers(self, unit, address, count):
        """Read holding registers."""
        with self._lock:
            kwargs = {'unit': unit} if unit else {}
            return self._client.read_holding_registers(
                address,
                count,
                **kwargs)

    def write_coil(self, unit, address, value):
        """Write coil."""
        with self._lock:
            kwargs = {'unit': unit} if unit else {}
            self._client.write_coil(
                address,
                value,
                **kwargs)

    def write_register(self, unit, address, value):
        """Write register."""
        with self._lock:
            kwargs = {'unit': unit} if unit else {}
            self._client.write_register(
                address,
                value,
                **kwargs)

    def write_registers(self, unit, address, values):
        """Write registers."""
        with self._lock:
            kwargs = {'unit': unit} if unit else {}
            self._client.write_registers(
                address,
                values,
                **kwargs)
