"""Property-based tests for theme system.

Tests universal properties that should hold across all themes and inputs.
"""

import pytest
from hypothesis import given, strategies as st
from rich import box

from src.themes import ColorPalette, Theme, ThemeRegistry


# Feature: peepbeefy-enhancements, Property 10: Theme Box Style Consistency
@given(theme_name=st.sampled_from(ThemeRegistry.list_themes()))
@pytest.mark.property_test
def test_theme_box_style_consistency(theme_name: str):
    """**Validates: Requirements 7.4**
    
    Property 10: For any theme in the theme registry, calling get_box_style()
    should always return box.DOUBLE, maintaining the DOUBLE border style
    across all themes.
    """
    # Arrange
    theme = ThemeRegistry.get_theme(theme_name)
    
    # Act
    box_style = theme.get_box_style()
    
    # Assert
    assert box_style == box.DOUBLE, (
        f"Theme {theme_name} should return box.DOUBLE, got {box_style}"
    )


# Feature: peepbeefy-enhancements, Property 11: Theme Color Consistency
@given(
    theme_name=st.sampled_from(ThemeRegistry.list_themes()),
    text_content=st.text(min_size=1, max_size=100)
)
@pytest.mark.property_test
def test_theme_color_consistency(theme_name: str, text_content: str):
    """**Validates: Requirements 7.3**
    
    Property 11: For any theme and any UI element type (border, command,
    description, etc.), all styling functions should use colors exclusively
    from that theme's palette, ensuring visual consistency.
    """
    # Arrange
    theme = ThemeRegistry.get_theme(theme_name)
    palette = theme.palette
    
    # Collect all colors from the palette
    palette_colors = {
        palette.primary,
        palette.highlight,
        palette.success,
        palette.error,
        palette.warning,
        palette.dim,
        palette.text,
    }
    
    # Act - test all styling methods
    border_style = theme.get_border_style()
    command_text = theme.style_command(text_content)
    description_text = theme.style_description(text_content)
    
    # Assert - border style uses palette color
    assert border_style in palette_colors, (
        f"Border style {border_style} not in {theme_name} palette"
    )
    
    # Assert - command styling uses palette color
    if command_text.style:
        command_color = command_text.style.color
        if command_color:
            assert command_color.name in palette_colors, (
                f"Command color {command_color.name} not in {theme_name} palette"
            )
    
    # Assert - description styling uses palette color
    if description_text.style:
        desc_color = description_text.style.color
        if desc_color:
            assert desc_color.name in palette_colors, (
                f"Description color {desc_color.name} not in {theme_name} palette"
            )


@given(
    primary=st.text(min_size=7, max_size=7, alphabet="0123456789abcdef").map(lambda x: f"#{x}"),
    highlight=st.text(min_size=7, max_size=7, alphabet="0123456789abcdef").map(lambda x: f"#{x}"),
    success=st.text(min_size=7, max_size=7, alphabet="0123456789abcdef").map(lambda x: f"#{x}"),
    error=st.text(min_size=7, max_size=7, alphabet="0123456789abcdef").map(lambda x: f"#{x}"),
    warning=st.text(min_size=7, max_size=7, alphabet="0123456789abcdef").map(lambda x: f"#{x}"),
    dim=st.text(min_size=7, max_size=7, alphabet="0123456789abcdef").map(lambda x: f"#{x}"),
    text=st.text(min_size=7, max_size=7, alphabet="0123456789abcdef").map(lambda x: f"#{x}"),
)
@pytest.mark.property_test
def test_custom_theme_color_consistency(
    primary: str, highlight: str, success: str, error: str,
    warning: str, dim: str, text: str
):
    """Test that custom themes also maintain color consistency.
    
    This extends Property 11 to verify that any custom theme created
    with arbitrary colors will still maintain consistency.
    """
    # Arrange
    palette = ColorPalette(
        primary=primary,
        highlight=highlight,
        success=success,
        error=error,
        warning=warning,
        dim=dim,
        text=text,
    )
    theme = Theme("CustomTheme", palette)
    
    # Collect all colors from the palette
    palette_colors = {
        palette.primary,
        palette.highlight,
        palette.success,
        palette.error,
        palette.warning,
        palette.dim,
        palette.text,
    }
    
    # Act
    border_style = theme.get_border_style()
    
    # Assert
    assert border_style in palette_colors, (
        f"Border style {border_style} not in custom theme palette"
    )


@given(invalid_theme_name=st.text(min_size=1).filter(
    lambda x: x not in ThemeRegistry.list_themes()
))
@pytest.mark.property_test
def test_theme_fallback_to_default(invalid_theme_name: str):
    """Test that invalid theme names fall back to CRT_Cyan default.
    
    This ensures the application always has a valid theme even when
    given invalid configuration.
    """
    # Act
    theme = ThemeRegistry.get_theme(invalid_theme_name)
    
    # Assert
    assert theme.name == "CRT_Cyan", (
        f"Invalid theme name should fall back to CRT_Cyan, got {theme.name}"
    )
    assert theme == ThemeRegistry.THEMES["CRT_Cyan"]



# Feature: peepbeefy-enhancements, Property 35: Terminal Color Capability Fallback
@given(theme_name=st.sampled_from(ThemeRegistry.list_themes()))
@pytest.mark.property_test
def test_terminal_color_capability_fallback(theme_name: str):
    """**Validates: Requirements 15.2**
    
    Property 35: For any terminal that supports only 8-bit color (not RGB),
    the theme system should use ANSI fallback colors instead of RGB hex codes.
    """
    from src.themes import TerminalCapabilities
    
    # Arrange
    theme = ThemeRegistry.get_theme(theme_name)
    
    # Act
    fallback_palette = TerminalCapabilities.get_fallback_palette(theme)
    
    # Assert - fallback palette should use ANSI color names, not hex codes
    ansi_colors = {
        "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
        "bright_black", "bright_red", "bright_green", "bright_yellow",
        "bright_blue", "bright_magenta", "bright_cyan", "bright_white"
    }
    
    assert fallback_palette.primary in ansi_colors, (
        f"Fallback primary color should be ANSI, got {fallback_palette.primary}"
    )
    assert fallback_palette.highlight in ansi_colors, (
        f"Fallback highlight color should be ANSI, got {fallback_palette.highlight}"
    )
    assert fallback_palette.success in ansi_colors, (
        f"Fallback success color should be ANSI, got {fallback_palette.success}"
    )
    assert fallback_palette.error in ansi_colors, (
        f"Fallback error color should be ANSI, got {fallback_palette.error}"
    )
    assert fallback_palette.warning in ansi_colors, (
        f"Fallback warning color should be ANSI, got {fallback_palette.warning}"
    )
    assert fallback_palette.dim in ansi_colors, (
        f"Fallback dim color should be ANSI, got {fallback_palette.dim}"
    )
    assert fallback_palette.text in ansi_colors, (
        f"Fallback text color should be ANSI, got {fallback_palette.text}"
    )


@pytest.mark.property_test
def test_terminal_dimensions_returns_valid_size():
    """Test that terminal dimension detection returns valid dimensions.
    
    Ensures that get_dimensions() always returns a tuple of positive integers.
    """
    from src.themes import TerminalCapabilities
    
    # Act
    width, height = TerminalCapabilities.get_dimensions()
    
    # Assert
    assert isinstance(width, int), f"Width should be int, got {type(width)}"
    assert isinstance(height, int), f"Height should be int, got {type(height)}"
    assert width > 0, f"Width should be positive, got {width}"
    assert height > 0, f"Height should be positive, got {height}"
    # Reasonable bounds for terminal size
    assert width >= 20, f"Width should be at least 20, got {width}"
    assert height >= 10, f"Height should be at least 10, got {height}"


@pytest.mark.property_test
def test_rgb_support_detection_returns_bool():
    """Test that RGB support detection returns a boolean value."""
    from src.themes import TerminalCapabilities
    
    # Act
    supports_rgb = TerminalCapabilities.supports_rgb()
    
    # Assert
    assert isinstance(supports_rgb, bool), (
        f"supports_rgb() should return bool, got {type(supports_rgb)}"
    )


@pytest.mark.property_test
def test_256_color_support_detection_returns_bool():
    """Test that 256-color support detection returns a boolean value."""
    from src.themes import TerminalCapabilities
    
    # Act
    supports_256 = TerminalCapabilities.supports_256_color()
    
    # Assert
    assert isinstance(supports_256, bool), (
        f"supports_256_color() should return bool, got {type(supports_256)}"
    )
