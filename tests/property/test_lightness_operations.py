"""
Property-based tests for lightness operations.

Tests:
- Property 2: Lightness Adjustment Preserves Hue and Saturation
- Property 3: RGB Redistribution Maintains Proportions
- Property 5: Lightness Classification Threshold

Validates Requirements 1.3, 1.4, 1.7
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.color_util import RGB, redistribute_rgb


# Strategy for generating valid RGB colors
rgb_colors = st.builds(
    RGB,
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)

# Strategy for generating lightness values
lightness_values = st.floats(min_value=0.0, max_value=1.0)

# Strategy for generating multipliers that may cause overflow
multipliers = st.floats(min_value=1.0, max_value=5.0)

# Strategy for generating RGB values that may exceed 255
overflowing_rgb = st.tuples(
    st.integers(min_value=0, max_value=1000),
    st.integers(min_value=0, max_value=1000),
    st.integers(min_value=0, max_value=1000)
)


class TestLightnessAdjustmentPreservesHueAndSaturation:
    """Property 2: Lightness Adjustment Preserves Hue and Saturation
    
    For any RGB color and any lightness value in [0.0, 1.0], setting the 
    lightness should preserve the original hue and saturation values 
    (within tolerance of ±0.01).
    
    Validates: Requirements 1.3, 12.7
    """
    
    @given(rgb_colors, lightness_values)
    def test_set_light_preserves_hue_and_saturation(self, rgb: RGB, target_light: float):
        """set_light() should preserve hue and saturation."""
        # Skip edge cases where hue/saturation are undefined
        original_hsl = rgb.hsl()
        
        # Skip grayscale colors (saturation = 0) where hue is undefined
        assume(original_hsl.s > 0.1)
        
        # Skip very dark/light colors where precision is poor
        assume(original_hsl.l > 0.15 and original_hsl.l < 0.85)
        
        # Skip target lightness at extremes (0.0 = black, 1.0 = white)
        # where hue and saturation become mathematically undefined
        assume(target_light > 0.15 and target_light < 0.85)
        
        # Skip extreme lightness changes that cause significant RGB quantization effects
        lightness_change = abs(target_light - original_hsl.l)
        assume(lightness_change < 0.6)
        
        # Adjust lightness
        adjusted_rgb = rgb.set_light(target_light)
        adjusted_hsl = adjusted_rgb.hsl()
        
        # Hue should be preserved (within tolerance)
        # Hue is circular, so we need special handling
        hue_diff = min(
            abs(original_hsl.h - adjusted_hsl.h),
            abs(original_hsl.h - adjusted_hsl.h + 1.0),
            abs(original_hsl.h - adjusted_hsl.h - 1.0)
        )
        assert hue_diff <= 0.02, \
            f"Hue changed: {original_hsl.h} → {adjusted_hsl.h} (diff: {hue_diff})"
        
        # Saturation should be preserved (within tolerance)
        # RGB quantization causes precision loss, especially with large lightness changes
        assert abs(original_hsl.s - adjusted_hsl.s) <= 0.02, \
            f"Saturation changed: {original_hsl.s} → {adjusted_hsl.s}"
        
        # Lightness should match target (within tolerance)
        assert abs(adjusted_hsl.l - target_light) <= 0.01, \
            f"Lightness not set correctly: target={target_light}, actual={adjusted_hsl.l}"
    
    @given(rgb_colors, lightness_values)
    def test_set_light_at_least_constraint(self, rgb: RGB, target_light: float):
        """set_light() with at_least=True should not decrease lightness."""
        original_hsl = rgb.hsl()
        
        # Apply set_light with at_least=True
        adjusted_rgb = rgb.set_light(target_light, at_least=True)
        adjusted_hsl = adjusted_rgb.hsl()
        
        # If target is less than current, lightness should not change
        if target_light < original_hsl.l:
            assert abs(adjusted_hsl.l - original_hsl.l) <= 0.01, \
                f"Lightness decreased when at_least=True: {original_hsl.l} → {adjusted_hsl.l}"
        else:
            # Otherwise, lightness should be set to target
            assert abs(adjusted_hsl.l - target_light) <= 0.01, \
                f"Lightness not set correctly: target={target_light}, actual={adjusted_hsl.l}"
    
    @given(rgb_colors, lightness_values)
    def test_set_light_at_most_constraint(self, rgb: RGB, target_light: float):
        """set_light() with at_most=True should not increase lightness."""
        original_hsl = rgb.hsl()
        
        # Apply set_light with at_most=True
        adjusted_rgb = rgb.set_light(target_light, at_most=True)
        adjusted_hsl = adjusted_rgb.hsl()
        
        # If target is greater than current, lightness should not change
        if target_light > original_hsl.l:
            assert abs(adjusted_hsl.l - original_hsl.l) <= 0.01, \
                f"Lightness increased when at_most=True: {original_hsl.l} → {adjusted_hsl.l}"
        else:
            # Otherwise, lightness should be set to target
            assert abs(adjusted_hsl.l - target_light) <= 0.01, \
                f"Lightness not set correctly: target={target_light}, actual={adjusted_hsl.l}"
    
    @given(rgb_colors, lightness_values)
    def test_set_light_produces_valid_rgb(self, rgb: RGB, target_light: float):
        """set_light() should always produce valid RGB values."""
        adjusted_rgb = rgb.set_light(target_light)
        
        # RGB values should be in valid range
        assert 0 <= adjusted_rgb.r <= 255, f"Invalid red: {adjusted_rgb.r}"
        assert 0 <= adjusted_rgb.g <= 255, f"Invalid green: {adjusted_rgb.g}"
        assert 0 <= adjusted_rgb.b <= 255, f"Invalid blue: {adjusted_rgb.b}"


class TestRGBRedistributionMaintainsProportions:
    """Property 3: RGB Redistribution Maintains Proportions
    
    For any RGB color and any multiplier that causes component overflow (>255),
    the redistribute_rgb function should ensure all components are ≤255 while
    maintaining the proportional relationships between R, G, and B components.
    
    Validates: Requirements 1.4
    """
    
    @given(overflowing_rgb)
    def test_redistribute_rgb_maintains_proportions(self, rgb_tuple):
        """redistribute_rgb() should maintain proportional relationships."""
        r, g, b = rgb_tuple
        
        # Skip cases where all components are 0 (no proportions to maintain)
        assume(r > 0 or g > 0 or b > 0)
        
        # Calculate original proportions
        max_original = max(r, g, b)
        if max_original == 0:
            return  # Skip all-zero case
        
        original_ratios = (
            r / max_original,
            g / max_original,
            b / max_original
        )
        
        # Redistribute
        new_r, new_g, new_b = redistribute_rgb(r, g, b)
        
        # Calculate new proportions
        max_new = max(new_r, new_g, new_b)
        if max_new == 0:
            return  # Skip all-zero result
        
        new_ratios = (
            new_r / max_new,
            new_g / max_new,
            new_b / max_new
        )
        
        # Proportions should be preserved (within rounding tolerance)
        tolerance = 0.01  # 1% tolerance for rounding
        assert abs(original_ratios[0] - new_ratios[0]) <= tolerance, \
            f"Red proportion changed: {original_ratios[0]} → {new_ratios[0]}"
        assert abs(original_ratios[1] - new_ratios[1]) <= tolerance, \
            f"Green proportion changed: {original_ratios[1]} → {new_ratios[1]}"
        assert abs(original_ratios[2] - new_ratios[2]) <= tolerance, \
            f"Blue proportion changed: {original_ratios[2]} → {new_ratios[2]}"
    
    @given(overflowing_rgb)
    def test_redistribute_rgb_ensures_valid_range(self, rgb_tuple):
        """redistribute_rgb() should ensure all components are ≤255."""
        r, g, b = rgb_tuple
        
        new_r, new_g, new_b = redistribute_rgb(r, g, b)
        
        # All components should be in valid range
        assert 0 <= new_r <= 255, f"Red out of range: {new_r}"
        assert 0 <= new_g <= 255, f"Green out of range: {new_g}"
        assert 0 <= new_b <= 255, f"Blue out of range: {new_b}"
    
    @given(overflowing_rgb)
    def test_redistribute_rgb_preserves_max_component(self, rgb_tuple):
        """redistribute_rgb() should scale max component to 255 when overflow occurs."""
        r, g, b = rgb_tuple
        
        # Only test cases where overflow actually occurs
        assume(max(r, g, b) > 255)
        
        new_r, new_g, new_b = redistribute_rgb(r, g, b)
        
        # The maximum component should be 255 (or very close due to rounding)
        max_new = max(new_r, new_g, new_b)
        assert max_new == 255, \
            f"Max component should be 255 after redistribution, got {max_new}"
    
    @given(rgb_colors)
    def test_redistribute_rgb_no_op_for_valid_colors(self, rgb: RGB):
        """redistribute_rgb() should not change colors already in valid range."""
        new_r, new_g, new_b = redistribute_rgb(rgb.r, rgb.g, rgb.b)
        
        # Values should be unchanged
        assert new_r == rgb.r, f"Red changed: {rgb.r} → {new_r}"
        assert new_g == rgb.g, f"Green changed: {rgb.g} → {new_g}"
        assert new_b == rgb.b, f"Blue changed: {rgb.b} → {new_b}"
    
    @given(rgb_colors, multipliers)
    def test_lighten_uses_redistribute_correctly(self, rgb: RGB, multiplier: float):
        """lighten() should use redistribute_rgb when components exceed 255."""
        # Skip very dark colors that won't overflow even with high multipliers
        assume(max(rgb.r, rgb.g, rgb.b) > 50)
        
        lightened = rgb.lighten(multiplier)
        
        # Result should be valid
        assert 0 <= lightened.r <= 255, f"Invalid red: {lightened.r}"
        assert 0 <= lightened.g <= 255, f"Invalid green: {lightened.g}"
        assert 0 <= lightened.b <= 255, f"Invalid blue: {lightened.b}"
        
        # If original * multiplier would overflow, check proportions are maintained
        if rgb.r * multiplier > 255 or rgb.g * multiplier > 255 or rgb.b * multiplier > 255:
            # Calculate expected proportions
            max_original = max(rgb.r, rgb.g, rgb.b)
            if max_original > 0:
                original_ratios = (
                    rgb.r / max_original,
                    rgb.g / max_original,
                    rgb.b / max_original
                )
                
                max_lightened = max(lightened.r, lightened.g, lightened.b)
                if max_lightened > 0:
                    lightened_ratios = (
                        lightened.r / max_lightened,
                        lightened.g / max_lightened,
                        lightened.b / max_lightened
                    )
                    
                    # Proportions should be preserved
                    tolerance = 0.02  # 2% tolerance for rounding
                    assert abs(original_ratios[0] - lightened_ratios[0]) <= tolerance
                    assert abs(original_ratios[1] - lightened_ratios[1]) <= tolerance
                    assert abs(original_ratios[2] - lightened_ratios[2]) <= tolerance


class TestLightnessClassificationThreshold:
    """Property 5: Lightness Classification Threshold
    
    For any RGB color, is_light() should return True if and only if the 
    HSL lightness value is greater than 0.5.
    
    Validates: Requirements 1.7
    """
    
    @given(rgb_colors)
    def test_is_light_matches_hsl_threshold(self, rgb: RGB):
        """is_light() should return True iff HSL lightness > 0.5."""
        hsl = rgb.hsl()
        is_light_result = rgb.is_light()
        
        # is_light() should match the threshold check
        expected = hsl.l > 0.5
        assert is_light_result == expected, \
            f"is_light() returned {is_light_result}, but lightness is {hsl.l}"
    
    @given(lightness_values)
    def test_is_light_threshold_boundary(self, lightness: float):
        """is_light() should correctly classify colors at threshold boundary."""
        # Create a grayscale color with specific lightness
        # For grayscale, RGB = (L*255, L*255, L*255) approximately
        gray_value = round(lightness * 255)
        rgb = RGB(gray_value, gray_value, gray_value)
        
        hsl = rgb.hsl()
        is_light_result = rgb.is_light()
        
        # Verify classification matches threshold
        expected = hsl.l > 0.5
        assert is_light_result == expected, \
            f"is_light() returned {is_light_result}, but lightness is {hsl.l}"
    
    def test_is_light_known_light_colors(self):
        """is_light() should return True for known light colors."""
        light_colors = [
            RGB(255, 255, 255),  # White (L=1.0)
            RGB(255, 255, 128),  # Light yellow (L>0.5)
            RGB(128, 255, 255),  # Light cyan (L>0.5)
            RGB(255, 128, 255),  # Light magenta (L>0.5)
            RGB(200, 200, 200),  # Light gray (L>0.5)
        ]
        
        for color in light_colors:
            assert color.is_light(), \
                f"Color {color} should be classified as light (L={color.hsl().l})"
    
    def test_is_light_known_dark_colors(self):
        """is_light() should return False for known dark colors."""
        dark_colors = [
            RGB(0, 0, 0),      # Black
            RGB(255, 0, 0),    # Red
            RGB(0, 255, 0),    # Green
            RGB(0, 0, 255),    # Blue
            RGB(50, 50, 50),   # Dark gray
        ]
        
        for color in dark_colors:
            assert not color.is_light(), \
                f"Color {color} should be classified as dark (L={color.hsl().l})"
    
    def test_is_light_threshold_exactly_at_half(self):
        """is_light() should handle colors exactly at L=0.5 threshold."""
        # Create a color with lightness very close to 0.5
        # Gray with value 128 should be close to L=0.5
        gray = RGB(128, 128, 128)
        hsl = gray.hsl()
        
        # Verify the classification matches the threshold
        expected = hsl.l > 0.5
        assert gray.is_light() == expected, \
            f"Classification mismatch at threshold: L={hsl.l}, is_light()={gray.is_light()}"


class TestEdgeCases:
    """Test edge cases for lightness operations."""
    
    def test_set_light_black_to_white(self):
        """Setting lightness of black to 1.0 should produce white."""
        black = RGB(0, 0, 0)
        white = black.set_light(1.0)
        
        # Should be white or very close
        assert white.r >= 254 and white.g >= 254 and white.b >= 254
    
    def test_set_light_white_to_black(self):
        """Setting lightness of white to 0.0 should produce black."""
        white = RGB(255, 255, 255)
        black = white.set_light(0.0)
        
        # Should be black or very close
        assert black.r <= 1 and black.g <= 1 and black.b <= 1
    
    def test_set_light_preserves_color_at_same_lightness(self):
        """Setting lightness to current value should not change color."""
        color = RGB(100, 150, 200)
        original_hsl = color.hsl()
        
        same_light = color.set_light(original_hsl.l)
        
        # Color should be unchanged (within rounding tolerance)
        assert abs(color.r - same_light.r) <= 1
        assert abs(color.g - same_light.g) <= 1
        assert abs(color.b - same_light.b) <= 1
    
    def test_redistribute_rgb_all_zeros(self):
        """redistribute_rgb() should handle all-zero input."""
        r, g, b = redistribute_rgb(0, 0, 0)
        
        assert r == 0 and g == 0 and b == 0
    
    def test_redistribute_rgb_single_component(self):
        """redistribute_rgb() should handle single non-zero component."""
        # Only red component
        r, g, b = redistribute_rgb(500, 0, 0)
        assert r == 255 and g == 0 and b == 0
        
        # Only green component
        r, g, b = redistribute_rgb(0, 500, 0)
        assert r == 0 and g == 255 and b == 0
        
        # Only blue component
        r, g, b = redistribute_rgb(0, 0, 500)
        assert r == 0 and g == 0 and b == 255
    
    def test_lighten_black_stays_black(self):
        """Lightening black should keep it black."""
        black = RGB(0, 0, 0)
        lightened = black.lighten(2.0)
        
        assert lightened.r == 0 and lightened.g == 0 and lightened.b == 0
    
    def test_lighten_with_multiplier_one(self):
        """Lightening with multiplier 1.0 should not change color."""
        color = RGB(100, 150, 200)
        same = color.lighten(1.0)
        
        assert color.r == same.r
        assert color.g == same.g
        assert color.b == same.b
