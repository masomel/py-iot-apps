"""
Support for SleepIQ sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.sleepiq/
"""
from homeassistant.components import sleepiq
from homeassistant.components.binary_sensor import BinarySensorDevice

DEPENDENCIES = ['sleepiq']


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the SleepIQ sensors."""
    if discovery_info is None:
        return

    data = sleepiq.DATA
    data.update()

    dev = list()
    for bed_id, _ in data.beds.items():
        for side in sleepiq.SIDES:
            dev.append(IsInBedBinarySensor(data, bed_id, side))
    add_devices(dev)


class IsInBedBinarySensor(sleepiq.SleepIQSensor, BinarySensorDevice):
    """Implementation of a SleepIQ presence sensor."""

    def __init__(self, sleepiq_data, bed_id, side):
        """Initialize the sensor."""
        sleepiq.SleepIQSensor.__init__(self, sleepiq_data, bed_id, side)
        self.type = sleepiq.IS_IN_BED
        self._state = None
        self._name = sleepiq.SENSOR_TYPES[self.type]
        self.update()

    @property
    def is_on(self):
        """Return the status of the sensor."""
        return self._state is True

    @property
    def sensor_class(self):
        """Return the class of this sensor."""
        return "occupancy"

    def update(self):
        """Get the latest data from SleepIQ and updates the states."""
        sleepiq.SleepIQSensor.update(self)
        self._state = self.side.is_in_bed
