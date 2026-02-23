"""
Property-based tests for unified ANSI interface.

Tests:
- Property 9: Unified ANSI Interface Consistency

Validates Requirements 2.7
"""

import pytest
from hypothesis import given, strategies as st
from src.color_util import RGB, AnsiMode


# Strategy for generating valid RGB colors
rgb_colors = st.builds(
    RGB,
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)

# Strategy for generating valid AnsiMode values
ansi_modes = st.sampled_from(["rgb", "8bit", "ansi", "default"])


class TestUnifiedANSIInterfaceConsistency:
    """Property 9: Unified ANSI Interface Consistency
    
    For any RGB color and any valid AnsiMode ("rgb", "8bit", "ansi"), to_ansi(mode)
    should produce output equivalent to calling the mode-specific method
    (to_ansi_rgb, to_ansi_8bit, or to_ansi_16).
    
    Validates: Requirements 2.7
    """
    
    @given(rgb_colors, st.booleans())
    def test_rgb_mode_delegates_to_ansi_rgb(self, rgb: RGB, foreground: bool):
        """to_ansi(mode="rgb") should produce same output as to_ansi_rgb()."""
        unified = rgb.to_ansi(mode="rgb", foreground=foreground)
        specific = rgb.to_ansi_rgb(foreground=foreground)
        
        assert unified == specific, \
            f"RGB mode mismatch for RGB{rgb}: " \
            f"to_ansi('rgb')='{unified}' != to_ansi_rgb()='{specific}'"
    
    @given(rgb_colors, st.booleans())
    def test_8bit_mode_delegates_to_ansi_8bit(self, rgb: RGB, foreground: bool):
        """to_ansi(mode="8bit") should produce same output as to_ansi_8bit()."""
        unified = rgb.to_ansi(mode="8bit", foreground=foreground)
        specific = rgb.to_ansi_8bit(foreground=foreground)
        
        assert unified == specific, \
            f"8-bit mode mismatch for RGB{rgb}: " \
            f"to_ansi('8bit')='{unified}' != to_ansi_8bit()='{specific}'"
    
    @given(rgb_colors, st.booleans())
    def test_ansi_mode_uses_8bit_fallback(self, rgb: RGB, foreground: bool):
        """to_ansi(mode="ansi") should use 8-bit as fallback."""
        unified = rgb.to_ansi(mode="ansi", foreground=foreground)
        fallback = rgb.to_ansi_8bit(foreground=foreground)
        
        assert unified == fallback, \
            f"ANSI mode should use 8-bit fallback for RGB{rgb}: " \
            f"to_ansi('ansi')='{unified}' != to_ansi_8bit()='{fallback}'"
    
    @given(rgb_colors, st.booleans())
    def test_default_mode_uses_8bit_fallback(self, rgb: RGB, foreground: bool):
        """to_ansi(mode="default") should use 8-bit as safe default."""
        unified = rgb.to_ansi(mode="default", foreground=foreground)
        fallback = rgb.to_ansi_8bit(foreground=foreground)
        
        assert unified == fallback, \
            f"Default mode should use 8-bit fallback for RGB{rgb}: " \
            f"to_ansi('default')='{unified}' != to_ansi_8bit()='{fallback}'"
    
    @given(rgb_colors, ansi_modes, st.booleans())
    def test_all_modes_produce_valid_ansi_codes(self, rgb: RGB, mode: AnsiMode, foreground: bool):
        """All modes should produce valid ANSI escape sequences."""
        ansi_code = rgb.to_ansi(mode=mode, foreground=foreground)
        
        # Should be a non-empty string
        assert isinstance(ansi_code, str), \
            f"ANSI code should be string, got {type(ansi_code)}"
        assert len(ansi_code) > 0, \
            f"ANSI code should not be empty for mode '{mode}'"
        
        # Should start with ANSI escape sequence
        assert ansi_code.startswith("\033["), \
            f"ANSI code should start with '\\033[', got '{repr(ansi_code)}'"
        
        # Should end with 'm'
        assert ansi_code.endswith("m"), \
            f"ANSI code should end with 'm', got '{ansi_code}'"
    
    @given(rgb_colors, ansi_modes, st.booleans())
    def test_foreground_background_prefix_consistency(self, rgb: RGB, mode: AnsiMode, foreground: bool):
        """Foreground codes should use 38 prefix, background should use 48."""
        ansi_code = rgb.to_ansi(mode=mode, foreground=foreground)
        
        if foreground:
            # Foreground should contain "38;" somewhere after the escape sequence
            assert ";38;" in ansi_code or ansi_code.startswith("\033[38;"), \
                f"Foreground code should contain '38' prefix, got '{ansi_code}'"
        else:
            # Background should contain "48;" somewhere after the escape sequence
            assert ";48;" in ansi_code or ansi_code.startswith("\033[48;"), \
                f"Background code should contain '48' prefix, got '{ansi_code}'"
    
    @given(rgb_colors, ansi_modes)
    def test_same_color_same_mode_produces_same_output(self, rgb: RGB, mode: AnsiMode):
        """Same RGB and mode should always produce identical output."""
        code1 = rgb.to_ansi(mode=mode, foreground=True)
        code2 = rgb.to_ansi(mode=mode, foreground=True)
        
        assert code1 == code2, \
            f"Same RGB{rgb} and mode '{mode}' produced different codes: " \
            f"'{code1}' vs '{code2}'"
    
    @given(rgb_colors, ansi_modes)
    def test_mode_parameter_affects_output_format(self, rgb: RGB, mode: AnsiMode):
        """Different modes should produce different ANSI code formats."""
        ansi_code = rgb.to_ansi(mode=mode, foreground=True)
        
        if mode == "rgb":
            # RGB mode should use 38;2;R;G;B format
            assert ";2;" in ansi_code, \
                f"RGB mode should use ';2;' format, got '{ansi_code}'"
        elif mode in ("8bit", "ansi", "default"):
            # 8-bit modes should use 38;5;N format
            assert ";5;" in ansi_code, \
                f"8-bit mode should use ';5;' format, got '{ansi_code}'"
    
    @given(rgb_colors)
    def test_default_mode_parameter(self, rgb: RGB):
        """Calling to_ansi() without mode should use default mode."""
        default = rgb.to_ansi()
        explicit_default = rgb.to_ansi(mode="default")
        
        assert default == explicit_default, \
            f"Default mode parameter should match explicit 'default': " \
            f"to_ansi()='{default}' != to_ansi('default')='{explicit_default}'"
    
    @given(rgb_colors)
    def test_default_foreground_parameter(self, rgb: RGB):
        """Calling to_ansi() without foreground should default to foreground=True."""
        default = rgb.to_ansi(mode="rgb")
        explicit_fg = rgb.to_ansi(mode="rgb", foreground=True)
        
        assert default == explicit_fg, \
            f"Default foreground parameter should be True: " \
            f"to_ansi('rgb')='{default}' != to_ansi('rgb', True)='{explicit_fg}'"


class TestModeEquivalence:
    """Test equivalence relationships between different modes."""
    
    @given(rgb_colors, st.booleans())
    def test_ansi_and_default_modes_equivalent(self, rgb: RGB, foreground: bool):
        """ANSI and default modes should produce identical output."""
        ansi_mode = rgb.to_ansi(mode="ansi", foreground=foreground)
        default_mode = rgb.to_ansi(mode="default", foreground=foreground)
        
        assert ansi_mode == default_mode, \
            f"ANSI and default modes should be equivalent for RGB{rgb}: " \
            f"ansi='{ansi_mode}' != default='{default_mode}'"
    
    @given(rgb_colors, st.booleans())
    def test_rgb_mode_differs_from_8bit_mode(self, rgb: RGB, foreground: bool):
        """RGB and 8-bit modes should produce different format codes."""
        rgb_code = rgb.to_ansi(mode="rgb", foreground=foreground)
        bit8_code = rgb.to_ansi(mode="8bit", foreground=foreground)
        
        # RGB mode should use [38;2; or [48;2; format
        # 8-bit mode should use [38;5; or [48;5; format
        prefix = "38" if foreground else "48"
        
        assert f"[{prefix};2;" in rgb_code, \
            f"RGB mode should use '[{prefix};2;' format, got '{rgb_code}'"
        assert f"[{prefix};5;" in bit8_code, \
            f"8-bit mode should use '[{prefix};5;' format, got '{bit8_code}'"
        
        # They should use different format indicators
        assert (f"[{prefix};2;" in rgb_code) and (f"[{prefix};2;" not in bit8_code), \
            f"RGB and 8-bit modes should use different formats"
        assert (f"[{prefix};5;" in bit8_code) and (f"[{prefix};5;" not in rgb_code), \
            f"RGB and 8-bit modes should use different formats"


class TestEdgeCases:
    """Test edge cases for unified ANSI interface."""
    
    def test_black_all_modes(self):
        """Black (0,0,0) should work in all modes."""
        black = RGB(0, 0, 0)
        
        rgb_fg = black.to_ansi(mode="rgb", foreground=True)
        rgb_bg = black.to_ansi(mode="rgb", foreground=False)
        bit8_fg = black.to_ansi(mode="8bit", foreground=True)
        bit8_bg = black.to_ansi(mode="8bit", foreground=False)
        ansi_fg = black.to_ansi(mode="ansi", foreground=True)
        default_fg = black.to_ansi(mode="default", foreground=True)
        
        # RGB mode
        assert rgb_fg == "\033[38;2;0;0;0m"
        assert rgb_bg == "\033[48;2;0;0;0m"
        
        # 8-bit mode (black is grayscale code 232)
        assert bit8_fg == "\033[38;5;232m"
        assert bit8_bg == "\033[48;5;232m"
        
        # ANSI and default should match 8-bit
        assert ansi_fg == bit8_fg
        assert default_fg == bit8_fg
    
    def test_white_all_modes(self):
        """White (255,255,255) should work in all modes."""
        white = RGB(255, 255, 255)
        
        rgb_fg = white.to_ansi(mode="rgb", foreground=True)
        rgb_bg = white.to_ansi(mode="rgb", foreground=False)
        bit8_fg = white.to_ansi(mode="8bit", foreground=True)
        bit8_bg = white.to_ansi(mode="8bit", foreground=False)
        ansi_fg = white.to_ansi(mode="ansi", foreground=True)
        default_fg = white.to_ansi(mode="default", foreground=True)
        
        # RGB mode
        assert rgb_fg == "\033[38;2;255;255;255m"
        assert rgb_bg == "\033[48;2;255;255;255m"
        
        # 8-bit mode (white is grayscale code 255)
        assert bit8_fg == "\033[38;5;255m"
        assert bit8_bg == "\033[48;5;255m"
        
        # ANSI and default should match 8-bit
        assert ansi_fg == bit8_fg
        assert default_fg == bit8_fg
    
    def test_pure_red_all_modes(self):
        """Pure red (255,0,0) should work in all modes."""
        red = RGB(255, 0, 0)
        
        rgb_fg = red.to_ansi(mode="rgb", foreground=True)
        bit8_fg = red.to_ansi(mode="8bit", foreground=True)
        ansi_fg = red.to_ansi(mode="ansi", foreground=True)
        default_fg = red.to_ansi(mode="default", foreground=True)
        
        # RGB mode
        assert rgb_fg == "\033[38;2;255;0;0m"
        
        # 8-bit mode (red is color cube code 196)
        assert bit8_fg == "\033[38;5;196m"
        
        # ANSI and default should match 8-bit
        assert ansi_fg == bit8_fg
        assert default_fg == bit8_fg
    
    def test_pure_green_all_modes(self):
        """Pure green (0,255,0) should work in all modes."""
        green = RGB(0, 255, 0)
        
        rgb_fg = green.to_ansi(mode="rgb", foreground=True)
        bit8_fg = green.to_ansi(mode="8bit", foreground=True)
        ansi_fg = green.to_ansi(mode="ansi", foreground=True)
        default_fg = green.to_ansi(mode="default", foreground=True)
        
        # RGB mode
        assert rgb_fg == "\033[38;2;0;255;0m"
        
        # 8-bit mode (green is color cube code 46)
        assert bit8_fg == "\033[38;5;46m"
        
        # ANSI and default should match 8-bit
        assert ansi_fg == bit8_fg
        assert default_fg == bit8_fg
    
    def test_pure_blue_all_modes(self):
        """Pure blue (0,0,255) should work in all modes."""
        blue = RGB(0, 0, 255)
        
        rgb_fg = blue.to_ansi(mode="rgb", foreground=True)
        bit8_fg = blue.to_ansi(mode="8bit", foreground=True)
        ansi_fg = blue.to_ansi(mode="ansi", foreground=True)
        default_fg = blue.to_ansi(mode="default", foreground=True)
        
        # RGB mode
        assert rgb_fg == "\033[38;2;0;0;255m"
        
        # 8-bit mode (blue is color cube code 21)
        assert bit8_fg == "\033[38;5;21m"
        
        # ANSI and default should match 8-bit
        assert ansi_fg == bit8_fg
        assert default_fg == bit8_fg
    
    def test_gray_all_modes(self):
        """Gray (128,128,128) should work in all modes."""
        gray = RGB(128, 128, 128)
        
        rgb_fg = gray.to_ansi(mode="rgb", foreground=True)
        bit8_fg = gray.to_ansi(mode="8bit", foreground=True)
        ansi_fg = gray.to_ansi(mode="ansi", foreground=True)
        default_fg = gray.to_ansi(mode="default", foreground=True)
        
        # RGB mode
        assert rgb_fg == "\033[38;2;128;128;128m"
        
        # 8-bit mode (gray is grayscale, code should be in range 232-255)
        assert bit8_fg.startswith("\033[38;5;")
        # Extract code
        code = int(bit8_fg.split(";")[2].rstrip("m"))
        assert 232 <= code <= 255, f"Gray should use grayscale code, got {code}"
        
        # ANSI and default should match 8-bit
        assert ansi_fg == bit8_fg
        assert default_fg == bit8_fg


class TestConsistency:
    """Test consistency properties across the unified interface."""
    
    @given(rgb_colors, ansi_modes)
    def test_interface_is_deterministic(self, rgb: RGB, mode: AnsiMode):
        """Same inputs should always produce same outputs."""
        result1 = rgb.to_ansi(mode=mode, foreground=True)
        result2 = rgb.to_ansi(mode=mode, foreground=True)
        result3 = rgb.to_ansi(mode=mode, foreground=False)
        result4 = rgb.to_ansi(mode=mode, foreground=False)
        
        assert result1 == result2, \
            f"Foreground calls should be deterministic"
        assert result3 == result4, \
            f"Background calls should be deterministic"
    
    @given(rgb_colors, ansi_modes)
    def test_foreground_and_background_differ_only_in_prefix(self, rgb: RGB, mode: AnsiMode):
        """Foreground and background should differ only in prefix (38 vs 48)."""
        fg_code = rgb.to_ansi(mode=mode, foreground=True)
        bg_code = rgb.to_ansi(mode=mode, foreground=False)
        
        # Replace 38 with 48 in foreground code
        fg_as_bg = fg_code.replace("[38;", "[48;")
        
        assert fg_as_bg == bg_code, \
            f"Codes should differ only in prefix for mode '{mode}': " \
            f"fg='{fg_code}', bg='{bg_code}'"
    
    @given(rgb_colors, ansi_modes)
    def test_output_is_usable_string(self, rgb: RGB, mode: AnsiMode):
        """Output should be a usable string that can be concatenated."""
        ansi_code = rgb.to_ansi(mode=mode, foreground=True)
        text = "Test"
        reset = "\033[0m"
        
        # Should be able to create colored text
        colored_text = ansi_code + text + reset
        
        assert isinstance(colored_text, str)
        assert text in colored_text
        assert colored_text.startswith(ansi_code)
        assert colored_text.endswith(reset)
