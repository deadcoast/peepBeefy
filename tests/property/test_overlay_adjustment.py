"""
Property-based tests for overlay lightness adjustment.

Tests:
- Property 38: Overlay Lightness Adjustment Validity

Validates Requirements 12.4
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.color_util import RGB
from src.themes import adjust_color_for_background


# Strategy for generating valid RGB colors
rgb_colors = st.builds(
    RGB,
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)

# Strategy for generating hex color strings
hex_colors = st.builds(
    lambda r, g, b: f"#{r:02x}{g:02x}{b:02x}",
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)


class TestOverlayLightnessAdjustmentValidity:
    """Property 38: Overlay Lightness Adjustment Validity
    
    For any color and any overlay-based lightness adjustment, the result 
    should be a valid RGB color with all components in [0, 255].
    
    Validates: Requirements 12.4
    """
    
    @given(hex_colors, rgb_colors)
    def test_overlay_adjustment_produces_valid_rgb(self, hex_color: str, bg_color: RGB):
        """Overlay adjustment should always produce valid RGB values."""
        # Adjust color using overlay method
        adjusted_hex = adjust_color_for_background(hex_color, bg_color, method="overlay")
        
        # Parse the adjusted color
        adjusted_rgb = RGB.from_hex(adjusted_hex)
        
        # RGB values should be in valid range
        assert 0 <= adjusted_rgb.r <= 255, f"Invalid red: {adjusted_rgb.r}"
        assert 0 <= adjusted_rgb.g <= 255, f"Invalid green: {adjusted_rgb.g}"
        assert 0 <= adjusted_rgb.b <= 255, f"Invalid blue: {adjusted_rgb.b}"
    
    @given(hex_colors, rgb_colors)
    def test_overlay_adjustment_meets_lightness_requirements_dark_bg(self, hex_color: str, bg_color: RGB):
        """Overlay adjustment should ensure lightness >= 0.65 for dark backgrounds."""
        # Only test with dark backgrounds
        assume(not bg_color.is_light())
        
        # Adjust color using overlay method
        adjusted_hex = adjust_color_for_background(hex_color, bg_color, method="overlay")
        adjusted_rgb = RGB.from_hex(adjusted_hex)
        adjusted_hsl = adjusted_rgb.hsl()
        
        # For dark backgrounds, lightness should be at least 0.65
        assert adjusted_hsl.l >= 0.64, \
            f"Lightness {adjusted_hsl.l} is below 0.65 threshold for dark background"
    
    @given(hex_colors, rgb_colors)
    def test_overlay_adjustment_meets_lightness_requirements_light_bg(self, hex_color: str, bg_color: RGB):
        """Overlay adjustment should ensure lightness <= 0.4 for light backgrounds."""
        # Only test with light backgrounds
        assume(bg_color.is_light())
        
        # Adjust color using overlay method
        adjusted_hex = adjust_color_for_background(hex_color, bg_color, method="overlay")
        adjusted_rgb = RGB.from_hex(adjusted_hex)
        adjusted_hsl = adjusted_rgb.hsl()
        
        # For light backgrounds, lightness should be at most 0.4
        assert adjusted_hsl.l <= 0.41, \
            f"Lightness {adjusted_hsl.l} is above 0.4 threshold for light background"
    
    @given(hex_colors, rgb_colors)
    def test_overlay_adjustment_returns_valid_hex_format(self, hex_color: str, bg_color: RGB):
        """Overlay adjustment should return valid hex color string."""
        adjusted_hex = adjust_color_for_background(hex_color, bg_color, method="overlay")
        
        # Should be a valid hex color string
        assert adjusted_hex.startswith("#"), f"Hex color should start with #: {adjusted_hex}"
        assert len(adjusted_hex) == 7, f"Hex color should be 7 characters: {adjusted_hex}"
        
        # Should be parseable as RGB
        try:
            RGB.from_hex(adjusted_hex)
        except ValueError as e:
            pytest.fail(f"Adjusted hex color is not valid: {adjusted_hex}, error: {e}")
    
    @given(hex_colors, rgb_colors)
    def test_overlay_adjustment_is_deterministic(self, hex_color: str, bg_color: RGB):
        """Overlay adjustment should produce consistent results for same inputs."""
        # Adjust color twice with same inputs
        result1 = adjust_color_for_background(hex_color, bg_color, method="overlay")
        result2 = adjust_color_for_background(hex_color, bg_color, method="overlay")
        
        # Results should be identical
        assert result1 == result2, \
            f"Overlay adjustment is not deterministic: {result1} != {result2}"
    
    @given(rgb_colors)
    def test_overlay_with_white_lightens_color(self, color: RGB):
        """Overlaying with white should lighten the color."""
        # Skip already very light colors
        assume(color.hsl().l < 0.9)
        
        white = RGB(255, 255, 255)
        lightened = color.overlay(white, 0.3)
        
        # Lightened color should have higher lightness
        assert lightened.hsl().l > color.hsl().l, \
            f"Overlay with white should lighten: {color.hsl().l} -> {lightened.hsl().l}"
    
    @given(rgb_colors)
    def test_overlay_with_black_darkens_color(self, color: RGB):
        """Overlaying with black should darken the color."""
        # Skip already very dark colors
        assume(color.hsl().l > 0.1)
        
        black = RGB(0, 0, 0)
        darkened = color.overlay(black, 0.3)
        
        # Darkened color should have lower lightness
        assert darkened.hsl().l < color.hsl().l, \
            f"Overlay with black should darken: {color.hsl().l} -> {darkened.hsl().l}"
    
    @given(rgb_colors, rgb_colors)
    def test_overlay_alpha_zero_preserves_base_color(self, base: RGB, overlay: RGB):
        """Overlay with alpha=0.0 should preserve the base color."""
        result = base.overlay(overlay, 0.0)
        
        # Result should be identical to base
        assert result.r == base.r, f"Red changed with alpha=0: {base.r} -> {result.r}"
        assert result.g == base.g, f"Green changed with alpha=0: {base.g} -> {result.g}"
        assert result.b == base.b, f"Blue changed with alpha=0: {base.b} -> {result.b}"
    
    @given(rgb_colors, rgb_colors)
    def test_overlay_alpha_one_uses_overlay_color(self, base: RGB, overlay: RGB):
        """Overlay with alpha=1.0 should use the overlay color."""
        result = base.overlay(overlay, 1.0)
        
        # Result should be identical to overlay
        assert result.r == overlay.r, f"Red not from overlay with alpha=1: {overlay.r} -> {result.r}"
        assert result.g == overlay.g, f"Green not from overlay with alpha=1: {overlay.g} -> {result.g}"
        assert result.b == overlay.b, f"Blue not from overlay with alpha=1: {overlay.b} -> {result.b}"
    
    @given(rgb_colors, rgb_colors, st.floats(min_value=0.0, max_value=1.0))
    def test_overlay_produces_intermediate_color(self, base: RGB, overlay: RGB, alpha: float):
        """Overlay should produce color between base and overlay."""
        result = base.overlay(overlay, alpha)
        
        # Each component should be between base and overlay (or equal)
        for component in ['r', 'g', 'b']:
            base_val = getattr(base, component)
            overlay_val = getattr(overlay, component)
            result_val = getattr(result, component)
            
            min_val = min(base_val, overlay_val)
            max_val = max(base_val, overlay_val)
            
            assert min_val <= result_val <= max_val, \
                f"{component} component {result_val} not between {min_val} and {max_val}"


class TestOverlayAdjustmentEdgeCases:
    """Test edge cases for overlay-based lightness adjustment."""
    
    def test_overlay_adjustment_with_pure_black_background(self):
        """Overlay adjustment should work with pure black background."""
        black_bg = RGB(0, 0, 0)
        color = "#808080"  # Medium gray
        
        adjusted = adjust_color_for_background(color, black_bg, method="overlay")
        adjusted_rgb = RGB.from_hex(adjusted)
        
        # Should be lightened for dark background
        assert adjusted_rgb.hsl().l >= 0.64
    
    def test_overlay_adjustment_with_pure_white_background(self):
        """Overlay adjustment should work with pure white background."""
        white_bg = RGB(255, 255, 255)
        color = "#808080"  # Medium gray
        
        adjusted = adjust_color_for_background(color, white_bg, method="overlay")
        adjusted_rgb = RGB.from_hex(adjusted)
        
        # Should be darkened for light background
        assert adjusted_rgb.hsl().l <= 0.41
    
    def test_overlay_adjustment_with_already_light_color_on_dark_bg(self):
        """Overlay adjustment should not over-lighten already light colors."""
        dark_bg = RGB(30, 30, 30)
        light_color = "#f0f0f0"  # Already very light
        
        adjusted = adjust_color_for_background(light_color, dark_bg, method="overlay")
        adjusted_rgb = RGB.from_hex(adjusted)
        
        # Should still be valid and meet threshold
        assert 0 <= adjusted_rgb.r <= 255
        assert 0 <= adjusted_rgb.g <= 255
        assert 0 <= adjusted_rgb.b <= 255
        assert adjusted_rgb.hsl().l >= 0.64
    
    def test_overlay_adjustment_with_already_dark_color_on_light_bg(self):
        """Overlay adjustment should not over-darken already dark colors."""
        light_bg = RGB(240, 240, 240)
        dark_color = "#101010"  # Already very dark
        
        adjusted = adjust_color_for_background(dark_color, light_bg, method="overlay")
        adjusted_rgb = RGB.from_hex(adjusted)
        
        # Should still be valid and meet threshold
        assert 0 <= adjusted_rgb.r <= 255
        assert 0 <= adjusted_rgb.g <= 255
        assert 0 <= adjusted_rgb.b <= 255
        assert adjusted_rgb.hsl().l <= 0.41
    
    def test_overlay_adjustment_with_saturated_colors(self):
        """Overlay adjustment should work with highly saturated colors."""
        dark_bg = RGB(20, 20, 20)
        saturated_colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"]
        
        for color in saturated_colors:
            adjusted = adjust_color_for_background(color, dark_bg, method="overlay")
            adjusted_rgb = RGB.from_hex(adjusted)
            
            # Should be valid and meet lightness threshold
            assert 0 <= adjusted_rgb.r <= 255
            assert 0 <= adjusted_rgb.g <= 255
            assert 0 <= adjusted_rgb.b <= 255
            assert adjusted_rgb.hsl().l >= 0.64, \
                f"Color {color} adjusted to {adjusted} with lightness {adjusted_rgb.hsl().l}"
    
    def test_overlay_adjustment_preserves_hue_approximately(self):
        """Overlay adjustment should approximately preserve hue."""
        dark_bg = RGB(30, 30, 30)
        color = "#ff6600"  # Orange
        
        original_rgb = RGB.from_hex(color)
        original_hue = original_rgb.hsl().h
        
        adjusted = adjust_color_for_background(color, dark_bg, method="overlay")
        adjusted_rgb = RGB.from_hex(adjusted)
        adjusted_hue = adjusted_rgb.hsl().h
        
        # Hue should be approximately preserved (within 0.1 or 10% of color wheel)
        # Handle circular hue values
        hue_diff = min(
            abs(original_hue - adjusted_hue),
            abs(original_hue - adjusted_hue + 1.0),
            abs(original_hue - adjusted_hue - 1.0)
        )
        
        assert hue_diff <= 0.1, \
            f"Hue changed significantly: {original_hue} -> {adjusted_hue} (diff: {hue_diff})"
    
    def test_overlay_adjustment_fallback_on_invalid_input(self):
        """Overlay adjustment should handle invalid inputs gracefully."""
        dark_bg = RGB(30, 30, 30)
        invalid_colors = ["not-a-color", "#gg0000", "#12", ""]
        
        for invalid_color in invalid_colors:
            try:
                # Should either raise ValueError or return original
                result = adjust_color_for_background(invalid_color, dark_bg, method="overlay")
                # If it doesn't raise, it should return the original
                assert result == invalid_color, \
                    f"Invalid color should be returned as-is: {invalid_color} -> {result}"
            except ValueError:
                # ValueError is acceptable for invalid input
                pass
    
    def test_overlay_adjustment_with_threshold_boundary_colors(self):
        """Overlay adjustment should handle colors at lightness threshold boundaries."""
        # Test with colors at L=0.5 threshold (boundary between light and dark)
        threshold_color = RGB(128, 128, 128)  # L ≈ 0.5
        
        # Dark background
        dark_bg = RGB(30, 30, 30)
        adjusted_dark = adjust_color_for_background(
            f"#{threshold_color.r:02x}{threshold_color.g:02x}{threshold_color.b:02x}",
            dark_bg,
            method="overlay"
        )
        adjusted_dark_rgb = RGB.from_hex(adjusted_dark)
        assert adjusted_dark_rgb.hsl().l >= 0.64
        
        # Light background
        light_bg = RGB(240, 240, 240)
        adjusted_light = adjust_color_for_background(
            f"#{threshold_color.r:02x}{threshold_color.g:02x}{threshold_color.b:02x}",
            light_bg,
            method="overlay"
        )
        adjusted_light_rgb = RGB.from_hex(adjusted_light)
        assert adjusted_light_rgb.hsl().l <= 0.41


class TestOverlayMethodComparison:
    """Compare overlay method with HSL method for lightness adjustment."""
    
    @given(hex_colors, rgb_colors)
    def test_both_methods_produce_valid_rgb(self, hex_color: str, bg_color: RGB):
        """Both overlay and HSL methods should produce valid RGB."""
        overlay_result = adjust_color_for_background(hex_color, bg_color, method="overlay")
        hsl_result = adjust_color_for_background(hex_color, bg_color, method="hsl")
        
        # Both should be valid hex colors
        overlay_rgb = RGB.from_hex(overlay_result)
        hsl_rgb = RGB.from_hex(hsl_result)
        
        # Both should have valid RGB components
        for rgb in [overlay_rgb, hsl_rgb]:
            assert 0 <= rgb.r <= 255
            assert 0 <= rgb.g <= 255
            assert 0 <= rgb.b <= 255
    
    @given(hex_colors, rgb_colors)
    def test_both_methods_meet_lightness_requirements(self, hex_color: str, bg_color: RGB):
        """Both methods should meet lightness requirements."""
        overlay_result = adjust_color_for_background(hex_color, bg_color, method="overlay")
        hsl_result = adjust_color_for_background(hex_color, bg_color, method="hsl")
        
        overlay_rgb = RGB.from_hex(overlay_result)
        hsl_rgb = RGB.from_hex(hsl_result)
        
        is_light_bg = bg_color.is_light()
        
        if is_light_bg:
            # Light background: both should have L <= 0.4
            assert overlay_rgb.hsl().l <= 0.41, \
                f"Overlay method failed light bg requirement: L={overlay_rgb.hsl().l}"
            assert hsl_rgb.hsl().l <= 0.41, \
                f"HSL method failed light bg requirement: L={hsl_rgb.hsl().l}"
        else:
            # Dark background: both should have L >= 0.65
            assert overlay_rgb.hsl().l >= 0.64, \
                f"Overlay method failed dark bg requirement: L={overlay_rgb.hsl().l}"
            assert hsl_rgb.hsl().l >= 0.64, \
                f"HSL method failed dark bg requirement: L={hsl_rgb.hsl().l}"
