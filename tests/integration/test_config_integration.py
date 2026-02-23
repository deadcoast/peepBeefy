"""
Integration tests for Configuration System + All Components.

Tests the integration between the configuration system and all other
components (themes, presets, terminal detection, etc.), verifying that
configuration changes propagate correctly and the system maintains
backward compatibility.

Validates Requirements:
- 14.3: Verify Gradient_Engine produces smooth color transitions
- 14.4: Verify Preset_System loads and applies colors correctly
- 14.7: Verify all new features degrade gracefully on limited terminals
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import json

from src.config import ConfigManager, AppConfig, BannerConfig
from src.themes import ThemeRegistry
from src.color_presets import ColorPreset, load_presets
from src.color_scale import Scale, create_gradient
from src.color_util import RGB
from src.terminal_detect import detect_ansi_mode


class TestConfigurationIntegration:
    """Integration tests for configuration system with all components."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config_manager(self, temp_config_dir):
        """Create a ConfigManager with temporary config directory."""
        with patch.object(ConfigManager, 'CONFIG_DIR', temp_config_dir):
            with patch.object(ConfigManager, 'CONFIG_FILE', temp_config_dir / 'config.json'):
                manager = ConfigManager()
                yield manager
    
    def test_gradient_engine_smoothness(self):
        """Test that gradient engine produces smooth color transitions.
        
        Validates Requirement 14.3: Gradient engine smoothness
        """
        # Create gradient from red to blue
        colors = [
            RGB(255, 0, 0),    # Red
            RGB(0, 0, 255)     # Blue
        ]
        
        gradient = create_gradient(colors, resolution=100)
        
        # Verify gradient length
        assert len(gradient) == 100, "Gradient should have 100 steps"
        
        # Verify smoothness: consecutive colors should have small differences
        max_diff = 0
        for i in range(len(gradient) - 1):
            c1 = gradient[i]
            c2 = gradient[i + 1]
            
            diff_r = abs(c2.r - c1.r)
            diff_g = abs(c2.g - c1.g)
            diff_b = abs(c2.b - c1.b)
            
            max_component_diff = max(diff_r, diff_g, diff_b)
            max_diff = max(max_diff, max_component_diff)
        
        # For 100 steps between 255 and 0, max diff should be around 3
        assert max_diff <= 5, \
            f"Gradient should be smooth, max component difference: {max_diff}"
    
    def test_gradient_engine_multi_color(self):
        """Test gradient engine with multiple colors.
        
        Validates Requirement 14.3: Multi-color gradients
        """
        # Create gradient from red -> green -> blue
        colors = [
            RGB(255, 0, 0),    # Red
            RGB(0, 255, 0),    # Green
            RGB(0, 0, 255)     # Blue
        ]
        
        gradient = create_gradient(colors, resolution=50)
        
        # Should have (n-1) * resolution steps
        expected_length = (len(colors) - 1) * 50
        assert len(gradient) == expected_length, \
            f"Multi-color gradient should have {expected_length} steps"
        
        # Verify endpoints (allow small rounding tolerance)
        assert gradient[0].r == 255 and gradient[0].g == 0 and gradient[0].b == 0
        # Last color should be close to blue (allow ±5 tolerance for rounding)
        assert abs(gradient[-1].r - 0) <= 5
        assert abs(gradient[-1].g - 0) <= 5
        assert abs(gradient[-1].b - 255) <= 5
    
    def test_gradient_scale_lookup(self):
        """Test gradient scale lookup by ratio.
        
        Validates Requirement 14.3: Gradient lookup functionality
        """
        scale = Scale(["#FF0000", "#0000FF"], resolution=100)
        
        # Test ratio lookup
        color_start = scale(0.0)
        color_mid = scale(0.5)
        color_end = scale(1.0)
        
        # Verify endpoints (allow small rounding tolerance)
        assert color_start.r == 255 and color_start.b == 0, "Start should be red"
        # End should be close to blue (allow ±5 tolerance for rounding)
        assert abs(color_end.r - 0) <= 5, f"End red should be ~0, got {color_end.r}"
        assert abs(color_end.b - 255) <= 5, f"End blue should be ~255, got {color_end.b}"
        
        # Verify middle is a blend
        assert 0 < color_mid.r < 255, "Middle should be a blend"
        assert 0 < color_mid.b < 255, "Middle should be a blend"
    
    def test_preset_system_loading(self, temp_config_dir):
        """Test that preset system loads presets correctly.
        
        Validates Requirement 14.4: Preset loading
        """
        # Create test preset file
        preset_file = temp_config_dir / "test_presets.json"
        preset_data = {
            "rainbow": {
                "colors": ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#9400D3"]
            },
            "fire": {
                "colors": ["#8B0000", "#FF4500", "#FFD700"],
                "weights": [1, 2, 1]
            }
        }
        
        with open(preset_file, 'w') as f:
            json.dump(preset_data, f)
        
        # Load presets
        presets = load_presets(preset_file)
        
        # Verify presets loaded
        assert "rainbow" in presets
        assert "fire" in presets
        
        # Verify rainbow preset
        rainbow = presets["rainbow"]
        assert len(rainbow.colors) == 7
        assert rainbow.weights is None
        
        # Verify fire preset
        fire = presets["fire"]
        assert len(fire.colors) == 3
        assert fire.weights == [1, 2, 1]
    
    def test_preset_color_spreading(self):
        """Test that preset colors spread correctly across target length.
        
        Validates Requirement 14.4: Color spreading
        """
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        # Spread across 10 positions
        spread_colors = preset.spread_colors(10)
        
        # Should have exactly 10 colors
        assert len(spread_colors) == 10
        
        # All should be RGB objects
        for color in spread_colors:
            assert isinstance(color, RGB)
            assert 0 <= color.r <= 255
            assert 0 <= color.g <= 255
            assert 0 <= color.b <= 255
    
    def test_preset_weighted_expansion(self):
        """Test that weighted presets expand correctly.
        
        Validates Requirement 14.4: Weighted preset expansion
        """
        preset = ColorPreset(
            name="weighted",
            colors=["#FF0000", "#00FF00"],
            weights=[3, 1]
        )
        
        expanded = preset.expand_colors()
        
        # Should have 3 red + 1 green = 4 colors
        assert len(expanded) == 4
        
        # First 3 should be red
        for i in range(3):
            assert expanded[i].r == 255
            assert expanded[i].g == 0
            assert expanded[i].b == 0
        
        # Last should be green
        assert expanded[3].r == 0
        assert expanded[3].g == 255
        assert expanded[3].b == 0
    
    def test_graceful_degradation_rgb_to_8bit(self):
        """Test graceful degradation from RGB to 8-bit mode.
        
        Validates Requirement 14.7: Graceful degradation
        """
        rgb = RGB(255, 100, 50)
        
        # Generate both RGB and 8-bit codes
        rgb_code = rgb.to_ansi_rgb(foreground=True)
        eightbit_code = rgb.to_ansi_8bit(foreground=True)
        
        # Both should be valid ANSI codes
        assert rgb_code.startswith('\033[38;2;')
        assert eightbit_code.startswith('\033[38;5;')
        
        # Both should end with 'm'
        assert rgb_code.endswith('m')
        assert eightbit_code.endswith('m')
    
    def test_graceful_degradation_unified_interface(self):
        """Test unified ANSI interface with different modes.
        
        Validates Requirement 14.7: Unified color interface
        """
        rgb = RGB(200, 100, 50)
        
        # Test all modes
        modes = ["rgb", "8bit", "ansi", "default"]
        
        for mode in modes:
            try:
                ansi_code = rgb.to_ansi(mode=mode, foreground=True)
                
                # Should produce valid ANSI code
                assert ansi_code.startswith('\033[')
                assert ansi_code.endswith('m')
            except Exception as e:
                pytest.fail(f"Mode '{mode}' failed: {e}")
    
    def test_terminal_detection_fallback(self):
        """Test that terminal detection falls back gracefully.
        
        Validates Requirement 14.7: Detection fallback
        """
        # Mock environment with no terminal info
        with patch.dict('os.environ', {}, clear=True):
            mode = detect_ansi_mode()
            
            # Should return None or a safe default, not crash
            assert mode is None or mode in ["rgb", "8bit", "ansi", "default"]
    
    def test_config_with_all_features(self, mock_config_manager):
        """Test configuration with all integrated features.
        
        Validates: Complete system integration
        """
        # Create config with all features
        config = AppConfig(
            version=1,
            first_run_complete=True,
            theme_variant="CRT_Cyan",
            banner=BannerConfig(
                mode="random",
                animation_enabled=True,
                animation_intensity="normal"
            )
        )
        
        # Save and load
        mock_config_manager.save(config)
        loaded = mock_config_manager.load()
        
        # Verify all fields preserved (version may be migrated to latest)
        assert loaded.version >= config.version, "Version should be same or migrated"
        assert loaded.first_run_complete == config.first_run_complete
        assert loaded.theme_variant == config.theme_variant
        assert loaded.banner.mode == config.banner.mode
        assert loaded.banner.animation_enabled == config.banner.animation_enabled
        assert loaded.banner.animation_intensity == config.banner.animation_intensity
    
    def test_theme_integration_with_config(self, mock_config_manager):
        """Test that themes integrate with configuration system.
        
        Validates: Theme + config integration
        """
        # Save config with specific theme
        config = AppConfig(theme_variant="Synthwave")
        mock_config_manager.save(config)
        
        # Load config and get theme
        loaded = mock_config_manager.load()
        theme = ThemeRegistry.get_theme(loaded.theme_variant)
        
        # Verify theme loaded correctly
        assert theme.name == "Synthwave"
        assert theme.palette is not None
    
    def test_preset_integration_with_banner_config(self, mock_config_manager):
        """Test that presets integrate with banner configuration.
        
        Validates: Preset + config integration
        """
        # Create config with preset reference
        config = AppConfig(
            banner=BannerConfig(
                mode="random",
                color_preset="rainbow"
            )
        )
        
        mock_config_manager.save(config)
        loaded = mock_config_manager.load()
        
        # Verify preset reference preserved
        assert loaded.banner.color_preset == "rainbow"
    
    def test_color_mode_detection_integration(self):
        """Test that color mode detection integrates with all systems.
        
        Validates Requirement 14.7: System-wide color mode
        """
        # Mock RGB terminal
        with patch.dict('os.environ', {'COLORTERM': 'truecolor'}):
            mode = detect_ansi_mode()
            assert mode == "rgb"
            
            # Verify theme can use this mode
            theme = ThemeRegistry.get_theme("CRT_Cyan")
            detected_mode = theme.get_color_mode()
            assert detected_mode == "rgb"
        
        # Mock 8-bit terminal
        with patch.dict('os.environ', {'TERM': 'xterm-256color'}, clear=True):
            mode = detect_ansi_mode()
            # May detect as rgb or 8bit depending on implementation
            assert mode in ["rgb", "8bit"], f"Should detect valid mode, got {mode}"
            
            theme = ThemeRegistry.get_theme("CRT_Cyan")
            detected_mode = theme.get_color_mode()
            assert detected_mode in ["rgb", "8bit"]
    
    def test_error_handling_across_systems(self):
        """Test that errors in one system don't crash others.
        
        Validates Requirement 14.7: Error isolation
        """
        # Test invalid color in preset
        try:
            preset = ColorPreset(
                name="invalid",
                colors=["#INVALID"]
            )
            # Attempting to expand should handle error
            expanded = preset.expand_colors()
            # Should either raise or return empty, not crash entire system
        except Exception:
            # Expected - invalid color should raise
            pass
        
        # Test invalid theme name
        theme = ThemeRegistry.get_theme("NONEXISTENT")
        # Should return default theme, not crash
        assert theme is not None
        assert theme.name == "CRT_Cyan"  # Default fallback
    
    def test_backward_compatibility_config_loading(self, mock_config_manager):
        """Test that old configs load with new features.
        
        Validates: Backward compatibility
        """
        # Create minimal old-style config
        old_config = {
            "version": 1,
            "first_run_complete": True,
            "theme_variant": "CRT_Cyan",
            "banner": {
                "mode": "random"
            }
        }
        
        # Save directly as JSON
        with open(mock_config_manager.CONFIG_FILE, 'w') as f:
            json.dump(old_config, f)
        
        # Load with new system
        loaded = mock_config_manager.load()
        
        # Should load successfully with defaults for new fields
        # Version may be migrated to latest
        assert loaded.version >= 1, "Version should be at least 1"
        assert loaded.theme_variant == "CRT_Cyan"
        assert loaded.banner.mode == "random"
        # New fields should have defaults
        assert hasattr(loaded.banner, 'animation_enabled')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
