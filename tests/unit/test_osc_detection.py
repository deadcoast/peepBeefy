"""
Unit tests for OSC background color detection.

Tests the OSC response parsing and background color detection
functionality in terminal_detect.py.
"""

import pytest
from src.terminal_detect import parse_osc_rgb_response
from src.color_util import RGB


class TestOSCResponseParsing:
    """Test OSC 11 response parsing."""
    
    def test_parse_valid_osc_response(self):
        """Test parsing a valid OSC 11 response."""
        # Standard format: ESC ] 11 ; rgb:RRRR/GGGG/BBBB BEL
        response = "\033]11;rgb:0000/0000/0000\007"
        result = parse_osc_rgb_response(response)
        
        assert result is not None
        assert result.r == 0
        assert result.g == 0
        assert result.b == 0
    
    def test_parse_white_background(self):
        """Test parsing white background color."""
        response = "\033]11;rgb:ffff/ffff/ffff\007"
        result = parse_osc_rgb_response(response)
        
        assert result is not None
        assert result.r == 255
        assert result.g == 255
        assert result.b == 255
    
    def test_parse_gray_background(self):
        """Test parsing gray background color."""
        # 50% gray: 0x8000 in 16-bit = 32768 / 65535 ≈ 0.5 → 128 in 8-bit
        response = "\033]11;rgb:8000/8000/8000\007"
        result = parse_osc_rgb_response(response)
        
        assert result is not None
        # Allow small rounding tolerance
        assert 127 <= result.r <= 128
        assert 127 <= result.g <= 128
        assert 127 <= result.b <= 128
    
    def test_parse_colored_background(self):
        """Test parsing a colored background."""
        # Dark blue: R=0, G=0, B=0x4000 (25% blue)
        response = "\033]11;rgb:0000/0000/4000\007"
        result = parse_osc_rgb_response(response)
        
        assert result is not None
        assert result.r == 0
        assert result.g == 0
        # 0x4000 / 0xFFFF ≈ 0.25 → 64 in 8-bit
        assert 63 <= result.b <= 64
    
    def test_parse_response_with_prefix(self):
        """Test parsing response with terminal-specific prefix."""
        # Some terminals add extra characters before the rgb: part
        response = "^[]11;rgb:ffff/0000/0000^G"
        result = parse_osc_rgb_response(response)
        
        assert result is not None
        assert result.r == 255
        assert result.g == 0
        assert result.b == 0
    
    def test_parse_response_with_esc_backslash_terminator(self):
        r"""Test parsing response with ESC \ terminator instead of BEL."""
        response = "\033]11;rgb:0000/ffff/0000\033\\"
        result = parse_osc_rgb_response(response)
        
        assert result is not None
        assert result.r == 0
        assert result.g == 255
        assert result.b == 0
    
    def test_parse_invalid_format(self):
        """Test parsing invalid OSC response returns None."""
        invalid_responses = [
            "",
            "not an osc response",
            "\033]11;invalid\007",
            "\033]11;rgb:ZZZ/0000/0000\007",
            "\033]11;rgb:0000\007",  # Missing components
            "rgb:0000/0000",  # Incomplete
        ]
        
        for response in invalid_responses:
            result = parse_osc_rgb_response(response)
            assert result is None, f"Expected None for invalid response: {response}"
    
    def test_parse_uppercase_hex(self):
        """Test parsing with uppercase hex values."""
        response = "\033]11;rgb:FFFF/AAAA/5555\007"
        result = parse_osc_rgb_response(response)
        
        assert result is not None
        assert result.r == 255
        # 0xAAAA / 0xFFFF ≈ 0.667 → 170 in 8-bit
        assert 169 <= result.g <= 170
        # 0x5555 / 0xFFFF ≈ 0.333 → 85 in 8-bit
        assert 84 <= result.b <= 85
    
    def test_16bit_to_8bit_conversion_accuracy(self):
        """Test that 16-bit to 8-bit conversion is accurate."""
        # Test known conversion points
        test_cases = [
            ("0000", 0),      # Min value
            ("ffff", 255),    # Max value
            ("8000", 128),    # Mid value (approximately)
            ("4000", 64),     # Quarter value (approximately)
            ("c000", 192),    # Three-quarter value (approximately)
        ]
        
        for hex_val, expected_8bit in test_cases:
            response = f"\033]11;rgb:{hex_val}/{hex_val}/{hex_val}\007"
            result = parse_osc_rgb_response(response)
            
            assert result is not None
            # Allow ±1 tolerance for rounding
            assert abs(result.r - expected_8bit) <= 1
            assert abs(result.g - expected_8bit) <= 1
            assert abs(result.b - expected_8bit) <= 1


class TestBackgroundColorDetection:
    """Test background color detection integration."""
    
    def test_get_background_color_graceful_failure(self):
        """Test that get_background_color returns None on failure."""
        # This test just verifies the function doesn't crash
        # Actual detection may fail in test environment (no TTY)
        from src.terminal_detect import get_background_color
        
        result = get_background_color()
        # In test environment, this will likely return None
        # We just verify it doesn't raise an exception
        assert result is None or isinstance(result, RGB)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
