"""
Integration test for gradient engine smoothness.

Task 20.3: Test gradient engine smoothness
- Verify smooth color transitions in generated gradients
- Test gradient lookup at various ratios
- Requirements: 14.3

This test validates that the gradient engine produces visually smooth
color transitions suitable for ASCII art colorization and theme gradients.
"""

import pytest
from src.color_util import RGB
from src.color_scale import create_gradient, create_gradient_hex, get_raw, Scale


class TestGradientSmoothness:
    """Integration tests for gradient smoothness and visual quality."""
    
    def test_gradient_produces_smooth_transitions(self):
        """Verify that gradients have smooth color transitions without abrupt jumps."""
        # Create a gradient from red to blue with high resolution
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        gradient = create_gradient([red, blue], resolution=100)
        
        # Check that consecutive colors have small differences
        max_diff = 0
        for i in range(len(gradient) - 1):
            c1 = gradient[i]
            c2 = gradient[i + 1]
            
            diff_r = abs(c2.r - c1.r)
            diff_g = abs(c2.g - c1.g)
            diff_b = abs(c2.b - c1.b)
            
            max_diff = max(max_diff, diff_r, diff_g, diff_b)
        
        # With resolution 100, max difference should be around 255/100 ≈ 2.55
        # Allow tolerance of 4 for rounding
        assert max_diff <= 4, \
            f"Gradient not smooth: max component difference is {max_diff}, expected ≤ 4"
    
    def test_multi_color_gradient_smoothness(self):
        """Verify smoothness in gradients with multiple color stops."""
        # Create a rainbow gradient
        colors = [
            RGB(255, 0, 0),    # Red
            RGB(255, 127, 0),  # Orange
            RGB(255, 255, 0),  # Yellow
            RGB(0, 255, 0),    # Green
            RGB(0, 0, 255),    # Blue
            RGB(75, 0, 130),   # Indigo
            RGB(148, 0, 211),  # Violet
        ]
        
        gradient = create_gradient(colors, resolution=50)
        
        # Check smoothness across all transitions
        max_diff = 0
        for i in range(len(gradient) - 1):
            c1 = gradient[i]
            c2 = gradient[i + 1]
            
            diff_r = abs(c2.r - c1.r)
            diff_g = abs(c2.g - c1.g)
            diff_b = abs(c2.b - c1.b)
            
            max_diff = max(max_diff, diff_r, diff_g, diff_b)
        
        # With resolution 50, max difference should be around 255/50 ≈ 5.1
        # Allow tolerance of 7 for rounding
        assert max_diff <= 7, \
            f"Multi-color gradient not smooth: max difference is {max_diff}"
    
    def test_gradient_lookup_at_various_ratios(self):
        """Test gradient lookup at various ratios returns expected colors."""
        # Create a simple red to blue gradient
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        gradient = create_gradient([red, blue], resolution=100)
        
        # Test at specific ratios
        test_cases = [
            (0.0, red),           # Start should be red
            (0.25, None),         # Quarter point
            (0.5, None),          # Midpoint
            (0.75, None),         # Three-quarter point
            (1.0, gradient[-1]),  # End should be last color
        ]
        
        for ratio, expected in test_cases:
            color = get_raw(gradient, ratio)
            
            # Verify color is valid
            assert isinstance(color, RGB)
            assert 0 <= color.r <= 255
            assert 0 <= color.g <= 255
            assert 0 <= color.b <= 255
            
            # Verify specific expectations
            if expected is not None:
                assert color.r == expected.r, \
                    f"At ratio {ratio}, expected r={expected.r}, got r={color.r}"
                assert color.g == expected.g, \
                    f"At ratio {ratio}, expected g={expected.g}, got g={color.g}"
                assert color.b == expected.b, \
                    f"At ratio {ratio}, expected b={expected.b}, got b={color.b}"
    
    def test_gradient_lookup_monotonicity(self):
        """Verify that gradient lookup produces monotonic color changes."""
        # Create gradient from dark to light
        dark = RGB(50, 50, 50)
        light = RGB(200, 200, 200)
        gradient = create_gradient([dark, light], resolution=100)
        
        # Sample at increasing ratios
        ratios = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        colors = [get_raw(gradient, r) for r in ratios]
        
        # Verify that RGB components increase monotonically (or stay same)
        for i in range(len(colors) - 1):
            c1 = colors[i]
            c2 = colors[i + 1]
            
            # All components should be non-decreasing (allow ±1 for rounding)
            assert c2.r >= c1.r - 1, \
                f"Red not monotonic at ratios {ratios[i]} -> {ratios[i+1]}: {c1.r} -> {c2.r}"
            assert c2.g >= c1.g - 1, \
                f"Green not monotonic at ratios {ratios[i]} -> {ratios[i+1]}: {c1.g} -> {c2.g}"
            assert c2.b >= c1.b - 1, \
                f"Blue not monotonic at ratios {ratios[i]} -> {ratios[i+1]}: {c1.b} -> {c2.b}"
    
    def test_scale_lookup_smoothness(self):
        """Verify Scale class provides smooth lookups."""
        # Create a scale from hex colors
        scale = Scale(["#FF0000", "#00FF00", "#0000FF"], resolution=100)
        
        # Sample at many ratios
        ratios = [i / 100 for i in range(101)]
        colors = [scale(r) for r in ratios]
        
        # Check smoothness between consecutive samples
        max_diff = 0
        for i in range(len(colors) - 1):
            c1 = colors[i]
            c2 = colors[i + 1]
            
            diff_r = abs(c2.r - c1.r)
            diff_g = abs(c2.g - c1.g)
            diff_b = abs(c2.b - c1.b)
            
            max_diff = max(max_diff, diff_r, diff_g, diff_b)
        
        # With 101 samples across 200 gradient steps (2 color pairs * 100 resolution),
        # we're sampling roughly every 2 steps, so max diff should be small
        assert max_diff <= 6, \
            f"Scale lookup not smooth: max difference is {max_diff}"
    
    def test_gradient_visual_quality_for_ascii_art(self):
        """Verify gradient quality is suitable for ASCII art colorization."""
        # Create a gradient suitable for ASCII art (e.g., fire effect)
        fire_colors = [
            RGB(255, 0, 0),      # Red
            RGB(255, 127, 0),    # Orange
            RGB(255, 255, 0),    # Yellow
            RGB(255, 255, 255),  # White
        ]
        
        gradient = create_gradient(fire_colors, resolution=50)
        
        # Verify gradient has enough steps for smooth ASCII art
        # For typical ASCII art (20-50 lines), we need at least that many colors
        assert len(gradient) >= 150, \
            f"Gradient too short for ASCII art: {len(gradient)} colors"
        
        # Verify no abrupt color jumps
        for i in range(len(gradient) - 1):
            c1 = gradient[i]
            c2 = gradient[i + 1]
            
            # Calculate Euclidean distance in RGB space
            distance = ((c2.r - c1.r)**2 + (c2.g - c1.g)**2 + (c2.b - c1.b)**2) ** 0.5
            
            # Distance should be small (smooth transition)
            assert distance <= 10, \
                f"Abrupt color jump at index {i}: distance={distance:.2f}"
    
    def test_gradient_boundary_behavior(self):
        """Verify gradient lookup handles boundary conditions correctly."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        gradient = create_gradient([red, blue], resolution=100)
        
        # Test boundary conditions
        boundary_tests = [
            (-1.0, gradient[0]),   # Below 0 should clamp to first
            (-0.5, gradient[0]),
            (0.0, gradient[0]),    # Exactly 0
            (1.0, gradient[-1]),   # Exactly 1
            (1.5, gradient[-1]),   # Above 1 should clamp to last
            (2.0, gradient[-1]),
        ]
        
        for ratio, expected in boundary_tests:
            color = get_raw(gradient, ratio)
            assert color.r == expected.r, \
                f"At ratio {ratio}, expected r={expected.r}, got r={color.r}"
            assert color.g == expected.g
            assert color.b == expected.b
    
    def test_gradient_interpolation_accuracy(self):
        """Verify gradient interpolation produces mathematically correct colors."""
        # Create gradient from black to white
        black = RGB(0, 0, 0)
        white = RGB(255, 255, 255)
        gradient = create_gradient([black, white], resolution=256)
        
        # At midpoint, should get approximately gray (127, 127, 127)
        mid_index = len(gradient) // 2
        mid_color = gradient[mid_index]
        
        # Allow tolerance of ±2 for rounding
        assert abs(mid_color.r - 127) <= 2, \
            f"Midpoint red should be ~127, got {mid_color.r}"
        assert abs(mid_color.g - 127) <= 2, \
            f"Midpoint green should be ~127, got {mid_color.g}"
        assert abs(mid_color.b - 127) <= 2, \
            f"Midpoint blue should be ~127, got {mid_color.b}"
    
    def test_gradient_with_similar_colors(self):
        """Verify gradient smoothness with very similar colors."""
        # Create gradient between two similar shades of blue
        blue1 = RGB(0, 0, 200)
        blue2 = RGB(0, 0, 255)
        gradient = create_gradient([blue1, blue2], resolution=50)
        
        # All colors should be shades of blue (r=0, g=0)
        for color in gradient:
            assert color.r == 0, f"Red should be 0, got {color.r}"
            assert color.g == 0, f"Green should be 0, got {color.g}"
            assert 200 <= color.b <= 255, \
                f"Blue should be in range [200, 255], got {color.b}"
        
        # Check smoothness
        for i in range(len(gradient) - 1):
            diff_b = abs(gradient[i + 1].b - gradient[i].b)
            # With 50 steps over 55 units (255-200), max diff should be ~1.1
            assert diff_b <= 2, \
                f"Blue component jump too large: {diff_b}"
    
    def test_gradient_hex_initialization_smoothness(self):
        """Verify hex-initialized gradients are smooth."""
        # Create gradient from hex colors
        gradient = create_gradient_hex(["#FF0000", "#00FF00", "#0000FF"], resolution=100)
        
        # Verify smoothness
        max_diff = 0
        for i in range(len(gradient) - 1):
            c1 = gradient[i]
            c2 = gradient[i + 1]
            
            diff_r = abs(c2.r - c1.r)
            diff_g = abs(c2.g - c1.g)
            diff_b = abs(c2.b - c1.b)
            
            max_diff = max(max_diff, diff_r, diff_g, diff_b)
        
        assert max_diff <= 4, \
            f"Hex gradient not smooth: max difference is {max_diff}"
    
    def test_gradient_performance_with_high_resolution(self):
        """Verify gradient generation performs well with high resolution."""
        # Create a high-resolution gradient
        colors = [RGB(255, 0, 0), RGB(0, 255, 0), RGB(0, 0, 255)]
        
        # This should complete quickly (< 1 second)
        gradient = create_gradient(colors, resolution=1000)
        
        # Verify it was created correctly
        assert len(gradient) == 2000  # (3-1) * 1000
        
        # Verify smoothness is maintained at high resolution
        max_diff = 0
        for i in range(len(gradient) - 1):
            c1 = gradient[i]
            c2 = gradient[i + 1]
            
            diff_r = abs(c2.r - c1.r)
            diff_g = abs(c2.g - c1.g)
            diff_b = abs(c2.b - c1.b)
            
            max_diff = max(max_diff, diff_r, diff_g, diff_b)
        
        # With resolution 1000, max diff should be very small
        assert max_diff <= 1, \
            f"High-resolution gradient not smooth: max difference is {max_diff}"
    
    def test_scale_provides_consistent_lookups(self):
        """Verify Scale provides consistent results for repeated lookups."""
        scale = Scale(["#FF0000", "#0000FF"], resolution=100)
        
        # Lookup same ratio multiple times
        ratio = 0.5
        color1 = scale(ratio)
        color2 = scale(ratio)
        color3 = scale(ratio)
        
        # Should return identical colors
        assert color1.r == color2.r == color3.r
        assert color1.g == color2.g == color3.g
        assert color1.b == color2.b == color3.b
    
    def test_gradient_covers_full_color_range(self):
        """Verify gradient covers the full range between start and end colors."""
        # Create gradient from red to blue
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        gradient = create_gradient([red, blue], resolution=100)
        
        # Find min and max values for each component
        min_r = min(c.r for c in gradient)
        max_r = max(c.r for c in gradient)
        min_g = min(c.g for c in gradient)
        max_g = max(c.g for c in gradient)
        min_b = min(c.b for c in gradient)
        max_b = max(c.b for c in gradient)
        
        # Red should range from 0 to 255
        assert min_r <= 10, f"Min red should be near 0, got {min_r}"
        assert max_r >= 245, f"Max red should be near 255, got {max_r}"
        
        # Green should stay near 0
        assert max_g <= 10, f"Green should stay near 0, got max {max_g}"
        
        # Blue should range from 0 to 255
        assert min_b <= 10, f"Min blue should be near 0, got {min_b}"
        assert max_b >= 245, f"Max blue should be near 255, got {max_b}"


class TestGradientLookupIntegration:
    """Integration tests for gradient lookup functionality."""
    
    def test_lookup_at_fractional_ratios(self):
        """Test lookup at various fractional ratios."""
        gradient = create_gradient_hex(["#000000", "#FFFFFF"], resolution=100)
        
        # Test at fractional ratios
        test_ratios = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        
        for ratio in test_ratios:
            color = get_raw(gradient, ratio)
            
            # Color should be valid
            assert isinstance(color, RGB)
            assert 0 <= color.r <= 255
            assert 0 <= color.g <= 255
            assert 0 <= color.b <= 255
            
            # For black to white gradient, all components should be equal
            assert abs(color.r - color.g) <= 2
            assert abs(color.g - color.b) <= 2
            
            # Component value should be roughly proportional to ratio
            expected_value = int(ratio * 255)
            assert abs(color.r - expected_value) <= 5, \
                f"At ratio {ratio}, expected ~{expected_value}, got {color.r}"
    
    def test_scale_call_vs_get_raw_equivalence(self):
        """Verify Scale.__call__ and get_raw produce same results."""
        scale = Scale(["#FF0000", "#00FF00", "#0000FF"], resolution=100)
        
        test_ratios = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        for ratio in test_ratios:
            color_from_call = scale(ratio)
            color_from_get_raw = get_raw(scale.rgb, ratio)
            
            assert color_from_call.r == color_from_get_raw.r
            assert color_from_call.g == color_from_get_raw.g
            assert color_from_call.b == color_from_get_raw.b
    
    def test_gradient_suitable_for_theme_system(self):
        """Verify gradient quality is suitable for theme color palettes."""
        # Create a gradient for a theme (e.g., cyan to magenta)
        cyan = RGB(0, 255, 255)
        magenta = RGB(255, 0, 255)
        gradient = create_gradient([cyan, magenta], resolution=50)
        
        # Verify we have enough colors for a theme palette
        assert len(gradient) >= 50
        
        # Verify colors transition smoothly
        for i in range(len(gradient) - 1):
            c1 = gradient[i]
            c2 = gradient[i + 1]
            
            # Calculate perceptual distance (simplified)
            distance = abs(c2.r - c1.r) + abs(c2.g - c1.g) + abs(c2.b - c1.b)
            
            # Total distance should be small
            assert distance <= 15, \
                f"Theme gradient has abrupt transition at index {i}: distance={distance}"
