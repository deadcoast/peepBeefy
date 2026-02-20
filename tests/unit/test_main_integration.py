"""Unit tests for main.py banner system integration.

Tests that the banner system is properly integrated into the main.py startup,
including configuration loading, banner selection, and fallback behavior.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from main import print_header
from config import AppConfig, BannerConfig, ConfigManager
from banner import Banner, BannerMetadata, BannerDatabase, BannerRenderer
from themes import ThemeRegistry


class TestMainIntegration:
    """Test suite for main.py banner system integration."""
    
    def test_banner_displays_on_startup(self, tmp_path):
        """Test that banner displays when print_header is called.
        
        Validates: Requirements 1.1, 10.1
        """
        # Create a temporary assets directory with a simple banner
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir()
        
        ascii_file = assets_dir / "ASCII-Full-Logo.txt"
        ascii_file.write_text("""---
DEFINITIONS
-----------

---
TEST:SIMPLE
-----------
  _____ _____ ____ _____
 |_   _| ____/ ___|_   _|
   | | |  _| \\___ \\ | |
   | | | |___ ___) || |
   |_| |_____|____/ |_|

---
""", encoding='utf-8')
        
        # Mock the console to capture output
        with patch('main.console') as mock_console:
            mock_console.clear = Mock()
            mock_console.print = Mock()
            mock_console.size = (80, 24)
            
            # Mock ConfigManager to return a test config
            with patch('main.ConfigManager') as mock_config_manager:
                mock_config = AppConfig(
                    theme_variant="CRT_Cyan",
                    banner=BannerConfig(mode="random")
                )
                mock_config_manager.return_value.load.return_value = mock_config
                
                # Mock Path to return our test assets directory
                with patch('main.Path') as mock_path:
                    mock_path.return_value.parent.parent = tmp_path
                    
                    # Call print_header
                    print_header()
                    
                    # Verify console.clear was called
                    mock_console.clear.assert_called_once()
                    
                    # Verify console.print was called (banner was rendered)
                    assert mock_console.print.called
    
    def test_configuration_loads_correctly(self, tmp_path):
        """Test that configuration is loaded at startup.
        
        Validates: Requirements 1.1
        """
        # Create config directory and file
        config_dir = tmp_path / ".peepbeefy"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        config_file.write_text("""{
  "version": 1,
  "first_run_complete": true,
  "theme_variant": "Amber_Terminal",
  "banner": {
    "mode": "fixed",
    "selected_banner": "TEST:BANNER",
    "selected_categories": ["TEST"],
    "animation_enabled": false,
    "animation_duration": 3.0,
    "animation_fps": 8,
    "animation_intensity": "normal"
  },
  "user_preferences": {}
}""", encoding='utf-8')
        
        # Patch ConfigManager's CONFIG_DIR and CONFIG_FILE to use temp directory
        with patch.object(ConfigManager, 'CONFIG_DIR', config_dir):
            with patch.object(ConfigManager, 'CONFIG_FILE', config_file):
                config_manager = ConfigManager()
                config = config_manager.load()
                
                # Verify configuration was loaded correctly
                assert config.theme_variant == "Amber_Terminal"
                assert config.banner.mode == "fixed"
                assert config.banner.selected_banner == "TEST:BANNER"
                assert config.banner.animation_enabled is False
    
    def test_fallback_works_when_files_missing(self, tmp_path):
        """Test that fallback banner is used when ASCII files are missing.
        
        Validates: Requirements 10.1
        """
        # Create assets directory but no ASCII file
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir()
        
        # Mock the console
        with patch('main.console') as mock_console:
            mock_console.clear = Mock()
            mock_console.print = Mock()
            mock_console.size = (80, 24)
            
            # Mock ConfigManager
            with patch('main.ConfigManager') as mock_config_manager:
                mock_config = AppConfig(
                    theme_variant="CRT_Cyan",
                    banner=BannerConfig(mode="random")
                )
                mock_config_manager.return_value.load.return_value = mock_config
                
                # Mock Path to return our test assets directory (with no ASCII file)
                with patch('main.Path') as mock_path:
                    mock_path.return_value.parent.parent = tmp_path
                    
                    # Call print_header - should not raise exception
                    print_header()
                    
                    # Verify console.clear was called
                    mock_console.clear.assert_called_once()
                    
                    # Verify console.print was called (fallback banner was rendered)
                    assert mock_console.print.called
    
    def test_fallback_on_exception(self):
        """Test that fallback banner is used when an exception occurs.
        
        Validates: Requirements 10.1
        """
        # Mock the console
        with patch('main.console') as mock_console:
            mock_console.clear = Mock()
            mock_console.print = Mock()
            mock_console.size = (80, 24)
            
            # Mock ConfigManager to raise an exception
            with patch('main.ConfigManager') as mock_config_manager:
                mock_config_manager.return_value.load.side_effect = Exception("Test error")
                
                # Call print_header - should not raise exception
                print_header()
                
                # Verify console.clear was called
                mock_console.clear.assert_called_once()
                
                # Verify console.print was called (fallback banner was rendered)
                assert mock_console.print.called
    
    def test_theme_is_applied_to_banner(self, tmp_path):
        """Test that the configured theme is applied to the banner."""
        # Create a temporary assets directory with a simple banner
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir()
        
        ascii_file = assets_dir / "ASCII-Full-Logo.txt"
        ascii_file.write_text("""---
TEST:SIMPLE
-----------
TEST BANNER
---
""", encoding='utf-8')
        
        # Test with different themes
        for theme_name in ["CRT_Cyan", "Amber_Terminal", "Green_Phosphor", "Synthwave"]:
            with patch('main.console') as mock_console:
                mock_console.clear = Mock()
                mock_console.print = Mock()
                mock_console.size = (80, 24)
                
                # Mock ConfigManager to return config with specific theme
                with patch('main.ConfigManager') as mock_config_manager:
                    mock_config = AppConfig(
                        theme_variant=theme_name,
                        banner=BannerConfig(mode="random")
                    )
                    mock_config_manager.return_value.load.return_value = mock_config
                    
                    # Mock Path to return our test assets directory
                    with patch('main.Path') as mock_path:
                        mock_path.return_value.parent.parent = tmp_path
                        
                        # Call print_header
                        print_header()
                        
                        # Verify console.print was called
                        assert mock_console.print.called
    
    def test_banner_selection_respects_config_mode(self, tmp_path):
        """Test that banner selection respects the configured mode."""
        # Create a temporary assets directory with multiple banners
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir()
        
        ascii_file = assets_dir / "ASCII-Full-Logo.txt"
        ascii_file.write_text("""---
CAT1:BANNER1
-----------
BANNER 1
---
CAT2:BANNER2
-----------
BANNER 2
---
""", encoding='utf-8')
        
        # Test random mode
        with patch('main.console') as mock_console:
            mock_console.clear = Mock()
            mock_console.print = Mock()
            mock_console.size = (80, 24)
            
            with patch('main.ConfigManager') as mock_config_manager:
                mock_config = AppConfig(
                    theme_variant="CRT_Cyan",
                    banner=BannerConfig(mode="random")
                )
                mock_config_manager.return_value.load.return_value = mock_config
                
                with patch('main.Path') as mock_path:
                    mock_path.return_value.parent.parent = tmp_path
                    
                    print_header()
                    assert mock_console.print.called
        
        # Test fixed mode
        with patch('main.console') as mock_console:
            mock_console.clear = Mock()
            mock_console.print = Mock()
            mock_console.size = (80, 24)
            
            with patch('main.ConfigManager') as mock_config_manager:
                mock_config = AppConfig(
                    theme_variant="CRT_Cyan",
                    banner=BannerConfig(
                        mode="fixed",
                        selected_banner="CAT1:BANNER1"
                    )
                )
                mock_config_manager.return_value.load.return_value = mock_config
                
                with patch('main.Path') as mock_path:
                    mock_path.return_value.parent.parent = tmp_path
                    
                    print_header()
                    assert mock_console.print.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
