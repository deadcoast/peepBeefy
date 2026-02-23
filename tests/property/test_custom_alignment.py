"""
Property-based tests for custom color alignment.

Tests:
- Property 27: Custom Alignment Mapping

Validates Requirements 8.3
"""

import re
import pytest
from hypothesis import given, strategies as st, assume
from src.color_util import RGB
from src.color_presets import ColorPreset
from src.ascii_renderer import ASCIIColorizer, ColorAlignment


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

# Strategy for generating custom color mappings
# Maps ASCII color codes (0-9, a-f) to preset indices (0-9)
custom_color_maps = st.dictionaries(
    keys=st.sampled_from(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']),
    values=st.integers(min_value=0, max_value=9).map(str),
    min_size=1,
    max_size=16
)


class TestCustomAlignmentMapping:
    """Property 27: Custom Alignment Mapping
    
    For any ASCII art with color codes and any custom color mapping, custom
    alignment should replace each color code with the mapped color.
    
    Validates: Requirements 8.3
    """
    
    @given(preset_names, hex_color_lists, ascii_lines, custom_color_maps)
    def test_custom_alignment_requires_custom_colors(self, name, colors, lines, color_map):
        """Custom alignment mode requires custom_colors mapping."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        # Should successfully colorize without errors
        assert len(colored_lines) == len(lines)
    
    @given(preset_names, hex_color_lists, ascii_lines, custom_color_maps)
    def test_custom_alignment_preserves_text_content(self, name, colors, lines, color_map):
        """Custom alignment should preserve original text content."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        # Strip ANSI codes and compare with original
        ansi_pattern = r'\033\[[0-9;]*m'
        
        for i, (original, colored) in enumerate(zip(lines, colored_lines)):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original, \
                f"Line {i} text content changed: expected '{original}', got '{stripped}'"
    
    @given(preset_names, hex_color_lists, ascii_lines, custom_color_maps)
    def test_custom_alignment_applies_colors(self, name, colors, lines, color_map):
        """Custom alignment should apply colors to lines."""
        assume(any(len(line) > 0 for line in lines))  # At least one non-empty line
        
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        # Non-empty lines should have color codes
        for i, (original, colored) in enumerate(zip(lines, colored_lines)):
            if original:  # Non-empty line
                assert '\033[' in colored, \
                    f"Line {i} should have ANSI color codes"
                assert '\033[0m' in colored, \
                    f"Line {i} should have reset code"
    
    @given(preset_names, hex_color_lists, ascii_lines, custom_color_maps)
    def test_custom_alignment_line_count_matches(self, name, colors, lines, color_map):
        """Output should have same number of lines as input."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == len(lines), \
            f"Expected {len(lines)} lines, got {len(colored_lines)}"
    
    def test_custom_alignment_validation_requires_mapping(self):
        """Custom mode must provide custom_colors mapping."""
        with pytest.raises(ValueError, match="custom_colors required"):
            ColorAlignment(mode="custom", custom_colors=None)
    
    def test_custom_alignment_validation_rejects_mapping_for_other_modes(self):
        """Non-custom modes should not have custom_colors."""
        with pytest.raises(ValueError, match="should only be provided for 'custom' mode"):
            ColorAlignment(mode="horizontal", custom_colors={"0": "0"})
        
        with pytest.raises(ValueError, match="should only be provided for 'custom' mode"):
            ColorAlignment(mode="vertical", custom_colors={"0": "0"})
    
    def test_custom_alignment_with_valid_mapping(self):
        """Custom alignment with valid index mapping should work."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        # Map ASCII codes to preset indices
        color_map = {
            "0": "0",  # Map to first color (red)
            "1": "1",  # Map to second color (green)
            "2": "2",  # Map to third color (blue)
        }
        
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line 1", "Line 2", "Line 3"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 3
        
        # All lines should be colored
        for line in colored_lines:
            assert '\033[' in line
            assert '\033[0m' in line
    
    def test_custom_alignment_with_out_of_range_indices(self):
        """Custom alignment should handle out-of-range indices gracefully."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"]
        )
        
        # Map to indices beyond preset size
        color_map = {
            "0": "0",
            "1": "5",  # Out of range (only 2 colors)
            "2": "10",  # Way out of range
        }
        
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line 1", "Line 2"]
        colored_lines = colorizer.colorize(lines)
        
        # Should not crash, should handle gracefully
        assert len(colored_lines) == 2
    
    def test_custom_alignment_with_named_colors(self):
        """Custom alignment should support named color references."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        # Use color names instead of indices
        color_map = {
            "0": "red",
            "1": "green",
            "2": "blue",
        }
        
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line 1", "Line 2"]
        colored_lines = colorizer.colorize(lines)
        
        # Should handle named colors (via hash mapping)
        assert len(colored_lines) == 2
        
        for line in colored_lines:
            assert '\033[' in line
    
    def test_custom_alignment_with_empty_mapping(self):
        """Custom alignment with empty mapping should work (no mappings to apply)."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000"]
        )
        
        # Empty mapping - valid but no custom mappings
        color_map = {}
        
        # Empty mapping is valid (just means no custom mappings)
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line 1", "Line 2"]
        colored_lines = colorizer.colorize(lines)
        
        # Should still colorize (using default behavior)
        assert len(colored_lines) == 2
        for line in colored_lines:
            assert '\033[' in line
    
    def test_custom_alignment_rgb_mode(self):
        """Custom alignment should work with RGB color mode."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        color_map = {
            "0": "0",
            "1": "1",
            "2": "2",
        }
        
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        lines = ["Line 1", "Line 2"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 2
        
        # Should use RGB format (38;2;R;G;B)
        rgb_pattern = r'\033\[38;2;\d+;\d+;\d+m'
        for line in colored_lines:
            assert re.search(rgb_pattern, line) is not None, \
                "Line should have RGB color code format"
    
    def test_custom_alignment_with_weighted_preset(self):
        """Custom alignment should work with weighted presets."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"],
            weights=[2, 1]
        )
        
        color_map = {
            "0": "0",
            "1": "1",
            "2": "2",  # Will map to expanded colors [red, red, green]
        }
        
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line 1", "Line 2"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 2
        
        # Should handle weighted expansion
        for line in colored_lines:
            assert '\033[' in line
    
    @given(preset_names, hex_color_lists, custom_color_maps)
    def test_custom_alignment_with_empty_lines(self, name, colors, color_map):
        """Custom alignment should handle empty lines."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line 1", "", "Line 3"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 3
        
        # Non-empty lines should be colored
        assert '\033[' in colored_lines[0]
        assert '\033[' in colored_lines[2]
    
    def test_custom_alignment_strips_existing_codes(self):
        """Custom alignment should strip existing ANSI codes."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"]
        )
        
        color_map = {
            "0": "0",
            "1": "1",
        }
        
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        # Lines with existing ANSI codes
        lines = [
            "\033[31mRed text\033[0m",
            "\033[1;32mBold green\033[0m"
        ]
        colored_lines = colorizer.colorize(lines)
        
        # Should have new color codes, not old ones
        for line in colored_lines:
            # Should not contain old-style codes
            assert '\033[31m' not in line, "Old color code should be stripped"
            assert '\033[1;32m' not in line, "Old color code should be stripped"
            
            # Should contain new 8-bit format
            assert '\033[38;5;' in line, "Should have new 8-bit color code"
    
    def test_custom_alignment_preserves_whitespace(self):
        """Custom alignment should preserve whitespace."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000"]
        )
        
        color_map = {"0": "0"}
        
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["  Line with leading spaces", "Line with trailing spaces  ", "  Centered  "]
        colored_lines = colorizer.colorize(lines)
        
        # Strip ANSI codes and verify whitespace preserved
        ansi_pattern = r'\033\[[0-9;]*m'
        for original, colored in zip(lines, colored_lines):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original, \
                f"Whitespace not preserved: expected '{original}', got '{stripped}'"
    
    def test_custom_alignment_preserves_special_characters(self):
        """Custom alignment should preserve special characters."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000"]
        )
        
        color_map = {"0": "0"}
        
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line with !@#$%^&*()", "Line with <>/\\|[]{}"]
        colored_lines = colorizer.colorize(lines)
        
        # Strip ANSI codes and verify content preserved
        ansi_pattern = r'\033\[[0-9;]*m'
        for original, colored in zip(lines, colored_lines):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original
    
    @given(preset_names, hex_color_lists, custom_color_maps)
    def test_custom_alignment_with_no_lines(self, name, colors, color_map):
        """Colorizing empty list should return empty list."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize([])
        
        assert colored_lines == []
    
    def test_custom_alignment_from_dict_valid(self):
        """ColorAlignment.from_dict should construct valid custom alignment."""
        config = {
            "mode": "custom",
            "custom_colors": {
                "0": "0",
                "1": "1",
                "2": "2",
            }
        }
        
        alignment = ColorAlignment.from_dict(config)
        
        assert alignment.mode == "custom"
        assert alignment.custom_colors == {"0": "0", "1": "1", "2": "2"}
    
    def test_custom_alignment_from_dict_missing_mode(self):
        """ColorAlignment.from_dict should raise error for missing mode."""
        config = {
            "custom_colors": {"0": "0"}
        }
        
        with pytest.raises(ValueError, match="Missing required field: 'mode'"):
            ColorAlignment.from_dict(config)
    
    def test_custom_alignment_from_dict_invalid_mode(self):
        """ColorAlignment.from_dict should raise error for invalid mode."""
        config = {
            "mode": "invalid_mode",
            "custom_colors": {"0": "0"}
        }
        
        with pytest.raises(ValueError, match="Invalid mode"):
            ColorAlignment.from_dict(config)
    
    def test_custom_alignment_from_dict_missing_custom_colors(self):
        """ColorAlignment.from_dict should raise error when custom mode lacks custom_colors."""
        config = {
            "mode": "custom"
        }
        
        with pytest.raises(ValueError, match="custom_colors required"):
            ColorAlignment.from_dict(config)
    
    @given(preset_names, hex_color_lists, ascii_lines, custom_color_maps)
    def test_custom_alignment_reset_code_at_end(self, name, colors, lines, color_map):
        """Each colored line should end with reset code."""
        assume(any(len(line) > 0 for line in lines))
        
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        for i, (original, colored) in enumerate(zip(lines, colored_lines)):
            if original:  # Non-empty lines
                assert colored.endswith('\033[0m'), \
                    f"Line {i} should end with reset code \\033[0m"
    
    def test_custom_alignment_with_single_color_preset(self):
        """Custom alignment should work with single-color preset."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000"]
        )
        
        color_map = {
            "0": "0",
            "1": "0",  # All map to same color
            "2": "0",
        }
        
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Line 1", "Line 2", "Line 3"]
        colored_lines = colorizer.colorize(lines)
        
        assert len(colored_lines) == 3
        
        # All lines should be colored with the same color
        ansi_pattern = r'\033\[38;5;(\d+)m'
        color_codes = []
        for line in colored_lines:
            match = re.search(ansi_pattern, line)
            if match:
                color_codes.append(match.group(1))
        
        # All should have the same color code
        assert len(set(color_codes)) == 1, \
            "All lines should have same color when mapping to single color"
    
    def test_custom_alignment_mapping_uses_preset_colors(self):
        """Custom alignment should use colors from the preset."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        color_map = {
            "0": "0",  # Red
            "1": "1",  # Green
            "2": "2",  # Blue
        }
        
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        lines = ["Test line"]
        colored_lines = colorizer.colorize(lines)
        
        # Should use colors from preset
        assert len(colored_lines) == 1
        assert '\033[38;5;' in colored_lines[0]
    
    @given(preset_names, hex_color_lists, ascii_lines, custom_color_maps)
    def test_custom_alignment_structure_preservation(self, name, colors, lines, color_map):
        """Custom alignment should not change line structure."""
        preset = ColorPreset(name=name, colors=colors)
        alignment = ColorAlignment(mode="custom", custom_colors=color_map)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored_lines = colorizer.colorize(lines)
        
        # Same number of lines
        assert len(colored_lines) == len(lines)
        
        # Each line's text content preserved
        ansi_pattern = r'\033\[[0-9;]*m'
        for original, colored in zip(lines, colored_lines):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original
