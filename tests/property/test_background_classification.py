"""Property tests for background lightness classification (Property 37).

Tests that background colors are correctly classified as light or dark
based on HSL lightness threshold, validating Requirement 12.1.
"""

import pytest
from hypothesis import given, strategies as st, assume

from src.color_util import RGB


@given(
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255),
)
def test_background_lightness_classification_threshold(
    r: int,
    g: int,
    b: int,
):
    """Property 37: Background Lightness Classification.
    
    PROPERTY: For any RGB background color, the Theme_System MUST classify
    it as "light" if HSL lightness > 0.5, otherwise "dark".
    
    VALIDATES: Requirement 12.1 - Terminal background lightness detection.
    """
    # Create RGB color
    bg_color = RGB(r, g, b)
    
    # Get HSL lightness
    hsl = bg_color.hsl()
    lightness = hsl.l
    
    # Classify using is_light() method
    is_light = bg_color.is_light()
    
    # Verify classification matches threshold
    if lightness > 0.5:
        assert is_light is True, (
            f"Color RGB({r}, {g}, {b}) with lightness {lightness:.3f} > 0.5 "
            f"should be classified as light, but is_light() returned {is_light}"
        )
    else:
        assert is_light is False, (
            f"Color RGB({r}, {g}, {b}) with lightness {lightness:.3f} <= 0.5 "
            f"should be classified as dark, but is_light() returned {is_light}"
        )


@given(
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255),
)
def test_background_classification_consistency(
    r: int,
    g: int,
    b: int,
):
    """Property 37: Background Lightness Classification (Consistency).
    
    PROPERTY: The classification MUST be consistent - calling is_light()
    multiple times on the same color MUST return the same result.
    
    VALIDATES: Requirement 12.1 - Deterministic classification.
    """
    bg_color = RGB(r, g, b)
    
    # Call is_light() multiple times
    result1 = bg_color.is_light()
    result2 = bg_color.is_light()
    result3 = bg_color.is_light()
    
    # Verify consistency
    assert result1 == result2 == result3, (
        f"is_light() returned inconsistent results for RGB({r}, {g}, {b}): "
        f"{result1}, {result2}, {result3}"
    )


def test_background_classification_boundary_cases():
    """Property 37: Background Lightness Classification (Boundary Cases).
    
    PROPERTY: The classification MUST handle boundary cases correctly:
    - Pure black (0, 0, 0) → dark (lightness = 0.0)
    - Pure white (255, 255, 255) → light (lightness = 1.0)
    - Mid-gray (128, 128, 128) → light (lightness ≈ 0.502 due to RGB→HSL conversion)
    
    VALIDATES: Requirement 12.1 - Correct boundary classification.
    """
    # Pure black - should be dark
    black = RGB(0, 0, 0)
    assert black.is_light() is False
    assert black.hsl().l == 0.0
    
    # Pure white - should be light
    white = RGB(255, 255, 255)
    assert white.is_light() is True
    assert white.hsl().l == 1.0
    
    # Mid-gray - RGB(128, 128, 128) has lightness ≈ 0.502 (slightly > 0.5)
    mid_gray = RGB(128, 128, 128)
    lightness = mid_gray.hsl().l
    # Verify it's classified based on actual lightness value
    assert mid_gray.is_light() == (lightness > 0.5)
    # RGB(128, 128, 128) should be light due to conversion precision
    assert mid_gray.is_light() is True


@given(
    lightness=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
def test_background_classification_from_lightness(
    lightness: float,
):
    """Property 37: Background Lightness Classification (From Lightness).
    
    PROPERTY: For any lightness value, creating a grayscale color with that
    lightness MUST be classified according to the 0.5 threshold, accounting
    for round-trip conversion precision.
    
    VALIDATES: Requirement 12.1 - Lightness-based classification.
    """
    from src.color_util import HSL
    
    # Create grayscale color with specific lightness (hue=0, saturation=0)
    hsl = HSL(h=0.0, s=0.0, l=lightness)
    rgb = hsl.rgb()
    
    # Get the actual lightness after round-trip conversion
    actual_lightness = rgb.hsl().l
    
    # Verify classification matches the actual lightness after conversion
    is_light = rgb.is_light()
    
    if actual_lightness > 0.5:
        assert is_light is True, (
            f"Grayscale color with actual lightness {actual_lightness:.6f} > 0.5 "
            f"(original: {lightness:.6f}) should be classified as light"
        )
    else:
        assert is_light is False, (
            f"Grayscale color with actual lightness {actual_lightness:.6f} <= 0.5 "
            f"(original: {lightness:.6f}) should be classified as dark"
        )


@given(
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255),
)
def test_background_classification_hue_saturation_independence(
    r: int,
    g: int,
    b: int,
):
    """Property 37: Background Lightness Classification (Hue/Saturation Independence).
    
    PROPERTY: The classification MUST depend only on lightness, not on
    hue or saturation. Two colors with the same lightness (after accounting
    for RGB→HSL→RGB conversion precision) MUST have the same classification.
    
    VALIDATES: Requirement 12.1 - Lightness-only classification.
    """
    color1 = RGB(r, g, b)
    hsl1 = color1.hsl()
    
    # Create another color with same lightness but different hue/saturation
    # by creating a grayscale color with the same lightness
    from src.color_util import HSL
    hsl2 = HSL(h=0.0, s=0.0, l=hsl1.l)
    color2 = hsl2.rgb()
    
    # Get actual lightness after round-trip conversion
    actual_lightness2 = color2.hsl().l
    
    # Both colors should have the same classification if their actual
    # lightness values (after conversion) are on the same side of 0.5
    if (hsl1.l > 0.5 and actual_lightness2 > 0.5) or \
       (hsl1.l <= 0.5 and actual_lightness2 <= 0.5):
        assert color1.is_light() == color2.is_light(), (
            f"Colors with similar lightness should have same classification: "
            f"RGB({r}, {g}, {b}) lightness={hsl1.l:.6f} -> {color1.is_light()}, "
            f"RGB({color2.r}, {color2.g}, {color2.b}) lightness={actual_lightness2:.6f} -> {color2.is_light()}"
        )


def test_background_classification_real_world_examples():
    """Property 37: Background Lightness Classification (Real-World Examples).
    
    Test with actual terminal background colors to ensure correct
    classification for common scenarios.
    
    VALIDATES: Requirement 12.1 - Real-world terminal compatibility.
    """
    # Common dark terminal backgrounds
    dark_backgrounds = [
        RGB(0, 0, 0),           # Pure black
        RGB(30, 30, 30),        # Dark gray (common in modern terminals)
        RGB(40, 44, 52),        # One Dark theme background
        RGB(46, 52, 64),        # Nord theme background
        RGB(35, 38, 39),        # Dracula theme background
    ]
    
    for bg in dark_backgrounds:
        assert bg.is_light() is False, (
            f"Dark background RGB({bg.r}, {bg.g}, {bg.b}) "
            f"with lightness {bg.hsl().l:.3f} should be classified as dark"
        )
    
    # Common light terminal backgrounds
    light_backgrounds = [
        RGB(255, 255, 255),     # Pure white
        RGB(250, 250, 250),     # Off-white
        RGB(253, 246, 227),     # Solarized Light background
        RGB(238, 238, 238),     # Light gray
        RGB(245, 245, 245),     # Very light gray
    ]
    
    for bg in light_backgrounds:
        assert bg.is_light() is True, (
            f"Light background RGB({bg.r}, {bg.g}, {bg.b}) "
            f"with lightness {bg.hsl().l:.3f} should be classified as light"
        )


@given(
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255),
)
def test_background_classification_inverse_relationship(
    r: int,
    g: int,
    b: int,
):
    """Property 37: Background Lightness Classification (Inverse Relationship).
    
    PROPERTY: If a color is classified as light, its inverse (255-r, 255-g, 255-b)
    SHOULD be classified as dark (and vice versa), assuming the lightness
    values are on opposite sides of the 0.5 threshold.
    
    VALIDATES: Requirement 12.1 - Symmetric classification behavior.
    """
    color = RGB(r, g, b)
    inverse = RGB(255 - r, 255 - g, 255 - b)
    
    color_lightness = color.hsl().l
    inverse_lightness = inverse.hsl().l
    
    # If lightnesses are on opposite sides of 0.5, classifications should differ
    if (color_lightness > 0.5 and inverse_lightness <= 0.5) or \
       (color_lightness <= 0.5 and inverse_lightness > 0.5):
        assert color.is_light() != inverse.is_light(), (
            f"Color RGB({r}, {g}, {b}) with lightness {color_lightness:.3f} "
            f"and its inverse RGB({inverse.r}, {inverse.g}, {inverse.b}) "
            f"with lightness {inverse_lightness:.3f} should have different classifications"
        )


@given(
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255),
)
def test_background_classification_matches_hsl_threshold(
    r: int,
    g: int,
    b: int,
):
    """Property 37: Background Lightness Classification (HSL Threshold Match).
    
    PROPERTY: The is_light() method MUST return exactly the same result
    as comparing HSL lightness to 0.5 threshold.
    
    VALIDATES: Requirement 12.1 - Consistent threshold application.
    """
    bg_color = RGB(r, g, b)
    
    # Get classification from is_light()
    is_light_result = bg_color.is_light()
    
    # Get classification from direct HSL comparison
    hsl = bg_color.hsl()
    threshold_result = hsl.l > 0.5
    
    # They must match exactly
    assert is_light_result == threshold_result, (
        f"is_light() returned {is_light_result} but HSL lightness {hsl.l:.3f} > 0.5 "
        f"evaluates to {threshold_result} for RGB({r}, {g}, {b})"
    )


def test_background_classification_threshold_precision():
    """Property 37: Background Lightness Classification (Threshold Precision).
    
    PROPERTY: Colors with lightness very close to 0.5 MUST be classified
    consistently based on the exact threshold, accounting for RGB→HSL→RGB
    conversion precision.
    
    VALIDATES: Requirement 12.1 - Precise threshold handling.
    """
    from src.color_util import HSL
    
    # Test colors just below threshold
    just_below = HSL(h=0.0, s=0.0, l=0.499).rgb()
    assert just_below.is_light() is False
    
    # Test colors just above threshold
    just_above = HSL(h=0.0, s=0.0, l=0.501).rgb()
    assert just_above.is_light() is True
    
    # Test exactly at threshold - need to check actual lightness after conversion
    # HSL(0, 0, 0.5) → RGB(128, 128, 128) → HSL has lightness ≈ 0.502
    at_threshold = HSL(h=0.0, s=0.0, l=0.5).rgb()
    actual_lightness = at_threshold.hsl().l
    # Classification should match actual lightness after round-trip
    assert at_threshold.is_light() == (actual_lightness > 0.5)


@given(
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255),
)
def test_background_classification_type_safety(
    r: int,
    g: int,
    b: int,
):
    """Property 37: Background Lightness Classification (Type Safety).
    
    PROPERTY: The is_light() method MUST always return a boolean value,
    never None or any other type.
    
    VALIDATES: Requirement 12.1 - Type-safe classification.
    """
    bg_color = RGB(r, g, b)
    result = bg_color.is_light()
    
    # Verify result is a boolean
    assert isinstance(result, bool), (
        f"is_light() must return bool, got {type(result).__name__}: {result}"
    )
    
    # Verify it's exactly True or False (not truthy/falsy)
    assert result is True or result is False
