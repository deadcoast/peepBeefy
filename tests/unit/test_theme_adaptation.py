"""Unit tests for theme adaptation system."""

import pytest
from src.themes import Theme, ColorPalette, adjust_color_for_background
from src.color_util import RGB


class TestColorAdjustment:
    """Test color adjustment for different backgrounds."""
    
    def test_adjust_for_dark_background_hsl(self):
        """Test that colors are lightened for dark backgrounds using HSL."""
        dark_bg = RGB(20, 20, 20)  # Very dark background
        dark_color = "#1a1a1a"  # Dark color that needs lightening
        
        adjusted = adjust_color_for_background(dark_color, dark_bg, method="hsl")
        adjusted_rgb = RGB.from_hex(adjusted)
        
        # Should be lightened to at least 0.65
        assert adjusted_rgb.hsl().l >= 0.65
    
    def test_adjust_for_light_background_hsl(self):
        """Test that colors are darkened for light backgrounds using HSL."""
        light_bg = RGB(240, 240, 240)  # Very light background
        light_color = "#f0f0f0"  # Light color that needs darkening
        
        adjusted = adjust_color_for_background(light_color, light_bg, method="hsl")
        adjusted_rgb = RGB.from_hex(adjusted)
        
        # Should be darkened to at most 0.4
        assert adjusted_rgb.hsl().l <= 0.4
    
    def test_adjust_preserves_hue_saturation(self):
        """Test that HSL adjustment preserves hue and saturation."""
        dark_bg = RGB(20, 20, 20)
        cyan_color = "#00d7d7"
        
        original = RGB.from_hex(cyan_color)
        adjusted = adjust_color_for_background(cyan_color, dark_bg, method="hsl")
        adjusted_rgb = RGB.from_hex(adjusted)
        
        # Hue and saturation should be approximately preserved
        assert abs(original.hsl().h - adjusted_rgb.hsl().h) < 0.01
        assert abs(original.hsl().s - adjusted_rgb.hsl().s) < 0.01
    
    def test_adjust_for_dark_background_overlay(self):
        """Test overlay-based adjustment for dark backgrounds."""
        dark_bg = RGB(20, 20, 20)
        dark_color = "#1a1a1a"
        
        adjusted = adjust_color_for_background(dark_color, dark_bg, method="overlay")
        adjusted_rgb = RGB.from_hex(adjusted)
        
        # Should be lightened to at least 0.65
        assert adjusted_rgb.hsl().l >= 0.65
    
    def test_adjust_for_light_background_overlay(self):
        """Test overlay-based adjustment for light backgrounds."""
        light_bg = RGB(240, 240, 240)
        light_color = "#f0f0f0"
        
        adjusted = adjust_color_for_background(light_color, light_bg, method="overlay")
        adjusted_rgb = RGB.from_hex(adjusted)
        
        # Should be darkened to at most 0.4
        assert adjusted_rgb.hsl().l <= 0.4
    
    def test_already_suitable_color_unchanged(self):
        """Test that colors already suitable for background are minimally changed."""
        dark_bg = RGB(20, 20, 20)
        suitable_color = "#aaaaaa"  # Already light enough
        
        original = RGB.from_hex(suitable_color)
        adjusted = adjust_color_for_background(suitable_color, dark_bg, method="hsl")
        adjusted_rgb = RGB.from_hex(adjusted)
        
        # Should be very close to original since it already meets requirements
        # (lightness >= 0.65 for dark background)
        if original.hsl().l >= 0.65:
            assert abs(original.hsl().l - adjusted_rgb.hsl().l) < 0.05


class TestColorPaletteRGBConversion:
    """Test ColorPalette RGB conversion methods."""
    
    def test_to_rgb_palette(self):
        """Test conversion of palette to RGB objects."""
        palette = ColorPalette(
            primary="#00d7d7",
            highlight="#5fffff",
            success="#00ff87",
            error="#ff005f",
            warning="#ffd700",
            dim="#6c6c6c",
            text="#ffffff",
        )
        
        rgb_palette = palette.to_rgb_palette()
        
        assert isinstance(rgb_palette['primary'], RGB)
        assert rgb_palette['primary'] == RGB(0, 215, 215)
        assert rgb_palette['text'] == RGB(255, 255, 255)
    
    def test_adjust_for_background_dark(self):
        """Test palette adjustment for dark background."""
        palette = ColorPalette(
            primary="#1a1a1a",  # Too dark
            highlight="#2a2a2a",  # Too dark
            success="#00ff87",  # Already suitable
            error="#ff005f",  # Already suitable
            warning="#ffd700",  # Already suitable
            dim="#3a3a3a",  # Too dark
            text="#4a4a4a",  # Too dark
        )
        
        dark_bg = RGB(20, 20, 20)
        adjusted = palette.adjust_for_background(dark_bg)
        
        # All colors should meet minimum lightness for dark background
        rgb_palette = adjusted.to_rgb_palette()
        for name, color in rgb_palette.items():
            assert color.hsl().l >= 0.65, f"{name} color too dark: {color.hsl().l}"
    
    def test_adjust_for_background_light(self):
        """Test palette adjustment for light background."""
        palette = ColorPalette(
            primary="#f0f0f0",  # Too light
            highlight="#e0e0e0",  # Too light
            success="#00ff87",  # Might be suitable
            error="#ff005f",  # Might be suitable
            warning="#ffd700",  # Too light
            dim="#d0d0d0",  # Too light
            text="#ffffff",  # Too light
        )
        
        light_bg = RGB(240, 240, 240)
        adjusted = palette.adjust_for_background(light_bg)
        
        # All colors should meet maximum lightness for light background
        rgb_palette = adjusted.to_rgb_palette()
        for name, color in rgb_palette.items():
            assert color.hsl().l <= 0.4, f"{name} color too light: {color.hsl().l}"


class TestThemeAdaptation:
    """Test Theme adaptation methods."""
    
    def test_get_color_mode(self):
        """Test color mode detection."""
        theme = Theme("Test", ColorPalette(
            primary="#00d7d7",
            highlight="#5fffff",
            success="#00ff87",
            error="#ff005f",
            warning="#ffd700",
            dim="#6c6c6c",
            text="#ffffff",
        ))
        
        mode = theme.get_color_mode()
        
        # Should return one of the valid modes
        assert mode in ["rgb", "8bit", "ansi", "default"]
    
    def test_adapt_to_terminal_with_dark_background(self):
        """Test theme adaptation for dark terminal background."""
        theme = Theme("Test", ColorPalette(
            primary="#1a1a1a",
            highlight="#2a2a2a",
            success="#00ff87",
            error="#ff005f",
            warning="#ffd700",
            dim="#3a3a3a",
            text="#4a4a4a",
        ))
        
        dark_bg = RGB(20, 20, 20)
        adapted = theme.adapt_to_terminal(dark_bg)
        
        # Should return a new theme
        assert isinstance(adapted, Theme)
        assert adapted.name == "Test_adapted"
        
        # Colors should be adjusted for dark background
        rgb_palette = adapted.palette.to_rgb_palette()
        for name, color in rgb_palette.items():
            assert color.hsl().l >= 0.65, f"{name} not adjusted properly"
    
    def test_adapt_to_terminal_with_light_background(self):
        """Test theme adaptation for light terminal background."""
        theme = Theme("Test", ColorPalette(
            primary="#f0f0f0",
            highlight="#e0e0e0",
            success="#00ff87",
            error="#ff005f",
            warning="#ffd700",
            dim="#d0d0d0",
            text="#ffffff",
        ))
        
        light_bg = RGB(240, 240, 240)
        adapted = theme.adapt_to_terminal(light_bg)
        
        # Should return a new theme
        assert isinstance(adapted, Theme)
        
        # Colors should be adjusted for light background
        rgb_palette = adapted.palette.to_rgb_palette()
        for name, color in rgb_palette.items():
            assert color.hsl().l <= 0.4, f"{name} not adjusted properly"
    
    def test_adapt_to_terminal_without_background(self):
        """Test theme adaptation when background detection fails."""
        theme = Theme("Test", ColorPalette(
            primary="#00d7d7",
            highlight="#5fffff",
            success="#00ff87",
            error="#ff005f",
            warning="#ffd700",
            dim="#6c6c6c",
            text="#ffffff",
        ))
        
        # Pass None to simulate detection failure
        adapted = theme.adapt_to_terminal(None)
        
        # Should return original theme when detection fails
        assert adapted == theme or adapted.name == theme.name
