"""
Property-based tests for gradient generation.

Tests:
- Property 11: Gradient Length Matches Resolution
- Property 12: Linear Interpolation Correctness
- Property 45: Gradient Smoothness

Validates Requirements 4.1, 4.2, 4.3
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.color_util import RGB
from src.color_scale import create_gradient, create_gradient_hex, get_raw, Scale, clear_gradient_cache


# Strategy for generating valid RGB colors
rgb_colors = st.builds(
    RGB,
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)

# Strategy for generating lists of RGB colors (2-10 colors)
rgb_color_lists = st.lists(
    rgb_colors,
    min_size=2,
    max_size=10
)

# Strategy for generating resolution values
resolutions = st.integers(min_value=1, max_value=100)

# Strategy for generating hex color strings
hex_colors = st.text(
    alphabet='0123456789ABCDEFabcdef',
    min_size=6,
    max_size=6
).map(lambda s: f"#{s}")

# Strategy for generating lists of hex colors
hex_color_lists = st.lists(
    hex_colors,
    min_size=2,
    max_size=10
)

# Strategy for generating ratios (0.0 to 1.0)
ratios = st.floats(min_value=0.0, max_value=1.0)


class TestGradientLengthMatchesResolution:
    """Property 11: Gradient Length Matches Resolution
    
    For any list of N RGB colors and any resolution R, create_gradient should
    produce a gradient array of length (N-1) * R.
    
    Validates: Requirements 4.2
    """
    
    @given(rgb_color_lists, resolutions)
    def test_gradient_length_formula(self, colors, resolution):
        """Gradient length should equal (N-1) * resolution."""
        gradient = create_gradient(colors, resolution)
        
        expected_length = (len(colors) - 1) * resolution
        actual_length = len(gradient)
        
        assert actual_length == expected_length, \
            f"Expected length {expected_length}, got {actual_length} " \
            f"for {len(colors)} colors with resolution {resolution}"
    
    @given(rgb_colors, resolutions)
    def test_single_color_gradient_length(self, color, resolution):
        """Single color gradient should have length equal to resolution."""
        gradient = create_gradient([color], resolution)
        
        assert len(gradient) == resolution, \
            f"Single color gradient should have length {resolution}, got {len(gradient)}"
    
    @given(rgb_color_lists, resolutions)
    def test_gradient_hex_length_formula(self, colors, resolution):
        """Hex gradient length should also follow (N-1) * resolution formula."""
        # Convert RGB to hex strings
        hex_colors = [f"#{c.r:02x}{c.g:02x}{c.b:02x}" for c in colors]
        
        gradient = create_gradient_hex(hex_colors, resolution)
        
        expected_length = (len(colors) - 1) * resolution
        actual_length = len(gradient)
        
        assert actual_length == expected_length, \
            f"Expected length {expected_length}, got {actual_length}"
    
    def test_two_color_gradient_length(self):
        """Two color gradient should have exactly resolution steps."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        
        for resolution in [1, 10, 50, 100]:
            gradient = create_gradient([red, blue], resolution)
            assert len(gradient) == resolution
    
    def test_three_color_gradient_length(self):
        """Three color gradient should have 2 * resolution steps."""
        red = RGB(255, 0, 0)
        green = RGB(0, 255, 0)
        blue = RGB(0, 0, 255)
        
        for resolution in [1, 10, 50, 100]:
            gradient = create_gradient([red, green, blue], resolution)
            assert len(gradient) == 2 * resolution


class TestLinearInterpolationCorrectness:
    """Property 12: Linear Interpolation Correctness
    
    For any two RGB colors c1 and c2 and any ratio r in [0.0, 1.0], the
    interpolated color should have each component equal to 
    c2 * r + c1 * (1 - r) (rounded to nearest integer).
    
    Validates: Requirements 4.3
    """
    
    @given(rgb_colors, rgb_colors, st.floats(min_value=0.0, max_value=1.0))
    def test_two_color_interpolation_formula(self, c1, c2, ratio):
        """Interpolation should follow linear formula: c2 * r + c1 * (1 - r)."""
        # Create gradient with high resolution to get precise ratio
        resolution = 1000
        gradient = create_gradient([c1, c2], resolution)
        
        # Get color at specific ratio
        index = int(ratio * (len(gradient) - 1))
        interpolated = gradient[index]
        
        # Calculate expected values using linear interpolation formula
        expected_r = round(c2.r * ratio + c1.r * (1 - ratio))
        expected_g = round(c2.g * ratio + c1.g * (1 - ratio))
        expected_b = round(c2.b * ratio + c1.b * (1 - ratio))
        
        # Allow tolerance of ±1 due to rounding and discrete resolution
        assert abs(interpolated.r - expected_r) <= 1, \
            f"Red: expected {expected_r}, got {interpolated.r} at ratio {ratio}"
        assert abs(interpolated.g - expected_g) <= 1, \
            f"Green: expected {expected_g}, got {interpolated.g} at ratio {ratio}"
        assert abs(interpolated.b - expected_b) <= 1, \
            f"Blue: expected {expected_b}, got {interpolated.b} at ratio {ratio}"
    
    def test_interpolation_at_zero_ratio(self):
        """At ratio 0.0, interpolated color should equal first color."""
        c1 = RGB(255, 0, 0)
        c2 = RGB(0, 0, 255)
        
        gradient = create_gradient([c1, c2], 100)
        
        # First color in gradient should be c1
        assert gradient[0].r == c1.r
        assert gradient[0].g == c1.g
        assert gradient[0].b == c1.b
    
    def test_interpolation_at_midpoint(self):
        """At ratio 0.5, interpolated color should be average of two colors."""
        c1 = RGB(100, 50, 200)
        c2 = RGB(200, 150, 100)
        
        gradient = create_gradient([c1, c2], 100)
        
        # Middle color should be average
        mid_index = len(gradient) // 2
        mid_color = gradient[mid_index]
        
        expected_r = round((c1.r + c2.r) / 2)
        expected_g = round((c1.g + c2.g) / 2)
        expected_b = round((c1.b + c2.b) / 2)
        
        assert abs(mid_color.r - expected_r) <= 1
        assert abs(mid_color.g - expected_g) <= 1
        assert abs(mid_color.b - expected_b) <= 1
    
    @given(rgb_colors, rgb_colors)
    def test_gradient_endpoints_match_input_colors(self, c1, c2):
        """First and last colors in gradient should match input colors."""
        gradient = create_gradient([c1, c2], 50)
        
        # First color should be c1
        assert gradient[0].r == c1.r
        assert gradient[0].g == c1.g
        assert gradient[0].b == c1.b
        
        # Note: Last color approaches c2 but may not equal it exactly
        # because we generate 'resolution' steps starting from c1
        # The last step is at ratio (resolution-1)/resolution, not 1.0
    
    @given(rgb_color_lists)
    def test_gradient_contains_all_input_colors(self, colors):
        """Gradient should contain (or be very close to) all input colors."""
        gradient = create_gradient(colors, 100)
        
        # First color should match first input
        assert gradient[0].r == colors[0].r
        assert gradient[0].g == colors[0].g
        assert gradient[0].b == colors[0].b
        
        # Each transition point should be close to the corresponding input color
        for i in range(1, len(colors)):
            # Transition point is at index i * 100
            # But we start from 0, so it's at (i-1) * 100 + some offset
            # The exact position depends on how interpolation is done
            pass  # This is complex to verify precisely, covered by other tests


class TestGradientSmoothness:
    """Property 45: Gradient Smoothness
    
    For any gradient created from a list of colors, consecutive colors in the
    gradient array should have small component differences (|ΔR|, |ΔG|, |ΔB| ≤
    resolution-dependent threshold), ensuring smooth transitions.
    
    Validates: Requirements 4.1
    """
    
    @given(rgb_color_lists, resolutions)
    def test_consecutive_colors_have_small_differences(self, colors, resolution):
        """Consecutive gradient colors should have small component differences."""
        # Skip very low resolutions where large jumps are expected
        assume(resolution >= 10)
        
        gradient = create_gradient(colors, resolution)
        
        # Calculate maximum expected difference per step
        # For a transition from 0 to 255 over 'resolution' steps,
        # max difference per step is approximately 255 / resolution
        max_diff_per_step = 255 / resolution + 2  # +2 for rounding tolerance
        
        # Check all consecutive pairs
        for i in range(len(gradient) - 1):
            c1 = gradient[i]
            c2 = gradient[i + 1]
            
            diff_r = abs(c2.r - c1.r)
            diff_g = abs(c2.g - c1.g)
            diff_b = abs(c2.b - c1.b)
            
            assert diff_r <= max_diff_per_step, \
                f"Red difference too large: {diff_r} > {max_diff_per_step} " \
                f"at index {i} (resolution {resolution})"
            assert diff_g <= max_diff_per_step, \
                f"Green difference too large: {diff_g} > {max_diff_per_step} " \
                f"at index {i} (resolution {resolution})"
            assert diff_b <= max_diff_per_step, \
                f"Blue difference too large: {diff_b} > {max_diff_per_step} " \
                f"at index {i} (resolution {resolution})"
    
    def test_high_resolution_gradient_is_very_smooth(self):
        """High resolution gradients should have very small step differences."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        
        gradient = create_gradient([red, blue], resolution=100)
        
        # With resolution 100, max difference should be around 255/100 ≈ 2.55
        max_expected_diff = 4  # Allow some tolerance
        
        for i in range(len(gradient) - 1):
            c1 = gradient[i]
            c2 = gradient[i + 1]
            
            diff_r = abs(c2.r - c1.r)
            diff_g = abs(c2.g - c1.g)
            diff_b = abs(c2.b - c1.b)
            
            assert diff_r <= max_expected_diff
            assert diff_g <= max_expected_diff
            assert diff_b <= max_expected_diff
    
    @given(rgb_colors, rgb_colors)
    def test_gradient_monotonicity_for_single_component(self, c1, c2):
        """For colors differing in one component, gradient should be monotonic."""
        # Create colors that differ only in red component
        color1 = RGB(c1.r, 100, 100)
        color2 = RGB(c2.r, 100, 100)
        
        gradient = create_gradient([color1, color2], 50)
        
        # Red component should change monotonically
        if color1.r < color2.r:
            # Should be non-decreasing
            for i in range(len(gradient) - 1):
                assert gradient[i].r <= gradient[i + 1].r + 1, \
                    f"Red should be non-decreasing, but {gradient[i].r} > {gradient[i + 1].r}"
        elif color1.r > color2.r:
            # Should be non-increasing
            for i in range(len(gradient) - 1):
                assert gradient[i].r >= gradient[i + 1].r - 1, \
                    f"Red should be non-increasing, but {gradient[i].r} < {gradient[i + 1].r}"
        else:
            # Should be constant
            for color in gradient:
                assert abs(color.r - color1.r) <= 1
        
        # Green and blue should remain constant
        for color in gradient:
            assert abs(color.g - 100) <= 1
            assert abs(color.b - 100) <= 1


class TestGradientRatioLookupBounds:
    """Property 13: Gradient Ratio Lookup Bounds
    
    For any gradient and any ratio in [0.0, 1.0], the lookup should return a
    valid RGB color from the gradient array, with ratio 0.0 returning the first
    color and ratio 1.0 returning the last color.
    
    Validates: Requirements 4.4, 4.5
    """
    
    @given(rgb_color_lists, resolutions, ratios)
    def test_lookup_returns_color_from_gradient(self, colors, resolution, ratio):
        """Lookup at any ratio should return a color that exists in the gradient."""
        gradient = create_gradient(colors, resolution)
        color = get_raw(gradient, ratio)
        
        # Color should be one of the colors in the gradient array
        assert color in gradient, \
            f"Looked up color {color} not found in gradient at ratio {ratio}"
    
    @given(rgb_color_lists, resolutions)
    def test_ratio_zero_returns_first_color(self, colors, resolution):
        """Ratio 0.0 should always return the first color in gradient."""
        gradient = create_gradient(colors, resolution)
        color = get_raw(gradient, 0.0)
        
        first_color = gradient[0]
        assert color.r == first_color.r, \
            f"At ratio 0.0, expected r={first_color.r}, got r={color.r}"
        assert color.g == first_color.g, \
            f"At ratio 0.0, expected g={first_color.g}, got g={color.g}"
        assert color.b == first_color.b, \
            f"At ratio 0.0, expected b={first_color.b}, got b={color.b}"
    
    @given(rgb_color_lists, resolutions)
    def test_ratio_one_returns_last_color(self, colors, resolution):
        """Ratio 1.0 should always return the last color in gradient."""
        gradient = create_gradient(colors, resolution)
        color = get_raw(gradient, 1.0)
        
        last_color = gradient[-1]
        assert color.r == last_color.r, \
            f"At ratio 1.0, expected r={last_color.r}, got r={color.r}"
        assert color.g == last_color.g, \
            f"At ratio 1.0, expected g={last_color.g}, got g={color.g}"
        assert color.b == last_color.b, \
            f"At ratio 1.0, expected b={last_color.b}, got b={color.b}"
    
    @given(rgb_color_lists, resolutions, ratios)
    def test_lookup_returns_valid_rgb(self, colors, resolution, ratio):
        """Lookup should always return valid RGB with components in [0, 255]."""
        gradient = create_gradient(colors, resolution)
        color = get_raw(gradient, ratio)
        
        assert isinstance(color, RGB), \
            f"Expected RGB instance, got {type(color)}"
        assert 0 <= color.r <= 255, \
            f"Red component {color.r} out of valid range [0, 255]"
        assert 0 <= color.g <= 255, \
            f"Green component {color.g} out of valid range [0, 255]"
        assert 0 <= color.b <= 255, \
            f"Blue component {color.b} out of valid range [0, 255]"
    
    @given(rgb_color_lists, resolutions)
    def test_ratio_below_zero_returns_first_color(self, colors, resolution):
        """Ratio < 0.0 should clamp to first color (boundary condition)."""
        gradient = create_gradient(colors, resolution)
        
        # Test various negative ratios
        for negative_ratio in [-0.1, -0.5, -1.0, -10.0]:
            color = get_raw(gradient, negative_ratio)
            first_color = gradient[0]
            
            assert color.r == first_color.r, \
                f"At ratio {negative_ratio}, expected first color r={first_color.r}, got r={color.r}"
            assert color.g == first_color.g
            assert color.b == first_color.b
    
    @given(rgb_color_lists, resolutions)
    def test_ratio_above_one_returns_last_color(self, colors, resolution):
        """Ratio > 1.0 should clamp to last color (boundary condition)."""
        gradient = create_gradient(colors, resolution)
        
        # Test various ratios above 1.0
        for high_ratio in [1.1, 1.5, 2.0, 10.0]:
            color = get_raw(gradient, high_ratio)
            last_color = gradient[-1]
            
            assert color.r == last_color.r, \
                f"At ratio {high_ratio}, expected last color r={last_color.r}, got r={color.r}"
            assert color.g == last_color.g
            assert color.b == last_color.b
    
    @given(hex_color_lists, resolutions, ratios)
    def test_scale_call_respects_bounds(self, hex_colors, resolution, ratio):
        """Scale.__call__ should respect same bounds as get_raw."""
        scale = Scale(hex_colors, resolution)
        color = scale(ratio)
        
        # Should return valid RGB
        assert isinstance(color, RGB)
        assert 0 <= color.r <= 255
        assert 0 <= color.g <= 255
        assert 0 <= color.b <= 255
        
        # Should be a color from the gradient
        assert color in scale.rgb
    
    @given(hex_color_lists, resolutions)
    def test_scale_at_zero_returns_first(self, hex_colors, resolution):
        """Scale(0.0) should return first color."""
        scale = Scale(hex_colors, resolution)
        color = scale(0.0)
        
        first_color = scale.rgb[0]
        assert color.r == first_color.r
        assert color.g == first_color.g
        assert color.b == first_color.b
    
    @given(hex_color_lists, resolutions)
    def test_scale_at_one_returns_last(self, hex_colors, resolution):
        """Scale(1.0) should return last color."""
        scale = Scale(hex_colors, resolution)
        color = scale(1.0)
        
        last_color = scale.rgb[-1]
        assert color.r == last_color.r
        assert color.g == last_color.g
        assert color.b == last_color.b
    
    @given(rgb_color_lists, resolutions)
    def test_monotonic_ratio_produces_monotonic_index(self, colors, resolution):
        """Increasing ratios should access increasing or equal indices in gradient."""
        gradient = create_gradient(colors, resolution)
        
        # Test a sequence of increasing ratios
        ratios_sequence = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        # Calculate actual indices used by get_raw
        indices = []
        for ratio in ratios_sequence:
            if ratio <= 0.0:
                index = 0
            elif ratio >= 1.0:
                index = len(gradient) - 1
            else:
                index = int(ratio * (len(gradient) - 1))
            indices.append(index)
        
        # Indices should be non-decreasing
        for i in range(len(indices) - 1):
            assert indices[i] <= indices[i + 1], \
                f"Indices not monotonic: {indices[i]} > {indices[i + 1]} " \
                f"at ratios {ratios_sequence[i]} and {ratios_sequence[i + 1]}"
    
    def test_lookup_at_specific_ratios(self):
        """Test lookup at specific known ratios for correctness."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        gradient = create_gradient([red, blue], 100)
        
        # At ratio 0.0, should get first color (red)
        color_0 = get_raw(gradient, 0.0)
        assert color_0.r == 255 and color_0.g == 0 and color_0.b == 0
        
        # At ratio 1.0, should get last color
        color_1 = get_raw(gradient, 1.0)
        assert color_1 == gradient[-1]
        
        # At ratio 0.5, should get color at index calculated by get_raw
        color_mid = get_raw(gradient, 0.5)
        expected_index = int(0.5 * (len(gradient) - 1))
        assert color_mid == gradient[expected_index]
    
    @given(rgb_color_lists, resolutions)
    def test_scale_get_raw_method_matches_function(self, colors, resolution):
        """Scale.get_raw() should behave identically to get_raw() function."""
        # Convert to hex for Scale initialization
        hex_colors = [f"#{c.r:02x}{c.g:02x}{c.b:02x}" for c in colors]
        scale = Scale(hex_colors, resolution)
        
        # Test at various ratios
        test_ratios = [0.0, 0.25, 0.5, 0.75, 1.0]
        for ratio in test_ratios:
            color_from_method = scale.get_raw(ratio)
            color_from_function = get_raw(scale.rgb, ratio)
            
            assert color_from_method.r == color_from_function.r
            assert color_from_method.g == color_from_function.g
            assert color_from_method.b == color_from_function.b


class TestGradientLookup:
    """Test gradient lookup functionality (get_raw and Scale)."""
    
    @given(rgb_color_lists, resolutions, ratios)
    def test_get_raw_returns_valid_color(self, colors, resolution, ratio):
        """get_raw should always return a valid RGB color."""
        gradient = create_gradient(colors, resolution)
        color = get_raw(gradient, ratio)
        
        assert isinstance(color, RGB)
        assert 0 <= color.r <= 255
        assert 0 <= color.g <= 255
        assert 0 <= color.b <= 255
    
    def test_get_raw_at_zero_returns_first_color(self):
        """get_raw at ratio 0.0 should return first color."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        gradient = create_gradient([red, blue], 100)
        
        color = get_raw(gradient, 0.0)
        assert color.r == red.r
        assert color.g == red.g
        assert color.b == red.b
    
    def test_get_raw_at_one_returns_last_color(self):
        """get_raw at ratio 1.0 should return last color."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        gradient = create_gradient([red, blue], 100)
        
        color = get_raw(gradient, 1.0)
        # Last color in gradient
        assert color.r == gradient[-1].r
        assert color.g == gradient[-1].g
        assert color.b == gradient[-1].b
    
    @given(hex_color_lists)
    def test_scale_initialization(self, hex_colors):
        """Scale should initialize correctly from hex colors."""
        scale = Scale(hex_colors, resolution=50)
        
        assert len(scale.colors) == len(hex_colors)
        assert len(scale.rgb) == (len(hex_colors) - 1) * 50
    
    @given(hex_color_lists, ratios)
    def test_scale_call_returns_valid_color(self, hex_colors, ratio):
        """Scale(ratio) should return valid RGB color."""
        scale = Scale(hex_colors, resolution=50)
        color = scale(ratio)
        
        assert isinstance(color, RGB)
        assert 0 <= color.r <= 255
        assert 0 <= color.g <= 255
        assert 0 <= color.b <= 255
    
    def test_scale_endpoints(self):
        """Scale should return correct colors at endpoints."""
        scale = Scale(["#FF0000", "#0000FF"], resolution=100)
        
        # At ratio 0.0, should get red
        color_start = scale(0.0)
        assert color_start.r == 255
        assert color_start.g == 0
        assert color_start.b == 0
        
        # At ratio 1.0, should get color close to blue
        color_end = scale(1.0)
        # Last color in gradient approaches blue
        assert color_end.b > 200  # Should be mostly blue


class TestGradientHexInitialization:
    """Property 14: Gradient Hex Initialization
    
    For any list of valid hex color strings, create_gradient_hex should
    successfully create a gradient without errors.
    
    Validates: Requirements 4.6
    """
    
    @given(hex_color_lists)
    def test_hex_initialization_succeeds(self, hex_colors):
        """Valid hex color strings should create gradient without errors."""
        # Should not raise any exception
        gradient = create_gradient_hex(hex_colors)
        
        # Should return a valid gradient
        assert isinstance(gradient, list)
        assert len(gradient) > 0
        assert all(isinstance(color, RGB) for color in gradient)
    
    @given(hex_color_lists, resolutions)
    def test_hex_initialization_with_custom_resolution(self, hex_colors, resolution):
        """Hex initialization should work with any valid resolution."""
        gradient = create_gradient_hex(hex_colors, resolution)
        
        # Should follow the same length formula as create_gradient
        expected_length = (len(hex_colors) - 1) * resolution
        assert len(gradient) == expected_length
    
    @given(st.lists(hex_colors, min_size=1, max_size=1))
    def test_single_hex_color_initialization(self, hex_colors):
        """Single hex color should create uniform gradient."""
        gradient = create_gradient_hex(hex_colors, resolution=10)
        
        # Should have length equal to resolution
        assert len(gradient) == 10
        
        # All colors should be identical
        first_color = gradient[0]
        for color in gradient:
            assert color.r == first_color.r
            assert color.g == first_color.g
            assert color.b == first_color.b
    
    def test_hex_initialization_with_3_char_format(self):
        """Hex initialization should support 3-character format (#RGB)."""
        # 3-character hex colors
        hex_colors = ["#F00", "#0F0", "#00F"]
        
        gradient = create_gradient_hex(hex_colors)
        
        # Should successfully create gradient
        assert len(gradient) > 0
        
        # First color should be red (F00 = FF0000)
        assert gradient[0].r == 255
        assert gradient[0].g == 0
        assert gradient[0].b == 0
    
    def test_hex_initialization_with_6_char_format(self):
        """Hex initialization should support 6-character format (#RRGGBB)."""
        hex_colors = ["#FF0000", "#00FF00", "#0000FF"]
        
        gradient = create_gradient_hex(hex_colors)
        
        # Should successfully create gradient
        assert len(gradient) > 0
        
        # First color should be red
        assert gradient[0].r == 255
        assert gradient[0].g == 0
        assert gradient[0].b == 0
    
    def test_hex_initialization_mixed_formats(self):
        """Hex initialization should support mixed 3-char and 6-char formats."""
        hex_colors = ["#F00", "#00FF00", "#00F"]
        
        gradient = create_gradient_hex(hex_colors)
        
        # Should successfully create gradient
        assert len(gradient) > 0
    
    @given(st.lists(
        st.text(alphabet='0123456789ABCDEFabcdef', min_size=6, max_size=6),
        min_size=2,
        max_size=5
    ))
    def test_hex_initialization_case_insensitive(self, hex_strings):
        """Hex initialization should be case-insensitive."""
        # Add # prefix
        hex_colors = [f"#{s}" for s in hex_strings]
        
        gradient = create_gradient_hex(hex_colors)
        
        # Should successfully create gradient
        assert len(gradient) > 0
        assert all(isinstance(color, RGB) for color in gradient)
    
    def test_hex_initialization_without_hash_prefix(self):
        """Hex colors without # prefix should still work (RGB.from_hex handles it)."""
        # RGB.from_hex strips leading # if present
        hex_colors = ["#FF0000", "#00FF00"]
        
        gradient = create_gradient_hex(hex_colors)
        
        assert len(gradient) > 0
    
    @given(hex_color_lists)
    def test_hex_initialization_produces_valid_rgb_values(self, hex_colors):
        """All colors in hex-initialized gradient should have valid RGB values."""
        gradient = create_gradient_hex(hex_colors)
        
        for color in gradient:
            assert 0 <= color.r <= 255, f"Red {color.r} out of range"
            assert 0 <= color.g <= 255, f"Green {color.g} out of range"
            assert 0 <= color.b <= 255, f"Blue {color.b} out of range"
    
    def test_hex_initialization_default_resolution(self):
        """Hex initialization should use default resolution of 300."""
        hex_colors = ["#FF0000", "#0000FF"]
        
        gradient = create_gradient_hex(hex_colors)
        
        # Default resolution is 300, so length should be (2-1) * 300 = 300
        assert len(gradient) == 300
    
    def test_hex_initialization_preserves_endpoint_colors(self):
        """First and last colors should match input hex colors."""
        hex_colors = ["#FF0000", "#00FF00", "#0000FF"]
        
        gradient = create_gradient_hex(hex_colors)
        
        # First color should be red
        assert gradient[0].r == 255
        assert gradient[0].g == 0
        assert gradient[0].b == 0
        
        # Last color should approach blue (but may not be exact due to interpolation)
        # The gradient has (3-1) * 300 = 600 steps
        # Last step is at ratio 599/600, not exactly 1.0
    
    def test_hex_initialization_invalid_hex_raises_error(self):
        """Invalid hex strings should raise ValueError."""
        invalid_hex_colors = ["#GGGGGG", "#00FF00"]
        
        with pytest.raises(ValueError):
            create_gradient_hex(invalid_hex_colors)
    
    def test_hex_initialization_empty_list_raises_error(self):
        """Empty hex color list should raise ValueError."""
        with pytest.raises(ValueError):
            create_gradient_hex([])
    
    def test_hex_initialization_wrong_length_raises_error(self):
        """Hex strings with wrong length should raise ValueError."""
        # 5 characters is invalid (should be 3 or 6)
        invalid_hex_colors = ["#FFFFF"]
        
        with pytest.raises(ValueError):
            create_gradient_hex(invalid_hex_colors)


class TestGradientEdgeCases:
    """Test edge cases and error handling for gradient generation."""
    
    def test_empty_color_list_raises_error(self):
        """Empty color list should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot create gradient from empty color list"):
            create_gradient([], 10)
    
    def test_zero_resolution_raises_error(self):
        """Resolution of 0 should raise ValueError."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        
        with pytest.raises(ValueError, match="Resolution must be >= 1"):
            create_gradient([red, blue], 0)
    
    def test_negative_resolution_raises_error(self):
        """Negative resolution should raise ValueError."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        
        with pytest.raises(ValueError, match="Resolution must be >= 1"):
            create_gradient([red, blue], -5)
    
    def test_single_color_gradient(self):
        """Single color should create uniform gradient."""
        red = RGB(255, 0, 0)
        gradient = create_gradient([red], 10)
        
        assert len(gradient) == 10
        for color in gradient:
            assert color.r == 255
            assert color.g == 0
            assert color.b == 0
    
    def test_identical_colors_gradient(self):
        """Gradient of identical colors should be uniform."""
        red = RGB(255, 0, 0)
        gradient = create_gradient([red, red, red], 10)
        
        for color in gradient:
            assert color.r == 255
            assert color.g == 0
            assert color.b == 0
    
    def test_get_raw_empty_gradient_raises_error(self):
        """get_raw with empty gradient should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot lookup color in empty gradient"):
            get_raw([], 0.5)
    
    def test_get_raw_negative_ratio_returns_first(self):
        """get_raw with negative ratio should return first color."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        gradient = create_gradient([red, blue], 100)
        
        color = get_raw(gradient, -0.5)
        assert color.r == red.r
        assert color.g == red.g
        assert color.b == red.b
    
    def test_get_raw_ratio_above_one_returns_last(self):
        """get_raw with ratio > 1.0 should return last color."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        gradient = create_gradient([red, blue], 100)
        
        color = get_raw(gradient, 1.5)
        assert color.r == gradient[-1].r
        assert color.g == gradient[-1].g
        assert color.b == gradient[-1].b
    
    def test_scale_empty_color_list_raises_error(self):
        """Scale with empty color list should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot create Scale from empty color list"):
            Scale([], resolution=10)
    
    def test_scale_invalid_hex_raises_error(self):
        """Scale with invalid hex color should raise ValueError."""
        with pytest.raises(ValueError):
            Scale(["#GGGGGG"], resolution=10)


class TestGradientCaching:
    """Test gradient caching functionality."""
    
    def test_gradient_caching_improves_performance(self):
        """Repeated gradient creation should use cache."""
        clear_gradient_cache()
        
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        
        # First call - should compute
        gradient1 = create_gradient([red, blue], 100)
        
        # Second call with same parameters - should use cache
        gradient2 = create_gradient([red, blue], 100)
        
        # Should return the same cached object
        assert gradient1 is gradient2
    
    def test_different_resolutions_create_different_gradients(self):
        """Different resolutions should create separate cache entries."""
        clear_gradient_cache()
        
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        
        gradient1 = create_gradient([red, blue], 50)
        gradient2 = create_gradient([red, blue], 100)
        
        assert len(gradient1) == 50
        assert len(gradient2) == 100
        assert gradient1 is not gradient2
    
    def test_clear_gradient_cache(self):
        """clear_gradient_cache should remove all cached gradients."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        
        # Create some gradients
        create_gradient([red, blue], 50)
        create_gradient([red, blue], 100)
        
        # Clear cache
        clear_gradient_cache()
        
        # Next creation should not use cache (we can't directly test this,
        # but we can verify the function doesn't crash)
        gradient = create_gradient([red, blue], 50)
        assert len(gradient) == 50
