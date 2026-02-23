"""
Property-based tests for RGB ANSI format generation.

Tests:
- Property 6: RGB ANSI Format Correctness

Validates Requirements 2.1, 2.6
"""

import re
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


class TestRGBANSIFormatCorrectness:
    """Property 6: RGB ANSI Format Correctness
    
    For any RGB color, to_ansi_rgb(foreground=True) should produce a string 
    matching the format `\\033[38;2;R;G;Bm` with the exact R, G, B values, 
    and to_ansi_rgb(foreground=False) should use prefix `\\033[48;2;R;G;Bm`.
    
    Validates: Requirements 2.1, 2.6
    """
    
    @given(rgb_colors)
    def test_foreground_ansi_format(self, rgb: RGB):
        """Foreground RGB ANSI codes should match format \\033[38;2;R;G;Bm."""
        ansi_code = rgb.to_ansi_rgb(foreground=True)
        
        # Expected format: \033[38;2;R;G;Bm
        expected = f"\033[38;2;{rgb.r};{rgb.g};{rgb.b}m"
        
        assert ansi_code == expected, \
            f"Foreground ANSI format mismatch: got '{ansi_code}', expected '{expected}'"
    
    @given(rgb_colors)
    def test_background_ansi_format(self, rgb: RGB):
        """Background RGB ANSI codes should match format \\033[48;2;R;G;Bm."""
        ansi_code = rgb.to_ansi_rgb(foreground=False)
        
        # Expected format: \033[48;2;R;G;Bm
        expected = f"\033[48;2;{rgb.r};{rgb.g};{rgb.b}m"
        
        assert ansi_code == expected, \
            f"Background ANSI format mismatch: got '{ansi_code}', expected '{expected}'"
    
    @given(rgb_colors)
    def test_foreground_uses_38_prefix(self, rgb: RGB):
        """Foreground codes should use 38 prefix."""
        ansi_code = rgb.to_ansi_rgb(foreground=True)
        
        # Should start with \033[38;2;
        assert ansi_code.startswith("\033[38;2;"), \
            f"Foreground code should start with '\\033[38;2;', got '{ansi_code}'"
    
    @given(rgb_colors)
    def test_background_uses_48_prefix(self, rgb: RGB):
        """Background codes should use 48 prefix."""
        ansi_code = rgb.to_ansi_rgb(foreground=False)
        
        # Should start with \033[48;2;
        assert ansi_code.startswith("\033[48;2;"), \
            f"Background code should start with '\\033[48;2;', got '{ansi_code}'"
    
    @given(rgb_colors)
    def test_ansi_code_ends_with_m(self, rgb: RGB):
        """All ANSI codes should end with 'm'."""
        fg_code = rgb.to_ansi_rgb(foreground=True)
        bg_code = rgb.to_ansi_rgb(foreground=False)
        
        assert fg_code.endswith("m"), \
            f"Foreground code should end with 'm', got '{fg_code}'"
        assert bg_code.endswith("m"), \
            f"Background code should end with 'm', got '{bg_code}'"
    
    @given(rgb_colors)
    def test_ansi_code_contains_exact_rgb_values(self, rgb: RGB):
        """ANSI codes should contain exact RGB values as strings."""
        fg_code = rgb.to_ansi_rgb(foreground=True)
        bg_code = rgb.to_ansi_rgb(foreground=False)
        
        # Extract RGB values from ANSI code using regex
        # Note: \033 is the actual escape character, not \\033
        fg_pattern = r"\033\[38;2;(\d+);(\d+);(\d+)m"
        bg_pattern = r"\033\[48;2;(\d+);(\d+);(\d+)m"
        
        fg_match = re.match(fg_pattern, fg_code)
        bg_match = re.match(bg_pattern, bg_code)
        
        assert fg_match is not None, \
            f"Foreground code doesn't match expected pattern: '{repr(fg_code)}'"
        assert bg_match is not None, \
            f"Background code doesn't match expected pattern: '{repr(bg_code)}'"
        
        # Verify extracted values match original RGB
        fg_r, fg_g, fg_b = map(int, fg_match.groups())
        bg_r, bg_g, bg_b = map(int, bg_match.groups())
        
        assert fg_r == rgb.r, f"Foreground red mismatch: {fg_r} != {rgb.r}"
        assert fg_g == rgb.g, f"Foreground green mismatch: {fg_g} != {rgb.g}"
        assert fg_b == rgb.b, f"Foreground blue mismatch: {fg_b} != {rgb.b}"
        
        assert bg_r == rgb.r, f"Background red mismatch: {bg_r} != {rgb.r}"
        assert bg_g == rgb.g, f"Background green mismatch: {bg_g} != {rgb.g}"
        assert bg_b == rgb.b, f"Background blue mismatch: {bg_b} != {rgb.b}"
    
    @given(rgb_colors)
    def test_ansi_code_has_no_extra_characters(self, rgb: RGB):
        """ANSI codes should not contain extra whitespace or characters."""
        fg_code = rgb.to_ansi_rgb(foreground=True)
        bg_code = rgb.to_ansi_rgb(foreground=False)
        
        # Count semicolons - should be exactly 4 for RGB format (38;2;R;G;B)
        assert fg_code.count(";") == 4, \
            f"Foreground code should have 4 semicolons, got {fg_code.count(';')}"
        assert bg_code.count(";") == 4, \
            f"Background code should have 4 semicolons, got {bg_code.count(';')}"
        
        # Should not contain spaces
        assert " " not in fg_code, \
            f"Foreground code should not contain spaces: '{fg_code}'"
        assert " " not in bg_code, \
            f"Background code should not contain spaces: '{bg_code}'"
    
    @given(rgb_colors)
    def test_foreground_and_background_differ_only_in_prefix(self, rgb: RGB):
        """Foreground and background codes should differ only in the prefix (38 vs 48)."""
        fg_code = rgb.to_ansi_rgb(foreground=True)
        bg_code = rgb.to_ansi_rgb(foreground=False)
        
        # Replace 38 with 48 in foreground code
        fg_as_bg = fg_code.replace("[38;", "[48;")
        
        assert fg_as_bg == bg_code, \
            f"Codes should differ only in prefix: fg='{fg_code}', bg='{bg_code}'"


class TestEdgeCases:
    """Test edge cases for RGB ANSI format generation."""
    
    def test_black_ansi_format(self):
        """Black (0,0,0) should produce correct ANSI codes."""
        black = RGB(0, 0, 0)
        
        fg = black.to_ansi_rgb(foreground=True)
        bg = black.to_ansi_rgb(foreground=False)
        
        assert fg == "\033[38;2;0;0;0m"
        assert bg == "\033[48;2;0;0;0m"
    
    def test_white_ansi_format(self):
        """White (255,255,255) should produce correct ANSI codes."""
        white = RGB(255, 255, 255)
        
        fg = white.to_ansi_rgb(foreground=True)
        bg = white.to_ansi_rgb(foreground=False)
        
        assert fg == "\033[38;2;255;255;255m"
        assert bg == "\033[48;2;255;255;255m"
    
    def test_pure_red_ansi_format(self):
        """Pure red (255,0,0) should produce correct ANSI codes."""
        red = RGB(255, 0, 0)
        
        fg = red.to_ansi_rgb(foreground=True)
        bg = red.to_ansi_rgb(foreground=False)
        
        assert fg == "\033[38;2;255;0;0m"
        assert bg == "\033[48;2;255;0;0m"
    
    def test_pure_green_ansi_format(self):
        """Pure green (0,255,0) should produce correct ANSI codes."""
        green = RGB(0, 255, 0)
        
        fg = green.to_ansi_rgb(foreground=True)
        bg = green.to_ansi_rgb(foreground=False)
        
        assert fg == "\033[38;2;0;255;0m"
        assert bg == "\033[48;2;0;255;0m"
    
    def test_pure_blue_ansi_format(self):
        """Pure blue (0,0,255) should produce correct ANSI codes."""
        blue = RGB(0, 0, 255)
        
        fg = blue.to_ansi_rgb(foreground=True)
        bg = blue.to_ansi_rgb(foreground=False)
        
        assert fg == "\033[38;2;0;0;255m"
        assert bg == "\033[48;2;0;0;255m"
    
    def test_gray_ansi_format(self):
        """Gray (128,128,128) should produce correct ANSI codes."""
        gray = RGB(128, 128, 128)
        
        fg = gray.to_ansi_rgb(foreground=True)
        bg = gray.to_ansi_rgb(foreground=False)
        
        assert fg == "\033[38;2;128;128;128m"
        assert bg == "\033[48;2;128;128;128m"
    
    def test_single_digit_values(self):
        """Single-digit RGB values should not be zero-padded."""
        color = RGB(1, 2, 3)
        
        fg = color.to_ansi_rgb(foreground=True)
        bg = color.to_ansi_rgb(foreground=False)
        
        # Should be "1;2;3" not "001;002;003"
        assert fg == "\033[38;2;1;2;3m"
        assert bg == "\033[48;2;1;2;3m"
    
    def test_mixed_digit_lengths(self):
        """RGB values with different digit lengths should format correctly."""
        color = RGB(5, 50, 255)
        
        fg = color.to_ansi_rgb(foreground=True)
        bg = color.to_ansi_rgb(foreground=False)
        
        assert fg == "\033[38;2;5;50;255m"
        assert bg == "\033[48;2;5;50;255m"
    
    def test_default_foreground_parameter(self):
        """Calling to_ansi_rgb() without parameters should default to foreground."""
        color = RGB(100, 150, 200)
        
        default = color.to_ansi_rgb()
        explicit_fg = color.to_ansi_rgb(foreground=True)
        
        assert default == explicit_fg, \
            "Default should be foreground mode"
        assert default.startswith("\033[38;2;"), \
            "Default should use foreground prefix (38)"


class TestANSICodeUsability:
    """Test that generated ANSI codes are usable in terminal output."""
    
    @given(rgb_colors)
    def test_ansi_code_is_string(self, rgb: RGB):
        """ANSI codes should be strings."""
        fg = rgb.to_ansi_rgb(foreground=True)
        bg = rgb.to_ansi_rgb(foreground=False)
        
        assert isinstance(fg, str), "Foreground code should be a string"
        assert isinstance(bg, str), "Background code should be a string"
    
    @given(rgb_colors)
    def test_ansi_code_is_not_empty(self, rgb: RGB):
        """ANSI codes should not be empty strings."""
        fg = rgb.to_ansi_rgb(foreground=True)
        bg = rgb.to_ansi_rgb(foreground=False)
        
        assert len(fg) > 0, "Foreground code should not be empty"
        assert len(bg) > 0, "Background code should not be empty"
    
    @given(rgb_colors)
    def test_ansi_code_can_be_concatenated(self, rgb: RGB):
        """ANSI codes should be concatenable with text."""
        fg = rgb.to_ansi_rgb(foreground=True)
        text = "Hello, World!"
        reset = "\033[0m"
        
        # Should be able to create colored text
        colored_text = fg + text + reset
        
        assert text in colored_text, "Text should be present in colored string"
        assert colored_text.startswith(fg), "Should start with ANSI code"
        assert colored_text.endswith(reset), "Should end with reset code"
