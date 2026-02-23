"""
Property-based tests for Minecraft-style color code parsing.

Tests Properties 30, 31, and 32 from the design document.
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.color_util import color, printc, RGB
import re
import io
import sys
from contextlib import redirect_stdout


# Strategy for generating valid Minecraft color codes (&0-&f)
minecraft_color_codes = st.sampled_from([
    '0', '1', '2', '3', '4', '5', '6', '7',
    '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'
])

# Strategy for generating valid formatting codes (&l, &o, &n, &r)
formatting_codes = st.sampled_from(['l', 'o', 'n', 'r'])

# Strategy for generating valid extended codes (&-, &~, &*)
extended_codes = st.sampled_from(['-', '~', '*'])

# Strategy for generating valid hex colors
hex_color_6char = st.text(
    alphabet='0123456789ABCDEFabcdef',
    min_size=6,
    max_size=6
)

hex_color_3char = st.text(
    alphabet='0123456789ABCDEFabcdef',
    min_size=3,
    max_size=3
)

# Strategy for generating valid RGB component values
rgb_component = st.integers(min_value=0, max_value=255)


class TestProperty30_MinecraftColorCodeReplacement:
    """Property 30: Minecraft Color Code Replacement
    
    For any string containing Minecraft color codes (&0-&f, &l, &o, &n, &r, &-, &~, &*),
    the color() function should replace all codes with their corresponding ANSI escape sequences.
    """
    
    @given(
        code=minecraft_color_codes,
        text_before=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20),
        text_after=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20)
    )
    def test_minecraft_color_codes_replaced(self, code, text_before, text_after):
        """Minecraft color codes (&0-&f) should be replaced with ANSI 8-bit codes."""
        input_str = f"{text_before}&{code}{text_after}"
        result = color(input_str)
        
        # The color code should be replaced with an ANSI escape sequence
        assert f'&{code}' not in result, f"Color code &{code} was not replaced"
        
        # Result should contain an ANSI 8-bit color code (format: \033[38;5;Nm)
        assert '\033[38;5;' in result, "Result should contain ANSI 8-bit color code"
        
        # The text before and after should be preserved
        assert text_before in result or text_before == "", "Text before code should be preserved"
        assert text_after in result or text_after == "", "Text after code should be preserved"
    
    @given(
        code=formatting_codes,
        text_before=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20),
        text_after=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20)
    )
    def test_formatting_codes_replaced(self, code, text_before, text_after):
        """Formatting codes (&l, &o, &n, &r) should be replaced with ANSI sequences."""
        input_str = f"{text_before}&{code}{text_after}"
        result = color(input_str)
        
        # The formatting code should be replaced
        assert f'&{code}' not in result, f"Formatting code &{code} was not replaced"
        
        # Result should contain an ANSI escape sequence
        assert '\033[' in result, "Result should contain ANSI escape sequence"
        
        # The text before and after should be preserved
        assert text_before in result or text_before == "", "Text before code should be preserved"
        assert text_after in result or text_after == "", "Text after code should be preserved"
    
    @given(
        code=extended_codes,
        text_before=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20),
        text_after=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20)
    )
    def test_extended_codes_replaced(self, code, text_before, text_after):
        """Extended codes (&-, &~, &*) should be replaced with their mappings."""
        input_str = f"{text_before}&{code}{text_after}"
        result = color(input_str)
        
        # The extended code should be replaced
        assert f'&{code}' not in result, f"Extended code &{code} was not replaced"
        
        # The text before and after should be preserved
        assert text_before in result or text_before == "", "Text before code should be preserved"
        # Note: text_after might not be preserved if code is '-' (newline)
        if code != '-':
            assert text_after in result or text_after == "", "Text after code should be preserved"
    
    @given(
        codes=st.lists(
            st.one_of(minecraft_color_codes, formatting_codes, extended_codes),
            min_size=1,
            max_size=5
        ),
        text_segments=st.lists(
            st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=10),
            min_size=2,
            max_size=6
        )
    )
    def test_multiple_codes_all_replaced(self, codes, text_segments):
        """Multiple color codes in a string should all be replaced."""
        # Ensure we have enough text segments
        while len(text_segments) < len(codes) + 1:
            text_segments.append("")
        
        # Build input string with interleaved text and codes
        input_parts = []
        for i, code in enumerate(codes):
            input_parts.append(text_segments[i])
            input_parts.append(f'&{code}')
        input_parts.append(text_segments[len(codes)])
        
        input_str = ''.join(input_parts)
        result = color(input_str)
        
        # All color codes should be replaced
        for code in codes:
            # Count occurrences in input
            input_count = input_str.count(f'&{code}')
            # Count occurrences in output (should be 0)
            output_count = result.count(f'&{code}')
            assert output_count == 0, f"Color code &{code} was not fully replaced (found {output_count} times)"


class TestProperty31_RGBColorCodeParsing:
    """Property 31: RGB Color Code Parsing
    
    For any string containing RGB color codes in formats &gf(#RRGGBB), &gb(#RRGGBB),
    or &gf(R,G,B), the color() function should parse and convert them to ANSI RGB escape codes.
    """
    
    @given(
        hex_color=hex_color_6char,
        text_before=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20),
        text_after=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20)
    )
    def test_rgb_hex_foreground_parsing(self, hex_color, text_before, text_after):
        """RGB hex foreground codes &gf(#RRGGBB) should be parsed correctly."""
        input_str = f"{text_before}&gf(#{hex_color}){text_after}"
        result = color(input_str)
        
        # The RGB code should be replaced
        assert f'&gf(#{hex_color})' not in result, "RGB hex code was not replaced"
        
        # Result should contain ANSI RGB foreground code (format: \033[38;2;R;G;Bm)
        assert '\033[38;2;' in result, "Result should contain ANSI RGB foreground code"
        
        # Extract the RGB values from the hex color
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # The specific RGB values should appear in the result
        expected_code = f'\033[38;2;{r};{g};{b}m'
        assert expected_code in result, f"Expected ANSI code {expected_code} not found in result"
        
        # The text before and after should be preserved
        assert text_before in result or text_before == "", "Text before code should be preserved"
        assert text_after in result or text_after == "", "Text after code should be preserved"
    
    @given(
        hex_color=hex_color_6char,
        text_before=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20),
        text_after=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20)
    )
    def test_rgb_hex_background_parsing(self, hex_color, text_before, text_after):
        """RGB hex background codes &gb(#RRGGBB) should be parsed correctly."""
        input_str = f"{text_before}&gb(#{hex_color}){text_after}"
        result = color(input_str)
        
        # The RGB code should be replaced
        assert f'&gb(#{hex_color})' not in result, "RGB hex code was not replaced"
        
        # Result should contain ANSI RGB background code (format: \033[48;2;R;G;Bm)
        assert '\033[48;2;' in result, "Result should contain ANSI RGB background code"
        
        # Extract the RGB values from the hex color
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # The specific RGB values should appear in the result
        expected_code = f'\033[48;2;{r};{g};{b}m'
        assert expected_code in result, f"Expected ANSI code {expected_code} not found in result"
    
    @given(
        hex_color=hex_color_3char,
        text_before=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20),
        text_after=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20)
    )
    def test_rgb_hex_3char_parsing(self, hex_color, text_before, text_after):
        """RGB hex codes with 3-character format &gf(#RGB) should be parsed correctly."""
        input_str = f"{text_before}&gf(#{hex_color}){text_after}"
        result = color(input_str)
        
        # The RGB code should be replaced
        assert f'&gf(#{hex_color})' not in result, "RGB hex code was not replaced"
        
        # Result should contain ANSI RGB code
        assert '\033[38;2;' in result, "Result should contain ANSI RGB code"
        
        # Extract the RGB values from the 3-char hex color (expand each char)
        r = int(hex_color[0] * 2, 16)
        g = int(hex_color[1] * 2, 16)
        b = int(hex_color[2] * 2, 16)
        
        # The specific RGB values should appear in the result
        expected_code = f'\033[38;2;{r};{g};{b}m'
        assert expected_code in result, f"Expected ANSI code {expected_code} not found in result"
    
    @given(
        r=rgb_component,
        g=rgb_component,
        b=rgb_component,
        text_before=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20),
        text_after=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20)
    )
    def test_rgb_comma_foreground_parsing(self, r, g, b, text_before, text_after):
        """RGB comma-separated foreground codes &gf(R,G,B) should be parsed correctly."""
        input_str = f"{text_before}&gf({r},{g},{b}){text_after}"
        result = color(input_str)
        
        # The RGB code should be replaced
        assert f'&gf({r},{g},{b})' not in result, "RGB comma code was not replaced"
        
        # Result should contain ANSI RGB foreground code
        assert '\033[38;2;' in result, "Result should contain ANSI RGB foreground code"
        
        # The specific RGB values should appear in the result
        expected_code = f'\033[38;2;{r};{g};{b}m'
        assert expected_code in result, f"Expected ANSI code {expected_code} not found in result"
        
        # The text before and after should be preserved
        assert text_before in result or text_before == "", "Text before code should be preserved"
        assert text_after in result or text_after == "", "Text after code should be preserved"
    
    @given(
        r=rgb_component,
        g=rgb_component,
        b=rgb_component,
        text_before=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20),
        text_after=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=0, max_size=20)
    )
    def test_rgb_comma_background_parsing(self, r, g, b, text_before, text_after):
        """RGB comma-separated background codes &gb(R,G,B) should be parsed correctly."""
        input_str = f"{text_before}&gb({r},{g},{b}){text_after}"
        result = color(input_str)
        
        # The RGB code should be replaced
        assert f'&gb({r},{g},{b})' not in result, "RGB comma code was not replaced"
        
        # Result should contain ANSI RGB background code
        assert '\033[48;2;' in result, "Result should contain ANSI RGB background code"
        
        # The specific RGB values should appear in the result
        expected_code = f'\033[48;2;{r};{g};{b}m'
        assert expected_code in result, f"Expected ANSI code {expected_code} not found in result"
    
    @given(
        hex_color=st.text(alphabet='0123456789ABCDEFabcdef', min_size=1, max_size=2)
    )
    def test_invalid_hex_color_preserved(self, hex_color):
        """Invalid hex colors should be left as-is (not replaced)."""
        # Only test truly invalid lengths (1-2 chars, not 3 or 6)
        assume(len(hex_color) not in [3, 6])
        
        input_str = f"&gf(#{hex_color})"
        result = color(input_str)
        
        # Invalid hex color should be preserved (not replaced)
        assert f'&gf(#{hex_color})' in result, "Invalid hex color should be preserved"
    
    @given(
        r=st.integers(min_value=256, max_value=1000),
        g=rgb_component,
        b=rgb_component
    )
    def test_invalid_rgb_values_preserved(self, r, g, b):
        """Invalid RGB values (>255) should be left as-is (not replaced)."""
        input_str = f"&gf({r},{g},{b})"
        result = color(input_str)
        
        # Invalid RGB values should be preserved (not replaced)
        # Note: The implementation creates RGB object which validates in __post_init__
        # So invalid values will cause the code to be left as-is
        assert f'&gf({r},{g},{b})' in result, "Invalid RGB values should be preserved"


class TestProperty32_AutomaticResetCodeAppending:
    """Property 32: Automatic Reset Code Appending
    
    For any string, printc() should ensure the output ends with the ANSI reset code \033[0m.
    """
    
    @given(
        text=st.text(min_size=0, max_size=100)
    )
    def test_printc_appends_reset_code(self, text):
        """printc() should append reset code to any string."""
        # Capture stdout using redirect_stdout context manager
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            printc(text)
        
        output = output_buffer.getvalue()
        
        # Output should end with reset code followed by newline
        assert output.rstrip('\n').endswith('\033[0m'), "Output should end with ANSI reset code"
    
    @given(
        code=minecraft_color_codes,
        text=st.text(alphabet=st.characters(blacklist_characters='&'), min_size=1, max_size=50)
    )
    def test_printc_appends_reset_after_colored_text(self, code, text):
        """printc() should append reset code even when text contains color codes."""
        input_str = f"&{code}{text}"
        
        # Capture stdout using redirect_stdout context manager
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            printc(input_str)
        
        output = output_buffer.getvalue()
        
        # Output should end with reset code
        assert output.rstrip('\n').endswith('\033[0m'), "Output should end with ANSI reset code"
        
        # Output should contain the colored text
        assert text in output or len(text) == 0, "Colored text should be in output"
    
    @given(
        text=st.text(min_size=1, max_size=50)
    )
    def test_printc_does_not_duplicate_reset_code(self, text):
        """printc() should not duplicate reset code if already present."""
        # Add reset code to the input
        input_str = f"{text}\033[0m"
        
        # Capture stdout using redirect_stdout context manager
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            printc(input_str)
        
        output = output_buffer.getvalue().rstrip('\n')
        
        # Output should end with exactly one reset code
        assert output.endswith('\033[0m'), "Output should end with reset code"
        
        # Count occurrences of reset code at the end
        # Remove the final reset code and check if another exists right before it
        without_final_reset = output[:-4]  # Remove \033[0m
        if without_final_reset.endswith('\033[0m'):
            pytest.fail("Reset code was duplicated")
    
    @given(
        codes=st.lists(
            minecraft_color_codes,
            min_size=2,
            max_size=5
        ),
        text_segments=st.lists(
            st.text(alphabet=st.characters(blacklist_characters='&'), min_size=1, max_size=10),
            min_size=2,
            max_size=6
        )
    )
    def test_printc_appends_reset_after_multiple_codes(self, codes, text_segments):
        """printc() should append reset code even with multiple color codes."""
        # Ensure we have enough text segments
        while len(text_segments) < len(codes) + 1:
            text_segments.append("X")
        
        # Build input string with interleaved text and codes
        input_parts = []
        for i, code in enumerate(codes):
            input_parts.append(text_segments[i])
            input_parts.append(f'&{code}')
        input_parts.append(text_segments[len(codes)])
        
        input_str = ''.join(input_parts)
        
        # Capture stdout using redirect_stdout context manager
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            printc(input_str)
        
        output = output_buffer.getvalue()
        
        # Output should end with reset code
        assert output.rstrip('\n').endswith('\033[0m'), "Output should end with ANSI reset code"


# Edge case tests
class TestColorCodeParsingEdgeCases:
    """Additional edge case tests for color code parsing."""
    
    def test_empty_string(self):
        """Empty string should be handled correctly."""
        result = color("")
        assert result == "", "Empty string should remain empty"
    
    def test_no_color_codes(self):
        """String without color codes should be unchanged."""
        input_str = "Plain text without codes"
        result = color(input_str)
        assert result == input_str, "String without codes should be unchanged"
    
    def test_ampersand_without_code(self):
        """Ampersand not followed by valid code should be preserved."""
        input_str = "Text with & ampersand"
        result = color(input_str)
        assert '&' in result, "Standalone ampersand should be preserved"
    
    def test_mixed_code_types(self):
        """String with mixed code types should handle all correctly."""
        input_str = "&cRed &lBold &gf(#FF0000)Custom"
        result = color(input_str)
        
        # All codes should be replaced
        assert '&c' not in result
        assert '&l' not in result
        assert '&gf(#FF0000)' not in result
        
        # Result should contain ANSI codes
        assert '\033[' in result
    
    def test_consecutive_codes(self):
        """Consecutive color codes should all be processed."""
        input_str = "&c&l&nText"
        result = color(input_str)
        
        # All codes should be replaced
        assert '&c' not in result
        assert '&l' not in result
        assert '&n' not in result
        
        # Text should be preserved
        assert 'Text' in result
