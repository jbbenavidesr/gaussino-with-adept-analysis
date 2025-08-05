from decimal import Decimal

import pytest

from analysis.units import (
    convert_unit,
    parse_unit,
    convert_to_base_unit,
    convert_from_base_unit,
)

# --- Tests for the core parsing function ---


@pytest.mark.parametrize(
    "unit_str, expected_prefix, expected_base",
    [
        # Single-character prefixes
        ("km", "k", "m"),
        ("mg", "m", "g"),
        ("µs", "µ", "s"),
        ("cm", "c", "m"),
        ("GV", "G", "V"),
        # Two-character prefixes
        ("daN", "da", "N"),
        ("daV", "da", "V"),
        # No prefix
        ("m", "", "m"),
        ("g", "", "g"),
        ("V", "", "V"),
    ],
)
def test_parse_unit(unit_str, expected_prefix, expected_base):
    """
    Test that parse_unit correctly separates prefixes from base units.
    """
    assert parse_unit(unit_str) == (expected_prefix, expected_base)


# --- Tests for the public conversion functions ---


@pytest.mark.parametrize(
    "value, current_unit, target_unit, base, expected_result",
    [
        # From larger to smaller
        (Decimal("1"), "kg", "g", "g", Decimal("1000")),
        (Decimal("1"), "km", "m", "m", Decimal("1000")),
        (Decimal("10"), "m", "cm", "m", Decimal("1000")),
        (Decimal("1"), "ms", "µs", "s", Decimal("1000")),
        (Decimal("1"), "eV", "neV", "eV", Decimal("1e9")),
        # From smaller to larger
        (Decimal("1000"), "g", "kg", "g", Decimal("1")),
        (Decimal("100"), "cm", "m", "m", Decimal("1")),
        (Decimal("1000"), "µs", "ms", "s", Decimal("1")),
        (Decimal("1e9"), "neV", "eV", "eV", Decimal("1")),
        # Conversions with no prefix
        (Decimal("1000"), "m", "km", "m", Decimal("1")),
        (Decimal("1"), "kg", "g", "g", Decimal("1000")),
        (Decimal("500"), "g", "kg", "g", Decimal("0.5")),
        # Converting to the same unit
        (Decimal("42.0"), "cm", "cm", "m", Decimal("42.0")),
        (Decimal("100"), "m", "m", "m", Decimal("100")),
        # A case where float precision would fail but Decimal succeeds
        (Decimal("3"), "m", "cm", "m", Decimal("300")),
    ],
)
def test_convert_unit_conversions(
    value, current_unit, target_unit, base, expected_result
):
    """
    Test various valid conversions using convert_unit.
    """
    assert convert_unit(value, current_unit, target_unit, base) == expected_result


@pytest.mark.parametrize(
    "value, unit, expected_result",
    [
        (Decimal("1"), "km", Decimal("1000")),
        (Decimal("100"), "cm", Decimal("1")),
        (Decimal("1"), "kg", Decimal("1000")),
        (Decimal("5"), "mm", Decimal("0.005")),
        (Decimal("1"), "m", Decimal("1")),
        (Decimal("1e6"), "µV", Decimal("1")),
    ],
)
def test_convert_to_base_unit_conversions(value, unit, expected_result):
    """
    Test conversions to base units using convert_to_base_unit.
    """
    assert convert_to_base_unit(value, unit) == expected_result


@pytest.mark.parametrize(
    "value, target_unit, expected_result",
    [
        (Decimal("1000"), "km", Decimal("1")),
        (Decimal("1"), "cm", Decimal("100")),
        (Decimal("1000"), "g", Decimal("1000")),
        (Decimal("0.005"), "mm", Decimal("5")),
        (Decimal("1.0"), "m", Decimal("1.0")),
        (Decimal("1.0"), "µV", Decimal("1e6")),
    ],
)
def test_convert_from_base_unit_conversions(value, target_unit, expected_result):
    """
    Test conversions from base units using convert_from_base_unit.
    """
    assert convert_from_base_unit(value, target_unit) == expected_result


@pytest.mark.parametrize(
    "value, current_unit, target_unit, base, error_message",
    [
        (Decimal("10"), "kg", "m", "m", "Base unit mismatch"),
        (Decimal("100"), "cm", "g", "m", "Base unit mismatch"),
        (Decimal("1"), "km", "g", "m", "Base unit mismatch"),
    ],
)
def test_convert_unit_raises_error_on_base_unit_mismatch(
    value, current_unit, target_unit, base, error_message
):
    """
    Test that a ValueError is raised when the base units don't match.
    """
    with pytest.raises(ValueError, match=error_message):
        convert_unit(value, current_unit, target_unit, base)
