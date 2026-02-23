"""Property tests for OSC response parsing (Property 33).

Tests that OSC 11 responses are correctly parsed to extract RGB values,
validating Requirement 10.4.
"""

import pytest
from hypothesis import given, strategies as st, assume

from src.terminal_detect import parse_osc_rgb_response
from src.color_util import RGB


# Strategy for generating valid 16-bit hex values (0000-FFFF)
hex_16bit = st.integers(min_value=0, max_value=65535).map(lambda x: f"{x:04X}")


@given(
    r_16bit=st.integers(min_value=0, max_value=65535),
    g_16bit=st.integers(min_value=0, max_value=65535),
    b_16bit=st.integers(min_value=0, max_value=65535),
)
def test_osc_response_parsing_extracts_correct_rgb_values(
    r_16bit: int,
    g_16bit: int,
    b_16bit: int,
):
    """Property 33: OSC Response Parsing.
    
    PROPERTY: For any valid OSC 11 response in format "rgb:RRRR/GGGG/BBBB",
    the parser MUST extract RGB values correctly, converting 16-bit values
    to 8-bit (0-255) range.
    
    VALIDATES: Requirement 10.4 - OSC response parsing converts 16-bit to 8-bit.
    """
    # Format OSC response with 16-bit hex values
    response = f"rgb:{r_16bit:04X}/{g_16bit:04X}/{b_16bit:04X}"
    
    # Parse the response
    result = parse_osc_rgb_response(response)
    
    # Verify parsing succeeded
    assert result is not None
    assert hasattr(result, 'r') and hasattr(result, 'g') and hasattr(result, 'b')
    
    # Calculate expected 8-bit values
    expected_r = round(r_16bit / 65535.0 * 255)
    expected_g = round(g_16bit / 65535.0 * 255)
    expected_b = round(b_16bit / 65535.0 * 255)
    
    # Verify conversion is correct
    assert result.r == expected_r
    assert result.g == expected_g
    assert result.b == expected_b
    
    # Verify all components are in valid 8-bit range
    assert 0 <= result.r <= 255
    assert 0 <= result.g <= 255
    assert 0 <= result.b <= 255


@given(
    r_16bit=st.integers(min_value=0, max_value=65535),
    g_16bit=st.integers(min_value=0, max_value=65535),
    b_16bit=st.integers(min_value=0, max_value=65535),
    prefix=st.sampled_from(["", "\x1b]11;", "ESC]11;", "\x1b]11;rgb:", "some_prefix_"]),
    suffix=st.sampled_from(["", "\x07", "\x1b\\", "BEL", "_some_suffix"]),
)
def test_osc_parsing_handles_various_response_formats(
    r_16bit: int,
    g_16bit: int,
    b_16bit: int,
    prefix: str,
    suffix: str,
):
    """Property 33: OSC Response Parsing (Format Flexibility).
    
    PROPERTY: The parser MUST extract RGB values from OSC responses
    regardless of prefixes or suffixes, as long as the "rgb:RRRR/GGGG/BBBB"
    pattern is present.
    
    VALIDATES: Requirement 10.4 - Robust parsing of terminal responses.
    """
    # Format OSC response with various prefixes/suffixes
    response = f"{prefix}rgb:{r_16bit:04X}/{g_16bit:04X}/{b_16bit:04X}{suffix}"
    
    # Parse the response
    result = parse_osc_rgb_response(response)
    
    # Verify parsing succeeded
    assert result is not None
    
    # Calculate expected 8-bit values
    expected_r = round(r_16bit / 65535.0 * 255)
    expected_g = round(g_16bit / 65535.0 * 255)
    expected_b = round(b_16bit / 65535.0 * 255)
    
    # Verify conversion is correct
    assert result.r == expected_r
    assert result.g == expected_g
    assert result.b == expected_b


@given(
    r_16bit=st.integers(min_value=0, max_value=65535),
    g_16bit=st.integers(min_value=0, max_value=65535),
    b_16bit=st.integers(min_value=0, max_value=65535),
    case_variant=st.sampled_from(["upper", "lower", "mixed"]),
)
def test_osc_parsing_handles_case_variations(
    r_16bit: int,
    g_16bit: int,
    b_16bit: int,
    case_variant: str,
):
    """Property 33: OSC Response Parsing (Case Insensitivity).
    
    PROPERTY: The parser MUST handle hex values in uppercase, lowercase,
    or mixed case formats.
    
    VALIDATES: Requirement 10.4 - Flexible hex parsing.
    """
    # Format hex values with different cases
    if case_variant == "upper":
        response = f"rgb:{r_16bit:04X}/{g_16bit:04X}/{b_16bit:04X}"
    elif case_variant == "lower":
        response = f"rgb:{r_16bit:04x}/{g_16bit:04x}/{b_16bit:04x}"
    else:  # mixed
        response = f"rgb:{r_16bit:04X}/{g_16bit:04x}/{b_16bit:04X}"
    
    # Parse the response
    result = parse_osc_rgb_response(response)
    
    # Verify parsing succeeded
    assert result is not None
    
    # Calculate expected 8-bit values
    expected_r = round(r_16bit / 65535.0 * 255)
    expected_g = round(g_16bit / 65535.0 * 255)
    expected_b = round(b_16bit / 65535.0 * 255)
    
    # Verify conversion is correct
    assert result.r == expected_r
    assert result.g == expected_g
    assert result.b == expected_b


@given(
    invalid_response=st.sampled_from([
        "",
        "invalid",
        "rgb:",
        "rgb:XXXX/YYYY/ZZZZ",
        "rgb:FF/FF/FF",  # Too short (2 digits instead of 4)
        "rgb:FFFFF/FFFFF/FFFFF",  # Too long (5 digits instead of 4)
        "rgb:1234/5678",  # Missing blue component
        "rgb:1234",  # Missing green and blue
        "1234/5678/9ABC",  # Missing "rgb:" prefix
        "rgb:1234-5678-9ABC",  # Wrong separator
    ])
)
def test_osc_parsing_returns_none_for_invalid_responses(
    invalid_response: str,
):
    """Property 33: OSC Response Parsing (Invalid Input Handling).
    
    PROPERTY: The parser MUST return None for invalid or malformed
    OSC responses without raising exceptions.
    
    VALIDATES: Requirement 10.4 - Graceful handling of parsing failures.
    """
    # Parse invalid response
    result = parse_osc_rgb_response(invalid_response)
    
    # Verify parsing failed gracefully
    assert result is None


def test_osc_parsing_accepts_extra_components():
    """Property 33: OSC Response Parsing (Robustness).
    
    PROPERTY: The parser SHOULD extract the first valid RGB triplet
    even if extra components are present (robustness for terminal variations).
    
    VALIDATES: Requirement 10.4 - Robust parsing of terminal responses.
    """
    # Response with extra component (some terminals might send this)
    response = "rgb:1234/5678/9ABC/FFFF"
    result = parse_osc_rgb_response(response)
    
    # Parser should extract the first three components
    assert result is not None
    assert result.r == round(0x1234 / 65535.0 * 255)
    assert result.g == round(0x5678 / 65535.0 * 255)
    assert result.b == round(0x9ABC / 65535.0 * 255)


@given(
    r_16bit=st.integers(min_value=0, max_value=65535),
    g_16bit=st.integers(min_value=0, max_value=65535),
    b_16bit=st.integers(min_value=0, max_value=65535),
)
def test_osc_parsing_boundary_values(
    r_16bit: int,
    g_16bit: int,
    b_16bit: int,
):
    """Property 33: OSC Response Parsing (Boundary Values).
    
    PROPERTY: The parser MUST correctly handle boundary values:
    - 0000 (min) → 0 (8-bit)
    - FFFF (max) → 255 (8-bit)
    
    VALIDATES: Requirement 10.4 - Correct 16-bit to 8-bit conversion.
    """
    response = f"rgb:{r_16bit:04X}/{g_16bit:04X}/{b_16bit:04X}"
    result = parse_osc_rgb_response(response)
    
    assert result is not None
    
    # Test specific boundary cases
    if r_16bit == 0:
        assert result.r == 0
    if r_16bit == 65535:
        assert result.r == 255
    
    if g_16bit == 0:
        assert result.g == 0
    if g_16bit == 65535:
        assert result.g == 255
    
    if b_16bit == 0:
        assert result.b == 0
    if b_16bit == 65535:
        assert result.b == 255


@given(
    r_16bit=st.integers(min_value=0, max_value=65535),
    g_16bit=st.integers(min_value=0, max_value=65535),
    b_16bit=st.integers(min_value=0, max_value=65535),
)
def test_osc_parsing_conversion_accuracy(
    r_16bit: int,
    g_16bit: int,
    b_16bit: int,
):
    """Property 33: OSC Response Parsing (Conversion Accuracy).
    
    PROPERTY: The 16-bit to 8-bit conversion MUST use the formula:
    8bit = round(16bit / 65535.0 * 255)
    
    This ensures accurate color representation with proper rounding.
    
    VALIDATES: Requirement 10.4 - Accurate color conversion.
    """
    response = f"rgb:{r_16bit:04X}/{g_16bit:04X}/{b_16bit:04X}"
    result = parse_osc_rgb_response(response)
    
    assert result is not None
    
    # Verify the conversion formula is applied correctly
    expected_r = round(r_16bit / 65535.0 * 255)
    expected_g = round(g_16bit / 65535.0 * 255)
    expected_b = round(b_16bit / 65535.0 * 255)
    
    assert result.r == expected_r
    assert result.g == expected_g
    assert result.b == expected_b
    
    # Verify the conversion maintains color fidelity
    # (8-bit value should be proportional to 16-bit value)
    if r_16bit > 0:
        ratio_r = result.r / 255.0
        expected_ratio_r = r_16bit / 65535.0
        assert abs(ratio_r - expected_ratio_r) < 0.01  # Within 1% tolerance
    
    if g_16bit > 0:
        ratio_g = result.g / 255.0
        expected_ratio_g = g_16bit / 65535.0
        assert abs(ratio_g - expected_ratio_g) < 0.01
    
    if b_16bit > 0:
        ratio_b = result.b / 255.0
        expected_ratio_b = b_16bit / 65535.0
        assert abs(ratio_b - expected_ratio_b) < 0.01


def test_osc_parsing_real_world_examples():
    """Property 33: OSC Response Parsing (Real-World Examples).
    
    Test with actual OSC responses from various terminals to ensure
    compatibility with real-world formats.
    
    VALIDATES: Requirement 10.4 - Real terminal compatibility.
    """
    # Example from xterm with black background
    response1 = "\x1b]11;rgb:0000/0000/0000\x07"
    result1 = parse_osc_rgb_response(response1)
    assert result1 is not None
    assert result1.r == 0
    assert result1.g == 0
    assert result1.b == 0
    
    # Example from xterm with white background
    response2 = "\x1b]11;rgb:FFFF/FFFF/FFFF\x07"
    result2 = parse_osc_rgb_response(response2)
    assert result2 is not None
    assert result2.r == 255
    assert result2.g == 255
    assert result2.b == 255
    
    # Example from terminal with gray background
    response3 = "rgb:8080/8080/8080"
    result3 = parse_osc_rgb_response(response3)
    assert result3 is not None
    assert result3.r == 128
    assert result3.g == 128
    assert result3.b == 128
    
    # Example from terminal with custom color
    response4 = "\x1b]11;rgb:2E2E/3436/3636\x1b\\"
    result4 = parse_osc_rgb_response(response4)
    assert result4 is not None
    # 0x2E2E = 11822, 0x3436 = 13366, 0x3636 = 13878
    assert result4.r == round(11822 / 65535.0 * 255)
    assert result4.g == round(13366 / 65535.0 * 255)
    assert result4.b == round(13878 / 65535.0 * 255)
