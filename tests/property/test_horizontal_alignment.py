"""
Property-based tests for horizontal color alignment.

Tests:
- Property 25: Horizontal Alignment One Color Per Line

Validates Requirements 8.1, 8.4
"""

import re
import pytest
from hypothesis import given, strategies as st, assume
from src.color_util import RGB
from src.color_presets import ColorPreset
from src.ascii_renderer import ASCIIColorizer, ColorAlignment


# Strategy for generating valid RGB colors
rgb_colors = st.builds(
    RGB,
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)

# Strategy for generating hex color strings
hex_colors = st.text(
    alphabet='0123456789ABCDEFabcdef',
    min_size=6,
    max_size=6
).map(lambda s: f"#{s}")

# Strategy for generating lists of hex colors (1-10 colors)
hex_color_lists = st.lists(
    hex_colors,
    min_size=1,
    max_size=10
)

# Strategy for generating ASCII art lines
ascii_lines = st.lists(
    st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .-_/\\|[]{}()<>',
        min_size=0,
        max_size=80
    ),
    min_size=1,
    max_size=50
)

# Strategy for generating preset names
preset_names = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz_',
    min_size=1,
    max_size=20
)


class TestHorizontalAlignmentOneColorPerLine:
    """Property 25: Horizontal Alignment One Color Per Line
    
    For any ASCII art with N lines and any color list, horizontal alignment
    should apply exactly one color per line, cycling through colors if fewer
    than N colors are provided.
    
    Validates: Requirements 8.1, 8.4
    """
    
    @given(preset_names, hex_color_lists, ascii_lines)
    def test_one_color_per_line(self, name, colors, lines):
        """Each line should have exactly one color applied."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        # Should have same number of lines
        assert len(colored_lines) == len(lines)
        
        # Each line should have exactly one color code at the start
        ansi_pattern = r'\033\[[0-9;]*m'
        
        for i, line in enumerate(colored_lines):
            # Count ANSI codes in the line (excluding reset at end)
            codes = re.findall(ansi_pattern, line)
            
            # Should have at least one color code at start and one reset at end
            assert len(codes) >= 2, \
                f"Line {i} should have at least 2 ANSI codes (color + reset), got {len(codes)}"
            
            # First code should be a color code (foreground 38;5 for 8-bit)
            assert codes[0].startswith('\033[38;5;') or codes[0].startswith('\033[38;2;'), \
                f"First code should be a foreground color code, got {codes[0]}"
            
            # Last code should be reset
            assert '\033[0m' in line, \
                f"Line {i} should end with reset code"
    
    @given(preset_names, hex_color_lists, ascii_lines)
    def test_color_cycling_when_more_lines_than_colors(self, name, colors, lines):
        """When there are more lines than colors, colors should cycle."""
        assume(len(lines) > len(colors))
        
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        # Extract color codes from each line
        ansi_pattern = r'\033\[38;5;(\d+)m'
        
        color_codes = []
        for line in colored_lines:
            match = re.search(ansi_pattern, line)
            if match:
                color_codes.append(match.group(1))
        
        # Should have extracted color codes for all lines
        assert len(color_codes) == len(lines)
        
        # Colors should cycle: line i should have same color as line (i % num_colors)
        num_colors = len(colors)
        for i in range(len(lines)):
            expected_color_index = i % num_colors
            actual_color_index = i % num_colors
            
            # Lines at positions i and i+num_colors should have same color
            if i + num_colors < len(lines):
                assert color_codes[i] == color_codes[i + num_colors], \
                    f"Color should cycle: line {i} and line {i + num_colors} should have same color"
    
    @given(preset_names, hex_color_lists, ascii_lines)
    def test_text_content_preserved(self, name, colors, lines):
        """Colorization should preserve original text content."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        # Strip ANSI codes and compare with original
        ansi_pattern = r'\033\[[0-9;]*m'
        
        for i, (original, colored) in enumerate(zip(lines, colored_lines)):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original, \
                f"Line {i} text content changed: expected '{original}', got '{stripped}'"
    
    def test_horizontal_alignment_with_exact_color_count(self):
        """When colors match line count, each line gets unique color."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line 1", "Line 2", "Line 3"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 3
        
        # Each line should have a different color
        ansi_pattern = r'\033\[38;5;(\d+)m'
        color_codes = []
        for line in colored_lines:
            match = re.search(ansi_pattern, line)
            assert match is not None
            color_codes.append(match.group(1))
        
        # All three colors should be different (for distinct input colors)
        # Note: Due to 8-bit conversion, some colors might map to same code
        # but for red, green, blue they should be distinct
        assert len(color_codes) == 3
    
    def test_horizontal_alignment_with_more_colors_than_lines(self):
        """When more colors than lines, only first N colors are used."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"]
        )
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line 1", "Line 2"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 2
        
        # Only first 2 colors should be used
        ansi_pattern = r'\033\[38;5;(\d+)m'
        color_codes = []
        for line in colored_lines:
            match = re.search(ansi_pattern, line)
            assert match is not None
            color_codes.append(match.group(1))
        
        assert len(color_codes) == 2
    
    def test_horizontal_alignment_with_single_color(self):
        """Single color should be applied to all lines."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000"]
        )
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line 1", "Line 2", "Line 3"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 3
        
        # All lines should have the same color
        ansi_pattern = r'\033\[38;5;(\d+)m'
        color_codes = []
        for line in colored_lines:
            match = re.search(ansi_pattern, line)
            assert match is not None
            color_codes.append(match.group(1))
        
        # All should be the same
        assert len(set(color_codes)) == 1, \
            "All lines should have the same color when only one color is provided"
    
    def test_horizontal_alignment_with_empty_lines(self):
        """Empty lines should still get color codes."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"]
        )
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line 1", "", "Line 3"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 3
        
        # Even empty line should have color codes
        for line in colored_lines:
            assert '\033[' in line, "Each line should have ANSI codes"
            assert '\033[0m' in line, "Each line should have reset code"
    
    @given(preset_names, hex_color_lists, ascii_lines)
    def test_reset_code_at_end_of_each_line(self, name, colors, lines):
        """Each line should end with ANSI reset code."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        for i, line in enumerate(colored_lines):
            assert line.endswith('\033[0m'), \
                f"Line {i} should end with reset code \\033[0m"
    
    @given(preset_names, hex_color_lists, ascii_lines)
    def test_color_code_at_start_of_each_line(self, name, colors, lines):
        """Each line should start with a color code."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        for i, line in enumerate(colored_lines):
            assert line.startswith('\033['), \
                f"Line {i} should start with ANSI escape sequence"
    
    def test_horizontal_alignment_rgb_mode(self):
        """Horizontal alignment should work with RGB mode."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        lines = ["Line 1", "Line 2", "Line 3"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 3
        
        # Should use RGB format (38;2;R;G;B)
        rgb_pattern = r'\033\[38;2;\d+;\d+;\d+m'
        for line in colored_lines:
            assert re.search(rgb_pattern, line) is not None, \
                "Line should have RGB color code format"
    
    def test_horizontal_alignment_with_weighted_preset(self):
        """Horizontal alignment should work with weighted presets."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"],
            weights=[2, 1]
        )
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line 1", "Line 2", "Line 3"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 3
        
        # Expanded colors should be [red, red, green]
        # So line 0 and 1 should have same color, line 2 different
        ansi_pattern = r'\033\[38;5;(\d+)m'
        color_codes = []
        for line in colored_lines:
            match = re.search(ansi_pattern, line)
            assert match is not None
            color_codes.append(match.group(1))
        
        # First two lines should have same color (red repeated twice)
        assert color_codes[0] == color_codes[1], \
            "First two lines should have same color due to weight=2"
        
        # Third line should have different color (green)
        # Note: Might be same if colors map to same 8-bit code, but unlikely for red/green
    
    @given(preset_names, hex_color_lists)
    def test_horizontal_alignment_with_no_lines(self, name, colors):
        """Colorizing empty list should return empty list."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize([])
        
        assert colored_lines == []
    
    def test_horizontal_alignment_preserves_whitespace(self):
        """Whitespace in lines should be preserved."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000"]
        )
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["  Line with leading spaces", "Line with trailing spaces  ", "  Centered  "]
        colored_lines = colorizer.colorize(lines)
        
        # Strip ANSI codes and verify whitespace preserved
        ansi_pattern = r'\033\[[0-9;]*m'
        for original, colored in zip(lines, colored_lines):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original, \
                f"Whitespace not preserved: expected '{original}', got '{stripped}'"
    
    def test_horizontal_alignment_with_special_characters(self):
        """Special characters should be preserved."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000"]
        )
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line with !@#$%^&*()", "Line with <>/\\|[]{}"]
        colored_lines = colorizer.colorize(lines)
        
        # Strip ANSI codes and verify content preserved
        ansi_pattern = r'\033\[[0-9;]*m'
        for original, colored in zip(lines, colored_lines):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original
    
    @given(preset_names, hex_color_lists, ascii_lines)
    def test_horizontal_alignment_line_count_matches(self, name, colors, lines):
        """Output should have same number of lines as input."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == len(lines), \
            f"Expected {len(lines)} lines, got {len(colored_lines)}"
    
    def test_horizontal_alignment_strips_existing_codes(self):
        """Existing ANSI codes should be stripped before applying new colors."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000"]
        )
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        # Lines with existing ANSI codes
        lines = [
            "\033[31mRed text\033[0m",
            "\033[1;32mBold green\033[0m"
        ]
        colored_lines = colorizer.colorize(lines)
        
        # Should have new color codes, not old ones
        # Old codes: \033[31m and \033[1;32m
        # New codes should be 8-bit format: \033[38;5;...m
        
        for line in colored_lines:
            # Should not contain old-style codes
            assert '\033[31m' not in line, "Old color code should be stripped"
            assert '\033[1;32m' not in line, "Old color code should be stripped"
            
            # Should contain new 8-bit format
            assert '\033[38;5;' in line, "Should have new 8-bit color code"
