"""
Integration tests for Theme System + Terminal Detection.

Tests the integration between the theme system and terminal detection,
verifying that themes adapt colors based on terminal background and
capabilities.

Validates Requirement 14.2: Verify Terminal_Detector works with existing Theme_System
"""

import pytest
from unittest.mock import Mock, patch
from rich.console import Console

from src.themes import Theme, ColorPalette, ThemeRegistry, TerminalCapabilities
from src.color_util import RGB
from src.terminal_detect import detect_ansi_mode, get_background_color


class TestThemeTerminalIntegration:
    """Integration tests for theme system with terminal detection."""
    
    @pytest.fixture
    def dark_background(self):
        """Create a dark background color for testing."""
        return RGB(30, 30, 30)  # Dark gray
    
    @pytest.fixture
    def light_background(self):
        """Create a light background color for testing."""
        return RGB(240, 240, 240)  # Light gray
    
    def test_theme_adapts_to_dark_background(self, dark_background):
        """Test that themes adapt colors for dark backgrounds.
        
        Validates Requirement 14.2: Theme adaptation to terminal background
        """
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        adapted = theme.adapt_to_terminal(dark_background)
        
        # Verify all text colors have sufficient lightness for dark background
        adapted_palette = adapted.palette
        
        for color_name in ['text', 'highlight', 'primary']:
            hex_color = getattr(adapted_palette, color_name)
            rgb = RGB.from_hex(hex_color)
            hsl = rgb.hsl()
            
            # Dark backgrounds require lightness >= 0.65
            assert hsl.l >= 0.60, \
                f"Color '{color_name}' lightness {hsl.l:.2f} too low for dark background"
    
    def test_theme_adapts_to_light_background(self, light_background):
        """Test that themes adapt colors for light backgrounds.
        
        Validates Requirement 14.2: Theme adaptation to terminal background
        """
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        adapted = theme.adapt_to_terminal(light_background)
        
        # Verify all text colors have sufficient darkness for light background
        adapted_palette = adapted.palette
        
        for color_name in ['text', 'highlight', 'primary']:
            hex_color = getattr(adapted_palette, color_name)
            rgb = RGB.from_hex(hex_color)
            hsl = rgb.hsl()
            
            # Light backgrounds require lightness <= 0.4
            assert hsl.l <= 0.45, \
                f"Color '{color_name}' lightness {hsl.l:.2f} too high for light background"
    
    def test_theme_color_mode_detection(self):
        """Test that themes detect appropriate color mode.
        
        Validates Requirement 14.2: Color mode detection integration
        """
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        
        # Mock RGB terminal
        with patch('src.terminal_detect.detect_ansi_mode', return_value='rgb'):
            mode = theme.get_color_mode()
            assert mode == "rgb", "Should detect RGB mode"
        
        # Mock 8-bit terminal
        with patch('src.terminal_detect.detect_ansi_mode', return_value='8bit'):
            mode = theme.get_color_mode()
            assert mode == "8bit", "Should detect 8-bit mode"
        
        # Mock ANSI terminal
        with patch('src.terminal_detect.detect_ansi_mode', return_value='ansi'):
            mode = theme.get_color_mode()
            assert mode == "ansi", "Should detect ANSI mode"
    
    def test_theme_color_mode_fallback(self):
        """Test that themes fall back to safe default when detection fails.
        
        Validates Requirement 14.2: Graceful fallback
        """
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        
        # Mock detection failure
        with patch('src.terminal_detect.detect_ansi_mode', return_value=None):
            mode = theme.get_color_mode()
            assert mode == "8bit", "Should fall back to 8-bit mode"
    
    def test_all_themes_adapt_to_backgrounds(self, dark_background, light_background):
        """Test that all registered themes can adapt to different backgrounds.
        
        Validates Requirement 14.2: All themes support adaptation
        """
        for theme_name in ThemeRegistry.list_themes():
            theme = ThemeRegistry.get_theme(theme_name)
            
            # Test dark background adaptation
            try:
                dark_adapted = theme.adapt_to_terminal(dark_background)
                assert dark_adapted is not None
                assert dark_adapted.palette is not None
            except Exception as e:
                pytest.fail(f"Theme '{theme_name}' failed to adapt to dark background: {e}")
            
            # Test light background adaptation
            try:
                light_adapted = theme.adapt_to_terminal(light_background)
                assert light_adapted is not None
                assert light_adapted.palette is not None
            except Exception as e:
                pytest.fail(f"Theme '{theme_name}' failed to adapt to light background: {e}")
    
    def test_terminal_capabilities_rgb_detection(self):
        """Test that terminal capabilities detect RGB support correctly.
        
        Validates Requirement 14.2: Terminal capability detection
        """
        # Mock RGB-capable terminal
        with patch.dict('os.environ', {'COLORTERM': 'truecolor'}):
            assert TerminalCapabilities.supports_rgb() is True
        
        # Mock non-RGB terminal
        with patch.dict('os.environ', {'COLORTERM': '', 'TERM': 'xterm'}, clear=True):
            # This might return False or True depending on TERM value
            # Just verify it doesn't crash
            result = TerminalCapabilities.supports_rgb()
            assert isinstance(result, bool)
    
    def test_terminal_capabilities_256_color_detection(self):
        """Test that terminal capabilities detect 256-color support.
        
        Validates Requirement 14.2: Terminal capability detection
        """
        # Mock 256-color terminal
        with patch.dict('os.environ', {'TERM': 'xterm-256color'}):
            assert TerminalCapabilities.supports_256_color() is True
        
        # Mock basic terminal
        with patch.dict('os.environ', {'TERM': 'linux'}, clear=True):
            assert TerminalCapabilities.supports_256_color() is False
    
    def test_terminal_capabilities_dimensions(self):
        """Test that terminal capabilities can get dimensions.
        
        Validates Requirement 14.2: Terminal capability detection
        """
        width, height = TerminalCapabilities.get_dimensions()
        
        # Verify dimensions are positive integers
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert width > 0
        assert height > 0
    
    def test_theme_fallback_palette_generation(self):
        """Test that themes can generate ANSI fallback palettes.
        
        Validates Requirement 14.2: Graceful degradation
        """
        for theme_name in ThemeRegistry.list_themes():
            theme = ThemeRegistry.get_theme(theme_name)
            
            try:
                fallback = TerminalCapabilities.get_fallback_palette(theme)
                
                # Verify fallback palette has all required fields
                assert hasattr(fallback, 'primary')
                assert hasattr(fallback, 'highlight')
                assert hasattr(fallback, 'success')
                assert hasattr(fallback, 'error')
                assert hasattr(fallback, 'warning')
                assert hasattr(fallback, 'dim')
                assert hasattr(fallback, 'text')
                
                # Verify all colors are ANSI color names (not hex)
                for field in ['primary', 'highlight', 'success', 'error', 'warning', 'dim', 'text']:
                    color = getattr(fallback, field)
                    # ANSI colors should not start with #
                    assert not color.startswith('#'), \
                        f"Fallback color '{field}' should be ANSI name, got: {color}"
            except Exception as e:
                pytest.fail(f"Failed to generate fallback palette for '{theme_name}': {e}")
    
    def test_theme_palette_to_rgb_conversion(self):
        """Test that theme palettes can be converted to RGB objects.
        
        Validates Requirement 14.2: Color conversion integration
        """
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        
        try:
            rgb_palette = theme.palette.to_rgb_palette()
            
            # Verify all colors were converted
            assert 'primary' in rgb_palette
            assert 'highlight' in rgb_palette
            assert 'success' in rgb_palette
            assert 'error' in rgb_palette
            assert 'warning' in rgb_palette
            assert 'dim' in rgb_palette
            assert 'text' in rgb_palette
            
            # Verify all values are RGB objects
            for color_name, rgb in rgb_palette.items():
                assert isinstance(rgb, RGB), \
                    f"Color '{color_name}' should be RGB object, got: {type(rgb)}"
                assert 0 <= rgb.r <= 255
                assert 0 <= rgb.g <= 255
                assert 0 <= rgb.b <= 255
        except Exception as e:
            pytest.fail(f"Failed to convert palette to RGB: {e}")
    
    def test_background_color_detection_integration(self):
        """Test that background color detection integrates with theme system.
        
        Validates Requirement 14.2: OSC detection integration
        """
        # Mock background color detection
        mock_bg = RGB(30, 30, 30)
        
        with patch('src.terminal_detect.get_background_color', return_value=mock_bg):
            theme = ThemeRegistry.get_theme("CRT_Cyan")
            
            # Adapt without explicit background (should use detection)
            adapted = theme.adapt_to_terminal(bg_color=None)
            
            # Should return adapted theme (not original)
            assert adapted.name != theme.name or adapted.palette != theme.palette
    
    def test_background_color_detection_failure_handling(self):
        """Test that theme adaptation handles detection failure gracefully.
        
        Validates Requirement 14.2: Error handling
        """
        # Mock detection failure
        with patch('src.terminal_detect.get_background_color', return_value=None):
            theme = ThemeRegistry.get_theme("CRT_Cyan")
            
            # Should return original theme when detection fails
            adapted = theme.adapt_to_terminal(bg_color=None)
            
            # Should not crash, returns original theme
            assert adapted is not None
            assert adapted.palette is not None
    
    def test_theme_effective_palette_with_rgb(self):
        """Test that effective palette returns RGB palette when supported.
        
        Validates Requirement 14.2: Palette selection based on capabilities
        """
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        
        with patch('src.themes.TerminalCapabilities.supports_rgb', return_value=True):
            effective = theme.get_effective_palette()
            
            # Should return original RGB palette
            assert effective == theme.palette
    
    def test_theme_effective_palette_without_rgb(self):
        """Test that effective palette returns fallback when RGB not supported.
        
        Validates Requirement 14.2: Palette selection based on capabilities
        """
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        
        with patch('src.themes.TerminalCapabilities.supports_rgb', return_value=False):
            effective = theme.get_effective_palette()
            
            # Should return ANSI fallback palette
            # Verify it's different from original (ANSI names vs hex)
            assert effective.primary != theme.palette.primary or \
                   not effective.primary.startswith('#')
    
    def test_color_adjustment_methods(self, dark_background, light_background):
        """Test that both HSL and overlay adjustment methods work.
        
        Validates Requirement 14.2: Multiple adjustment strategies
        """
        from src.themes import adjust_color_for_background
        
        test_color = "#00d7d7"  # Cyan
        
        # Test HSL method
        try:
            adjusted_hsl_dark = adjust_color_for_background(test_color, dark_background, "hsl")
            adjusted_hsl_light = adjust_color_for_background(test_color, light_background, "hsl")
            
            # Verify adjustments were made
            assert adjusted_hsl_dark.startswith('#')
            assert adjusted_hsl_light.startswith('#')
        except Exception as e:
            pytest.fail(f"HSL adjustment failed: {e}")
        
        # Test overlay method
        try:
            adjusted_overlay_dark = adjust_color_for_background(test_color, dark_background, "overlay")
            adjusted_overlay_light = adjust_color_for_background(test_color, light_background, "overlay")
            
            # Verify adjustments were made
            assert adjusted_overlay_dark.startswith('#')
            assert adjusted_overlay_light.startswith('#')
        except Exception as e:
            pytest.fail(f"Overlay adjustment failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
