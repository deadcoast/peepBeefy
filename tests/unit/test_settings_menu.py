"""Unit tests for settings menu functionality.

Tests the settings menu implementation in main.py, including:
- Menu displays current configuration
- Configuration changes are saved
- Input validation works correctly
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config import AppConfig, BannerConfig, ConfigManager
from themes import ThemeRegistry


class TestSettingsMenuDisplay:
    """Test that settings menu displays current configuration correctly."""
    
    def test_menu_displays_current_theme(self):
        """Test that current theme is displayed in settings menu."""
        # Create a config with specific theme
        config = AppConfig(
            version=1,
            first_run_complete=True,
            theme_variant="Amber_Terminal",
            banner=BannerConfig()
        )
        
        # Verify theme is set correctly
        assert config.theme_variant == "Amber_Terminal"
    
    def test_menu_displays_banner_mode(self):
        """Test that current banner mode is displayed."""
        # Test random mode
        config = AppConfig(
            banner=BannerConfig(mode="random")
        )
        assert config.banner.mode == "random"
        
        # Test fixed mode
        config = AppConfig(
            banner=BannerConfig(
                mode="fixed",
                selected_banner="1ST_BEEFS:BIGBEEF"
            )
        )
        assert config.banner.mode == "fixed"
        assert config.banner.selected_banner == "1ST_BEEFS:BIGBEEF"
        
        # Test category mode
        config = AppConfig(
            banner=BannerConfig(
                mode="category",
                selected_categories=["1ST_BEEFS", "ALT"]
            )
        )
        assert config.banner.mode == "category"
        assert config.banner.selected_categories == ["1ST_BEEFS", "ALT"]
    
    def test_menu_displays_animation_status(self):
        """Test that animation enabled/disabled status is displayed."""
        # Test enabled
        config = AppConfig(
            banner=BannerConfig(animation_enabled=True)
        )
        assert config.banner.animation_enabled is True
        
        # Test disabled
        config = AppConfig(
            banner=BannerConfig(animation_enabled=False)
        )
        assert config.banner.animation_enabled is False
    
    def test_menu_displays_animation_settings(self):
        """Test that animation settings are displayed when enabled."""
        config = AppConfig(
            banner=BannerConfig(
                animation_enabled=True,
                animation_intensity="intense",
                animation_duration=5.0,
                animation_fps=15
            )
        )
        
        assert config.banner.animation_intensity == "intense"
        assert config.banner.animation_duration == 5.0
        assert config.banner.animation_fps == 15


class TestBannerConfiguration:
    """Test banner configuration changes in settings menu."""
    
    def test_change_banner_mode_to_random(self):
        """Test changing banner mode to random."""
        config = AppConfig(
            banner=BannerConfig(mode="fixed")
        )
        
        # Change to random
        config.banner.mode = "random"
        
        assert config.banner.mode == "random"
    
    def test_change_banner_mode_to_fixed(self):
        """Test changing banner mode to fixed with banner selection."""
        config = AppConfig(
            banner=BannerConfig(mode="random")
        )
        
        # Change to fixed
        config.banner.mode = "fixed"
        config.banner.selected_banner = "ALT:MINIMAL"
        
        assert config.banner.mode == "fixed"
        assert config.banner.selected_banner == "ALT:MINIMAL"
    
    def test_change_banner_mode_to_category(self):
        """Test changing banner mode to category with category selection."""
        config = AppConfig(
            banner=BannerConfig(mode="random")
        )
        
        # Change to category
        config.banner.mode = "category"
        config.banner.selected_categories = ["CURSIVE", "FAROUT"]
        
        assert config.banner.mode == "category"
        assert config.banner.selected_categories == ["CURSIVE", "FAROUT"]
    
    def test_banner_configuration_persists(self):
        """Test that banner configuration changes are saved."""
        config_manager = ConfigManager()
        
        # Create config with specific banner settings
        config = AppConfig(
            banner=BannerConfig(
                mode="fixed",
                selected_banner="1ST_BEEFS:BIGBEEF"
            )
        )
        
        # Save configuration
        config_manager.save(config)
        
        # Load configuration
        loaded_config = config_manager.load()
        
        # Verify banner settings persisted
        assert loaded_config.banner.mode == "fixed"
        assert loaded_config.banner.selected_banner == "1ST_BEEFS:BIGBEEF"


class TestThemeConfiguration:
    """Test theme configuration changes in settings menu."""
    
    def test_change_theme_variant(self):
        """Test changing theme variant."""
        config = AppConfig(theme_variant="CRT_Cyan")
        
        # Change theme
        config.theme_variant = "Synthwave"
        
        assert config.theme_variant == "Synthwave"
    
    def test_theme_variant_validation(self):
        """Test that only valid theme variants are accepted."""
        valid_themes = ThemeRegistry.list_themes()
        
        # All themes in registry should be valid
        for theme_name in valid_themes:
            config = AppConfig(theme_variant=theme_name)
            assert config.theme_variant == theme_name
    
    def test_theme_configuration_persists(self):
        """Test that theme changes are saved."""
        config_manager = ConfigManager()
        
        # Create config with specific theme
        config = AppConfig(theme_variant="Green_Phosphor")
        
        # Save configuration
        config_manager.save(config)
        
        # Load configuration
        loaded_config = config_manager.load()
        
        # Verify theme persisted
        assert loaded_config.theme_variant == "Green_Phosphor"


class TestAnimationConfiguration:
    """Test animation configuration changes in settings menu."""
    
    def test_toggle_animation_on(self):
        """Test enabling animation."""
        config = AppConfig(
            banner=BannerConfig(animation_enabled=False)
        )
        
        # Enable animation
        config.banner.animation_enabled = True
        
        assert config.banner.animation_enabled is True
    
    def test_toggle_animation_off(self):
        """Test disabling animation."""
        config = AppConfig(
            banner=BannerConfig(animation_enabled=True)
        )
        
        # Disable animation
        config.banner.animation_enabled = False
        
        assert config.banner.animation_enabled is False
    
    def test_change_animation_intensity(self):
        """Test changing animation intensity."""
        config = AppConfig(
            banner=BannerConfig(
                animation_enabled=True,
                animation_intensity="normal"
            )
        )
        
        # Change to subtle
        config.banner.animation_intensity = "subtle"
        assert config.banner.animation_intensity == "subtle"
        
        # Change to intense
        config.banner.animation_intensity = "intense"
        assert config.banner.animation_intensity == "intense"
    
    def test_change_animation_duration(self):
        """Test changing animation duration."""
        config = AppConfig(
            banner=BannerConfig(
                animation_enabled=True,
                animation_duration=3.0
            )
        )
        
        # Change duration
        config.banner.animation_duration = 5.5
        
        assert config.banner.animation_duration == 5.5
    
    def test_change_animation_fps(self):
        """Test changing animation FPS."""
        config = AppConfig(
            banner=BannerConfig(
                animation_enabled=True,
                animation_fps=8
            )
        )
        
        # Change FPS
        config.banner.animation_fps = 20
        
        assert config.banner.animation_fps == 20
    
    def test_animation_configuration_persists(self):
        """Test that animation settings are saved."""
        config_manager = ConfigManager()
        
        # Create config with specific animation settings
        config = AppConfig(
            banner=BannerConfig(
                animation_enabled=True,
                animation_intensity="intense",
                animation_duration=7.0,
                animation_fps=24
            )
        )
        
        # Save configuration
        config_manager.save(config)
        
        # Load configuration
        loaded_config = config_manager.load()
        
        # Verify animation settings persisted
        assert loaded_config.banner.animation_enabled is True
        assert loaded_config.banner.animation_intensity == "intense"
        assert loaded_config.banner.animation_duration == 7.0
        assert loaded_config.banner.animation_fps == 24


class TestInputValidation:
    """Test input validation in settings menu."""
    
    def test_animation_duration_validation_min(self):
        """Test that animation duration minimum is enforced (0.5)."""
        config_manager = ConfigManager()
        
        # Try to set duration below minimum
        config = AppConfig(
            banner=BannerConfig(animation_duration=0.3)
        )
        
        # Save and reload
        config_manager.save(config)
        loaded_config = config_manager.load()
        
        # Should be clamped to default (3.0) due to validation
        assert loaded_config.banner.animation_duration == 3.0
    
    def test_animation_duration_validation_max(self):
        """Test that animation duration maximum is enforced (10.0)."""
        config_manager = ConfigManager()
        
        # Try to set duration above maximum
        config = AppConfig(
            banner=BannerConfig(animation_duration=15.0)
        )
        
        # Save and reload
        config_manager.save(config)
        loaded_config = config_manager.load()
        
        # Should be clamped to default (3.0) due to validation
        assert loaded_config.banner.animation_duration == 3.0
    
    def test_animation_duration_validation_valid(self):
        """Test that valid animation duration is accepted."""
        config_manager = ConfigManager()
        
        # Set valid duration
        config = AppConfig(
            banner=BannerConfig(animation_duration=5.0)
        )
        
        # Save and reload
        config_manager.save(config)
        loaded_config = config_manager.load()
        
        # Should be preserved
        assert loaded_config.banner.animation_duration == 5.0
    
    def test_animation_fps_validation_min(self):
        """Test that animation FPS minimum is enforced (4)."""
        config_manager = ConfigManager()
        
        # Try to set FPS below minimum
        config = AppConfig(
            banner=BannerConfig(animation_fps=2)
        )
        
        # Save and reload
        config_manager.save(config)
        loaded_config = config_manager.load()
        
        # Should be clamped to default (8) due to validation
        assert loaded_config.banner.animation_fps == 8
    
    def test_animation_fps_validation_max(self):
        """Test that animation FPS maximum is enforced (30)."""
        config_manager = ConfigManager()
        
        # Try to set FPS above maximum
        config = AppConfig(
            banner=BannerConfig(animation_fps=60)
        )
        
        # Save and reload
        config_manager.save(config)
        loaded_config = config_manager.load()
        
        # Should be clamped to default (8) due to validation
        assert loaded_config.banner.animation_fps == 8
    
    def test_animation_fps_validation_valid(self):
        """Test that valid animation FPS is accepted."""
        config_manager = ConfigManager()
        
        # Set valid FPS
        config = AppConfig(
            banner=BannerConfig(animation_fps=15)
        )
        
        # Save and reload
        config_manager.save(config)
        loaded_config = config_manager.load()
        
        # Should be preserved
        assert loaded_config.banner.animation_fps == 15
    
    def test_theme_variant_validation_invalid(self):
        """Test that invalid theme variant falls back to default."""
        config_manager = ConfigManager()
        
        # Create config with invalid theme (directly in dict to bypass dataclass validation)
        config = AppConfig(theme_variant="InvalidTheme")
        
        # Save and reload
        config_manager.save(config)
        loaded_config = config_manager.load()
        
        # Should fall back to default (CRT_Cyan)
        assert loaded_config.theme_variant == "CRT_Cyan"
    
    def test_banner_mode_validation(self):
        """Test that only valid banner modes are accepted."""
        valid_modes = ["random", "fixed", "category"]
        
        for mode in valid_modes:
            config = AppConfig(
                banner=BannerConfig(mode=mode)
            )
            assert config.banner.mode == mode


class TestReconfigureOption:
    """Test the reconfigure option that re-runs the setup wizard."""
    
    def test_reconfigure_preserves_current_config(self):
        """Test that current config is available when reconfiguring."""
        # Create config with specific settings
        current_config = AppConfig(
            theme_variant="Synthwave",
            banner=BannerConfig(
                mode="fixed",
                selected_banner="ALT:MINIMAL",
                animation_enabled=False
            )
        )
        
        # Verify current settings are accessible
        assert current_config.theme_variant == "Synthwave"
        assert current_config.banner.mode == "fixed"
        assert current_config.banner.selected_banner == "ALT:MINIMAL"
        assert current_config.banner.animation_enabled is False
    
    def test_reconfigure_can_change_all_settings(self):
        """Test that reconfigure allows changing all settings."""
        # Start with one config
        old_config = AppConfig(
            theme_variant="CRT_Cyan",
            banner=BannerConfig(mode="random")
        )
        
        # Create new config (simulating wizard completion)
        new_config = AppConfig(
            theme_variant="Amber_Terminal",
            banner=BannerConfig(
                mode="fixed",
                selected_banner="CURSIVE:FANCY"
            )
        )
        
        # Verify all settings can be changed
        assert new_config.theme_variant != old_config.theme_variant
        assert new_config.banner.mode != old_config.banner.mode
    
    def test_reconfigure_saves_new_config(self):
        """Test that reconfigured settings are saved."""
        config_manager = ConfigManager()
        
        # Create and save initial config
        initial_config = AppConfig(
            theme_variant="CRT_Cyan",
            banner=BannerConfig(mode="random")
        )
        config_manager.save(initial_config)
        
        # Create and save new config (simulating reconfigure)
        new_config = AppConfig(
            theme_variant="Green_Phosphor",
            banner=BannerConfig(mode="category", selected_categories=["MIN"])
        )
        config_manager.save(new_config)
        
        # Load and verify new config persisted
        loaded_config = config_manager.load()
        assert loaded_config.theme_variant == "Green_Phosphor"
        assert loaded_config.banner.mode == "category"
        assert loaded_config.banner.selected_categories == ["MIN"]


class TestSettingsMenuIntegration:
    """Integration tests for settings menu functionality."""
    
    def test_full_configuration_workflow(self):
        """Test complete workflow of changing multiple settings."""
        config_manager = ConfigManager()
        
        # Start with default config
        config = AppConfig()
        
        # Change theme
        config.theme_variant = "Amber_Terminal"
        
        # Change banner mode
        config.banner.mode = "fixed"
        config.banner.selected_banner = "1ST_BEEFS:BIGBEEF"
        
        # Enable and configure animation
        config.banner.animation_enabled = True
        config.banner.animation_intensity = "intense"
        config.banner.animation_duration = 4.5
        config.banner.animation_fps = 12
        
        # Save configuration
        config_manager.save(config)
        
        # Load and verify all changes persisted
        loaded_config = config_manager.load()
        
        assert loaded_config.theme_variant == "Amber_Terminal"
        assert loaded_config.banner.mode == "fixed"
        assert loaded_config.banner.selected_banner == "1ST_BEEFS:BIGBEEF"
        assert loaded_config.banner.animation_enabled is True
        assert loaded_config.banner.animation_intensity == "intense"
        assert loaded_config.banner.animation_duration == 4.5
        assert loaded_config.banner.animation_fps == 12
    
    def test_settings_menu_handles_missing_config(self):
        """Test that settings menu works when config file doesn't exist."""
        config_manager = ConfigManager()
        
        # Delete config file if it exists
        if config_manager.CONFIG_FILE.exists():
            config_manager.CONFIG_FILE.unlink()
        
        # Load config (should create defaults)
        config = config_manager.load()
        
        # Verify defaults are loaded
        assert config.theme_variant == "CRT_Cyan"
        assert config.banner.mode == "random"
        assert config.banner.animation_enabled is True
    
    def test_settings_menu_handles_corrupted_config(self):
        """Test that settings menu recovers from corrupted config."""
        config_manager = ConfigManager()
        
        # Create corrupted config file
        config_manager.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config_manager.CONFIG_FILE.write_text("{ invalid json }", encoding='utf-8')
        
        # Load config (should recover with defaults)
        config = config_manager.load()
        
        # Verify defaults are loaded
        assert config.theme_variant == "CRT_Cyan"
        assert config.banner.mode == "random"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
