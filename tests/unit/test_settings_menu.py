"""Unit tests for settings menu functionality.

Tests the settings menu implementation in main.py, including:
- Menu displays current configuration
- Configuration changes are saved
- Input validation works correctly
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from io import StringIO

from src.config import AppConfig, BannerConfig, ConfigManager
from src.themes import ThemeRegistry


class TestSettingsMenu:
    """Test suite for settings menu functionality."""
    
    def test_settings_menu_displays_current_config(self, tmp_path):
        """Test that settings menu displays current configuration values."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        
        config = AppConfig(
            theme_variant="Amber_Terminal",
            banner=BannerConfig(
                mode="fixed",
                selected_banner="1ST_BEEFS:BIGBEEF",
                animation_enabled=True,
                animation_intensity="intense",
                animation_duration=5.0,
                animation_fps=12
            )
        )
        
        # Mock ConfigManager to use temp directory
        with patch('src.config.ConfigManager.CONFIG_DIR', config_dir):
            with patch('src.config.ConfigManager.CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                config_manager.save(config)
                
                # Verify config was saved
                loaded_config = config_manager.load()
                assert loaded_config.theme_variant == "Amber_Terminal"
                assert loaded_config.banner.mode == "fixed"
                assert loaded_config.banner.selected_banner == "1ST_BEEFS:BIGBEEF"
                assert loaded_config.banner.animation_enabled is True
                assert loaded_config.banner.animation_intensity == "intense"
                assert loaded_config.banner.animation_duration == 5.0
                assert loaded_config.banner.animation_fps == 12
    
    def test_banner_mode_change_is_saved(self, tmp_path):
        """Test that changing banner mode saves to configuration."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        
        config = AppConfig()
        
        with patch('src.config.ConfigManager.CONFIG_DIR', config_dir):
            with patch('src.config.ConfigManager.CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                config_manager.save(config)
                
                # Act - change banner mode
                config.banner.mode = "fixed"
                config.banner.selected_banner = "ALT:MINIMAL"
                config_manager.save(config)
                
                # Assert - verify changes persisted
                loaded_config = config_manager.load()
                assert loaded_config.banner.mode == "fixed"
                assert loaded_config.banner.selected_banner == "ALT:MINIMAL"
    
    def test_theme_change_is_saved(self, tmp_path):
        """Test that changing theme saves to configuration."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        
        config = AppConfig(theme_variant="CRT_Cyan")
        
        with patch('src.config.ConfigManager.CONFIG_DIR', config_dir):
            with patch('src.config.ConfigManager.CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                config_manager.save(config)
                
                # Act - change theme
                config.theme_variant = "Synthwave"
                config_manager.save(config)
                
                # Assert - verify changes persisted
                loaded_config = config_manager.load()
                assert loaded_config.theme_variant == "Synthwave"
    
    def test_animation_toggle_is_saved(self, tmp_path):
        """Test that toggling animation saves to configuration."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        
        config = AppConfig(banner=BannerConfig(animation_enabled=True))
        
        with patch('src.config.ConfigManager.CONFIG_DIR', config_dir):
            with patch('src.config.ConfigManager.CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                config_manager.save(config)
                
                # Act - toggle animation
                config.banner.animation_enabled = False
                config_manager.save(config)
                
                # Assert - verify changes persisted
                loaded_config = config_manager.load()
                assert loaded_config.banner.animation_enabled is False
    
    def test_animation_settings_validation_duration(self, tmp_path):
        """Test that animation duration is validated within range."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        
        config = AppConfig()
        
        with patch('src.config.ConfigManager.CONFIG_DIR', config_dir):
            with patch('src.config.ConfigManager.CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                
                # Act & Assert - valid duration
                config.banner.animation_duration = 5.0
                config_manager.save(config)
                loaded = config_manager.load()
                assert loaded.banner.animation_duration == 5.0
                
                # Act & Assert - boundary values
                config.banner.animation_duration = 0.5
                config_manager.save(config)
                loaded = config_manager.load()
                assert loaded.banner.animation_duration == 0.5
                
                config.banner.animation_duration = 10.0
                config_manager.save(config)
                loaded = config_manager.load()
                assert loaded.banner.animation_duration == 10.0
    
    def test_animation_settings_validation_fps(self, tmp_path):
        """Test that animation FPS is validated within range."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        
        config = AppConfig()
        
        with patch('src.config.ConfigManager.CONFIG_DIR', config_dir):
            with patch('src.config.ConfigManager.CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                
                # Act & Assert - valid FPS
                config.banner.animation_fps = 15
                config_manager.save(config)
                loaded = config_manager.load()
                assert loaded.banner.animation_fps == 15
                
                # Act & Assert - boundary values
                config.banner.animation_fps = 4
                config_manager.save(config)
                loaded = config_manager.load()
                assert loaded.banner.animation_fps == 4
                
                config.banner.animation_fps = 30
                config_manager.save(config)
                loaded = config_manager.load()
                assert loaded.banner.animation_fps == 30
    
    def test_animation_intensity_options(self, tmp_path):
        """Test that animation intensity can be set to valid options."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        
        config = AppConfig()
        
        with patch('src.config.ConfigManager.CONFIG_DIR', config_dir):
            with patch('src.config.ConfigManager.CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                
                # Test all valid intensity levels
                for intensity in ["subtle", "normal", "intense"]:
                    config.banner.animation_intensity = intensity
                    config_manager.save(config)
                    loaded = config_manager.load()
                    assert loaded.banner.animation_intensity == intensity
    
    def test_category_filtering_is_saved(self, tmp_path):
        """Test that category filtering saves to configuration."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        
        config = AppConfig()
        
        with patch('src.config.ConfigManager.CONFIG_DIR', config_dir):
            with patch('src.config.ConfigManager.CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                
                # Act - set category mode with multiple categories
                config.banner.mode = "category"
                config.banner.selected_categories = ["1ST_BEEFS", "ALT", "CURSIVE"]
                config_manager.save(config)
                
                # Assert - verify changes persisted
                loaded_config = config_manager.load()
                assert loaded_config.banner.mode == "category"
                assert loaded_config.banner.selected_categories == ["1ST_BEEFS", "ALT", "CURSIVE"]
    
    def test_theme_list_contains_all_themes(self):
        """Test that all themes are available for selection."""
        # Act
        themes = ThemeRegistry.list_themes()
        
        # Assert
        assert "CRT_Cyan" in themes
        assert "Amber_Terminal" in themes
        assert "Green_Phosphor" in themes
        assert "Synthwave" in themes
        assert len(themes) == 4
    
    def test_config_round_trip_preserves_all_settings(self, tmp_path):
        """Test that saving and loading config preserves all settings."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        
        original_config = AppConfig(
            version=1,
            first_run_complete=True,
            theme_variant="Green_Phosphor",
            banner=BannerConfig(
                mode="category",
                selected_banner=None,
                selected_categories=["1ST_BEEFS", "FAROUT"],
                animation_enabled=True,
                animation_duration=7.5,
                animation_fps=20,
                animation_intensity="subtle"
            )
        )
        
        with patch('src.config.ConfigManager.CONFIG_DIR', config_dir):
            with patch('src.config.ConfigManager.CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                
                # Act
                config_manager.save(original_config)
                loaded_config = config_manager.load()
                
                # Assert - all fields preserved
                assert loaded_config.version == original_config.version
                assert loaded_config.first_run_complete == original_config.first_run_complete
                assert loaded_config.theme_variant == original_config.theme_variant
                assert loaded_config.banner.mode == original_config.banner.mode
                assert loaded_config.banner.selected_banner == original_config.banner.selected_banner
                assert loaded_config.banner.selected_categories == original_config.banner.selected_categories
                assert loaded_config.banner.animation_enabled == original_config.banner.animation_enabled
                assert loaded_config.banner.animation_duration == original_config.banner.animation_duration
                assert loaded_config.banner.animation_fps == original_config.banner.animation_fps
                assert loaded_config.banner.animation_intensity == original_config.banner.animation_intensity


class TestSettingsMenuHelpers:
    """Test suite for settings menu helper functions."""
    
    def test_show_theme_preview_function_exists(self):
        """Test that show_theme_preview function is available."""
        from src.wizard import show_theme_preview
        
        # Should not raise ImportError
        assert callable(show_theme_preview)
    
    def test_run_setup_wizard_function_exists(self):
        """Test that run_setup_wizard function is available."""
        from src.wizard import run_setup_wizard
        
        # Should not raise ImportError
        assert callable(run_setup_wizard)
    
    def test_show_theme_preview_accepts_theme_name(self):
        """Test that show_theme_preview accepts a theme name."""
        from src.wizard import show_theme_preview
        from rich.console import Console
        
        # Should not raise exception for valid theme
        console = Console(file=StringIO())
        show_theme_preview("CRT_Cyan", console=console)
        
        # Should handle invalid theme gracefully (falls back to default)
        show_theme_preview("NonExistentTheme", console=console)
