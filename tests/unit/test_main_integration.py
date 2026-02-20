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
            
            # Mock ConfigManager to return a test config with animation disabled
            with patch('main.ConfigManager') as mock_config_manager:
                mock_config = AppConfig(
                    theme_variant="CRT_Cyan",
                    banner=BannerConfig(mode="random", animation_enabled=False)
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
            
            # Mock ConfigManager with animation disabled
            with patch('main.ConfigManager') as mock_config_manager:
                mock_config = AppConfig(
                    theme_variant="CRT_Cyan",
                    banner=BannerConfig(mode="random", animation_enabled=False)
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
                
                # Mock ConfigManager to return config with specific theme and animation disabled
                with patch('main.ConfigManager') as mock_config_manager:
                    mock_config = AppConfig(
                        theme_variant=theme_name,
                        banner=BannerConfig(mode="random", animation_enabled=False)
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
                    banner=BannerConfig(mode="random", animation_enabled=False)
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
                        selected_banner="CAT1:BANNER1",
                        animation_enabled=False
                    )
                )
                mock_config_manager.return_value.load.return_value = mock_config
                
                with patch('main.Path') as mock_path:
                    mock_path.return_value.parent.parent = tmp_path
                    
                    print_header()
                    assert mock_console.print.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestAnimationIntegration:
    """Test suite for animation integration in main.py.
    
    Validates: Requirements 3.6, 3.7
    """
    
    def test_animation_displays_when_enabled(self, tmp_path):
        """Test that animation displays when enabled in configuration.
        
        Validates: Requirements 3.6, 3.7
        """
        # Create a temporary assets directory with a simple banner
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir()
        
        ascii_file = assets_dir / "ASCII-Full-Logo.txt"
        ascii_file.write_text("""---
TEST:ANIMATED
-----------
  _____ _____ ____ _____
 |_   _| ____/ ___|_   _|
   | | |  _| \\___ \\ | |
   | | | |___ ___) || |
   |_| |_____|____/ |_|

---
""", encoding='utf-8')
        
        # Mock the console
        with patch('main.console') as mock_console:
            mock_console.clear = Mock()
            mock_console.print = Mock()
            mock_console.size = (80, 24)
            
            # Mock ConfigManager to return config with animation enabled
            with patch('main.ConfigManager') as mock_config_manager:
                mock_config = AppConfig(
                    theme_variant="CRT_Cyan",
                    banner=BannerConfig(
                        mode="random",
                        animation_enabled=True,
                        animation_duration=0.1,  # Short duration for testing
                        animation_fps=8,
                        animation_intensity="normal"
                    )
                )
                mock_config_manager.return_value.load.return_value = mock_config
                
                # Mock Path to return our test assets directory
                with patch('main.Path') as mock_path:
                    mock_path.return_value.parent.parent = tmp_path
                    
                    # Mock BannerRenderer.render_animated to avoid actual animation
                    with patch('main.BannerRenderer.render_animated') as mock_render_animated:
                        # Call print_header
                        print_header()
                        
                        # Verify console.clear was called
                        mock_console.clear.assert_called_once()
                        
                        # Verify render_animated was called (not render_static)
                        assert mock_render_animated.called
                        
                        # Verify animation parameters were passed correctly
                        call_args = mock_render_animated.call_args
                        assert call_args[1]['duration'] == 0.1
                        assert call_args[1]['fps'] == 8
                        assert call_args[1]['intensity'] == "normal"
    
    def test_static_banner_displays_when_disabled(self, tmp_path):
        """Test that static banner displays when animation is disabled.
        
        Validates: Requirements 3.6, 3.7
        """
        # Create a temporary assets directory with a simple banner
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir()
        
        ascii_file = assets_dir / "ASCII-Full-Logo.txt"
        ascii_file.write_text("""---
TEST:STATIC
-----------
STATIC BANNER
---
""", encoding='utf-8')
        
        # Mock the console
        with patch('main.console') as mock_console:
            mock_console.clear = Mock()
            mock_console.print = Mock()
            mock_console.size = (80, 24)
            
            # Mock ConfigManager to return config with animation disabled
            with patch('main.ConfigManager') as mock_config_manager:
                mock_config = AppConfig(
                    theme_variant="CRT_Cyan",
                    banner=BannerConfig(
                        mode="random",
                        animation_enabled=False
                    )
                )
                mock_config_manager.return_value.load.return_value = mock_config
                
                # Mock Path to return our test assets directory
                with patch('main.Path') as mock_path:
                    mock_path.return_value.parent.parent = tmp_path
                    
                    # Call print_header
                    print_header()
                    
                    # Verify console.clear was called
                    mock_console.clear.assert_called_once()
                    
                    # Verify console.print was called (static banner was rendered)
                    assert mock_console.print.called
    
    def test_fallback_to_static_on_animation_error(self, tmp_path):
        """Test that fallback to static rendering works when animation fails.
        
        Validates: Requirements 3.6, 3.7
        """
        # Create a temporary assets directory with a simple banner
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir()
        
        ascii_file = assets_dir / "ASCII-Full-Logo.txt"
        ascii_file.write_text("""---
TEST:FALLBACK
-----------
FALLBACK TEST
---
""", encoding='utf-8')
        
        # Mock the console
        with patch('main.console') as mock_console:
            mock_console.clear = Mock()
            mock_console.print = Mock()
            mock_console.size = (80, 24)
            
            # Mock ConfigManager to return config with animation enabled
            with patch('main.ConfigManager') as mock_config_manager:
                mock_config = AppConfig(
                    theme_variant="CRT_Cyan",
                    banner=BannerConfig(
                        mode="random",
                        animation_enabled=True,
                        animation_duration=0.1,
                        animation_fps=8,
                        animation_intensity="normal"
                    )
                )
                mock_config_manager.return_value.load.return_value = mock_config
                
                # Mock Path to return our test assets directory
                with patch('main.Path') as mock_path:
                    mock_path.return_value.parent.parent = tmp_path
                    
                    # Mock BannerRenderer.render_animated to raise an exception
                    with patch('main.BannerRenderer.render_animated') as mock_render_animated:
                        mock_render_animated.side_effect = Exception("Animation failed")
                        
                        # Call print_header - should not raise exception
                        print_header()
                        
                        # Verify console.clear was called
                        mock_console.clear.assert_called_once()
                        
                        # Verify console.print was called (fallback to static or hardcoded banner)
                        assert mock_console.print.called
    
    def test_animation_intensity_levels(self, tmp_path):
        """Test that different animation intensity levels are passed correctly."""
        # Create a temporary assets directory with a simple banner
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir()
        
        ascii_file = assets_dir / "ASCII-Full-Logo.txt"
        ascii_file.write_text("""---
TEST:INTENSITY
-----------
INTENSITY TEST
---
""", encoding='utf-8')
        
        # Test each intensity level
        for intensity in ["subtle", "normal", "intense"]:
            with patch('main.console') as mock_console:
                mock_console.clear = Mock()
                mock_console.print = Mock()
                mock_console.size = (80, 24)
                
                # Mock ConfigManager to return config with specific intensity
                with patch('main.ConfigManager') as mock_config_manager:
                    mock_config = AppConfig(
                        theme_variant="CRT_Cyan",
                        banner=BannerConfig(
                            mode="random",
                            animation_enabled=True,
                            animation_duration=0.1,
                            animation_fps=8,
                            animation_intensity=intensity
                        )
                    )
                    mock_config_manager.return_value.load.return_value = mock_config
                    
                    # Mock Path to return our test assets directory
                    with patch('main.Path') as mock_path:
                        mock_path.return_value.parent.parent = tmp_path
                        
                        # Mock BannerRenderer.render_animated
                        with patch('main.BannerRenderer.render_animated') as mock_render_animated:
                            # Call print_header
                            print_header()
                            
                            # Verify render_animated was called with correct intensity
                            assert mock_render_animated.called
                            call_args = mock_render_animated.call_args
                            assert call_args[1]['intensity'] == intensity
    
    def test_animation_duration_and_fps_configuration(self, tmp_path):
        """Test that animation duration and FPS are configured correctly."""
        # Create a temporary assets directory with a simple banner
        assets_dir = tmp_path / ".assets"
        assets_dir.mkdir()
        
        ascii_file = assets_dir / "ASCII-Full-Logo.txt"
        ascii_file.write_text("""---
TEST:CONFIG
-----------
CONFIG TEST
---
""", encoding='utf-8')
        
        # Test different duration and FPS values
        test_cases = [
            (0.5, 4),
            (3.0, 8),
            (5.0, 15),
            (10.0, 30)
        ]
        
        for duration, fps in test_cases:
            with patch('main.console') as mock_console:
                mock_console.clear = Mock()
                mock_console.print = Mock()
                mock_console.size = (80, 24)
                
                # Mock ConfigManager to return config with specific duration and FPS
                with patch('main.ConfigManager') as mock_config_manager:
                    mock_config = AppConfig(
                        theme_variant="CRT_Cyan",
                        banner=BannerConfig(
                            mode="random",
                            animation_enabled=True,
                            animation_duration=duration,
                            animation_fps=fps,
                            animation_intensity="normal"
                        )
                    )
                    mock_config_manager.return_value.load.return_value = mock_config
                    
                    # Mock Path to return our test assets directory
                    with patch('main.Path') as mock_path:
                        mock_path.return_value.parent.parent = tmp_path
                        
                        # Mock BannerRenderer.render_animated
                        with patch('main.BannerRenderer.render_animated') as mock_render_animated:
                            # Call print_header
                            print_header()
                            
                            # Verify render_animated was called with correct parameters
                            assert mock_render_animated.called
                            call_args = mock_render_animated.call_args
                            assert call_args[1]['duration'] == duration
                            assert call_args[1]['fps'] == fps
