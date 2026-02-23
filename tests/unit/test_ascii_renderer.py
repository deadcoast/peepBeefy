"""Unit tests for ASCII renderer module."""

import pytest
from src.ascii_renderer import ColorAlignment, ASCIIColorizer
from src.color_presets import ColorPreset
from src.color_util import RGB


class TestColorAlignment:
    """Tests for ColorAlignment dataclass."""
    
    def test_horizontal_mode(self):
        """Test horizontal alignment mode creation."""
        alignment = ColorAlignment(mode="horizontal")
        assert alignment.mode == "horizontal"
        assert alignment.custom_colors is None
    
    def test_vertical_mode(self):
        """Test vertical alignment mode creation."""
        alignment = ColorAlignment(mode="vertical")
        assert alignment.mode == "vertical"
        assert alignment.custom_colors is None
    
    def test_custom_mode_requires_custom_colors(self):
        """Test that custom mode requires custom_colors."""
        with pytest.raises(ValueError, match="custom_colors required"):
            ColorAlignment(mode="custom")
    
    def test_custom_mode_with_colors(self):
        """Test custom mode with color mapping."""
        custom_colors = {"0": "0", "1": "1"}
        alignment = ColorAlignment(mode="custom", custom_colors=custom_colors)
        assert alignment.mode == "custom"
        assert alignment.custom_colors == custom_colors
    
    def test_non_custom_mode_rejects_custom_colors(self):
        """Test that non-custom modes reject custom_colors."""
        with pytest.raises(ValueError, match="should only be provided for 'custom' mode"):
            ColorAlignment(mode="horizontal", custom_colors={"0": "0"})
    
    def test_from_dict_horizontal(self):
        """Test from_dict with horizontal mode."""
        d = {"mode": "horizontal"}
        alignment = ColorAlignment.from_dict(d)
        assert alignment.mode == "horizontal"
        assert alignment.custom_colors is None
    
    def test_from_dict_custom(self):
        """Test from_dict with custom mode."""
        d = {"mode": "custom", "custom_colors": {"0": "0"}}
        alignment = ColorAlignment.from_dict(d)
        assert alignment.mode == "custom"
        assert alignment.custom_colors == {"0": "0"}
    
    def test_from_dict_missing_mode(self):
        """Test from_dict with missing mode field."""
        with pytest.raises(ValueError, match="Missing required field: 'mode'"):
            ColorAlignment.from_dict({})
    
    def test_from_dict_invalid_mode(self):
        """Test from_dict with invalid mode value."""
        with pytest.raises(ValueError, match="Invalid mode"):
            ColorAlignment.from_dict({"mode": "invalid"})


class TestASCIIColorizer:
    """Tests for ASCIIColorizer class."""
    
    @pytest.fixture
    def simple_preset(self):
        """Create a simple color preset for testing."""
        return ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
    
    @pytest.fixture
    def sample_ascii(self):
        """Sample ASCII art for testing."""
        return [
            "  ___  ",
            " /   \\ ",
            "|     |",
            " \\___/ "
        ]
    
    def test_colorize_empty_lines(self, simple_preset):
        """Test colorizing empty line list."""
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(simple_preset, alignment)
        result = colorizer.colorize([])
        assert result == []
    
    def test_strip_neofetch_codes(self, simple_preset):
        """Test stripping ANSI codes from lines."""
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(simple_preset, alignment)
        
        line_with_codes = "\033[38;5;196mRed text\033[0m"
        stripped = colorizer.strip_neofetch_codes(line_with_codes)
        assert stripped == "Red text"
        
        line_with_x1b = "\x1b[38;5;196mRed text\x1b[0m"
        stripped = colorizer.strip_neofetch_codes(line_with_x1b)
        assert stripped == "Red text"
    
    def test_colorize_horizontal(self, simple_preset, sample_ascii):
        """Test horizontal color alignment."""
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(simple_preset, alignment, ansi_mode="rgb")
        
        result = colorizer.colorize(sample_ascii)
        
        # Should have same number of lines
        assert len(result) == len(sample_ascii)
        
        # Each line should have ANSI codes
        for line in result:
            assert "\033[" in line
            assert "\033[0m" in line
        
        # Lines should cycle through colors
        # First line gets first color (red)
        assert "\033[38;2;255;0;0m" in result[0]
        # Second line gets second color (green)
        assert "\033[38;2;0;255;0m" in result[1]
        # Third line gets third color (blue)
        assert "\033[38;2;0;0;255m" in result[2]
        # Fourth line cycles back to first color (red)
        assert "\033[38;2;255;0;0m" in result[3]
    
    def test_colorize_vertical(self, simple_preset, sample_ascii):
        """Test vertical color alignment."""
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(simple_preset, alignment, ansi_mode="rgb")
        
        result = colorizer.colorize(sample_ascii)
        
        # Should have same number of lines
        assert len(result) == len(sample_ascii)
        
        # Each line should have ANSI codes
        for line in result:
            assert "\033[" in line
            assert "\033[0m" in line
        
        # Each character should potentially have its own color
        # (gradient across width)
        for line in result:
            # Count ANSI escape sequences
            ansi_count = line.count("\033[38;2;")
            # Should have multiple color codes for gradient effect
            assert ansi_count > 0
    
    def test_colorize_custom(self, simple_preset):
        """Test custom color alignment."""
        custom_colors = {"0": "0", "1": "1"}
        alignment = ColorAlignment(mode="custom", custom_colors=custom_colors)
        colorizer = ASCIIColorizer(simple_preset, alignment, ansi_mode="rgb")
        
        sample = ["Line 1", "Line 2"]
        result = colorizer.colorize(sample)
        
        # Should have same number of lines
        assert len(result) == len(sample)
        
        # Lines should have ANSI codes
        for line in result:
            assert "\033[" in line
    
    def test_colorize_preserves_structure(self, simple_preset, sample_ascii):
        """Test that colorization preserves ASCII structure."""
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(simple_preset, alignment)
        
        result = colorizer.colorize(sample_ascii)
        
        # Strip ANSI codes and verify text is unchanged
        import re
        ansi_pattern = r'\033\[[0-9;]*m'
        
        for original, colored in zip(sample_ascii, result):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original
    
    def test_colorize_with_8bit_mode(self, simple_preset, sample_ascii):
        """Test colorization with 8-bit ANSI mode."""
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(simple_preset, alignment, ansi_mode="8bit")
        
        result = colorizer.colorize(sample_ascii)
        
        # Should use 8-bit ANSI codes (38;5;N format)
        for line in result:
            assert "\033[38;5;" in line
    
    def test_colorize_cycles_colors(self, simple_preset):
        """Test that horizontal mode cycles through colors."""
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(simple_preset, alignment, ansi_mode="rgb")
        
        # Create more lines than colors
        many_lines = [f"Line {i}" for i in range(10)]
        result = colorizer.colorize(many_lines)
        
        # Should cycle through the 3 colors
        # Lines 0, 3, 6, 9 should have same color (red)
        assert "\033[38;2;255;0;0m" in result[0]
        assert "\033[38;2;255;0;0m" in result[3]
        assert "\033[38;2;255;0;0m" in result[6]
        assert "\033[38;2;255;0;0m" in result[9]
    
    def test_empty_preset_returns_uncolored(self, sample_ascii):
        """Test that empty preset returns uncolored lines."""
        # Create preset with no colors (should fail validation)
        # Instead, test with preset that has colors but we mock expand_colors
        alignment = ColorAlignment(mode="horizontal")
        preset = ColorPreset(name="empty", colors=["#FF0000"])
        colorizer = ASCIIColorizer(preset, alignment)
        
        # Mock expand_colors to return empty list
        original_expand = preset.expand_colors
        preset.expand_colors = lambda: []
        
        result = colorizer.colorize(sample_ascii)
        
        # Should return original lines unchanged
        assert result == sample_ascii
        
        # Restore original method
        preset.expand_colors = original_expand


class TestIntegration:
    """Integration tests for ASCII renderer."""
    
    def test_full_pipeline_horizontal(self):
        """Test complete pipeline with horizontal alignment."""
        preset = ColorPreset(
            name="rainbow",
            colors=["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#9400D3"]
        )
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        ascii_art = [
            "╔═══════════════╗",
            "║   PEEPBEEFY   ║",
            "║   ASCII ART   ║",
            "╚═══════════════╝"
        ]
        
        result = colorizer.colorize(ascii_art)
        
        # Verify structure preserved
        import re
        ansi_pattern = r'\033\[[0-9;]*m'
        for original, colored in zip(ascii_art, result):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original
        
        # Verify colors applied
        for line in result:
            assert "\033[38;2;" in line
            assert "\033[0m" in line
    
    def test_full_pipeline_vertical(self):
        """Test complete pipeline with vertical alignment."""
        preset = ColorPreset(
            name="fire",
            colors=["#FF0000", "#FF7F00", "#FFFF00"]
        )
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        ascii_art = [
            "  *  ",
            " *** ",
            "*****"
        ]
        
        result = colorizer.colorize(ascii_art)
        
        # Verify structure preserved
        import re
        ansi_pattern = r'\033\[[0-9;]*m'
        for original, colored in zip(ascii_art, result):
            stripped = re.sub(ansi_pattern, '', colored)
            assert stripped == original
        
        # Verify 8-bit codes used
        for line in result:
            assert "\033[38;5;" in line
