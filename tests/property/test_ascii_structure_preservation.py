"""
Property-based tests for ASCII structure preservation during colorization.

Tests Property 29 from the design document.
"""

import pytest
import re
from hypothesis import given, strategies as st, assume
from src.ascii_renderer import ColorAlignment, ASCIIColorizer
from src.color_presets import ColorPreset
from src.color_util import RGB


# Strategy for generating valid ASCII art lines
ascii_line = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Ps', 'Pe', 'Po', 'Sm', 'Zs'),
        min_codepoint=32,
        max_codepoint=126
    ),
    min_size=0,
    max_size=80
)

# Strategy for generating lists of ASCII art lines
ascii_art = st.lists(ascii_line, min_size=1, max_size=20)

# Strategy for generating color presets
color_preset_colors = st.lists(
    st.sampled_from([
        "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
        "#FF8800", "#8800FF", "#00FF88", "#88FF00", "#0088FF", "#FF0088"
    ]),
    min_size=1,
    max_size=10
)

# Strategy for generating alignment modes
alignment_mode = st.sampled_from(["horizontal", "vertical"])

# Strategy for generating ANSI modes
ansi_mode = st.sampled_from(["rgb", "8bit", "ansi", "default"])


def strip_ansi_codes(text: str) -> str:
    """Remove all ANSI escape sequences from text.
    
    Args:
        text: Text potentially containing ANSI codes
        
    Returns:
        Text with all ANSI codes removed
    """
    ansi_pattern = r'\033\[[0-9;]*m|\x1b\[[0-9;]*m'
    return re.sub(ansi_pattern, '', text)


class TestProperty29_ASCIIStructurePreservation:
    """Property 29: ASCII Structure Preservation
    
    For any ASCII art, colorization should not change the text content or whitespace
    structure—only ANSI color codes should be added.
    """
    
    @given(
        lines=ascii_art,
        colors=color_preset_colors,
        mode=alignment_mode,
        ansi=ansi_mode
    )
    def test_colorization_preserves_text_content(self, lines, colors, mode, ansi):
        """Colorization should preserve exact text content of ASCII art."""
        # Create preset and alignment
        preset = ColorPreset(name="test", colors=colors)
        alignment = ColorAlignment(mode=mode)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode=ansi)
        
        # Colorize the ASCII art
        result = colorizer.colorize(lines)
        
        # Should have same number of lines
        assert len(result) == len(lines), \
            f"Line count changed: expected {len(lines)}, got {len(result)}"
        
        # Strip ANSI codes and verify text is unchanged
        for i, (original, colored) in enumerate(zip(lines, result)):
            stripped = strip_ansi_codes(colored)
            assert stripped == original, \
                f"Line {i} text changed: expected '{original}', got '{stripped}'"
    
    @given(
        lines=ascii_art,
        colors=color_preset_colors
    )
    def test_horizontal_alignment_preserves_structure(self, lines, colors):
        """Horizontal alignment should preserve ASCII structure."""
        preset = ColorPreset(name="test", colors=colors)
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        result = colorizer.colorize(lines)
        
        # Verify structure preservation
        for original, colored in zip(lines, result):
            stripped = strip_ansi_codes(colored)
            assert stripped == original, "Horizontal alignment changed text content"
            
            # Verify line length (with ANSI codes) is greater than or equal to original
            # (ANSI codes add characters, but stripped should match)
            assert len(colored) >= len(original), \
                "Colored line should be at least as long as original (includes ANSI codes)"
    
    @given(
        lines=ascii_art,
        colors=color_preset_colors
    )
    def test_vertical_alignment_preserves_structure(self, lines, colors):
        """Vertical alignment should preserve ASCII structure."""
        preset = ColorPreset(name="test", colors=colors)
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        result = colorizer.colorize(lines)
        
        # Verify structure preservation
        for original, colored in zip(lines, result):
            stripped = strip_ansi_codes(colored)
            assert stripped == original, "Vertical alignment changed text content"
    
    @given(
        lines=ascii_art,
        colors=color_preset_colors,
        mode=alignment_mode
    )
    def test_whitespace_preservation(self, lines, colors, mode):
        """Colorization should preserve all whitespace characters."""
        # Filter to lines that contain whitespace
        whitespace_lines = [line for line in lines if ' ' in line or '\t' in line]
        assume(len(whitespace_lines) > 0)
        
        preset = ColorPreset(name="test", colors=colors)
        alignment = ColorAlignment(mode=mode)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        result = colorizer.colorize(whitespace_lines)
        
        # Verify whitespace is preserved
        for original, colored in zip(whitespace_lines, result):
            stripped = strip_ansi_codes(colored)
            
            # Count spaces in original and stripped
            original_spaces = original.count(' ')
            stripped_spaces = stripped.count(' ')
            assert original_spaces == stripped_spaces, \
                f"Space count changed: expected {original_spaces}, got {stripped_spaces}"
            
            # Count tabs in original and stripped
            original_tabs = original.count('\t')
            stripped_tabs = stripped.count('\t')
            assert original_tabs == stripped_tabs, \
                f"Tab count changed: expected {original_tabs}, got {stripped_tabs}"
    
    @given(
        lines=ascii_art,
        colors=color_preset_colors,
        mode=alignment_mode
    )
    def test_character_order_preservation(self, lines, colors, mode):
        """Colorization should preserve character order."""
        # Filter to non-empty lines
        non_empty_lines = [line for line in lines if line.strip()]
        assume(len(non_empty_lines) > 0)
        
        preset = ColorPreset(name="test", colors=colors)
        alignment = ColorAlignment(mode=mode)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        result = colorizer.colorize(non_empty_lines)
        
        # Verify character order is preserved
        for original, colored in zip(non_empty_lines, result):
            stripped = strip_ansi_codes(colored)
            
            # Characters should appear in same order
            assert list(stripped) == list(original), \
                "Character order changed during colorization"
    
    @given(
        lines=ascii_art,
        colors=color_preset_colors,
        mode=alignment_mode
    )
    def test_empty_lines_preserved(self, lines, colors, mode):
        """Empty lines should remain empty (except for ANSI codes)."""
        # Add some empty lines to the input
        lines_with_empty = lines + ["", "  ", ""]
        
        preset = ColorPreset(name="test", colors=colors)
        alignment = ColorAlignment(mode=mode)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        result = colorizer.colorize(lines_with_empty)
        
        # Verify empty lines remain empty after stripping ANSI codes
        for i, (original, colored) in enumerate(zip(lines_with_empty, result)):
            stripped = strip_ansi_codes(colored)
            assert stripped == original, \
                f"Line {i} changed: expected '{original}', got '{stripped}'"
    
    @given(
        lines=ascii_art,
        colors=color_preset_colors
    )
    def test_special_characters_preserved(self, lines, colors):
        """Special ASCII characters should be preserved."""
        # Add lines with special characters
        special_lines = lines + [
            "╔═══════════╗",
            "║  BOX ART  ║",
            "╚═══════════╝",
            "┌─┬─┐",
            "│ │ │",
            "└─┴─┘"
        ]
        
        preset = ColorPreset(name="test", colors=colors)
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        result = colorizer.colorize(special_lines)
        
        # Verify special characters are preserved
        for original, colored in zip(special_lines, result):
            stripped = strip_ansi_codes(colored)
            assert stripped == original, \
                f"Special characters changed: expected '{original}', got '{stripped}'"
    
    @given(
        lines=ascii_art,
        colors=color_preset_colors,
        mode=alignment_mode
    )
    def test_line_boundaries_preserved(self, lines, colors, mode):
        """Line boundaries should be preserved (no line merging or splitting)."""
        assume(len(lines) > 1)
        
        preset = ColorPreset(name="test", colors=colors)
        alignment = ColorAlignment(mode=mode)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        result = colorizer.colorize(lines)
        
        # Should have exact same number of lines
        assert len(result) == len(lines), \
            "Line count changed - lines were merged or split"
        
        # No line should contain newline characters (except at end if added)
        for i, line in enumerate(result):
            stripped = strip_ansi_codes(line)
            assert '\n' not in stripped, \
                f"Line {i} contains unexpected newline character"
    
    @given(
        lines=ascii_art,
        colors=color_preset_colors,
        mode=alignment_mode,
        ansi=ansi_mode
    )
    def test_only_ansi_codes_added(self, lines, colors, mode, ansi):
        """Only ANSI escape codes should be added, no other characters."""
        preset = ColorPreset(name="test", colors=colors)
        alignment = ColorAlignment(mode=mode)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode=ansi)
        
        result = colorizer.colorize(lines)
        
        for original, colored in zip(lines, result):
            # Remove ANSI codes
            stripped = strip_ansi_codes(colored)
            
            # Stripped version should exactly match original
            assert stripped == original, \
                "Non-ANSI characters were added or removed"
            
            # If colored is longer than original, the difference should only be ANSI codes
            if len(colored) > len(original):
                # The extra characters should be ANSI escape sequences
                # Pattern: \033[...m
                ansi_pattern = r'\033\[[0-9;]*m'
                ansi_codes = re.findall(ansi_pattern, colored)
                
                # Should have found at least one ANSI code
                assert len(ansi_codes) > 0, \
                    "Colored line is longer but contains no ANSI codes"
    
    @given(
        lines=st.lists(
            st.text(
                alphabet=st.characters(min_codepoint=32, max_codepoint=126),
                min_size=1,
                max_size=50
            ),
            min_size=1,
            max_size=10
        ),
        colors=color_preset_colors
    )
    def test_ascii_art_with_existing_ansi_codes(self, lines, colors):
        """ASCII art with existing ANSI codes should have them stripped and replaced."""
        # Add ANSI codes to some lines
        lines_with_ansi = [
            f"\033[38;5;196m{line}\033[0m" if i % 2 == 0 else line
            for i, line in enumerate(lines)
        ]
        
        preset = ColorPreset(name="test", colors=colors)
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        result = colorizer.colorize(lines_with_ansi)
        
        # Verify original text is preserved (without the old ANSI codes)
        for original, colored in zip(lines, result):
            stripped = strip_ansi_codes(colored)
            assert stripped == original, \
                "Original text not preserved after stripping old ANSI codes"


class TestStructurePreservationEdgeCases:
    """Edge case tests for structure preservation."""
    
    def test_single_character_lines(self):
        """Single character lines should be preserved."""
        lines = ["A", "B", "C"]
        preset = ColorPreset(name="test", colors=["#FF0000"])
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        result = colorizer.colorize(lines)
        
        for original, colored in zip(lines, result):
            stripped = strip_ansi_codes(colored)
            assert stripped == original
    
    def test_very_long_lines(self):
        """Very long lines should be preserved."""
        lines = ["A" * 200, "B" * 200]
        preset = ColorPreset(name="test", colors=["#FF0000", "#00FF00"])
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        result = colorizer.colorize(lines)
        
        for original, colored in zip(lines, result):
            stripped = strip_ansi_codes(colored)
            assert stripped == original
    
    def test_mixed_length_lines(self):
        """Lines of varying lengths should all be preserved."""
        lines = [
            "Short",
            "Medium length line",
            "Very long line with lots of characters here",
            "X"
        ]
        preset = ColorPreset(name="test", colors=["#FF0000", "#00FF00", "#0000FF"])
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        result = colorizer.colorize(lines)
        
        for original, colored in zip(lines, result):
            stripped = strip_ansi_codes(colored)
            assert stripped == original
    
    def test_unicode_box_drawing_characters(self):
        """Unicode box drawing characters should be preserved."""
        lines = [
            "┌─────────┐",
            "│ Content │",
            "└─────────┘"
        ]
        preset = ColorPreset(name="test", colors=["#FF0000"])
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        result = colorizer.colorize(lines)
        
        for original, colored in zip(lines, result):
            stripped = strip_ansi_codes(colored)
            assert stripped == original
    
    def test_lines_with_only_whitespace(self):
        """Lines with only whitespace should be preserved."""
        lines = ["   ", "\t\t", "  \t  "]
        preset = ColorPreset(name="test", colors=["#FF0000"])
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        result = colorizer.colorize(lines)
        
        for original, colored in zip(lines, result):
            stripped = strip_ansi_codes(colored)
            assert stripped == original
    
    def test_empty_preset_preserves_structure(self):
        """Even with empty preset, structure should be preserved."""
        lines = ["Line 1", "Line 2", "Line 3"]
        preset = ColorPreset(name="test", colors=["#FF0000"])
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        # Mock expand_colors to return empty list
        original_expand = preset.expand_colors
        preset.expand_colors = lambda: []
        
        result = colorizer.colorize(lines)
        
        # Should return original lines unchanged
        assert result == lines
        
        # Restore original method
        preset.expand_colors = original_expand
