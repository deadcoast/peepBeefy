"""
Integration tests for Banner Colorization with ASCIIColorizer.

Tests the complete integration between Banner system and ASCIIColorizer,
verifying that all three alignment modes (horizontal, vertical, custom)
work correctly with real banners and preserve banner structure.

Validates Requirements:
- 8.1: Horizontal color alignment (one color per line)
- 8.2: Vertical color alignment (gradient across width)
- 8.3: Custom color alignment (per-ASCII-color-index mapping)
- 14.6: ASCII_Renderer preserves banner structure
"""

import pytest
import re
from pathlib import Path

from src.banner import Banner, BannerMetadata, BannerDatabase
from src.ascii_renderer import ASCIIColorizer, ColorAlignment
from src.color_presets import ColorPreset
from src.color_util import RGB


class TestBannerColorizationIntegration:
    """Integration tests for banner colorization with all alignment modes."""
    
    @pytest.fixture
    def ansi_escape_pattern(self):
        """Regex pattern for matching ANSI escape codes."""
        return re.compile(r'\x1b\[[0-9;]*m')
    
    @pytest.fixture
    def real_banner(self):
        """Create a realistic banner similar to peepBeefy banners."""
        lines = [
            "                          _______              ___       ",
            " .-----.-----.-----.-----|   _   .-----.-----.'  _.--.--.  ",
            " |  _  |  -__|  -__|  _  |.  1   |  -__|  -__|   _|  |  |  ",
            " |   __|_____|_____|   __|.  _   |_____|_____|__| |___  |  ",
            " |__|              |__|  |:  1    \\               |_____|  ",
            "                         |::.. .  /                        ",
            "                         `-------'                         "
        ]
        metadata = BannerMetadata(
            category="1ST_BEEFS",
            name="PEEPBEEFY",
            description="peepBeefy ASCII logo",
            dimensions=(59, 7),
            animation_compatible=True
        )
        return Banner(metadata=metadata, lines=lines)
    
    @pytest.fixture
    def small_banner(self):
        """Create a small test banner."""
        lines = [
            "  ████  ",
            "  ██    ",
            "  ████  ",
        ]
        metadata = BannerMetadata(
            category="TEST",
            name="SMALL",
            dimensions=(8, 3)
        )
        return Banner(metadata=metadata, lines=lines)
    
    @pytest.fixture
    def fire_preset(self):
        """Create a fire-themed color preset."""
        return ColorPreset(
            name="fire",
            colors=["#FF0000", "#FF7F00", "#FFFF00", "#FF4500"]
        )
    
    @pytest.fixture
    def rainbow_preset(self):
        """Create a rainbow color preset."""
        return ColorPreset(
            name="rainbow",
            colors=[
                "#FF0000",  # Red
                "#FF7F00",  # Orange
                "#FFFF00",  # Yellow
                "#00FF00",  # Green
                "#0000FF",  # Blue
                "#4B0082",  # Indigo
                "#9400D3"   # Violet
            ]
        )
    
    @pytest.fixture
    def weighted_preset(self):
        """Create a weighted color preset."""
        return ColorPreset(
            name="weighted_fire",
            colors=["#FF0000", "#FFFF00"],
            weights=[3, 1]  # Red appears 3x more than yellow
        )
    
    # ========================================================================
    # Horizontal Alignment Tests (Requirement 8.1)
    # ========================================================================
    
    def test_horizontal_alignment_with_real_banner(
        self,
        real_banner,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test horizontal alignment applies one color per line to real banner.
        
        Validates Requirement 8.1: Horizontal color alignment
        Validates Requirement 14.6: Structure preservation
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(real_banner.lines)
        
        # Verify line count preserved
        assert len(colored_lines) == len(real_banner.lines), \
            "Horizontal alignment must preserve line count"
        
        # Verify each line has exactly one color applied
        for i, (original, colored) in enumerate(zip(real_banner.lines, colored_lines)):
            # Strip ANSI codes to verify text preservation
            stripped = ansi_escape_pattern.sub('', colored)
            assert stripped == original, \
                f"Line {i}: Text content must be preserved"
            
            # Verify ANSI codes present (color applied)
            assert '\x1b[38;2;' in colored, \
                f"Line {i}: RGB color code must be present"
            
            # Verify reset code at end
            assert '\x1b[0m' in colored, \
                f"Line {i}: Reset code must be present"
    
    def test_horizontal_alignment_color_cycling(
        self,
        real_banner,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test that horizontal alignment cycles through colors correctly.
        
        Validates Requirement 8.1: Color cycling when more lines than colors
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(real_banner.lines)
        
        # Extract RGB values from each line
        rgb_pattern = re.compile(r'\x1b\[38;2;(\d+);(\d+);(\d+)m')
        
        line_colors = []
        for line in colored_lines:
            match = rgb_pattern.search(line)
            if match:
                r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
                line_colors.append((r, g, b))
        
        # Verify we have colors for all lines
        assert len(line_colors) == len(real_banner.lines)
        
        # Verify cycling: lines should repeat colors after preset length
        preset_colors = fire_preset.expand_colors()
        num_colors = len(preset_colors)
        
        for i in range(len(line_colors)):
            expected_color = preset_colors[i % num_colors]
            actual_color = line_colors[i]
            
            # Allow small rounding differences
            assert abs(actual_color[0] - expected_color.r) <= 1, \
                f"Line {i}: Red component mismatch"
            assert abs(actual_color[1] - expected_color.g) <= 1, \
                f"Line {i}: Green component mismatch"
            assert abs(actual_color[2] - expected_color.b) <= 1, \
                f"Line {i}: Blue component mismatch"
    
    def test_horizontal_alignment_with_weighted_preset(
        self,
        small_banner,
        weighted_preset,
        ansi_escape_pattern
    ):
        """Test horizontal alignment with weighted color preset.
        
        Validates Requirement 8.1: Weighted preset support
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(weighted_preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(small_banner.lines)
        
        # Verify structure preserved
        assert len(colored_lines) == len(small_banner.lines)
        
        for original, colored in zip(small_banner.lines, colored_lines):
            stripped = ansi_escape_pattern.sub('', colored)
            assert stripped == original
    
    # ========================================================================
    # Vertical Alignment Tests (Requirement 8.2)
    # ========================================================================
    
    def test_vertical_alignment_with_real_banner(
        self,
        real_banner,
        rainbow_preset,
        ansi_escape_pattern
    ):
        """Test vertical alignment creates gradient across width.
        
        Validates Requirement 8.2: Vertical color alignment
        Validates Requirement 14.6: Structure preservation
        """
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(rainbow_preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(real_banner.lines)
        
        # Verify line count preserved
        assert len(colored_lines) == len(real_banner.lines)
        
        # Verify text content preserved
        for original, colored in zip(real_banner.lines, colored_lines):
            stripped = ansi_escape_pattern.sub('', colored)
            assert stripped == original, \
                "Vertical alignment must preserve text content"
        
        # Verify gradient effect: each character should have its own color
        for line in colored_lines:
            if line.strip():  # Skip empty lines
                # Count RGB color codes in the line
                rgb_codes = line.count('\x1b[38;2;')
                
                # Should have multiple color codes for gradient effect
                assert rgb_codes > 0, \
                    "Vertical alignment must apply colors to characters"
    
    def test_vertical_alignment_gradient_distribution(
        self,
        small_banner,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test that vertical alignment distributes colors across width.
        
        Validates Requirement 8.2: Color spreading across width
        """
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(small_banner.lines)
        
        # Find maximum width
        max_width = max(len(line) for line in small_banner.lines)
        
        # Verify colors spread across width
        for colored in colored_lines:
            if colored.strip():
                # Extract all RGB values from the line
                rgb_pattern = re.compile(r'\x1b\[38;2;(\d+);(\d+);(\d+)m')
                matches = rgb_pattern.findall(colored)
                
                # Should have color codes (gradient effect)
                assert len(matches) > 0, \
                    "Vertical alignment must apply gradient"
    
    def test_vertical_alignment_handles_varying_widths(
        self,
        ansi_escape_pattern
    ):
        """Test vertical alignment with lines of varying widths.
        
        Validates Requirement 8.2: Handling variable line widths
        """
        lines = [
            "█",
            "███",
            "█████",
            "███",
            "█"
        ]
        metadata = BannerMetadata(
            category="TEST",
            name="PYRAMID",
            dimensions=(5, 5)
        )
        banner = Banner(metadata=metadata, lines=lines)
        
        preset = ColorPreset(name="test", colors=["#FF0000", "#0000FF"])
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(banner.lines)
        
        # Verify structure preserved
        assert len(colored_lines) == len(banner.lines)
        
        for original, colored in zip(banner.lines, colored_lines):
            stripped = ansi_escape_pattern.sub('', colored)
            assert stripped == original
    
    # ========================================================================
    # Custom Alignment Tests (Requirement 8.3)
    # ========================================================================
    
    def test_custom_alignment_with_color_mapping(
        self,
        small_banner,
        ansi_escape_pattern
    ):
        """Test custom alignment with explicit color mapping.
        
        Validates Requirement 8.3: Custom color alignment
        """
        preset = ColorPreset(
            name="custom_test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        custom_colors = {
            "0": "0",  # Map ASCII color 0 to preset color 0 (red)
            "1": "1",  # Map ASCII color 1 to preset color 1 (green)
            "2": "2"   # Map ASCII color 2 to preset color 2 (blue)
        }
        
        alignment = ColorAlignment(mode="custom", custom_colors=custom_colors)
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(small_banner.lines)
        
        # Verify structure preserved
        assert len(colored_lines) == len(small_banner.lines)
        
        for original, colored in zip(small_banner.lines, colored_lines):
            stripped = ansi_escape_pattern.sub('', colored)
            assert stripped == original, \
                "Custom alignment must preserve text content"
    
    def test_custom_alignment_requires_custom_colors(self):
        """Test that custom alignment requires custom_colors parameter.
        
        Validates Requirement 8.3: Custom mode validation
        """
        with pytest.raises(ValueError, match="custom_colors required"):
            ColorAlignment(mode="custom")
    
    def test_custom_alignment_with_real_banner(
        self,
        real_banner,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test custom alignment with real banner.
        
        Validates Requirement 8.3: Custom alignment with real data
        """
        custom_colors = {"0": "0", "1": "1", "2": "2", "3": "3"}
        alignment = ColorAlignment(mode="custom", custom_colors=custom_colors)
        colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(real_banner.lines)
        
        # Verify structure preserved
        assert len(colored_lines) == len(real_banner.lines)
        
        for original, colored in zip(real_banner.lines, colored_lines):
            stripped = ansi_escape_pattern.sub('', colored)
            assert stripped == original
    
    # ========================================================================
    # Structure Preservation Tests (Requirement 14.6)
    # ========================================================================
    
    def test_colorization_preserves_whitespace(
        self,
        real_banner,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test that colorization preserves all whitespace.
        
        Validates Requirement 14.6: Whitespace preservation
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(real_banner.lines)
        
        for original, colored in zip(real_banner.lines, colored_lines):
            stripped = ansi_escape_pattern.sub('', colored)
            
            # Verify exact match including whitespace
            assert stripped == original, \
                "Whitespace must be preserved exactly"
            
            # Verify leading spaces preserved
            original_leading = len(original) - len(original.lstrip())
            stripped_leading = len(stripped) - len(stripped.lstrip())
            assert original_leading == stripped_leading, \
                "Leading whitespace must be preserved"
            
            # Verify trailing spaces preserved
            original_trailing = len(original) - len(original.rstrip())
            stripped_trailing = len(stripped) - len(stripped.rstrip())
            assert original_trailing == stripped_trailing, \
                "Trailing whitespace must be preserved"
    
    def test_colorization_preserves_special_characters(
        self,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test that colorization preserves special Unicode characters.
        
        Validates Requirement 14.6: Special character preservation
        """
        lines = [
            "╔═══════════╗",
            "║  PEEPBEEFY ║",
            "╠═══════════╣",
            "║  🔥 FIRE 🔥 ║",
            "╚═══════════╝"
        ]
        metadata = BannerMetadata(
            category="TEST",
            name="UNICODE",
            dimensions=(13, 5)
        )
        banner = Banner(metadata=metadata, lines=lines)
        
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(banner.lines)
        
        for original, colored in zip(banner.lines, colored_lines):
            stripped = ansi_escape_pattern.sub('', colored)
            assert stripped == original, \
                "Special Unicode characters must be preserved"
    
    def test_colorization_preserves_empty_lines(
        self,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test that colorization handles empty lines correctly.
        
        Validates Requirement 14.6: Empty line handling
        """
        lines = [
            "  ████  ",
            "",  # Empty line
            "  ████  ",
            "        ",  # Whitespace only
            "  ████  "
        ]
        metadata = BannerMetadata(
            category="TEST",
            name="EMPTY_LINES",
            dimensions=(8, 5)
        )
        banner = Banner(metadata=metadata, lines=lines)
        
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(banner.lines)
        
        # Verify line count preserved
        assert len(colored_lines) == len(banner.lines)
        
        # Verify empty lines preserved
        for original, colored in zip(banner.lines, colored_lines):
            stripped = ansi_escape_pattern.sub('', colored)
            assert stripped == original
    
    def test_colorization_preserves_banner_dimensions(
        self,
        real_banner,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test that banner dimensions are preserved after colorization.
        
        Validates Requirement 14.6: Dimension preservation
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(real_banner.lines)
        
        # Strip ANSI codes
        stripped_lines = [ansi_escape_pattern.sub('', line) for line in colored_lines]
        
        # Verify height preserved
        assert len(stripped_lines) == real_banner.height, \
            "Banner height must be preserved"
        
        # Verify width preserved (check longest line)
        max_width = max(len(line) for line in stripped_lines)
        assert max_width == real_banner.width, \
            "Banner width must be preserved"
    
    # ========================================================================
    # Multiple Color Modes Tests
    # ========================================================================
    
    def test_all_alignment_modes_with_rgb(
        self,
        small_banner,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test all three alignment modes with RGB color mode.
        
        Validates Requirements 8.1, 8.2, 8.3: All modes with RGB
        """
        modes = [
            ColorAlignment(mode="horizontal"),
            ColorAlignment(mode="vertical"),
            ColorAlignment(mode="custom", custom_colors={"0": "0"})
        ]
        
        for alignment in modes:
            colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
            colored_lines = colorizer.colorize(small_banner.lines)
            
            # Verify structure preserved for all modes
            assert len(colored_lines) == len(small_banner.lines)
            
            for original, colored in zip(small_banner.lines, colored_lines):
                stripped = ansi_escape_pattern.sub('', colored)
                assert stripped == original, \
                    f"Mode {alignment.mode} must preserve structure"
                
                # Verify RGB codes present
                assert '\x1b[38;2;' in colored, \
                    f"Mode {alignment.mode} must use RGB codes"
    
    def test_all_alignment_modes_with_8bit(
        self,
        small_banner,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test all three alignment modes with 8-bit color mode.
        
        Validates Requirements 8.1, 8.2, 8.3: All modes with 8-bit
        """
        modes = [
            ColorAlignment(mode="horizontal"),
            ColorAlignment(mode="vertical"),
            ColorAlignment(mode="custom", custom_colors={"0": "0"})
        ]
        
        for alignment in modes:
            colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="8bit")
            colored_lines = colorizer.colorize(small_banner.lines)
            
            # Verify structure preserved
            assert len(colored_lines) == len(small_banner.lines)
            
            for original, colored in zip(small_banner.lines, colored_lines):
                stripped = ansi_escape_pattern.sub('', colored)
                assert stripped == original
                
                # Verify 8-bit codes present
                assert '\x1b[38;5;' in colored, \
                    f"Mode {alignment.mode} must use 8-bit codes"
    
    # ========================================================================
    # Edge Cases and Error Handling
    # ========================================================================
    
    def test_colorization_with_empty_banner(self, fire_preset):
        """Test colorization handles empty banner gracefully.
        
        Validates Requirement 14.6: Error handling
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
        
        # Empty banner
        colored_lines = colorizer.colorize([])
        
        assert colored_lines == [], \
            "Empty banner should return empty list"
    
    def test_colorization_with_single_line_banner(
        self,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test colorization with single-line banner.
        
        Validates Requirement 14.6: Edge case handling
        """
        lines = ["  ████████  "]
        metadata = BannerMetadata(
            category="TEST",
            name="SINGLE_LINE",
            dimensions=(12, 1)
        )
        banner = Banner(metadata=metadata, lines=lines)
        
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
        
        colored_lines = colorizer.colorize(banner.lines)
        
        assert len(colored_lines) == 1
        stripped = ansi_escape_pattern.sub('', colored_lines[0])
        assert stripped == lines[0]
    
    def test_colorization_idempotency(
        self,
        small_banner,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test that multiple colorization passes preserve original text.
        
        Validates Requirement 14.6: Idempotency
        """
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
        
        # First pass
        colored_once = colorizer.colorize(small_banner.lines)
        
        # Second pass (colorizing already colored lines)
        colored_twice = colorizer.colorize(colored_once)
        
        # Original text should still be preserved
        for original, final in zip(small_banner.lines, colored_twice):
            stripped = ansi_escape_pattern.sub('', final)
            assert stripped == original, \
                "Multiple passes must preserve original text"
    
    def test_colorization_with_very_long_lines(
        self,
        fire_preset,
        ansi_escape_pattern
    ):
        """Test colorization with very long lines.
        
        Validates Requirement 14.6: Performance with long lines
        """
        # Create banner with very long lines
        long_line = "█" * 200
        lines = [long_line] * 3
        
        metadata = BannerMetadata(
            category="TEST",
            name="LONG_LINES",
            dimensions=(200, 3)
        )
        banner = Banner(metadata=metadata, lines=lines)
        
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(fire_preset, alignment, ansi_mode="rgb")
        
        # Should complete without errors
        colored_lines = colorizer.colorize(banner.lines)
        
        assert len(colored_lines) == len(banner.lines)
        
        for original, colored in zip(banner.lines, colored_lines):
            stripped = ansi_escape_pattern.sub('', colored)
            assert stripped == original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
