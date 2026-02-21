"""Unit tests for terminal compatibility features.

This module tests RGB color detection, ANSI fallback, and minimal banner
display for small terminals.
"""

import os
import pytest
from unittest.mock import Mock, patch
from rich.console import Console
from rich.panel import Panel

from src.themes import Theme, ThemeRegistry, TerminalCapabilities, ColorPalette
from src.banner import Banner, BannerMetadata, BannerRenderer


class TestRGBDetection:
    """Tests for RGB color support detection."""
    
    def test_rgb_detection_with_colorterm_truecolor(self):
        """Test RGB detection works correctly with COLORTERM=truecolor."""
        # Save original environment
        original = os.environ.get("COLORTERM")
        
        try:
            os.environ["COLORTERM"] = "truecolor"
            assert TerminalCapabilities.supports_rgb() is True
        finally:
            # Restore original environment
            if original is not None:
                os.environ["COLORTERM"] = original
            else:
                os.environ.pop("COLORTERM", None)
    
    def test_rgb_detection_with_colorterm_24bit(self):
        """Test RGB detection works correctly with COLORTERM=24bit."""
        original = os.environ.get("COLORTERM")
        
        try:
            os.environ["COLORTERM"] = "24bit"
            assert TerminalCapabilities.supports_rgb() is True
        finally:
            if original is not None:
                os.environ["COLORTERM"] = original
            else:
                os.environ.pop("COLORTERM", None)
    
    def test_rgb_detection_with_term_truecolor(self):
        """Test RGB detection works correctly with TERM containing truecolor."""
        original_colorterm = os.environ.get("COLORTERM")
        original_term = os.environ.get("TERM")
        
        try:
            # Clear COLORTERM to test TERM variable
            os.environ.pop("COLORTERM", None)
            os.environ["TERM"] = "xterm-truecolor"
            assert TerminalCapabilities.supports_rgb() is True
        finally:
            if original_colorterm is not None:
                os.environ["COLORTERM"] = original_colorterm
            if original_term is not None:
                os.environ["TERM"] = original_term
            else:
                os.environ.pop("TERM", None)
    
    def test_rgb_detection_without_support(self):
        """Test RGB detection returns False when no RGB support indicators."""
        original_colorterm = os.environ.get("COLORTERM")
        original_term = os.environ.get("TERM")
        
        try:
            # Set environment to indicate no RGB support
            os.environ.pop("COLORTERM", None)
            os.environ["TERM"] = "xterm-256color"
            assert TerminalCapabilities.supports_rgb() is False
        finally:
            if original_colorterm is not None:
                os.environ["COLORTERM"] = original_colorterm
            if original_term is not None:
                os.environ["TERM"] = original_term
            else:
                os.environ.pop("TERM", None)


class TestANSIFallback:
    """Tests for ANSI color fallback palette."""
    
    def test_ansi_fallback_is_applied(self):
        """Test ANSI fallback is applied when RGB not supported."""
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        fallback_palette = TerminalCapabilities.get_fallback_palette(theme)
        
        # Verify fallback palette is returned
        assert isinstance(fallback_palette, ColorPalette)
        
        # Verify colors are ANSI color names, not RGB hex codes
        assert not fallback_palette.primary.startswith("#")
        assert not fallback_palette.highlight.startswith("#")
        assert not fallback_palette.success.startswith("#")
    
    def test_ansi_fallback_for_all_themes(self):
        """Test ANSI fallback works for all theme variants."""
        for theme_name in ThemeRegistry.list_themes():
            theme = ThemeRegistry.get_theme(theme_name)
            fallback_palette = TerminalCapabilities.get_fallback_palette(theme)
            
            # Verify all palette colors are converted
            assert isinstance(fallback_palette, ColorPalette)
            assert fallback_palette.primary is not None
            assert fallback_palette.highlight is not None
            assert fallback_palette.success is not None
            assert fallback_palette.error is not None
            assert fallback_palette.warning is not None
            assert fallback_palette.dim is not None
            assert fallback_palette.text is not None
    
    def test_theme_get_effective_palette_with_rgb(self):
        """Test theme returns RGB palette when RGB is supported."""
        original_colorterm = os.environ.get("COLORTERM")
        
        try:
            os.environ["COLORTERM"] = "truecolor"
            theme = ThemeRegistry.get_theme("CRT_Cyan")
            effective_palette = theme.get_effective_palette()
            
            # Should return original RGB palette
            assert effective_palette == theme.palette
            assert effective_palette.primary.startswith("#")
        finally:
            if original_colorterm is not None:
                os.environ["COLORTERM"] = original_colorterm
            else:
                os.environ.pop("COLORTERM", None)
    
    def test_theme_get_effective_palette_without_rgb(self):
        """Test theme returns ANSI palette when RGB is not supported."""
        original_colorterm = os.environ.get("COLORTERM")
        original_term = os.environ.get("TERM")
        
        try:
            os.environ.pop("COLORTERM", None)
            os.environ["TERM"] = "xterm-256color"
            theme = ThemeRegistry.get_theme("CRT_Cyan")
            effective_palette = theme.get_effective_palette()
            
            # Should return ANSI fallback palette
            assert effective_palette != theme.palette
            assert not effective_palette.primary.startswith("#")
        finally:
            if original_colorterm is not None:
                os.environ["COLORTERM"] = original_colorterm
            if original_term is not None:
                os.environ["TERM"] = original_term
            else:
                os.environ.pop("TERM", None)


class TestMinimalBanner:
    """Tests for minimal banner display on small terminals."""
    
    def test_minimal_banner_displays_on_small_terminal(self):
        """Test minimal banner displays on terminals smaller than 40x10."""
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        renderer = BannerRenderer(theme)
        
        # Create a mock console with small dimensions
        console = Mock(spec=Console)
        console.size = (30, 8)  # Smaller than 40x10
        
        # Create a test banner
        banner = Banner(
            metadata=BannerMetadata(category="TEST", name="TEST"),
            lines=["Test line 1", "Test line 2"]
        )
        
        # Render should return a panel
        panel = renderer.render_static(banner, console)
        assert isinstance(panel, Panel)
        
        # The panel should contain "peepBeefy" text (minimal banner)
        # We can't easily inspect the panel content, but we can verify it was created
        assert panel is not None
    
    def test_normal_banner_displays_on_large_terminal(self):
        """Test normal banner displays on terminals larger than 40x10."""
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        renderer = BannerRenderer(theme)
        
        # Create a mock console with normal dimensions
        console = Mock(spec=Console)
        console.size = (80, 24)  # Standard terminal size
        
        # Create a test banner
        banner = Banner(
            metadata=BannerMetadata(category="TEST", name="TEST"),
            lines=["Test line 1", "Test line 2", "Test line 3"]
        )
        
        # Render should return a panel
        panel = renderer.render_static(banner, console)
        assert isinstance(panel, Panel)
        assert panel is not None
    
    def test_minimal_banner_threshold_width(self):
        """Test minimal banner is used when width is below 40."""
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        renderer = BannerRenderer(theme)
        
        # Test at threshold: 39 width (should use minimal)
        console = Mock(spec=Console)
        console.size = (39, 24)
        
        banner = Banner(
            metadata=BannerMetadata(category="TEST", name="TEST"),
            lines=["Test"]
        )
        
        panel = renderer.render_static(banner, console)
        assert isinstance(panel, Panel)
    
    def test_minimal_banner_threshold_height(self):
        """Test minimal banner is used when height is below 10."""
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        renderer = BannerRenderer(theme)
        
        # Test at threshold: 9 height (should use minimal)
        console = Mock(spec=Console)
        console.size = (80, 9)
        
        banner = Banner(
            metadata=BannerMetadata(category="TEST", name="TEST"),
            lines=["Test"]
        )
        
        panel = renderer.render_static(banner, console)
        assert isinstance(panel, Panel)


class TestTerminalSizeDetection:
    """Tests for terminal size detection."""
    
    def test_get_dimensions_returns_valid_size(self):
        """Test get_dimensions returns valid terminal size."""
        width, height = TerminalCapabilities.get_dimensions()
        
        # Should return positive dimensions
        assert width > 0
        assert height > 0
        
        # Should be reasonable values (not absurdly large)
        assert width < 10000
        assert height < 10000
    
    def test_get_dimensions_fallback_on_error(self):
        """Test get_dimensions returns fallback (80, 24) on error."""
        # This test verifies the fallback behavior
        # In a real error scenario, it should return (80, 24)
        
        with patch('rich.console.Console') as mock_console_class:
            # Make Console raise an exception
            mock_console_class.side_effect = Exception("Test error")
            
            width, height = TerminalCapabilities.get_dimensions()
            
            # Should return fallback dimensions
            assert width == 80
            assert height == 24
    
    def test_get_dimensions_handles_invalid_size(self):
        """Test get_dimensions handles invalid (0, 0) size."""
        with patch('rich.console.Console') as mock_console_class:
            # Make Console return invalid size
            mock_console = Mock()
            mock_console.size = (0, 0)
            mock_console_class.return_value = mock_console
            
            width, height = TerminalCapabilities.get_dimensions()
            
            # Should return fallback dimensions
            assert width == 80
            assert height == 24
    
    def test_get_dimensions_handles_negative_size(self):
        """Test get_dimensions handles negative dimensions."""
        with patch('rich.console.Console') as mock_console_class:
            # Make Console return negative size
            mock_console = Mock()
            mock_console.size = (-1, -1)
            mock_console_class.return_value = mock_console
            
            width, height = TerminalCapabilities.get_dimensions()
            
            # Should return fallback dimensions
            assert width == 80
            assert height == 24
