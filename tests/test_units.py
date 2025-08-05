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
        (1, "kg", "g", "g", 1000.0),
        (1, "km", "m", "m", 1000.0),
        (10, "m", "cm", "m", 1000.0),
        (1, "ms", "µs", "s", 1000.0),
        (1, "eV", "neV", "eV", 1e9),
        # From smaller to larger
        (1000, "g", "kg", "g", 1.0),
        (100, "cm", "m", "m", 1.0),
        (1000, "µs", "ms", "s", 1.0),
        (1e9, "neV", "eV", "eV", 1.0),
        # Conversions with no prefix
        (1000, "m", "km", "m", 1.0),
        (1, "kg", "g", "g", 1000.0),
        (500, "g", "kg", "g", 0.5),
        # Converting to the same unit
        (42.0, "cm", "cm", "m", 42.0),
        (100, "m", "m", "m", 100.0),
    ],
)
def test_convert_unit_conversions(
    value, current_unit, target_unit, base, expected_result
):
    """
    Test various valid conversions using convert_unit.
    """
    assert convert_unit(value, current_unit, target_unit, base) == pytest.approx(
        expected_result
    )


@pytest.mark.parametrize(
    "value, unit, expected_result",
    [
        (1, "km", 1000.0),
        (100, "cm", 1.0),
        (1, "kg", 1000.0),
        (5, "mm", 0.005),
        (1, "m", 1.0),
        (1e6, "µV", 1.0),
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
        (1000, "km", 1.0),
        (1, "cm", 100.0),
        (1000, "g", 1000.0),  # The unit 'g' has no prefix so should remain the same
        (0.005, "mm", 5.0),
        (1.0, "m", 1.0),
        (1.0, "µV", 1e6),
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
        (10, "kg", "m", "m", "Base unit mismatch: expected base 'm', got 'g' and 'm'"),
        (100, "cm", "g", "m", "Base unit mismatch: expected base 'm', got 'm' and 'g'"),
        (1, "km", "g", "m", "Base unit mismatch: expected base 'm', got 'm' and 'g'"),
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
