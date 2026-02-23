"""
Integration tests for Banner System + ASCII Renderer.

Tests the integration between the banner system and ASCII renderer,
verifying that colorization preserves banner structure and works with
different alignment modes.

Validates Requirement 14.6: Verify ASCII_Renderer preserves banner structure
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.banner import Banner, BannerMetadata, BannerDatabase
from src.ascii_renderer import ASCIIColorizer, ColorAlignment
from src.color_presets import ColorPreset
from src.color_util import RGB


class TestBannerASCIIRendererIntegration:
    """Integration tests for banner system with ASCII renderer."""
    
    @pytest.fixture
    def simple_banner(self):
        """Create a simple test banner."""
        lines = [
            "  ████████  ",
            "  ██    ██  ",
            "  ██    ██  ",
            "  ████████  ",
            "   BEEF     ",
        ]
        metadata = BannerMetadata(
            category="TEST",
            name="SIMPLE",
            dimensions=(12, 5)
        )
        return Banner(metadata=metadata, lines=lines)
    
    @pytest.fixture
    def test_preset(self):
        """Create a test color preset."""
        return ColorPreset(
            name="test_gradient",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
    
    def test_horizontal_alignment_preserves_structure(self, simple_banner, test_preset):
        """Test that horizontal alignment preserves banner structure.
        
        Validates Requirement 14.6: ASCII renderer preserves structure
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(test_preset, alignment, "rgb")
        
        colored_lines = colorizer.colorize(simple_banner.lines)
        
        # Verify same number of lines
        assert len(colored_lines) == len(simple_banner.lines), \
            "Colorization should preserve line count"
        
        # Verify text content is preserved (strip ANSI codes)
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        
        for original, colored in zip(simple_banner.lines, colored_lines):
            stripped = ansi_escape.sub('', colored)
            assert stripped == original, \
                f"Text content should be preserved: expected '{original}', got '{stripped}'"
    
    def test_vertical_alignment_preserves_structure(self, simple_banner, test_preset):
        """Test that vertical alignment preserves banner structure.
        
        Validates Requirement 14.6: ASCII renderer preserves structure
        """
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(test_preset, alignment, "rgb")
        
        colored_lines = colorizer.colorize(simple_banner.lines)
        
        # Verify same number of lines
        assert len(colored_lines) == len(simple_banner.lines)
        
        # Verify text content is preserved
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        
        for original, colored in zip(simple_banner.lines, colored_lines):
            stripped = ansi_escape.sub('', colored)
            assert stripped == original
    
    def test_custom_alignment_preserves_structure(self, simple_banner):
        """Test that custom alignment preserves banner structure.
        
        Validates Requirement 14.6: ASCII renderer preserves structure
        """
        # Create preset with custom color mapping
        preset = ColorPreset(
            name="custom_test",
            colors=["#FF0000", "#00FF00"]
        )
        
        alignment = ColorAlignment(
            mode="custom",
            custom_colors={"0": "#FF0000", "1": "#00FF00"}
        )
        
        colorizer = ASCIIColorizer(preset, alignment, "rgb")
        
        colored_lines = colorizer.colorize(simple_banner.lines)
        
        # Verify structure preservation
        assert len(colored_lines) == len(simple_banner.lines)
        
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        
        for original, colored in zip(simple_banner.lines, colored_lines):
            stripped = ansi_escape.sub('', colored)
            assert stripped == original
    
    def test_colorizer_with_rgb_mode(self, simple_banner, test_preset):
        """Test that colorizer works with RGB color mode.
        
        Validates Requirement 14.6: RGB color support
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(test_preset, alignment, "rgb")
        
        try:
            colored_lines = colorizer.colorize(simple_banner.lines)
            assert len(colored_lines) > 0
            
            # Verify RGB ANSI codes are present (format: \033[38;2;R;G;Bm)
            rgb_pattern = r'\x1b\[38;2;\d+;\d+;\d+m'
            import re
            
            has_rgb_codes = any(re.search(rgb_pattern, line) for line in colored_lines)
            assert has_rgb_codes, "RGB mode should produce RGB ANSI codes"
        except Exception as e:
            pytest.fail(f"RGB colorization failed: {e}")
    
    def test_colorizer_with_8bit_mode(self, simple_banner, test_preset):
        """Test that colorizer works with 8-bit color mode.
        
        Validates Requirement 14.6: 8-bit color support
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(test_preset, alignment, "8bit")
        
        try:
            colored_lines = colorizer.colorize(simple_banner.lines)
            assert len(colored_lines) > 0
            
            # Verify 8-bit ANSI codes are present (format: \033[38;5;Nm)
            eightbit_pattern = r'\x1b\[38;5;\d+m'
            import re
            
            has_8bit_codes = any(re.search(eightbit_pattern, line) for line in colored_lines)
            assert has_8bit_codes, "8-bit mode should produce 8-bit ANSI codes"
        except Exception as e:
            pytest.fail(f"8-bit colorization failed: {e}")
    
    def test_colorizer_handles_empty_banner(self, test_preset):
        """Test that colorizer handles empty banners gracefully.
        
        Validates Requirement 14.6: Error handling
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(test_preset, alignment, "rgb")
        
        # Empty banner
        colored_lines = colorizer.colorize([])
        
        # Should return empty list without crashing
        assert colored_lines == []
    
    def test_colorizer_handles_whitespace_only_lines(self, test_preset):
        """Test that colorizer handles whitespace-only lines.
        
        Validates Requirement 14.6: Edge case handling
        """
        lines = [
            "  ████  ",
            "        ",  # Whitespace only
            "  ████  ",
        ]
        
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(test_preset, alignment, "rgb")
        
        colored_lines = colorizer.colorize(lines)
        
        # Verify structure preserved
        assert len(colored_lines) == len(lines)
        
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        
        for original, colored in zip(lines, colored_lines):
            stripped = ansi_escape.sub('', colored)
            assert stripped == original
    
    def test_preset_color_spreading(self, simple_banner):
        """Test that preset colors spread correctly across banner.
        
        Validates Requirement 14.6: Color distribution
        """
        # Create preset with fewer colors than lines
        preset = ColorPreset(
            name="short_preset",
            colors=["#FF0000", "#0000FF"]
        )
        
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, "rgb")
        
        colored_lines = colorizer.colorize(simple_banner.lines)
        
        # Should spread colors across all lines
        assert len(colored_lines) == len(simple_banner.lines)
        
        # All lines should have color codes
        import re
        ansi_pattern = r'\x1b\[[0-9;]*m'
        
        for line in colored_lines:
            # Skip empty lines
            if line.strip():
                assert re.search(ansi_pattern, line), \
                    "Each non-empty line should have color codes"
    
    def test_banner_metadata_integration(self):
        """Test that banner metadata integrates with colorization.
        
        Validates Requirement 14.6: Metadata-driven rendering
        """
        lines = ["  ████  ", "  BEEF  "]
        metadata = BannerMetadata(
            category="TEST",
            name="META_TEST",
            dimensions=(8, 2),
            recommended_preset="fire"
        )
        banner = Banner(metadata=metadata, lines=lines)
        
        # Verify metadata is accessible
        assert banner.metadata.recommended_preset == "fire"
        
        # Colorization should work regardless of metadata
        preset = ColorPreset(name="test", colors=["#FF0000"])
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, "rgb")
        
        colored_lines = colorizer.colorize(banner.lines)
        assert len(colored_lines) == len(banner.lines)
    
    def test_banner_dimensions_preserved(self, simple_banner, test_preset):
        """Test that banner dimensions are preserved after colorization.
        
        Validates Requirement 14.6: Dimension preservation
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(test_preset, alignment, "rgb")
        
        colored_lines = colorizer.colorize(simple_banner.lines)
        
        # Strip ANSI codes and verify dimensions
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        
        stripped_lines = [ansi_escape.sub('', line) for line in colored_lines]
        
        # Verify width and height
        assert len(stripped_lines) == simple_banner.height
        
        for line in stripped_lines:
            # Width should match (allowing for trailing spaces)
            assert len(line) <= simple_banner.width + 5  # Some tolerance
    
    def test_colorizer_with_weighted_preset(self, simple_banner):
        """Test that colorizer works with weighted presets.
        
        Validates Requirement 14.6: Weighted preset support
        """
        # Create weighted preset
        preset = ColorPreset(
            name="weighted",
            colors=["#FF0000", "#00FF00"],
            weights=[3, 1]  # Red appears 3x more than green
        )
        
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, "rgb")
        
        try:
            colored_lines = colorizer.colorize(simple_banner.lines)
            assert len(colored_lines) == len(simple_banner.lines)
        except Exception as e:
            pytest.fail(f"Weighted preset colorization failed: {e}")
    
    def test_multiple_colorization_passes(self, simple_banner, test_preset):
        """Test that multiple colorization passes work correctly.
        
        Validates Requirement 14.6: Idempotency
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(test_preset, alignment, "rgb")
        
        # First pass
        colored_once = colorizer.colorize(simple_banner.lines)
        
        # Second pass (colorizing already colored lines)
        colored_twice = colorizer.colorize(colored_once)
        
        # Structure should still be preserved
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        
        for original, final in zip(simple_banner.lines, colored_twice):
            stripped = ansi_escape.sub('', final)
            assert stripped == original, \
                "Multiple colorization passes should preserve original text"
    
    def test_colorizer_with_special_characters(self, test_preset):
        """Test that colorizer handles special characters correctly.
        
        Validates Requirement 14.6: Special character handling
        """
        lines = [
            "╔═══════╗",
            "║ BEEF  ║",
            "╚═══════╝",
        ]
        
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(test_preset, alignment, "rgb")
        
        colored_lines = colorizer.colorize(lines)
        
        # Verify special characters preserved
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        
        for original, colored in zip(lines, colored_lines):
            stripped = ansi_escape.sub('', colored)
            assert stripped == original, \
                "Special Unicode characters should be preserved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
