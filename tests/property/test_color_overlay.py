"""
Property-based tests for color overlay operations.

Tests:
- Property 4: Color Overlay Produces Valid RGB

Validates Requirements 1.5
"""

import pytest
from hypothesis import given, strategies as st
from src.color_util import RGB


# Strategy for generating valid RGB colors
rgb_colors = st.builds(
    RGB,
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)

# Strategy for generating alpha values
alpha_values = st.floats(min_value=0.0, max_value=1.0)


class TestColorOverlayProducesValidRGB:
    """Property 4: Color Overlay Produces Valid RGB
    
    For any two RGB colors and any alpha value in [0.0, 1.0], the overlay 
    operation should produce a valid RGB color where each component is in 
    [0, 255] and equals the weighted average: (1-alpha)*c1 + alpha*c2.
    
    Validates: Requirements 1.5
    """
    
    @given(rgb_colors, rgb_colors, alpha_values)
    def test_overlay_produces_valid_rgb_components(self, base: RGB, overlay: RGB, alpha: float):
        """overlay() should produce RGB with all components in [0, 255]."""
        result = base.overlay(overlay, alpha)
        
        # All components should be in valid range
        assert 0 <= result.r <= 255, f"Red out of range: {result.r}"
        assert 0 <= result.g <= 255, f"Green out of range: {result.g}"
        assert 0 <= result.b <= 255, f"Blue out of range: {result.b}"
    
    @given(rgb_colors, rgb_colors, alpha_values)
    def test_overlay_weighted_average_formula(self, base: RGB, overlay: RGB, alpha: float):
        """overlay() should compute weighted average: (1-alpha)*base + alpha*overlay."""
        result = base.overlay(overlay, alpha)
        
        # Calculate expected values using the formula
        expected_r = round((1 - alpha) * base.r + alpha * overlay.r)
        expected_g = round((1 - alpha) * base.g + alpha * overlay.g)
        expected_b = round((1 - alpha) * base.b + alpha * overlay.b)
        
        # Results should match expected values (within rounding tolerance)
        assert abs(result.r - expected_r) <= 1, \
            f"Red mismatch: expected {expected_r}, got {result.r}"
        assert abs(result.g - expected_g) <= 1, \
            f"Green mismatch: expected {expected_g}, got {result.g}"
        assert abs(result.b - expected_b) <= 1, \
            f"Blue mismatch: expected {expected_b}, got {result.b}"
    
    @given(rgb_colors, rgb_colors)
    def test_overlay_alpha_zero_returns_base(self, base: RGB, overlay: RGB):
        """overlay() with alpha=0.0 should return the base color."""
        result = base.overlay(overlay, 0.0)
        
        # Result should be identical to base color
        assert result.r == base.r, f"Red changed: {base.r} → {result.r}"
        assert result.g == base.g, f"Green changed: {base.g} → {result.g}"
        assert result.b == base.b, f"Blue changed: {base.b} → {result.b}"
    
    @given(rgb_colors, rgb_colors)
    def test_overlay_alpha_one_returns_overlay(self, base: RGB, overlay: RGB):
        """overlay() with alpha=1.0 should return the overlay color."""
        result = base.overlay(overlay, 1.0)
        
        # Result should be identical to overlay color
        assert result.r == overlay.r, f"Red mismatch: {overlay.r} → {result.r}"
        assert result.g == overlay.g, f"Green mismatch: {overlay.g} → {result.g}"
        assert result.b == overlay.b, f"Blue mismatch: {overlay.b} → {result.b}"
    
    @given(rgb_colors, rgb_colors)
    def test_overlay_alpha_half_is_midpoint(self, base: RGB, overlay: RGB):
        """overlay() with alpha=0.5 should produce the midpoint color."""
        result = base.overlay(overlay, 0.5)
        
        # Calculate expected midpoint
        expected_r = round((base.r + overlay.r) / 2.0)
        expected_g = round((base.g + overlay.g) / 2.0)
        expected_b = round((base.b + overlay.b) / 2.0)
        
        # Results should match midpoint (within rounding tolerance)
        assert abs(result.r - expected_r) <= 1, \
            f"Red midpoint mismatch: expected {expected_r}, got {result.r}"
        assert abs(result.g - expected_g) <= 1, \
            f"Green midpoint mismatch: expected {expected_g}, got {result.g}"
        assert abs(result.b - expected_b) <= 1, \
            f"Blue midpoint mismatch: expected {expected_b}, got {result.b}"
    
    @given(rgb_colors, alpha_values)
    def test_overlay_with_self_returns_self(self, color: RGB, alpha: float):
        """overlay() of a color with itself should return the same color."""
        result = color.overlay(color, alpha)
        
        # Result should be identical to original color
        assert result.r == color.r, f"Red changed: {color.r} → {result.r}"
        assert result.g == color.g, f"Green changed: {color.g} → {result.g}"
        assert result.b == color.b, f"Blue changed: {color.b} → {result.b}"
    
    @given(rgb_colors, rgb_colors, alpha_values)
    def test_overlay_is_commutative_with_inverse_alpha(self, c1: RGB, c2: RGB, alpha: float):
        """overlay(c1, c2, alpha) should equal overlay(c2, c1, 1-alpha)."""
        result1 = c1.overlay(c2, alpha)
        result2 = c2.overlay(c1, 1.0 - alpha)
        
        # Results should be identical (within rounding tolerance)
        assert abs(result1.r - result2.r) <= 1, \
            f"Red mismatch: {result1.r} vs {result2.r}"
        assert abs(result1.g - result2.g) <= 1, \
            f"Green mismatch: {result1.g} vs {result2.g}"
        assert abs(result1.b - result2.b) <= 1, \
            f"Blue mismatch: {result1.b} vs {result2.b}"
    
    @given(rgb_colors, rgb_colors, alpha_values)
    def test_overlay_result_between_base_and_overlay(self, base: RGB, overlay: RGB, alpha: float):
        """overlay() result should be between base and overlay colors."""
        result = base.overlay(overlay, alpha)
        
        # For each component, result should be between base and overlay
        # (or equal to one of them)
        for component in ['r', 'g', 'b']:
            base_val = getattr(base, component)
            overlay_val = getattr(overlay, component)
            result_val = getattr(result, component)
            
            min_val = min(base_val, overlay_val)
            max_val = max(base_val, overlay_val)
            
            assert min_val <= result_val <= max_val, \
                f"{component.upper()} not between base and overlay: " \
                f"{base_val}, {overlay_val} → {result_val}"
    
    def test_overlay_invalid_alpha_raises_error(self):
        """overlay() should raise ValueError for alpha outside [0.0, 1.0]."""
        base = RGB(100, 100, 100)
        overlay = RGB(200, 200, 200)
        
        # Alpha < 0.0 should raise error
        with pytest.raises(ValueError, match="Alpha must be in"):
            base.overlay(overlay, -0.1)
        
        # Alpha > 1.0 should raise error
        with pytest.raises(ValueError, match="Alpha must be in"):
            base.overlay(overlay, 1.1)


class TestOverlayEdgeCases:
    """Test edge cases for color overlay operations."""
    
    def test_overlay_black_on_white(self):
        """Overlaying black on white should produce gray."""
        white = RGB(255, 255, 255)
        black = RGB(0, 0, 0)
        
        # 50% overlay should produce mid-gray
        result = white.overlay(black, 0.5)
        
        # Should be approximately (128, 128, 128)
        assert 127 <= result.r <= 128
        assert 127 <= result.g <= 128
        assert 127 <= result.b <= 128
    
    def test_overlay_white_on_black(self):
        """Overlaying white on black should produce gray."""
        black = RGB(0, 0, 0)
        white = RGB(255, 255, 255)
        
        # 50% overlay should produce mid-gray
        result = black.overlay(white, 0.5)
        
        # Should be approximately (128, 128, 128)
        assert 127 <= result.r <= 128
        assert 127 <= result.g <= 128
        assert 127 <= result.b <= 128
    
    def test_overlay_red_on_blue(self):
        """Overlaying red on blue should produce purple."""
        blue = RGB(0, 0, 255)
        red = RGB(255, 0, 0)
        
        # 50% overlay should produce purple
        result = blue.overlay(red, 0.5)
        
        # Should be approximately (128, 0, 128)
        assert 127 <= result.r <= 128
        assert result.g == 0
        assert 127 <= result.b <= 128
    
    def test_overlay_transparent_overlay(self):
        """Overlaying with very low alpha should barely change base."""
        base = RGB(100, 150, 200)
        overlay = RGB(255, 0, 0)
        
        # Very low alpha (1% overlay)
        result = base.overlay(overlay, 0.01)
        
        # Result should be very close to base
        assert abs(result.r - base.r) <= 2
        assert abs(result.g - base.g) <= 2
        assert abs(result.b - base.b) <= 2
    
    def test_overlay_opaque_overlay(self):
        """Overlaying with very high alpha should nearly replace base."""
        base = RGB(100, 150, 200)
        overlay = RGB(255, 0, 0)
        
        # Very high alpha (99% overlay)
        result = base.overlay(overlay, 0.99)
        
        # Result should be very close to overlay
        assert abs(result.r - overlay.r) <= 2
        assert abs(result.g - overlay.g) <= 2
        assert abs(result.b - overlay.b) <= 2
    
    def test_overlay_same_color_different_alphas(self):
        """Overlaying same color with different alphas should return same color."""
        base = RGB(100, 150, 200)
        
        # All alphas should return the same color when overlaying with itself
        for alpha in [0.0, 0.25, 0.5, 0.75, 1.0]:
            result = base.overlay(base, alpha)
            assert result.r == base.r
            assert result.g == base.g
            assert result.b == base.b
    
    def test_overlay_preserves_grayscale(self):
        """Overlaying two grayscale colors should produce grayscale."""
        gray1 = RGB(100, 100, 100)
        gray2 = RGB(200, 200, 200)
        
        result = gray1.overlay(gray2, 0.5)
        
        # Result should be grayscale (all components equal)
        assert result.r == result.g == result.b
    
    def test_overlay_multiple_times(self):
        """Multiple overlay operations should be composable."""
        base = RGB(0, 0, 0)
        white = RGB(255, 255, 255)
        
        # Overlay white multiple times with alpha=0.25 each
        # After 1st: 0.75*0 + 0.25*255 = 63.75 ≈ 64
        # After 2nd: 0.75*64 + 0.25*255 = 111.75 ≈ 112
        # After 3rd: 0.75*112 + 0.25*255 = 147.75 ≈ 148
        # After 4th: 0.75*148 + 0.25*255 = 174.75 ≈ 175
        result = base
        for _ in range(4):
            result = result.overlay(white, 0.25)
        
        # Result should be progressively lighter but not fully white
        # Expected around 175 based on the calculation above
        assert 170 <= result.r <= 180
        assert 170 <= result.g <= 180
        assert 170 <= result.b <= 180
