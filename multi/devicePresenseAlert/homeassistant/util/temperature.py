"""Temperature util functions."""
from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    UNIT_NOT_RECOGNIZED_TEMPLATE,
    TEMPERATURE
)


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert a Fahrenheit temperature to Celsius."""
    return (fahrenheit - 32.0) / 1.8


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a Celsius temperature to Fahrenheit."""
    return celsius * 1.8 + 32.0


def convert(temperature: float, from_unit: str, to_unit: str) -> float:
    """Convert a temperature from one unit to another."""
    if from_unit not in (TEMP_CELSIUS, TEMP_FAHRENHEIT):
        raise ValueError(UNIT_NOT_RECOGNIZED_TEMPLATE.format(from_unit,
                                                             TEMPERATURE))
    if to_unit not in (TEMP_CELSIUS, TEMP_FAHRENHEIT):
        raise ValueError(UNIT_NOT_RECOGNIZED_TEMPLATE.format(to_unit,
                                                             TEMPERATURE))

    if from_unit == to_unit:
        return temperature
    elif from_unit == TEMP_CELSIUS:
        return celsius_to_fahrenheit(temperature)
    else:
        return fahrenheit_to_celsius(temperature)
