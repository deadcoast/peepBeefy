"""Integration tests for first-run wizard.

Tests the complete first-run wizard flow including configuration saving,
wizard launching, and skip functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console

from src.wizard import SetupWizard
from src.config import ConfigManager, AppConfig, BannerConfig


class TestFirstRunWizard:
    """Integration tests for the first-run setup wizard."""
    
    def test_wizard_launches_on_first_run(self, tmp_path):
        """Test wizard launches when config file doesn't exist."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_file = config_dir / "config.json"
        
        # Ensure config doesn't exist
        assert not config_file.exists()
        
        # Create ConfigManager with temporary path
        with patch.object(ConfigManager, 'CONFIG_DIR', config_dir):
            with patch.object(ConfigManager, 'CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                
                # Act & Assert
                assert config_manager.is_first_run() is True
    
    def test_configuration_saved_after_wizard(self, tmp_path):
        """Test configuration is saved after wizard completes."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_file = config_dir / "config.json"
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir(parents=True)
        
        # Create a mock console
        console = Mock(spec=Console)
        console.size = (120, 40)
        console.input = Mock(return_value="")  # Simulate Enter key
        
        # Create wizard
        wizard = SetupWizard(console, assets_dir)
        
        # Mock the wizard methods to return correct types
        with patch.object(wizard, '_show_welcome', return_value=None):
            with patch.object(wizard, '_select_theme', return_value='CRT_Cyan'):
                with patch.object(wizard, '_select_banner_mode', return_value=BannerConfig(mode='random')):
                    with patch.object(wizard, '_select_animation_preferences', return_value={
                        "enabled": True,
                        "intensity": "normal",
                        "duration": 3.0,
                        "fps": 8
                    }):
                        # Act
                        config = wizard.run()
        
        # Save configuration
        with patch.object(ConfigManager, 'CONFIG_DIR', config_dir):
            with patch.object(ConfigManager, 'CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                config_manager.save(config)
        
        # Assert
        assert config_file.exists()
        
        # Verify config was saved correctly
        with patch.object(ConfigManager, 'CONFIG_DIR', config_dir):
            with patch.object(ConfigManager, 'CONFIG_FILE', config_file):
                loaded_config = ConfigManager().load()
                assert loaded_config.first_run_complete is True
                assert loaded_config.theme_variant == 'CRT_Cyan'
                assert loaded_config.banner.mode == 'random'
    
    def test_wizard_can_be_skipped(self, tmp_path):
        """Test wizard can be skipped to use default settings."""
        # Arrange
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir(parents=True)
        
        # Create a mock console
        console = Mock(spec=Console)
        console.size = (120, 40)
        
        # Create wizard
        wizard = SetupWizard(console, assets_dir)
        
        # Mock builtins.input to raise KeyboardInterrupt (simulating Ctrl+C)
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            # Act
            config = wizard.run()
        
        # Assert - should return default configuration
        assert config.first_run_complete is True
        assert config.theme_variant == 'CRT_Cyan'
        assert config.banner.mode == 'random'
        assert config.banner.animation_enabled is True
        assert config.banner.animation_intensity == 'normal'
    
    def test_wizard_theme_selection(self, tmp_path):
        """Test theme selection step in wizard."""
        # Arrange
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir(parents=True)
        
        console = Mock(spec=Console)
        console.size = (120, 40)
        
        wizard = SetupWizard(console, assets_dir)
        
        # Mock Prompt.ask to return choice "2" (Amber_Terminal)
        with patch('rich.prompt.Prompt.ask', return_value='2'):
            # Act
            theme = wizard._select_theme()
        
        # Assert
        assert theme == 'Amber_Terminal'
    
    def test_wizard_banner_mode_selection_random(self, tmp_path):
        """Test banner mode selection with random mode."""
        # Arrange
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir(parents=True)
        
        console = Mock(spec=Console)
        console.size = (120, 40)
        
        wizard = SetupWizard(console, assets_dir)
        
        # Mock Prompt.ask to return choice "1" (random mode)
        with patch('rich.prompt.Prompt.ask', return_value='1'):
            # Act
            banner_config = wizard._select_banner_mode()
        
        # Assert
        assert banner_config.mode == 'random'
        assert banner_config.selected_banner is None
        assert banner_config.selected_categories == ['1ST_BEEFS']
    
    def test_wizard_animation_preferences_enabled(self, tmp_path):
        """Test animation preferences with animation enabled."""
        # Arrange
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir(parents=True)
        
        console = Mock(spec=Console)
        console.size = (120, 40)
        
        wizard = SetupWizard(console, assets_dir)
        
        # Mock Confirm.ask to return True (enabled)
        # Mock Prompt.ask to return choice "3" (intense)
        with patch('rich.prompt.Confirm.ask', return_value=True):
            with patch('rich.prompt.Prompt.ask', return_value='3'):
                # Act
                animation_config = wizard._select_animation_preferences()
        
        # Assert
        assert animation_config["enabled"] is True
        assert animation_config["intensity"] == 'intense'
    
    def test_wizard_animation_preferences_disabled(self, tmp_path):
        """Test animation preferences with animation disabled."""
        # Arrange
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir(parents=True)
        
        console = Mock(spec=Console)
        console.size = (120, 40)
        
        wizard = SetupWizard(console, assets_dir)
        
        # Mock Confirm.ask to return False (disabled)
        with patch('rich.prompt.Confirm.ask', return_value=False):
            # Act
            animation_config = wizard._select_animation_preferences()
        
        # Assert
        assert animation_config["enabled"] is False
        assert animation_config["intensity"] == 'normal'  # Default intensity even when disabled
    
    def test_mark_first_run_complete(self, tmp_path):
        """Test marking first run as complete."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_file = config_dir / "config.json"
        
        with patch.object(ConfigManager, 'CONFIG_DIR', config_dir):
            with patch.object(ConfigManager, 'CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                
                # Create a default config
                config = AppConfig()
                config.first_run_complete = False
                config_manager.save(config)
                
                # Act
                config_manager.mark_first_run_complete()
                
                # Assert
                loaded_config = config_manager.load()
                assert loaded_config.first_run_complete is True
    
    def test_wizard_integration_with_main(self, tmp_path):
        """Test wizard integration with main.py startup flow."""
        # Arrange
        config_dir = tmp_path / ".peepbeefy"
        config_file = config_dir / "config.json"
        
        # Ensure config doesn't exist (first run)
        assert not config_file.exists()
        
        # Create a config to save
        config = AppConfig(
            first_run_complete=True,
            theme_variant='CRT_Cyan',
            banner=BannerConfig(mode='random')
        )
        
        with patch.object(ConfigManager, 'CONFIG_DIR', config_dir):
            with patch.object(ConfigManager, 'CONFIG_FILE', config_file):
                # Act - simulate what main.py does
                config_manager = ConfigManager()
                
                # Check first run
                assert config_manager.is_first_run() is True
                
                # Save configuration (simulating wizard completion)
                config_manager.save(config)
                
                # Mark first run as complete
                config_manager.mark_first_run_complete()
                
                # Assert
                assert config_file.exists()
                loaded_config = config_manager.load()
                assert loaded_config.first_run_complete is True
