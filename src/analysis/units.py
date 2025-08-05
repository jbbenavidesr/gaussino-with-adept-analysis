# units.py

from typing import Final

# Private constant for metric prefixes. Using Final makes it clear this should not be changed.
_METRIC_PREFIXES: Final[dict[str, float]] = {
    "Y": 1e24,  # yotta
    "Z": 1e21,  # zetta
    "E": 1e18,  # exa
    "P": 1e15,  # peta
    "T": 1e12,  # tera
    "G": 1e9,  # giga
    "M": 1e6,  # mega
    "k": 1e3,  # kilo
    "h": 1e2,  # hecto
    "da": 1e1,  # deca
    "": 1,  # no prefix
    "d": 1e-1,  # deci
    "c": 1e-2,  # centi
    "m": 1e-3,  # milli
    "u": 1e-6,  # micro (alternative to µ)
    "µ": 1e-6,  # micro
    "n": 1e-9,  # nano
    "p": 1e-12,  # pico
    "f": 1e-15,  # femto
    "a": 1e-18,  # atto
    "z": 1e-21,  # zepto
    "y": 1e-24,  # yocto
}


def _get_prefix_factor(prefix: str) -> float:
    """
    Returns the scale factor for a given metric prefix.
    Raises ValueError if the prefix is not known.
    """
    try:
        return _METRIC_PREFIXES[prefix]
    except KeyError:
        raise ValueError(f"Unknown metric prefix: '{prefix}'")


def parse_unit(unit_str: str) -> tuple[str, str]:
    """
    Parses a unit string to separate its prefix and base unit.

    Args:
        unit_str: The unit string (e.g., "kg", "cm").

    Returns:
        A tuple containing the prefix and the base unit.
    """
    if len(unit_str) > 2 and unit_str[:2] in _METRIC_PREFIXES:
        return unit_str[:2], unit_str[2:]
    if len(unit_str) > 1 and unit_str[0] in _METRIC_PREFIXES:
        return unit_str[0], unit_str[1:]

    return "", unit_str


def convert_unit(value: float, current_unit: str, target_unit: str, base: str) -> float:
    """
    Convert a value from one unit to another within the same metric system.

    Args:
        value: The numerical value to convert.
        current_unit: The unit of the current value (e.g., "kg", "cm").
        target_unit: The unit to convert the value to (e.g., "mg", "m").
        base: The base unit of the system (e.g., "g" for grams, "m" for meters).

    Returns:
        The converted numerical value.

    Raises:
        ValueError: If an unknown prefix is used or the base units do not match.

    Examples:
        >>> convert_unit(1, 'kg', 'mg', base='g')
        1000000.0
        >>> convert_unit(500, 'cm', 'm', base='m')
        5.0
    """
    current_prefix, current_base = parse_unit(current_unit)
    target_prefix, target_base = parse_unit(target_unit)

    if current_base != base or target_base != base:
        raise ValueError(
            f"Base unit mismatch: expected base '{base}', got '{current_base}' and '{target_base}'"
        )

    current_factor = _get_prefix_factor(current_prefix)
    target_factor = _get_prefix_factor(target_prefix)

    return value * current_factor / target_factor


# Additional entry point for convenience
def convert_to_base_unit(value: float, unit: str) -> float:
    """
    Converts a value from a given unit to its base unit.
    """
    prefix, base = parse_unit(unit)
    factor = _get_prefix_factor(prefix)
    return value * factor


# Another entry point
def convert_from_base_unit(value: float, target_unit: str) -> float:
    """
    Converts a value from a base unit to a target unit.
    """
    prefix, _ = parse_unit(target_unit)
    factor = _get_prefix_factor(prefix)
    return value / factor
