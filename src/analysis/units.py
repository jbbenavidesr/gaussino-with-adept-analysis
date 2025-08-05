# units.py

from decimal import Decimal, getcontext
from typing import Dict, Tuple, Final

# Set a high precision for Decimal calculations
# This is a global setting for the current thread/process
getcontext().prec = 50

# Private constant for metric prefixes. Using Decimal for precision.
_METRIC_PREFIXES: Final[Dict[str, Decimal]] = {
    "Y": Decimal("1e24"),  # yotta
    "Z": Decimal("1e21"),  # zetta
    "E": Decimal("1e18"),  # exa
    "P": Decimal("1e15"),  # peta
    "T": Decimal("1e12"),  # tera
    "G": Decimal("1e9"),  # giga
    "M": Decimal("1e6"),  # mega
    "k": Decimal("1e3"),  # kilo
    "h": Decimal("1e2"),  # hecto
    "da": Decimal("1e1"),  # deca
    "": Decimal("1"),  # no prefix
    "d": Decimal("1e-1"),  # deci
    "c": Decimal("1e-2"),  # centi
    "m": Decimal("1e-3"),  # milli
    "u": Decimal("1e-6"),  # micro (alternative to µ)
    "µ": Decimal("1e-6"),  # micro
    "n": Decimal("1e-9"),  # nano
    "p": Decimal("1e-12"),  # pico
    "f": Decimal("1e-15"),  # femto
    "a": Decimal("1e-18"),  # atto
    "z": Decimal("1e-21"),  # zepto
    "y": Decimal("1e-24"),  # yocto
}


def _get_prefix_factor(prefix: str) -> Decimal:
    """
    Returns the scale factor for a given metric prefix as a Decimal.
    Raises ValueError if the prefix is not known.
    """
    try:
        return _METRIC_PREFIXES[prefix]
    except KeyError:
        raise ValueError(f"Unknown metric prefix: '{prefix}'")


def parse_unit(unit_str: str) -> Tuple[str, str]:
    """
    Parses a unit string to separate its prefix and base unit.
    """
    if len(unit_str) > 2 and unit_str[:2] in _METRIC_PREFIXES:
        return unit_str[:2], unit_str[2:]
    if len(unit_str) > 1 and unit_str[0] in _METRIC_PREFIXES:
        return unit_str[0], unit_str[1:]

    return "", unit_str


def convert_unit(
    value: Decimal, current_unit: str, target_unit: str, base: str
) -> Decimal:
    """
    Convert a value from one unit to another within the same metric system.

    Args:
        value: The numerical value to convert, as a Decimal.
        current_unit: The unit of the current value (e.g., "kg", "cm").
        target_unit: The unit to convert the value to (e.g., "mg", "m").
        base: The base unit of the system (e.g., "g" for grams, "m" for meters).

    Returns:
        The converted numerical value as a Decimal.
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
def convert_to_base_unit(value: Decimal, unit: str) -> Decimal:
    """
    Converts a value from a given unit to its base unit.
    """
    prefix, _ = parse_unit(unit)
    factor = _get_prefix_factor(prefix)
    return value * factor


# Another entry point
def convert_from_base_unit(value: Decimal, target_unit: str) -> Decimal:
    """
    Converts a value from a base unit to a target unit.
    """
    prefix, _ = parse_unit(target_unit)
    factor = _get_prefix_factor(prefix)
    return value / factor
