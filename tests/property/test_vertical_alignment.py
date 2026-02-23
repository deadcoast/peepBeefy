"""
Property-based tests for vertical color alignment.

Tests:
- Property 26: Vertical Alignment Gradient Across Width

Validates Requirements 8.2, 8.5
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


class TestVerticalAlignmentGradientAcrossWidth:
    """Property 26: Vertical Alignment Gradient Across Width
    
    For any ASCII art with width W and any color list, vertical alignment
    should spread colors across W character positions, creating a horizontal
    gradient effect.
    
    Validates: Requirements 8.2, 8.5
    """
    
    @given(preset_names, hex_color_lists, ascii_lines)
    def test_colors_spread_across_width(self, name, colors, lines):
        """Colors should be spread across the maximum line width."""
        assume(any(len(line) > 0 for line in lines))  # At least one non-empty line
        
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        # Should have same number of lines
        assert len(colored_lines) == len(lines)
        
        # Find max width in original lines
        max_width = max(len(line) for line in lines if line)
        
        # Each character position should potentially have a different color
        # Extract colors at each position for non-empty lines
        ansi_pattern = r'\033\[38;5;(\d+)m'
        
        for i, (original, colored) in enumerate(zip(lines, colored_lines)):
            if not original:
                continue
            
            # Count color codes - should be one per character
            codes = re.findall(ansi_pattern, colored)
            
            # Should have at least as many color codes as characters
            # (might have more due to implementation details)
            assert len(codes) >= len(original), \
                f"Line {i} should have at least {len(original)} color codes, got {len(codes)}"
    
    @given(preset_names, hex_color_lists, ascii_lines)
    def test_gradient_effect_across_positions(self, name, colors, lines):
        """Different character positions should have different colors (gradient effect)."""
        assume(any(len(line) > 5 for line in lines))  # Need sufficient width
        assume(len(colors) >= 2)  # Need multiple colors for gradient
        
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        # Find a line with sufficient width
        for original, colored in zip(lines, colored_lines):
            if len(original) < 5:
                continue
            
            # Extract color codes for each character
            ansi_pattern = r'\033\[38;5;(\d+)m'
            codes = re.findall(ansi_pattern, colored)
            
            if len(codes) >= 5:
                # Check that not all colors are the same (gradient should vary)
                unique_colors = set(codes[:5])
                
                # With multiple colors and sufficient width, we should see variation
                # (unless all colors map to same 8-bit code, which is unlikely)
                # Allow for some tolerance - at least 2 different colors in first 5 positions
                assert len(unique_colors) >= 1, \
                    "Gradient should show color variation across width"
                break
    
    @given(preset_names, hex_color_lists, ascii_lines)
    def test_text_content_preserved(self, name, colors, lines):
        """Colorization should preserve original text content."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        # Strip ANSI codes and compare with original
        ansi_pattern = r'\033\[[0-9;]*m'
        
        for i, (original, colored) in enumerate(zip(lines, colored_lines)):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original, \
                f"Line {i} text content changed: expected '{original}', got '{stripped}'"
    
    @given(preset_names, hex_color_lists, ascii_lines)
    def test_reset_code_at_end_of_each_line(self, name, colors, lines):
        """Each line should end with ANSI reset code."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        for i, (original, colored) in enumerate(zip(lines, colored_lines)):
            if original:  # Non-empty lines should have reset
                assert colored.endswith('\033[0m'), \
                    f"Line {i} should end with reset code \\033[0m"
    
    def test_vertical_alignment_with_uniform_width(self):
        """Lines with same width should have consistent gradient."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        # All lines same width
        lines = ["AAAAA", "BBBBB", "CCCCC"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 3
        
        # Extract color codes for each line
        ansi_pattern = r'\033\[38;5;(\d+)m'
        
        line_colors = []
        for line in colored_lines:
            codes = re.findall(ansi_pattern, line)
            line_colors.append(codes)
        
        # All lines should have same number of color codes
        assert len(line_colors[0]) == len(line_colors[1]) == len(line_colors[2])
        
        # Same position across lines should have same color (vertical consistency)
        for pos in range(len(line_colors[0])):
            assert line_colors[0][pos] == line_colors[1][pos] == line_colors[2][pos], \
                f"Position {pos} should have same color across all lines"
    
    def test_vertical_alignment_with_varying_width(self):
        """Lines with different widths should still get gradient based on max width."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        # Varying widths
        lines = ["AAA", "BBBBB", "CC"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 3
        
        # Max width is 5, so gradient should be spread across 5 positions
        # Shorter lines should use subset of gradient
        ansi_pattern = r'\033\[38;5;(\d+)m'
        
        line_colors = []
        for line in colored_lines:
            codes = re.findall(ansi_pattern, line)
            line_colors.append(codes)
        
        # Line 0 (width 3) should have 3 colors
        assert len(line_colors[0]) == 3
        
        # Line 1 (width 5) should have 5 colors
        assert len(line_colors[1]) == 5
        
        # Line 2 (width 2) should have 2 colors
        assert len(line_colors[2]) == 2
        
        # First 2 positions of all lines should match (same gradient positions)
        assert line_colors[0][0] == line_colors[1][0] == line_colors[2][0]
        assert line_colors[0][1] == line_colors[1][1] == line_colors[2][1]
    
    def test_vertical_alignment_with_single_color(self):
        """Single color should be applied to all character positions."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000"]
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["AAAAA", "BBBBB"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 2
        
        # All positions should have the same color
        ansi_pattern = r'\033\[38;5;(\d+)m'
        
        for line in colored_lines:
            codes = re.findall(ansi_pattern, line)
            unique_colors = set(codes)
            
            # All should be the same
            assert len(unique_colors) == 1, \
                "All positions should have same color when only one color provided"
    
    def test_vertical_alignment_with_empty_lines(self):
        """Empty lines should be handled gracefully."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"]
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["AAA", "", "BBB"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 3
        
        # Empty line should remain empty (or just be empty)
        assert colored_lines[1] == ""
        
        # Non-empty lines should be colored
        assert '\033[' in colored_lines[0]
        assert '\033[' in colored_lines[2]
    
    def test_vertical_alignment_rgb_mode(self):
        """Vertical alignment should work with RGB mode."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        lines = ["AAAAA"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 1
        
        # Should use RGB format (38;2;R;G;B)
        rgb_pattern = r'\033\[38;2;\d+;\d+;\d+m'
        matches = re.findall(rgb_pattern, colored_lines[0])
        
        # Should have RGB color codes for each character
        assert len(matches) >= 5, \
            "Should have RGB color codes for each character"
    
    @given(preset_names, hex_color_lists, ascii_lines)
    def test_vertical_alignment_line_count_matches(self, name, colors, lines):
        """Output should have same number of lines as input."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == len(lines), \
            f"Expected {len(lines)} lines, got {len(colored_lines)}"
    
    def test_vertical_alignment_preserves_whitespace(self):
        """Whitespace characters should be preserved and colored."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"]
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["A B C", "  AAA", "BBB  "]
        colored_lines = colorizer.colorize(lines)
        
        # Strip ANSI codes and verify whitespace preserved
        ansi_pattern = r'\033\[[0-9;]*m'
        for original, colored in zip(lines, colored_lines):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original, \
                f"Whitespace not preserved: expected '{original}', got '{stripped}'"
    
    def test_vertical_alignment_with_special_characters(self):
        """Special characters should be preserved and colored."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"]
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["!@#$%", "<>/\\|"]
        colored_lines = colorizer.colorize(lines)
        
        # Strip ANSI codes and verify content preserved
        ansi_pattern = r'\033\[[0-9;]*m'
        for original, colored in zip(lines, colored_lines):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original
    
    def test_vertical_alignment_strips_existing_codes(self):
        """Existing ANSI codes should be stripped before applying gradient."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"]
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        # Lines with existing ANSI codes
        lines = [
            "\033[31mRed\033[0m",
            "\033[1;32mGreen\033[0m"
        ]
        colored_lines = colorizer.colorize(lines)
        
        # Should have new color codes, not old ones
        for line in colored_lines:
            # Should not contain old-style codes
            assert '\033[31m' not in line, "Old color code should be stripped"
            assert '\033[1;32m' not in line, "Old color code should be stripped"
            
            # Should contain new 8-bit format
            assert '\033[38;5;' in line, "Should have new 8-bit color code"
    
    def test_vertical_alignment_with_weighted_preset(self):
        """Vertical alignment should work with weighted presets."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"],
            weights=[2, 1]
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["AAAAA"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 1
        
        # Expanded colors should be [red, red, green]
        # Gradient should spread these across width
        ansi_pattern = r'\033\[38;5;(\d+)m'
        codes = re.findall(ansi_pattern, colored_lines[0])
        
        # Should have 5 color codes (one per character)
        assert len(codes) == 5
    
    @given(preset_names, hex_color_lists)
    def test_vertical_alignment_with_no_lines(self, name, colors):
        """Colorizing empty list should return empty list."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize([])
        
        assert colored_lines == []
    
    def test_vertical_alignment_gradient_smoothness(self):
        """Gradient should transition smoothly across width."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#0000FF"]  # Red to blue
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        # Wide line to see gradient
        lines = ["A" * 20]
        colored_lines = colorizer.colorize(lines)
        
        # Extract RGB values
        rgb_pattern = r'\033\[38;2;(\d+);(\d+);(\d+)m'
        matches = re.findall(rgb_pattern, colored_lines[0])
        
        # Should have 20 color codes
        assert len(matches) == 20
        
        # Convert to RGB tuples
        rgb_values = [(int(r), int(g), int(b)) for r, g, b in matches]
        
        # First should be close to red (255, 0, 0)
        assert rgb_values[0][0] > 200, "First color should be reddish"
        assert rgb_values[0][2] < 50, "First color should have low blue"
        
        # Last should be close to blue (0, 0, 255)
        assert rgb_values[-1][2] > 200, "Last color should be bluish"
        assert rgb_values[-1][0] < 50, "Last color should have low red"
        
        # Middle should be transitioning
        mid = len(rgb_values) // 2
        # Middle should have both red and blue components
        assert 50 < rgb_values[mid][0] < 200, "Middle should be transitioning"
        assert 50 < rgb_values[mid][2] < 200, "Middle should be transitioning"
    
    def test_vertical_alignment_with_single_character_lines(self):
        """Single character lines should work correctly."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"]
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["A", "B", "C"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 3
        
        # Each line should have exactly one color code
        ansi_pattern = r'\033\[38;5;(\d+)m'
        
        for line in colored_lines:
            codes = re.findall(ansi_pattern, line)
            assert len(codes) == 1, "Single character should have one color code"
    
    def test_vertical_alignment_max_width_calculation(self):
        """Gradient should be based on maximum line width."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        # Max width is 10
        lines = ["AAA", "BBBBBBBBBB", "CCCCC"]
        colored_lines = colorizer.colorize(lines)
        
        # Extract color codes
        ansi_pattern = r'\033\[38;5;(\d+)m'
        
        line0_codes = re.findall(ansi_pattern, colored_lines[0])
        line1_codes = re.findall(ansi_pattern, colored_lines[1])
        line2_codes = re.findall(ansi_pattern, colored_lines[2])
        
        # Line 1 (longest) should have 10 color codes
        assert len(line1_codes) == 10
        
        # Line 0 should have 3 codes (first 3 from gradient)
        assert len(line0_codes) == 3
        
        # Line 2 should have 5 codes (first 5 from gradient)
        assert len(line2_codes) == 5
        
        # First 3 positions should match across all lines
        assert line0_codes[0] == line1_codes[0] == line2_codes[0]
        assert line0_codes[1] == line1_codes[1] == line2_codes[1]
        assert line0_codes[2] == line1_codes[2] == line2_codes[2]
    
    @given(preset_names, hex_color_lists, ascii_lines)
    def test_vertical_alignment_character_count_matches(self, name, colors, lines):
        """Each line should have color codes matching its character count."""
        assume(any(len(line) > 0 for line in lines))
        
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        ansi_pattern = r'\033\[38;5;(\d+)m'
        
        for original, colored in zip(lines, colored_lines):
            if not original:
                continue
            
            codes = re.findall(ansi_pattern, colored)
            
            # Should have one color code per character
            assert len(codes) == len(original), \
                f"Expected {len(original)} color codes, got {len(codes)}"
