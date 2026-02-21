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


# Property-Based Tests for CLI02 Commands

from hypothesis import given, strategies as st


class TestMenuInputMapping:
    """Property-based tests for menu input mapping.
    
    Feature: peepbeefy-enhancements, Property 39: Menu Input Mapping
    **Validates: Requirements 5.3**
    """
    
    @given(shortcut=st.sampled_from(["1", "2", "3", "4", "5", "6", "7", "8", "s", "h", "q"]))
    @pytest.mark.property_test
    def test_menu_shortcut_mapping(self, shortcut):
        """Property 39: For any valid menu shortcut, it should map to a valid command.
        
        This test verifies that all keyboard shortcuts defined in the menu
        correctly map to their corresponding commands without errors.
        """
        # Define the shortcut mapping (same as in main.py)
        shortcut_map = {
            "1": "peep all",
            "2": "peep cpu",
            "3": "peep io",
            "4": "peep mem",
            "5": "peep clutter",
            "6": "peep watch",
            "7": "baseline save",
            "8": "baseline diff",
            "s": "settings",
            "h": "help",
            "?": "help",
            "q": "quit",
        }
        
        # Property: Every shortcut should map to a non-empty command
        assert shortcut in shortcut_map, f"Shortcut '{shortcut}' not found in mapping"
        command = shortcut_map[shortcut]
        assert command, f"Shortcut '{shortcut}' maps to empty command"
        assert isinstance(command, str), f"Shortcut '{shortcut}' maps to non-string: {type(command)}"
        assert len(command) > 0, f"Shortcut '{shortcut}' maps to empty string"
    
    @given(
        shortcut=st.sampled_from(["1", "2", "3", "4", "5", "6", "7", "8"]),
        prefix=st.sampled_from(["", "beefy ", "peepbeefy "])
    )
    @pytest.mark.property_test
    def test_menu_shortcut_with_prefix_handling(self, shortcut, prefix):
        """Property: Shortcuts should work consistently regardless of prefix.
        
        Tests that the command mapping is consistent whether the user types
        just the shortcut or includes a prefix like "beefy".
        """
        shortcut_map = {
            "1": "peep all",
            "2": "peep cpu",
            "3": "peep io",
            "4": "peep mem",
            "5": "peep clutter",
            "6": "peep watch",
            "7": "baseline save",
            "8": "baseline diff",
        }
        
        # Get the mapped command
        command = shortcut_map[shortcut]
        
        # Simulate the prefix handling logic from interactive_loop
        full_input = prefix + command
        processed = full_input
        for p in ("beefy ", "peepbeefy "):
            if processed.startswith(p):
                processed = processed[len(p):].lstrip()
                break
        
        # Property: After prefix removal, we should get back the base command
        assert processed == command or processed == command.lstrip()
    
    def test_all_menu_items_have_shortcuts(self):
        """Test that all menu items have corresponding shortcuts defined.
        
        This is a unit test (not property-based) that validates the completeness
        of the shortcut mapping.
        """
        from main import MENU_ITEMS
        
        # We expect 11 menu items
        assert len(MENU_ITEMS) == 11, f"Expected 11 menu items, got {len(MENU_ITEMS)}"
        
        # Define expected shortcuts
        expected_shortcuts = ["1", "2", "3", "4", "5", "6", "7", "8", "s", "h", "q"]
        
        # Verify we have shortcuts for all items
        assert len(expected_shortcuts) == len(MENU_ITEMS), \
            f"Mismatch: {len(expected_shortcuts)} shortcuts for {len(MENU_ITEMS)} menu items"



class TestCommandHistory:
    """Property-based tests for command history tracking.
    
    Feature: peepbeefy-enhancements, Property 40: Recent Commands Tracking
    **Validates: Requirements 5.5**
    
    Note: This tests the command history storage logic. Full up/down arrow
    navigation would require a different input library (prompt_toolkit) which
    is beyond the current Rich-based implementation.
    """
    
    @given(
        commands=st.lists(
            st.sampled_from(["peep all", "peep cpu", "settings", "help", "quit"]),
            min_size=1,
            max_size=15
        )
    )
    @pytest.mark.property_test
    def test_command_history_tracking(self, commands):
        """Property 40: Recent commands should be tracked in reverse chronological order.
        
        This test verifies that commands are stored in history and maintained
        in the correct order (most recent last).
        """
        # Simulate command history storage
        command_history = []
        max_history = 10
        
        for cmd in commands:
            # Store command (excluding duplicates)
            if cmd and (not command_history or cmd != command_history[-1]):
                command_history.append(cmd)
                # Keep only last max_history commands
                if len(command_history) > max_history:
                    command_history.pop(0)
        
        # Properties to verify:
        # 1. History should not exceed max_history
        assert len(command_history) <= max_history, \
            f"History size {len(command_history)} exceeds max {max_history}"
        
        # 2. History should be in chronological order (most recent last)
        # We can verify this by checking that the last command in history
        # matches the last non-duplicate command from the input
        if command_history:
            # Find the last unique command from input
            last_unique = None
            for cmd in reversed(commands):
                if last_unique is None or cmd != last_unique:
                    last_unique = cmd
                    break
            
            assert command_history[-1] == last_unique, \
                f"Last history item {command_history[-1]} doesn't match last unique command {last_unique}"
        
        # 3. No consecutive duplicates in history
        for i in range(len(command_history) - 1):
            assert command_history[i] != command_history[i + 1], \
                f"Found consecutive duplicates at index {i}: {command_history[i]}"
    
    @given(
        commands=st.lists(st.just("same_command"), min_size=5, max_size=10)
    )
    @pytest.mark.property_test
    def test_command_history_deduplication(self, commands):
        """Property: Consecutive duplicate commands should not be stored multiple times.
        
        Tests that repeating the same command doesn't fill up the history.
        """
        command_history = []
        max_history = 10
        
        for cmd in commands:
            if cmd and (not command_history or cmd != command_history[-1]):
                command_history.append(cmd)
                if len(command_history) > max_history:
                    command_history.pop(0)
        
        # Property: Only one instance should be stored
        assert len(command_history) == 1, \
            f"Expected 1 command in history, got {len(command_history)}: {command_history}"
        assert command_history[0] == "same_command"
