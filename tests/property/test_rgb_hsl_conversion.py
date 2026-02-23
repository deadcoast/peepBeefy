"""
Property-based tests for RGB-HSL color conversion.

Tests:
- Property 1: RGB-HSL Round-Trip Preservation
- Property 44: Hex Color Format Support

Validates Requirements 1.1, 1.2, 1.6
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.color_util import RGB, HSL


# Strategy for generating valid RGB colors
rgb_colors = st.builds(
    RGB,
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)

# Strategy for generating valid HSL colors
hsl_colors = st.builds(
    HSL,
    h=st.floats(min_value=0.0, max_value=1.0),
    s=st.floats(min_value=0.0, max_value=1.0),
    l=st.floats(min_value=0.0, max_value=1.0)
)

# Strategy for generating 6-character hex colors
hex_6char = st.text(
    alphabet='0123456789ABCDEFabcdef',
    min_size=6,
    max_size=6
).map(lambda s: f"#{s}")

# Strategy for generating 3-character hex colors
hex_3char = st.text(
    alphabet='0123456789ABCDEFabcdef',
    min_size=3,
    max_size=3
).map(lambda s: f"#{s}")

# Combined hex color strategy
hex_colors = st.one_of(hex_6char, hex_3char)


class TestRGBHSLRoundTrip:
    """Property 1: RGB-HSL Round-Trip Preservation
    
    For any valid RGB color, converting to HSL and back to RGB should produce
    a color equivalent to the original (within rounding tolerance of ±1 per component).
    
    Validates: Requirements 1.1, 1.2
    """
    
    @given(rgb_colors)
    def test_rgb_to_hsl_to_rgb_preserves_color(self, rgb: RGB):
        """RGB → HSL → RGB should preserve color within rounding tolerance."""
        # Convert RGB to HSL and back to RGB
        hsl = rgb.hsl()
        rgb_back = hsl.rgb()
        
        # Check each component is within ±1 (rounding tolerance)
        assert abs(rgb.r - rgb_back.r) <= 1, \
            f"Red component changed: {rgb.r} → {rgb_back.r}"
        assert abs(rgb.g - rgb_back.g) <= 1, \
            f"Green component changed: {rgb.g} → {rgb_back.g}"
        assert abs(rgb.b - rgb_back.b) <= 1, \
            f"Blue component changed: {rgb.b} → {rgb_back.b}"
    
    @given(hsl_colors)
    def test_hsl_to_rgb_to_hsl_preserves_color(self, hsl: HSL):
        """HSL → RGB → HSL should preserve color within rounding tolerance.
        
        Note: RGB quantization (255 discrete values) causes precision loss,
        especially for very dark/light colors with low saturation. The tolerance
        accounts for this mathematical reality of the conversion.
        """
        # Skip edge cases where hue/saturation become undefined:
        # - When lightness is 0.0 (black) or 1.0 (white), hue and saturation are undefined
        # - When saturation is 0 (grayscale), hue is undefined
        # - Very dark colors (l < 0.15) have high relative error due to RGB quantization
        assume(hsl.l > 0.15 and hsl.l < 0.85)  # Avoid very dark/light colors
        assume(hsl.s > 0.15)  # Avoid near-grayscale colors
        
        # Convert HSL to RGB and back to HSL
        rgb = hsl.rgb()
        hsl_back = rgb.hsl()
        
        # Check each component is within tolerance
        # Tolerance is higher for hue/saturation due to RGB quantization effects
        
        # Hue is circular, so we need special handling
        hue_diff = min(
            abs(hsl.h - hsl_back.h),
            abs(hsl.h - hsl_back.h + 1.0),
            abs(hsl.h - hsl_back.h - 1.0)
        )
        # Hue tolerance: 0.02 (about 7 degrees out of 360)
        assert hue_diff <= 0.02, \
            f"Hue changed: {hsl.h} → {hsl_back.h} (diff: {hue_diff})"
        
        # Saturation tolerance: 0.03 (3% absolute)
        assert abs(hsl.s - hsl_back.s) <= 0.03, \
            f"Saturation changed: {hsl.s} → {hsl_back.s}"
        
        # Lightness tolerance: 0.02 (2% absolute) - most stable component
        assert abs(hsl.l - hsl_back.l) <= 0.02, \
            f"Lightness changed: {hsl.l} → {hsl_back.l}"
    
    @given(rgb_colors)
    def test_rgb_hsl_conversion_produces_valid_values(self, rgb: RGB):
        """RGB to HSL conversion should produce valid HSL values."""
        hsl = rgb.hsl()
        
        # HSL values should be in valid range
        assert 0.0 <= hsl.h <= 1.0, f"Invalid hue: {hsl.h}"
        assert 0.0 <= hsl.s <= 1.0, f"Invalid saturation: {hsl.s}"
        assert 0.0 <= hsl.l <= 1.0, f"Invalid lightness: {hsl.l}"
    
    @given(hsl_colors)
    def test_hsl_rgb_conversion_produces_valid_values(self, hsl: HSL):
        """HSL to RGB conversion should produce valid RGB values."""
        rgb = hsl.rgb()
        
        # RGB values should be in valid range
        assert 0 <= rgb.r <= 255, f"Invalid red: {rgb.r}"
        assert 0 <= rgb.g <= 255, f"Invalid green: {rgb.g}"
        assert 0 <= rgb.b <= 255, f"Invalid blue: {rgb.b}"


class TestHexColorFormatSupport:
    """Property 44: Hex Color Format Support
    
    For any valid hex color string in either 6-character (#RRGGBB) or 
    3-character (#RGB) format, RGB.from_hex() should parse it correctly.
    
    Validates: Requirements 1.6
    """
    
    @given(hex_6char)
    def test_six_character_hex_parsing(self, hex_str: str):
        """6-character hex colors (#RRGGBB) should parse correctly."""
        rgb = RGB.from_hex(hex_str)
        
        # Extract expected values
        hex_clean = hex_str.lstrip("#")
        expected_r = int(hex_clean[0:2], 16)
        expected_g = int(hex_clean[2:4], 16)
        expected_b = int(hex_clean[4:6], 16)
        
        # Verify parsed values match
        assert rgb.r == expected_r, f"Red mismatch: {rgb.r} != {expected_r}"
        assert rgb.g == expected_g, f"Green mismatch: {rgb.g} != {expected_g}"
        assert rgb.b == expected_b, f"Blue mismatch: {rgb.b} != {expected_b}"
    
    @given(hex_3char)
    def test_three_character_hex_parsing(self, hex_str: str):
        """3-character hex colors (#RGB) should parse correctly."""
        rgb = RGB.from_hex(hex_str)
        
        # Extract expected values (each char is doubled)
        hex_clean = hex_str.lstrip("#")
        expected_r = int(hex_clean[0] * 2, 16)
        expected_g = int(hex_clean[1] * 2, 16)
        expected_b = int(hex_clean[2] * 2, 16)
        
        # Verify parsed values match
        assert rgb.r == expected_r, f"Red mismatch: {rgb.r} != {expected_r}"
        assert rgb.g == expected_g, f"Green mismatch: {rgb.g} != {expected_g}"
        assert rgb.b == expected_b, f"Blue mismatch: {rgb.b} != {expected_b}"
    
    @given(hex_colors)
    def test_hex_parsing_without_hash_prefix(self, hex_str: str):
        """Hex colors should parse correctly with or without # prefix."""
        hex_without_hash = hex_str.lstrip("#")
        
        rgb_with_hash = RGB.from_hex(hex_str)
        rgb_without_hash = RGB.from_hex(hex_without_hash)
        
        # Both should produce the same result
        assert rgb_with_hash.r == rgb_without_hash.r
        assert rgb_with_hash.g == rgb_without_hash.g
        assert rgb_with_hash.b == rgb_without_hash.b
    
    @given(hex_colors)
    def test_hex_round_trip_preservation(self, hex_str: str):
        """Parsing hex and converting back should preserve color."""
        rgb = RGB.from_hex(hex_str)
        
        # RGB values should be valid
        assert 0 <= rgb.r <= 255
        assert 0 <= rgb.g <= 255
        assert 0 <= rgb.b <= 255
        
        # Converting to hex and back should preserve values
        # (We don't have to_hex method, but we can verify the values are correct)
        hex_clean = hex_str.lstrip("#")
        if len(hex_clean) == 3:
            # Expand 3-char format
            hex_clean = ''.join([c * 2 for c in hex_clean])
        
        expected_r = int(hex_clean[0:2], 16)
        expected_g = int(hex_clean[2:4], 16)
        expected_b = int(hex_clean[4:6], 16)
        
        assert rgb.r == expected_r
        assert rgb.g == expected_g
        assert rgb.b == expected_b
    
    def test_invalid_hex_length_raises_error(self):
        """Invalid hex lengths should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid hex color length"):
            RGB.from_hex("#12")  # Too short
        
        with pytest.raises(ValueError, match="Invalid hex color length"):
            RGB.from_hex("#1234567")  # Too long
    
    def test_invalid_hex_characters_raise_error(self):
        """Invalid hex characters should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid hex color format"):
            RGB.from_hex("#GGGGGG")  # Invalid characters
        
        with pytest.raises(ValueError, match="Invalid hex color format"):
            RGB.from_hex("#12345Z")  # Invalid character


class TestEdgeCases:
    """Test edge cases for RGB-HSL conversion."""
    
    def test_black_conversion(self):
        """Black (0,0,0) should convert correctly."""
        black = RGB(0, 0, 0)
        hsl = black.hsl()
        rgb_back = hsl.rgb()
        
        assert rgb_back.r == 0
        assert rgb_back.g == 0
        assert rgb_back.b == 0
    
    def test_white_conversion(self):
        """White (255,255,255) should convert correctly."""
        white = RGB(255, 255, 255)
        hsl = white.hsl()
        rgb_back = hsl.rgb()
        
        assert abs(rgb_back.r - 255) <= 1
        assert abs(rgb_back.g - 255) <= 1
        assert abs(rgb_back.b - 255) <= 1
    
    def test_pure_red_conversion(self):
        """Pure red (255,0,0) should convert correctly."""
        red = RGB(255, 0, 0)
        hsl = red.hsl()
        rgb_back = hsl.rgb()
        
        assert abs(rgb_back.r - 255) <= 1
        assert abs(rgb_back.g - 0) <= 1
        assert abs(rgb_back.b - 0) <= 1
    
    def test_pure_green_conversion(self):
        """Pure green (0,255,0) should convert correctly."""
        green = RGB(0, 255, 0)
        hsl = green.hsl()
        rgb_back = hsl.rgb()
        
        assert abs(rgb_back.r - 0) <= 1
        assert abs(rgb_back.g - 255) <= 1
        assert abs(rgb_back.b - 0) <= 1
    
    def test_pure_blue_conversion(self):
        """Pure blue (0,0,255) should convert correctly."""
        blue = RGB(0, 0, 255)
        hsl = blue.hsl()
        rgb_back = hsl.rgb()
        
        assert abs(rgb_back.r - 0) <= 1
        assert abs(rgb_back.g - 0) <= 1
        assert abs(rgb_back.b - 255) <= 1
    
    def test_gray_conversion(self):
        """Gray colors should convert correctly."""
        gray = RGB(128, 128, 128)
        hsl = gray.hsl()
        rgb_back = hsl.rgb()
        
        assert abs(rgb_back.r - 128) <= 1
        assert abs(rgb_back.g - 128) <= 1
        assert abs(rgb_back.b - 128) <= 1
