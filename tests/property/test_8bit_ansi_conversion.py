"""
Property-based tests for 8-bit ANSI conversion.

Tests:
- Property 7: 8-bit ANSI Code Range Validity
- Property 8: Color Cube Formula Correctness

Validates Requirements 2.2, 2.3, 2.4, 2.5
"""

import re
import pytest
from hypothesis import given, strategies as st, assume
from src.color_util import RGB


# Strategy for generating valid RGB colors
rgb_colors = st.builds(
    RGB,
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)

# Strategy for generating low-saturation (grayscale) colors
grayscale_colors = st.builds(
    RGB,
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
).filter(lambda rgb: rgb.hsl().s < 0.1)

# Strategy for generating high-saturation (color cube) colors
saturated_colors = st.builds(
    RGB,
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
).filter(lambda rgb: rgb.hsl().s >= 0.1)


class TestEightBitANSICodeRangeValidity:
    """Property 7: 8-bit ANSI Code Range Validity
    
    For any RGB color, to_ansi_8bit() should produce a code in the valid range:
    grayscale colors (low saturation) should map to codes 232-255, and saturated
    colors should map to codes 16-231.
    
    Validates: Requirements 2.2, 2.3, 2.4
    """
    
    @given(rgb_colors)
    def test_8bit_code_in_valid_range(self, rgb: RGB):
        """All 8-bit ANSI codes should be in range 16-255."""
        ansi_code = rgb.to_ansi_8bit(foreground=True)
        
        # Extract the color code from format \033[38;5;Nm or \033[48;5;Nm
        pattern = r"\033\[(?:38|48);5;(\d+)m"
        match = re.match(pattern, ansi_code)
        
        assert match is not None, \
            f"8-bit ANSI code doesn't match expected pattern: '{repr(ansi_code)}'"
        
        code = int(match.group(1))
        
        # Valid 8-bit codes are 16-255 (0-15 are standard ANSI colors, not used here)
        assert 16 <= code <= 255, \
            f"8-bit code {code} out of valid range [16, 255] for RGB{rgb}"
    
    @given(grayscale_colors)
    def test_grayscale_codes_in_grayscale_range(self, rgb: RGB):
        """Low-saturation colors should map to grayscale codes 232-255."""
        hsl = rgb.hsl()
        assume(hsl.s < 0.1)  # Ensure low saturation
        
        ansi_code = rgb.to_ansi_8bit(foreground=True)
        
        # Extract the color code
        pattern = r"\033\[(?:38|48);5;(\d+)m"
        match = re.match(pattern, ansi_code)
        
        assert match is not None, \
            f"8-bit ANSI code doesn't match expected pattern: '{repr(ansi_code)}'"
        
        code = int(match.group(1))
        
        # Grayscale codes should be in range 232-255
        assert 232 <= code <= 255, \
            f"Grayscale code {code} out of range [232, 255] for RGB{rgb} with saturation {hsl.s:.3f}"
    
    @given(saturated_colors)
    def test_saturated_codes_in_color_cube_range(self, rgb: RGB):
        """High-saturation colors should map to color cube codes 16-231."""
        hsl = rgb.hsl()
        assume(hsl.s >= 0.1)  # Ensure high saturation
        
        ansi_code = rgb.to_ansi_8bit(foreground=True)
        
        # Extract the color code
        pattern = r"\033\[(?:38|48);5;(\d+)m"
        match = re.match(pattern, ansi_code)
        
        assert match is not None, \
            f"8-bit ANSI code doesn't match expected pattern: '{repr(ansi_code)}'"
        
        code = int(match.group(1))
        
        # Color cube codes should be in range 16-231
        assert 16 <= code <= 231, \
            f"Color cube code {code} out of range [16, 231] for RGB{rgb} with saturation {hsl.s:.3f}"
    
    @given(rgb_colors)
    def test_foreground_uses_38_prefix(self, rgb: RGB):
        """Foreground 8-bit codes should use 38;5 prefix."""
        ansi_code = rgb.to_ansi_8bit(foreground=True)
        
        assert ansi_code.startswith("\033[38;5;"), \
            f"Foreground 8-bit code should start with '\\033[38;5;', got '{ansi_code}'"
    
    @given(rgb_colors)
    def test_background_uses_48_prefix(self, rgb: RGB):
        """Background 8-bit codes should use 48;5 prefix."""
        ansi_code = rgb.to_ansi_8bit(foreground=False)
        
        assert ansi_code.startswith("\033[48;5;"), \
            f"Background 8-bit code should start with '\\033[48;5;', got '{ansi_code}'"
    
    @given(rgb_colors)
    def test_8bit_code_ends_with_m(self, rgb: RGB):
        """All 8-bit ANSI codes should end with 'm'."""
        fg_code = rgb.to_ansi_8bit(foreground=True)
        bg_code = rgb.to_ansi_8bit(foreground=False)
        
        assert fg_code.endswith("m"), \
            f"Foreground code should end with 'm', got '{fg_code}'"
        assert bg_code.endswith("m"), \
            f"Background code should end with 'm', got '{bg_code}'"
    
    @given(rgb_colors)
    def test_8bit_code_format_correctness(self, rgb: RGB):
        """8-bit codes should match format \\033[38;5;Nm or \\033[48;5;Nm."""
        fg_code = rgb.to_ansi_8bit(foreground=True)
        bg_code = rgb.to_ansi_8bit(foreground=False)
        
        fg_pattern = r"\033\[38;5;\d+m"
        bg_pattern = r"\033\[48;5;\d+m"
        
        assert re.fullmatch(fg_pattern, fg_code), \
            f"Foreground code doesn't match pattern: '{repr(fg_code)}'"
        assert re.fullmatch(bg_pattern, bg_code), \
            f"Background code doesn't match pattern: '{repr(bg_code)}'"


class TestColorCubeFormulaCorrectness:
    """Property 8: Color Cube Formula Correctness
    
    For any saturated RGB color converted to 8-bit, the color code should equal
    `16 + 36*r + 6*g + b` where r, g, b are the RGB components scaled to [0, 5].
    
    Validates: Requirements 2.5
    """
    
    @given(saturated_colors)
    def test_color_cube_formula(self, rgb: RGB):
        """Saturated colors should follow color cube formula: 16 + 36*r + 6*g + b."""
        hsl = rgb.hsl()
        assume(hsl.s >= 0.1)  # Ensure high saturation
        
        ansi_code = rgb.to_ansi_8bit(foreground=True)
        
        # Extract the color code
        pattern = r"\033\[(?:38|48);5;(\d+)m"
        match = re.match(pattern, ansi_code)
        
        assert match is not None, \
            f"8-bit ANSI code doesn't match expected pattern: '{repr(ansi_code)}'"
        
        actual_code = int(match.group(1))
        
        # Calculate expected code using color cube formula
        # Scale RGB [0, 255] to [0, 5]
        r_cube = round(rgb.r / 255.0 * 5)
        g_cube = round(rgb.g / 255.0 * 5)
        b_cube = round(rgb.b / 255.0 * 5)
        
        expected_code = 16 + 36 * r_cube + 6 * g_cube + b_cube
        
        assert actual_code == expected_code, \
            f"Color cube formula mismatch for RGB{rgb}: " \
            f"got {actual_code}, expected {expected_code} " \
            f"(r_cube={r_cube}, g_cube={g_cube}, b_cube={b_cube})"
    
    @given(saturated_colors)
    def test_cube_components_in_valid_range(self, rgb: RGB):
        """Cube components (r, g, b) should be in range [0, 5]."""
        hsl = rgb.hsl()
        assume(hsl.s >= 0.1)  # Ensure high saturation
        
        # Calculate cube components
        r_cube = round(rgb.r / 255.0 * 5)
        g_cube = round(rgb.g / 255.0 * 5)
        b_cube = round(rgb.b / 255.0 * 5)
        
        assert 0 <= r_cube <= 5, \
            f"Red cube component {r_cube} out of range [0, 5] for RGB{rgb}"
        assert 0 <= g_cube <= 5, \
            f"Green cube component {g_cube} out of range [0, 5] for RGB{rgb}"
        assert 0 <= b_cube <= 5, \
            f"Blue cube component {b_cube} out of range [0, 5] for RGB{rgb}"
    
    @given(saturated_colors)
    def test_color_cube_code_bounds(self, rgb: RGB):
        """Color cube codes should be bounded by formula constraints."""
        hsl = rgb.hsl()
        assume(hsl.s >= 0.1)  # Ensure high saturation
        
        ansi_code = rgb.to_ansi_8bit(foreground=True)
        
        # Extract the color code
        pattern = r"\033\[(?:38|48);5;(\d+)m"
        match = re.match(pattern, ansi_code)
        
        assert match is not None
        code = int(match.group(1))
        
        # Minimum: 16 + 36*0 + 6*0 + 0 = 16
        # Maximum: 16 + 36*5 + 6*5 + 5 = 16 + 180 + 30 + 5 = 231
        assert 16 <= code <= 231, \
            f"Color cube code {code} violates formula bounds [16, 231] for RGB{rgb}"
    
    @given(
        st.integers(min_value=0, max_value=5),
        st.integers(min_value=0, max_value=5),
        st.integers(min_value=0, max_value=5)
    )
    def test_formula_produces_valid_codes(self, r_cube: int, g_cube: int, b_cube: int):
        """Color cube formula should always produce codes in range [16, 231]."""
        code = 16 + 36 * r_cube + 6 * g_cube + b_cube
        
        assert 16 <= code <= 231, \
            f"Formula produced invalid code {code} for cube({r_cube}, {g_cube}, {b_cube})"
    
    @given(
        st.integers(min_value=0, max_value=5),
        st.integers(min_value=0, max_value=5),
        st.integers(min_value=0, max_value=5)
    )
    def test_formula_uniqueness(self, r_cube: int, g_cube: int, b_cube: int):
        """Each unique (r, g, b) cube coordinate should produce a unique code."""
        code = 16 + 36 * r_cube + 6 * g_cube + b_cube
        
        # Verify we can reverse the formula
        adjusted_code = code - 16
        
        # Extract components
        extracted_r = adjusted_code // 36
        remainder = adjusted_code % 36
        extracted_g = remainder // 6
        extracted_b = remainder % 6
        
        assert extracted_r == r_cube, \
            f"Formula not reversible: r_cube={r_cube}, extracted={extracted_r}"
        assert extracted_g == g_cube, \
            f"Formula not reversible: g_cube={g_cube}, extracted={extracted_g}"
        assert extracted_b == b_cube, \
            f"Formula not reversible: b_cube={b_cube}, extracted={extracted_b}"


class TestGrayscaleMapping:
    """Test grayscale mapping for low-saturation colors (codes 232-255)."""
    
    @given(grayscale_colors)
    def test_grayscale_lightness_mapping(self, rgb: RGB):
        """Grayscale codes should correlate with lightness."""
        hsl = rgb.hsl()
        assume(hsl.s < 0.1)  # Ensure low saturation
        
        ansi_code = rgb.to_ansi_8bit(foreground=True)
        
        # Extract the color code
        pattern = r"\033\[(?:38|48);5;(\d+)m"
        match = re.match(pattern, ansi_code)
        
        assert match is not None
        code = int(match.group(1))
        
        # Calculate expected grayscale code
        # Map lightness [0.0, 1.0] to grayscale codes [232, 255]
        expected_code = 232 + round(hsl.l * 23)
        expected_code = max(232, min(255, expected_code))
        
        assert code == expected_code, \
            f"Grayscale mapping mismatch for RGB{rgb} with lightness {hsl.l:.3f}: " \
            f"got {code}, expected {expected_code}"
    
    @given(grayscale_colors)
    def test_grayscale_monotonicity(self, rgb: RGB):
        """Lighter grayscale colors should have higher codes."""
        hsl = rgb.hsl()
        assume(hsl.s < 0.1)  # Ensure low saturation
        
        ansi_code = rgb.to_ansi_8bit(foreground=True)
        
        # Extract the color code
        pattern = r"\033\[(?:38|48);5;(\d+)m"
        match = re.match(pattern, ansi_code)
        
        assert match is not None
        code = int(match.group(1))
        
        # Code should increase with lightness
        # Minimum lightness (0.0) → code 232
        # Maximum lightness (1.0) → code 255
        min_expected = 232
        max_expected = 255
        
        # Code should be proportional to lightness
        normalized_code = (code - min_expected) / (max_expected - min_expected)
        
        # Allow some tolerance due to rounding
        assert abs(normalized_code - hsl.l) <= 0.05, \
            f"Grayscale code {code} not proportional to lightness {hsl.l:.3f} for RGB{rgb}"


class TestEdgeCases:
    """Test edge cases for 8-bit ANSI conversion."""
    
    def test_pure_black_8bit(self):
        """Pure black (0,0,0) should map to grayscale code 232."""
        black = RGB(0, 0, 0)
        
        fg = black.to_ansi_8bit(foreground=True)
        bg = black.to_ansi_8bit(foreground=False)
        
        # Black has lightness 0.0, should map to code 232
        assert fg == "\033[38;5;232m"
        assert bg == "\033[48;5;232m"
    
    def test_pure_white_8bit(self):
        """Pure white (255,255,255) should map to grayscale code 255."""
        white = RGB(255, 255, 255)
        
        fg = white.to_ansi_8bit(foreground=True)
        bg = white.to_ansi_8bit(foreground=False)
        
        # White has lightness 1.0, should map to code 255
        assert fg == "\033[38;5;255m"
        assert bg == "\033[48;5;255m"
    
    def test_pure_red_8bit(self):
        """Pure red (255,0,0) should map to color cube code 196."""
        red = RGB(255, 0, 0)
        
        fg = red.to_ansi_8bit(foreground=True)
        
        # Red: r=5, g=0, b=0 → 16 + 36*5 + 6*0 + 0 = 196
        assert fg == "\033[38;5;196m"
    
    def test_pure_green_8bit(self):
        """Pure green (0,255,0) should map to color cube code 46."""
        green = RGB(0, 255, 0)
        
        fg = green.to_ansi_8bit(foreground=True)
        
        # Green: r=0, g=5, b=0 → 16 + 36*0 + 6*5 + 0 = 46
        assert fg == "\033[38;5;46m"
    
    def test_pure_blue_8bit(self):
        """Pure blue (0,0,255) should map to color cube code 21."""
        blue = RGB(0, 0, 255)
        
        fg = blue.to_ansi_8bit(foreground=True)
        
        # Blue: r=0, g=0, b=5 → 16 + 36*0 + 6*0 + 5 = 21
        assert fg == "\033[38;5;21m"
    
    def test_mid_gray_8bit(self):
        """Mid gray (128,128,128) should map to grayscale code ~244."""
        gray = RGB(128, 128, 128)
        
        fg = gray.to_ansi_8bit(foreground=True)
        
        # Gray has low saturation, should use grayscale mapping
        # Lightness ~0.5 → code ~244
        pattern = r"\033\[38;5;(\d+)m"
        match = re.match(pattern, fg)
        
        assert match is not None
        code = int(match.group(1))
        
        # Should be in grayscale range
        assert 232 <= code <= 255
        
        # Should be roughly in the middle
        assert 240 <= code <= 248, \
            f"Mid gray should map to middle grayscale code, got {code}"
    
    def test_yellow_8bit(self):
        """Yellow (255,255,0) should map to color cube code 226."""
        yellow = RGB(255, 255, 0)
        
        fg = yellow.to_ansi_8bit(foreground=True)
        
        # Yellow: r=5, g=5, b=0 → 16 + 36*5 + 6*5 + 0 = 226
        assert fg == "\033[38;5;226m"
    
    def test_cyan_8bit(self):
        """Cyan (0,255,255) should map to color cube code 51."""
        cyan = RGB(0, 255, 255)
        
        fg = cyan.to_ansi_8bit(foreground=True)
        
        # Cyan: r=0, g=5, b=5 → 16 + 36*0 + 6*5 + 5 = 51
        assert fg == "\033[38;5;51m"
    
    def test_magenta_8bit(self):
        """Magenta (255,0,255) should map to color cube code 201."""
        magenta = RGB(255, 0, 255)
        
        fg = magenta.to_ansi_8bit(foreground=True)
        
        # Magenta: r=5, g=0, b=5 → 16 + 36*5 + 6*0 + 5 = 201
        assert fg == "\033[38;5;201m"
    
    def test_default_foreground_parameter(self):
        """Calling to_ansi_8bit() without parameters should default to foreground."""
        color = RGB(100, 150, 200)
        
        default = color.to_ansi_8bit()
        explicit_fg = color.to_ansi_8bit(foreground=True)
        
        assert default == explicit_fg, \
            "Default should be foreground mode"
        assert default.startswith("\033[38;5;"), \
            "Default should use foreground prefix (38)"


class TestConsistency:
    """Test consistency properties of 8-bit conversion."""
    
    @given(rgb_colors)
    def test_same_rgb_produces_same_code(self, rgb: RGB):
        """Same RGB color should always produce the same 8-bit code."""
        code1 = rgb.to_ansi_8bit(foreground=True)
        code2 = rgb.to_ansi_8bit(foreground=True)
        
        assert code1 == code2, \
            f"Same RGB{rgb} produced different codes: '{code1}' vs '{code2}'"
    
    @given(rgb_colors)
    def test_foreground_and_background_differ_only_in_prefix(self, rgb: RGB):
        """Foreground and background codes should differ only in prefix (38 vs 48)."""
        fg_code = rgb.to_ansi_8bit(foreground=True)
        bg_code = rgb.to_ansi_8bit(foreground=False)
        
        # Replace 38 with 48 in foreground code
        fg_as_bg = fg_code.replace("[38;", "[48;")
        
        assert fg_as_bg == bg_code, \
            f"Codes should differ only in prefix: fg='{fg_code}', bg='{bg_code}'"
    
    @given(rgb_colors)
    def test_8bit_code_is_string(self, rgb: RGB):
        """8-bit ANSI codes should be strings."""
        fg = rgb.to_ansi_8bit(foreground=True)
        bg = rgb.to_ansi_8bit(foreground=False)
        
        assert isinstance(fg, str), "Foreground code should be a string"
        assert isinstance(bg, str), "Background code should be a string"
    
    @given(rgb_colors)
    def test_8bit_code_is_not_empty(self, rgb: RGB):
        """8-bit ANSI codes should not be empty strings."""
        fg = rgb.to_ansi_8bit(foreground=True)
        bg = rgb.to_ansi_8bit(foreground=False)
        
        assert len(fg) > 0, "Foreground code should not be empty"
        assert len(bg) > 0, "Background code should not be empty"
