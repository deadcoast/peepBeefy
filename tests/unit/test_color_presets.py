"""Unit tests for color preset management system."""

import json
import pytest
from pathlib import Path
from src.color_presets import ColorPreset, load_presets, spread_colors_balanced
from src.color_util import RGB


class TestColorPreset:
    """Test ColorPreset dataclass functionality."""
    
    def test_simple_preset_creation(self):
        """Test creating a simple preset with colors only."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        assert preset.name == "test"
        assert len(preset.colors) == 3
        assert preset.weights is None
    
    def test_weighted_preset_creation(self):
        """Test creating a weighted preset."""
        preset = ColorPreset(
            name="weighted",
            colors=["#FF0000", "#00FF00"],
            weights=[2, 1]
        )
        assert preset.weights == [2, 1]
    
    def test_empty_colors_raises_error(self):
        """Test that empty color list raises ValueError."""
        with pytest.raises(ValueError, match="must have at least one color"):
            ColorPreset(name="empty", colors=[])
    
    def test_mismatched_weights_raises_error(self):
        """Test that mismatched weights length raises ValueError."""
        with pytest.raises(ValueError, match="weights length"):
            ColorPreset(
                name="bad",
                colors=["#FF0000", "#00FF00"],
                weights=[1, 2, 3]
            )
    
    def test_negative_weights_raises_error(self):
        """Test that negative weights raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            ColorPreset(
                name="bad",
                colors=["#FF0000"],
                weights=[0]
            )
    
    def test_expand_colors_without_weights(self):
        """Test expand_colors returns RGB list when no weights."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"]
        )
        expanded = preset.expand_colors()
        assert len(expanded) == 2
        assert all(isinstance(c, RGB) for c in expanded)
        assert expanded[0] == RGB(r=255, g=0, b=0)
        assert expanded[1] == RGB(r=0, g=255, b=0)
    
    def test_expand_colors_with_weights(self):
        """Test expand_colors applies weights correctly."""
        preset = ColorPreset(
            name="weighted",
            colors=["#FF0000", "#00FF00"],
            weights=[3, 1]
        )
        expanded = preset.expand_colors()
        assert len(expanded) == 4  # 3 + 1
        assert expanded[0] == RGB(r=255, g=0, b=0)
        assert expanded[1] == RGB(r=255, g=0, b=0)
        assert expanded[2] == RGB(r=255, g=0, b=0)
        assert expanded[3] == RGB(r=0, g=255, b=0)
    
    def test_spread_colors_exact_match(self):
        """Test spread_colors when length matches color count."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        spread = preset.spread_colors(3)
        assert len(spread) == 3
    
    def test_spread_colors_expand(self):
        """Test spread_colors when length > color count."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#0000FF"]
        )
        spread = preset.spread_colors(5)
        assert len(spread) == 5
    
    def test_spread_colors_contract(self):
        """Test spread_colors when length < color count."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
        )
        spread = preset.spread_colors(2)
        assert len(spread) == 2
    
    def test_spread_colors_invalid_length(self):
        """Test spread_colors raises error for invalid length."""
        preset = ColorPreset(name="test", colors=["#FF0000"])
        with pytest.raises(ValueError, match="must be positive"):
            preset.spread_colors(0)
    
    def test_adjust_lightness_dark_background_hsl(self):
        """Test lightness adjustment for dark background using HSL."""
        preset = ColorPreset(
            name="test",
            colors=["#330000"]  # Very dark red
        )
        adjusted = preset.adjust_lightness("dark", method="hsl")
        
        # Check that colors are lightened
        adjusted_rgb = adjusted.expand_colors()
        assert len(adjusted_rgb) == 1
        assert adjusted_rgb[0].hsl().l >= 0.65
    
    def test_adjust_lightness_light_background_hsl(self):
        """Test lightness adjustment for light background using HSL."""
        preset = ColorPreset(
            name="test",
            colors=["#FFCCCC"]  # Very light red
        )
        adjusted = preset.adjust_lightness("light", method="hsl")
        
        # Check that colors are darkened
        adjusted_rgb = adjusted.expand_colors()
        assert len(adjusted_rgb) == 1
        assert adjusted_rgb[0].hsl().l <= 0.4
    
    def test_adjust_lightness_dark_background_overlay(self):
        """Test lightness adjustment for dark background using overlay."""
        preset = ColorPreset(
            name="test",
            colors=["#330000"]  # Very dark red
        )
        adjusted = preset.adjust_lightness("dark", method="overlay")
        
        # Check that colors are lightened
        adjusted_rgb = adjusted.expand_colors()
        assert len(adjusted_rgb) == 1
        # Overlay should lighten the color
        assert adjusted_rgb[0].hsl().l > RGB.from_hex("#330000").hsl().l


class TestSpreadColorsBalanced:
    """Test spread_colors_balanced helper function."""
    
    def test_exact_match(self):
        """Test when target length equals color count."""
        colors = [RGB(255, 0, 0), RGB(0, 255, 0), RGB(0, 0, 255)]
        result = spread_colors_balanced(colors, 3)
        assert len(result) == 3
        assert result == colors
    
    def test_expand_colors(self):
        """Test expanding fewer colors to more positions."""
        colors = [RGB(255, 0, 0), RGB(0, 0, 255)]
        result = spread_colors_balanced(colors, 5)
        assert len(result) == 5
        # All positions should be filled
        assert all(c is not None for c in result)
    
    def test_contract_colors(self):
        """Test contracting more colors to fewer positions."""
        colors = [RGB(255, 0, 0), RGB(0, 255, 0), RGB(0, 0, 255), RGB(255, 255, 0)]
        result = spread_colors_balanced(colors, 2)
        assert len(result) == 2
    
    def test_single_color(self):
        """Test spreading a single color."""
        colors = [RGB(255, 0, 0)]
        result = spread_colors_balanced(colors, 5)
        assert len(result) == 5
        # All should be the same color
        assert all(c == colors[0] for c in result)
    
    def test_invalid_target_length(self):
        """Test that invalid target length raises error."""
        colors = [RGB(255, 0, 0)]
        with pytest.raises(ValueError, match="must be positive"):
            spread_colors_balanced(colors, 0)
    
    def test_empty_colors_raises_error(self):
        """Test that empty color list raises error."""
        with pytest.raises(ValueError, match="Cannot spread empty"):
            spread_colors_balanced([], 5)


class TestLoadPresets:
    """Test preset loading from JSON."""
    
    def test_load_simple_presets(self, tmp_path):
        """Test loading simple presets from JSON."""
        preset_file = tmp_path / "presets.json"
        preset_data = {
            "rainbow": ["#FF0000", "#00FF00", "#0000FF"],
            "fire": ["#FF0000", "#FF8C00"]
        }
        preset_file.write_text(json.dumps(preset_data))
        
        presets = load_presets(preset_file)
        assert len(presets) == 2
        assert "rainbow" in presets
        assert "fire" in presets
        assert presets["rainbow"].colors == ["#FF0000", "#00FF00", "#0000FF"]
    
    def test_load_weighted_presets(self, tmp_path):
        """Test loading weighted presets from JSON."""
        preset_file = tmp_path / "presets.json"
        preset_data = {
            "weighted": {
                "colors": ["#FF0000", "#00FF00"],
                "weights": [2, 1]
            }
        }
        preset_file.write_text(json.dumps(preset_data))
        
        presets = load_presets(preset_file)
        assert len(presets) == 1
        assert presets["weighted"].weights == [2, 1]
    
    def test_load_mixed_presets(self, tmp_path):
        """Test loading mix of simple and weighted presets."""
        preset_file = tmp_path / "presets.json"
        preset_data = {
            "simple": ["#FF0000"],
            "weighted": {
                "colors": ["#00FF00"],
                "weights": [1]
            }
        }
        preset_file.write_text(json.dumps(preset_data))
        
        presets = load_presets(preset_file)
        assert len(presets) == 2
        assert presets["simple"].weights is None
        assert presets["weighted"].weights == [1]
    
    def test_load_invalid_format_raises_error(self, tmp_path):
        """Test that invalid preset format raises error."""
        preset_file = tmp_path / "presets.json"
        preset_data = {
            "invalid": 123  # Not a list or dict
        }
        preset_file.write_text(json.dumps(preset_data))
        
        with pytest.raises(ValueError, match="Invalid preset format"):
            load_presets(preset_file)
    
    def test_load_nonexistent_file_raises_error(self, tmp_path):
        """Test that loading nonexistent file raises error."""
        preset_file = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_presets(preset_file)
    
    def test_load_invalid_json_raises_error(self, tmp_path):
        """Test that invalid JSON raises error."""
        preset_file = tmp_path / "presets.json"
        preset_file.write_text("not valid json {")
        
        with pytest.raises(json.JSONDecodeError):
            load_presets(preset_file)


class TestDefaultPresets:
    """Test that default presets file is valid."""
    
    def test_default_presets_exist(self):
        """Test that default presets file exists."""
        preset_file = Path("data/color_presets.json")
        assert preset_file.exists()
    
    def test_default_presets_load(self):
        """Test that default presets load successfully."""
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        assert len(presets) > 0
    
    def test_default_presets_have_required_themes(self):
        """Test that default presets include common themes."""
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        required_themes = ["rainbow", "fire", "ocean", "forest"]
        for theme in required_themes:
            assert theme in presets, f"Missing required theme: {theme}"
    
    def test_all_default_presets_valid(self):
        """Test that all default presets are valid."""
        preset_file = Path("data/color_presets.json")
        presets = load_presets(preset_file)
        
        for name, preset in presets.items():
            # Should be able to expand colors without error
            colors = preset.expand_colors()
            assert len(colors) > 0, f"Preset '{name}' has no colors"
            
            # All colors should be valid RGB
            for color in colors:
                assert isinstance(color, RGB)
                assert 0 <= color.r <= 255
                assert 0 <= color.g <= 255
                assert 0 <= color.b <= 255
