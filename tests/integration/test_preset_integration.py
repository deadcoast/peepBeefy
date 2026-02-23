"""
Integration tests for Color Preset System.

Tests the integration of the preset system with loading from JSON,
color spreading across different lengths, and application to ASCII art.

Validates Requirement 14.4: Verify Preset_System loads and applies colors correctly
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from src.color_presets import (
    ColorPreset,
    load_presets,
    get_presets_lazy,
    clear_preset_cache,
    spread_colors_balanced
)
from src.color_util import RGB
from src.ascii_renderer import ASCIIColorizer, ColorAlignment


class TestPresetLoading:
    """Integration tests for preset loading from JSON."""
    
    def test_load_default_presets_file(self):
        """Test loading the default color_presets.json file.
        
        Validates Requirement 14.4: Presets load from JSON correctly
        """
        preset_file = Path("data/color_presets.json")
        
        # Verify file exists
        assert preset_file.exists(), "Default preset file should exist"
        
        # Load presets
        presets = load_presets(preset_file)
        
        # Verify presets loaded
        assert len(presets) > 0, "Should load at least one preset"
        
        # Verify all presets are valid ColorPreset objects
        for name, preset in presets.items():
            assert isinstance(preset, ColorPreset), \
                f"Preset '{name}' should be ColorPreset instance"
            assert preset.name == name, \
                f"Preset name should match key"
            assert len(preset.colors) > 0, \
                f"Preset '{name}' should have at least one color"
    
    def test_load_all_preset_types(self):
        """Test loading both simple and weighted presets.
        
        Validates Requirement 14.4: Support for different preset formats
        """
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        # Find simple presets (list format)
        simple_presets = [p for p in presets.values() if p.weights is None]
        assert len(simple_presets) > 0, "Should have simple presets"
        
        # Find weighted presets (dict format with weights)
        weighted_presets = [p for p in presets.values() if p.weights is not None]
        assert len(weighted_presets) > 0, "Should have weighted presets"
        
        # Verify weighted presets have valid weights
        for preset in weighted_presets:
            assert len(preset.weights) == len(preset.colors), \
                f"Preset '{preset.name}' weights should match colors length"
            assert all(w > 0 for w in preset.weights), \
                f"Preset '{preset.name}' all weights should be positive"
    
    def test_lazy_loading_caching(self):
        """Test that lazy loading caches presets correctly.
        
        Validates Requirement 14.4: Performance optimization through caching
        """
        # Clear cache first
        clear_preset_cache()
        
        preset_file = Path("data/color_presets.json")
        
        # First call should load from disk
        presets1 = get_presets_lazy(preset_file)
        assert len(presets1) > 0
        
        # Second call should use cache (same object reference)
        presets2 = get_presets_lazy(preset_file)
        assert presets2 is presets1, "Should return cached presets"
        
        # Clear cache
        clear_preset_cache()
        
        # Third call should reload from disk (different object)
        presets3 = get_presets_lazy(preset_file)
        assert presets3 is not presets1, "Should reload after cache clear"
    
    def test_preset_validation_on_load(self):
        """Test that invalid presets are caught during loading.
        
        Validates Requirement 14.4: Error handling for invalid data
        """
        # Test with temporary invalid preset file
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Invalid: empty colors
            invalid_data = {
                "empty": []
            }
            json.dump(invalid_data, f)
            temp_file = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="must have at least one color"):
                load_presets(temp_file)
        finally:
            temp_file.unlink()
    
    def test_all_default_presets_expandable(self):
        """Test that all default presets can be expanded without errors.
        
        Validates Requirement 14.4: All presets are valid and usable
        """
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        for name, preset in presets.items():
            try:
                # Expand colors
                expanded = preset.expand_colors()
                
                # Verify expansion worked
                assert len(expanded) > 0, \
                    f"Preset '{name}' expansion should produce colors"
                
                # Verify all are RGB objects
                for i, color in enumerate(expanded):
                    assert isinstance(color, RGB), \
                        f"Preset '{name}' color {i} should be RGB"
                    assert 0 <= color.r <= 255
                    assert 0 <= color.g <= 255
                    assert 0 <= color.b <= 255
            except Exception as e:
                pytest.fail(f"Failed to expand preset '{name}': {e}")


class TestColorSpreading:
    """Integration tests for color spreading across different lengths."""
    
    def test_spread_to_various_lengths(self):
        """Test spreading presets to different target lengths.
        
        Validates Requirement 14.4: Color spreading across different lengths
        """
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        # Test with rainbow preset (7 colors)
        rainbow = presets["rainbow"]
        
        # Test spreading to various lengths
        test_lengths = [1, 3, 7, 10, 20, 50, 100]
        
        for length in test_lengths:
            spread = rainbow.spread_colors(length)
            
            # Verify exact length
            assert len(spread) == length, \
                f"Spread to {length} should produce exactly {length} colors"
            
            # Verify all are RGB objects
            assert all(isinstance(c, RGB) for c in spread), \
                f"All spread colors should be RGB objects"
    
    def test_spread_shorter_than_original(self):
        """Test spreading when target length is shorter than preset.
        
        Validates Requirement 14.4: Contraction behavior
        """
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        # Rainbow has 7 colors, spread to 3
        rainbow = presets["rainbow"]
        spread = rainbow.spread_colors(3)
        
        assert len(spread) == 3
        
        # Should sample from original colors
        # Verify colors are from the original palette
        original_colors = rainbow.expand_colors()
        for color in spread:
            # Each spread color should be close to at least one original
            found_match = False
            for orig in original_colors:
                if (abs(color.r - orig.r) <= 5 and
                    abs(color.g - orig.g) <= 5 and
                    abs(color.b - orig.b) <= 5):
                    found_match = True
                    break
            assert found_match, f"Spread color {color} should match an original color"
    
    def test_spread_longer_than_original(self):
        """Test spreading when target length is longer than preset.
        
        Validates Requirement 14.4: Expansion behavior
        """
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        # Fire has 5 colors, spread to 20
        fire = presets["fire"]
        spread = fire.spread_colors(20)
        
        assert len(spread) == 20
        
        # Should interpolate between original colors
        # Verify smooth transitions (no huge jumps)
        for i in range(len(spread) - 1):
            c1, c2 = spread[i], spread[i + 1]
            
            # Adjacent colors should be similar (within reasonable range)
            r_diff = abs(c1.r - c2.r)
            g_diff = abs(c1.g - c2.g)
            b_diff = abs(c1.b - c2.b)
            
            # Allow some variation but not huge jumps
            assert r_diff <= 100, f"R difference too large: {r_diff}"
            assert g_diff <= 100, f"G difference too large: {g_diff}"
            assert b_diff <= 100, f"B difference too large: {b_diff}"
    
    def test_weighted_preset_spreading(self):
        """Test spreading weighted presets.
        
        Validates Requirement 14.4: Weighted preset expansion
        """
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        # Get a weighted preset
        weighted_fire = presets["weighted_fire"]
        assert weighted_fire.weights is not None
        
        # Spread to various lengths
        for length in [5, 10, 20]:
            spread = weighted_fire.spread_colors(length)
            assert len(spread) == length
            
            # Verify all colors are valid
            for color in spread:
                assert isinstance(color, RGB)
                assert 0 <= color.r <= 255
                assert 0 <= color.g <= 255
                assert 0 <= color.b <= 255
    
    def test_single_color_spreading(self):
        """Test spreading a single-color preset.
        
        Validates Requirement 14.4: Edge case handling
        """
        # Create single-color preset
        single = ColorPreset(name="single", colors=["#FF0000"])
        
        # Spread to multiple positions
        spread = single.spread_colors(10)
        
        assert len(spread) == 10
        
        # All should be the same color
        for color in spread:
            assert color.r == 255
            assert color.g == 0
            assert color.b == 0


class TestPresetApplication:
    """Integration tests for applying presets to ASCII art."""
    
    def test_apply_preset_to_ascii_horizontal(self):
        """Test applying preset to ASCII art with horizontal alignment.
        
        Validates Requirement 14.4: Preset application to ASCII art
        """
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        # Get rainbow preset
        rainbow = presets["rainbow"]
        
        # Create test ASCII art
        ascii_lines = [
            "Line 1",
            "Line 2",
            "Line 3",
            "Line 4",
            "Line 5"
        ]
        
        # Create colorizer with horizontal alignment
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(
            preset=rainbow,
            alignment=alignment,
            ansi_mode="rgb"
        )
        
        # Colorize
        colorized = colorizer.colorize(ascii_lines)
        
        # Verify output
        assert len(colorized) == len(ascii_lines), \
            "Should preserve line count"
        
        # Each line should have ANSI codes
        for line in colorized:
            assert '\033[' in line, "Should contain ANSI escape codes"
    
    def test_apply_preset_to_ascii_vertical(self):
        """Test applying preset to ASCII art with vertical alignment.
        
        Validates Requirement 14.4: Vertical gradient application
        """
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        # Get ocean preset
        ocean = presets["ocean"]
        
        # Create test ASCII art
        ascii_lines = [
            "ABCDEFGHIJ",
            "KLMNOPQRST",
            "UVWXYZ0123"
        ]
        
        # Create colorizer with vertical alignment
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(
            preset=ocean,
            alignment=alignment,
            ansi_mode="rgb"
        )
        
        # Colorize
        colorized = colorizer.colorize(ascii_lines)
        
        # Verify output
        assert len(colorized) == len(ascii_lines)
        
        # Each line should have multiple color changes (gradient)
        for line in colorized:
            # Count ANSI escape sequences
            ansi_count = line.count('\033[38;2;')
            assert ansi_count > 1, \
                "Vertical alignment should have multiple colors per line"
    
    def test_apply_multiple_presets(self):
        """Test applying different presets to same ASCII art.
        
        Validates Requirement 14.4: Preset interchangeability
        """
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        # Test ASCII art
        ascii_lines = ["Test Line 1", "Test Line 2"]
        
        # Test with multiple presets
        preset_names = ["rainbow", "fire", "ocean", "forest"]
        
        for preset_name in preset_names:
            preset = presets[preset_name]
            
            alignment = ColorAlignment(mode="horizontal")
            colorizer = ASCIIColorizer(
                preset=preset,
                alignment=alignment,
                ansi_mode="rgb"
            )
            
            try:
                colorized = colorizer.colorize(ascii_lines)
                
                # Verify output
                assert len(colorized) == len(ascii_lines), \
                    f"Preset '{preset_name}' should preserve line count"
                
                # Verify colorization happened
                for line in colorized:
                    assert '\033[' in line, \
                        f"Preset '{preset_name}' should add ANSI codes"
            except Exception as e:
                pytest.fail(f"Failed to apply preset '{preset_name}': {e}")
    
    def test_preset_with_different_ansi_modes(self):
        """Test applying preset with different ANSI modes.
        
        Validates Requirement 14.4: Terminal compatibility
        """
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        rainbow = presets["rainbow"]
        ascii_lines = ["Test Line"]
        alignment = ColorAlignment(mode="horizontal")
        
        # Test RGB mode
        colorizer_rgb = ASCIIColorizer(
            preset=rainbow,
            alignment=alignment,
            ansi_mode="rgb"
        )
        colorized_rgb = colorizer_rgb.colorize(ascii_lines)
        assert '\033[38;2;' in colorized_rgb[0], "RGB mode should use 38;2 codes"
        
        # Test 8-bit mode
        colorizer_8bit = ASCIIColorizer(
            preset=rainbow,
            alignment=alignment,
            ansi_mode="8bit"
        )
        colorized_8bit = colorizer_8bit.colorize(ascii_lines)
        assert '\033[38;5;' in colorized_8bit[0], "8-bit mode should use 38;5 codes"
    
    def test_lightness_adjusted_preset_application(self):
        """Test applying lightness-adjusted presets.
        
        Validates Requirement 14.4: Background adaptation
        """
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        # Get a preset and adjust for dark background
        fire = presets["fire"]
        adjusted = fire.adjust_lightness("dark", method="hsl")
        
        # Apply to ASCII art
        ascii_lines = ["Test Line"]
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(
            preset=adjusted,
            alignment=alignment,
            ansi_mode="rgb"
        )
        
        colorized = colorizer.colorize(ascii_lines)
        
        # Verify colorization worked
        assert len(colorized) == 1
        assert '\033[' in colorized[0]
        
        # Verify adjusted colors are lighter
        adjusted_colors = adjusted.expand_colors()
        for color in adjusted_colors:
            assert color.hsl().l >= 0.60, \
                "Adjusted colors should be light enough for dark background"


class TestPresetSystemEndToEnd:
    """End-to-end integration tests for complete preset workflow."""
    
    def test_complete_workflow_load_spread_apply(self):
        """Test complete workflow: load → spread → apply.
        
        Validates Requirement 14.4: Complete integration
        """
        # 1. Load presets
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        # 2. Select preset
        rainbow = presets["rainbow"]
        
        # 3. Spread colors to match ASCII art length
        ascii_lines = [f"Line {i}" for i in range(10)]
        spread_colors = rainbow.spread_colors(len(ascii_lines))
        
        assert len(spread_colors) == len(ascii_lines)
        
        # 4. Apply to ASCII art
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(
            preset=rainbow,
            alignment=alignment,
            ansi_mode="rgb"
        )
        
        colorized = colorizer.colorize(ascii_lines)
        
        # 5. Verify final output
        assert len(colorized) == len(ascii_lines)
        for i, line in enumerate(colorized):
            assert '\033[' in line, f"Line {i} should be colorized"
            assert ascii_lines[i].strip() in line, \
                f"Line {i} should preserve original text"
    
    def test_lazy_loading_performance(self):
        """Test that lazy loading improves performance.
        
        Validates Requirement 14.4: Performance optimization
        """
        import time
        
        # Clear cache
        clear_preset_cache()
        
        preset_file = Path("data/color_presets.json")
        
        # First load (from disk)
        start1 = time.time()
        presets1 = get_presets_lazy(preset_file)
        time1 = time.time() - start1
        
        # Second load (from cache)
        start2 = time.time()
        presets2 = get_presets_lazy(preset_file)
        time2 = time.time() - start2
        
        # Cache should be faster (or at least not slower)
        # Allow some tolerance for timing variations
        assert time2 <= time1 * 1.5, \
            f"Cached load ({time2:.4f}s) should be faster than disk load ({time1:.4f}s)"
        
        # Verify same data
        assert len(presets1) == len(presets2)
    
    def test_error_recovery_invalid_preset(self):
        """Test error recovery when preset is invalid.
        
        Validates Requirement 14.4: Error handling
        """
        # Create invalid preset
        invalid = ColorPreset(name="invalid", colors=["#INVALID"])
        
        # Attempt to expand (should raise error)
        with pytest.raises(ValueError):
            invalid.expand_colors()
    
    def test_preset_reusability(self):
        """Test that presets can be reused multiple times.
        
        Validates Requirement 14.4: Preset reusability
        """
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        rainbow = presets["rainbow"]
        
        # Use same preset multiple times
        for _ in range(5):
            expanded = rainbow.expand_colors()
            assert len(expanded) > 0
            
            spread = rainbow.spread_colors(10)
            assert len(spread) == 10
        
        # Preset should remain unchanged
        assert len(rainbow.colors) == 7  # Rainbow has 7 colors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
