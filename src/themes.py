"""Theme system for peepBeefy.

This module provides color palettes and styling for the banner system,
supporting multiple retro terminal themes while maintaining the DOUBLE
box border aesthetic.
"""

from dataclasses import dataclass
from rich.style import Style
from rich import box
from rich.text import Text


def adjust_color_for_background(hex_color: str, bg_color: 'RGB', method: str = "hsl") -> str:
    """Adjust a color for readability on a given background.
    
    Ensures text colors meet minimum lightness requirements:
    - Dark backgrounds: lightness >= 0.65
    - Light backgrounds: lightness <= 0.4
    
    Args:
        hex_color: Hex color string to adjust (e.g., "#00d7d7")
        bg_color: RGB background color
        method: Adjustment method - "hsl" or "overlay"
        
    Returns:
        Adjusted hex color string
    """
    from src.color_util import RGB
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Parse the color
        color = RGB.from_hex(hex_color)
        is_light_bg = bg_color.is_light()
        
        if method == "hsl":
            # HSL-based adjustment preserving hue and saturation
            if is_light_bg:
                # Light background: ensure lightness <= 0.4
                adjusted = color.set_light(0.4, at_most=True)
            else:
                # Dark background: ensure lightness >= 0.65
                adjusted = color.set_light(0.65, at_least=True)
        elif method == "overlay":
            # Overlay-based adjustment
            if is_light_bg:
                # Darken by overlaying with black
                black = RGB(0, 0, 0)
                adjusted = color.overlay(black, 0.3)
                # Ensure we meet the threshold
                if adjusted.hsl().l > 0.4:
                    adjusted = adjusted.set_light(0.4, at_most=True)
            else:
                # Lighten by overlaying with white
                white = RGB(255, 255, 255)
                adjusted = color.overlay(white, 0.3)
                # Ensure we meet the threshold
                if adjusted.hsl().l < 0.65:
                    adjusted = adjusted.set_light(0.65, at_least=True)
        else:
            logger.warning(f"Unknown adjustment method '{method}', using hsl")
            return adjust_color_for_background(hex_color, bg_color, "hsl")
        
        # Convert back to hex
        adjusted_hex = f"#{adjusted.r:02x}{adjusted.g:02x}{adjusted.b:02x}"
        logger.debug(f"Adjusted {hex_color} -> {adjusted_hex} for {'light' if is_light_bg else 'dark'} background")
        return adjusted_hex
        
    except Exception as e:
        logger.warning(f"Error adjusting color {hex_color}: {e}, returning original")
        return hex_color


@dataclass
class ColorPalette:
    """Color definitions for a theme variant.
    
    Attributes:
        primary: Structural elements (borders, dividers)
        highlight: Active elements, commands
        success: Success states
        error: Error states
        warning: Warnings, dev commands
        dim: Secondary text
        text: Primary text
    """
    primary: str
    highlight: str
    success: str
    error: str
    warning: str
    dim: str
    text: str
    
    def to_rgb_palette(self) -> dict[str, 'RGB']:
        """Convert hex colors to RGB objects.
        
        Returns:
            Dictionary mapping field names to RGB objects
        """
        from src.color_util import RGB
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            return {
                'primary': RGB.from_hex(self.primary),
                'highlight': RGB.from_hex(self.highlight),
                'success': RGB.from_hex(self.success),
                'error': RGB.from_hex(self.error),
                'warning': RGB.from_hex(self.warning),
                'dim': RGB.from_hex(self.dim),
                'text': RGB.from_hex(self.text),
            }
        except Exception as e:
            logger.error(f"Error converting palette to RGB: {e}")
            raise
    
    def adjust_for_background(self, bg_color: 'RGB', method: str = "hsl") -> 'ColorPalette':
        """Adjust palette colors for readability on given background.
        
        Ensures all text colors meet minimum lightness requirements:
        - Dark backgrounds: lightness >= 0.65
        - Light backgrounds: lightness <= 0.4
        
        Args:
            bg_color: RGB background color
            method: Adjustment method - "hsl" or "overlay"
            
        Returns:
            New ColorPalette with adjusted colors
        """
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Adjust each color in the palette
            adjusted = ColorPalette(
                primary=adjust_color_for_background(self.primary, bg_color, method),
                highlight=adjust_color_for_background(self.highlight, bg_color, method),
                success=adjust_color_for_background(self.success, bg_color, method),
                error=adjust_color_for_background(self.error, bg_color, method),
                warning=adjust_color_for_background(self.warning, bg_color, method),
                dim=adjust_color_for_background(self.dim, bg_color, method),
                text=adjust_color_for_background(self.text, bg_color, method),
            )
            
            logger.debug(f"Adjusted palette for {'light' if bg_color.is_light() else 'dark'} background")
            return adjusted
            
        except Exception as e:
            logger.warning(f"Error adjusting palette: {e}, returning original")
            return self


class Theme:
    """Theme variant with color palette and styling rules.
    
    Provides consistent styling methods for all UI elements while
    maintaining the CRT retro terminal aesthetic with DOUBLE borders.
    
    Attributes:
        name: Theme identifier
        palette: Color palette for this theme
    """
    
    def __init__(self, name: str, palette: ColorPalette):
        """Initialize theme with name and color palette.
        
        Args:
            name: Theme identifier (e.g., "CRT_Cyan")
            palette: ColorPalette instance with theme colors
        """
        self.name = name
        self.palette = palette
    
    def get_box_style(self) -> box.Box:
        """Return box style for panels and borders.
        
        Always returns box.DOUBLE to maintain peepBeefy's retro aesthetic.
        
        Returns:
            box.DOUBLE for consistent DOUBLE border style
        """
        return box.DOUBLE
    
    def get_border_style(self) -> str:
        """Return border color style.
        
        Returns:
            Primary color from palette for borders
        """
        return self.palette.primary
    
    def get_effective_palette(self) -> ColorPalette:
        """Get the effective color palette based on terminal capabilities.
        
        Returns the original RGB palette if the terminal supports RGB,
        otherwise returns an ANSI fallback palette.
        
        Returns:
            ColorPalette appropriate for the terminal's capabilities
        """
        if TerminalCapabilities.supports_rgb():
            return self.palette
        else:
            return TerminalCapabilities.get_fallback_palette(self)
    
    def style_command(self, text: str) -> Text:
        """Apply command styling to text.
        
        Commands are styled with highlight color and bold formatting
        to make them stand out in the interface.
        
        Args:
            text: Command text to style
            
        Returns:
            Rich Text object with command styling applied
        """
        return Text(text, style=Style(color=self.palette.highlight, bold=True))
    
    def style_description(self, text: str) -> Text:
        """Apply description styling to text.
        
        Descriptions use dim color for secondary information that
        shouldn't compete with primary content.
        
        Args:
            text: Description text to style
            
        Returns:
            Rich Text object with description styling applied
        """
        return Text(text, style=Style(color=self.palette.dim))
    
    def get_color_mode(self) -> str:
        """Get appropriate color mode for terminal.
        
        Detects terminal capabilities and returns the best supported
        color mode: "rgb" for 24-bit color, "8bit" for 256-color,
        or "ansi" for basic 16-color terminals.
        
        Returns:
            Color mode string: "rgb", "8bit", or "ansi"
        """
        from src.terminal_detect import detect_ansi_mode
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            mode = detect_ansi_mode()
            if mode is None:
                logger.debug("Terminal detection returned None, defaulting to 8bit")
                return "8bit"
            logger.debug(f"Detected terminal color mode: {mode}")
            return mode
        except Exception as e:
            logger.warning(f"Error detecting color mode: {e}, defaulting to 8bit")
            return "8bit"
    
    def adapt_to_terminal(self, bg_color: 'RGB | None' = None) -> 'Theme':
        """Create terminal-adapted theme variant.
        
        Adapts the theme's color palette based on the terminal's background
        color to ensure text remains readable. If no background color is
        provided, attempts to detect it automatically.
        
        Args:
            bg_color: Optional RGB background color. If None, attempts detection.
            
        Returns:
            New Theme instance with adapted color palette
        """
        from src.terminal_detect import get_background_color
        from src.color_util import RGB
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Detect background color if not provided
            if bg_color is None:
                bg_color = get_background_color()
                if bg_color is None:
                    logger.debug("Could not detect background color, returning original theme")
                    return self
            
            # Classify background as light or dark
            is_light_bg = bg_color.is_light()
            light_dark = "light" if is_light_bg else "dark"
            
            logger.debug(f"Background classified as {light_dark} (lightness={bg_color.hsl().l:.2f})")
            
            # Adapt palette for background
            adapted_palette = self.palette.adjust_for_background(bg_color)
            
            # Create new theme with adapted palette
            adapted_theme = Theme(f"{self.name}_adapted", adapted_palette)
            logger.debug(f"Created adapted theme: {adapted_theme.name}")
            
            return adapted_theme
            
        except Exception as e:
            logger.warning(f"Error adapting theme to terminal: {e}, returning original theme")
            return self

    def get_color_mode(self) -> str:
        """Get appropriate color mode for terminal.

        Detects terminal capabilities and returns the best supported
        color mode: "rgb" for 24-bit color, "8bit" for 256-color,
        or "ansi" for basic 16-color terminals.

        Returns:
            Color mode string: "rgb", "8bit", or "ansi"
        """
        from src.terminal_detect import detect_ansi_mode
        import logging

        logger = logging.getLogger(__name__)

        try:
            mode = detect_ansi_mode()
            if mode is None:
                logger.debug("Terminal detection returned None, defaulting to 8bit")
                return "8bit"
            logger.debug(f"Detected terminal color mode: {mode}")
            return mode
        except Exception as e:
            logger.warning(f"Error detecting color mode: {e}, defaulting to 8bit")
            return "8bit"

    def adapt_to_terminal(self, bg_color: 'RGB | None' = None) -> 'Theme':
        """Create terminal-adapted theme variant.

        Adapts the theme's color palette based on the terminal's background
        color to ensure text remains readable. If no background color is
        provided, attempts to detect it automatically.

        Args:
            bg_color: Optional RGB background color. If None, attempts detection.

        Returns:
            New Theme instance with adapted color palette
        """
        from src.terminal_detect import get_background_color
        from src.color_util import RGB
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Detect background color if not provided
            if bg_color is None:
                bg_color = get_background_color()
                if bg_color is None:
                    logger.debug("Could not detect background color, returning original theme")
                    return self

            # Classify background as light or dark
            is_light_bg = bg_color.is_light()
            light_dark = "light" if is_light_bg else "dark"

            logger.debug(f"Background classified as {light_dark} (lightness={bg_color.hsl().l:.2f})")

            # Adapt palette for background
            adapted_palette = self.palette.adjust_for_background(bg_color)

            # Create new theme with adapted palette
            adapted_theme = Theme(f"{self.name}_adapted", adapted_palette)
            logger.debug(f"Created adapted theme: {adapted_theme.name}")

            return adapted_theme

        except Exception as e:
            logger.warning(f"Error adapting theme to terminal: {e}, returning original theme")
            return self




class ThemeRegistry:
    """Registry of available theme variants.
    
    Provides access to predefined themes and theme management functionality.
    All themes maintain the DOUBLE box border style while offering different
    color palettes for various retro terminal aesthetics.
    """
    
    THEMES = {
        "CRT_Cyan": Theme("CRT_Cyan", ColorPalette(
            primary="#00d7d7",      # Cyan borders and structural elements
            highlight="#5fffff",    # Bright cyan for commands
            success="#00ff87",      # Green for success states
            error="#ff005f",        # Red for errors
            warning="#ffd700",      # Gold for warnings
            dim="#6c6c6c",          # Gray for secondary text
            text="#ffffff",         # White for primary text
        )),
        "Amber_Terminal": Theme("Amber_Terminal", ColorPalette(
            primary="#ffb000",      # Amber borders
            highlight="#ffd700",    # Gold highlights
            success="#00ff87",      # Green for success
            error="#ff005f",        # Red for errors
            warning="#ff8c00",      # Dark orange for warnings
            dim="#6c6c6c",          # Gray for secondary text
            text="#ffedd5",         # Warm white for text
        )),
        "Green_Phosphor": Theme("Green_Phosphor", ColorPalette(
            primary="#00ff00",      # Classic green borders
            highlight="#7fff00",    # Chartreuse highlights
            success="#00ff87",      # Bright green for success
            error="#ff005f",        # Red for errors
            warning="#ffd700",      # Gold for warnings
            dim="#6c6c6c",          # Gray for secondary text
            text="#e0ffe0",         # Light green tinted text
        )),
        "Synthwave": Theme("Synthwave", ColorPalette(
            primary="#ff00ff",      # Magenta borders
            highlight="#ff6ec7",    # Pink highlights
            success="#00ff87",      # Green for success
            error="#ff005f",        # Red for errors
            warning="#ffd700",      # Gold for warnings
            dim="#6c6c6c",          # Gray for secondary text
            text="#ffffff",         # White for text
        )),
    }
    
    @classmethod
    def get_theme(cls, name: str) -> Theme:
        """Retrieve theme by name with fallback to default.
        
        If the requested theme is not found, returns the default CRT_Cyan
        theme to ensure the application always has a valid theme.
        
        Args:
            name: Theme identifier (e.g., "CRT_Cyan", "Amber_Terminal")
            
        Returns:
            Theme instance, defaulting to CRT_Cyan if name not found
        """
        return cls.THEMES.get(name, cls.THEMES["CRT_Cyan"])
    
    @classmethod
    def list_themes(cls) -> list[str]:
        """Return all available theme names.
        
        Returns:
            List of theme identifiers that can be used with get_theme()
        """
        return list(cls.THEMES.keys())



class TerminalCapabilities:
    """Detects and reports terminal capabilities.
    
    Provides static methods to detect terminal color support, dimensions,
    and generate fallback palettes for terminals with limited capabilities.
    """
    
    @staticmethod
    def supports_rgb() -> bool:
        """Check if terminal supports RGB (24-bit) color.
        
        Checks the COLORTERM environment variable for indicators of
        true color support (truecolor, 24bit), and also checks TERM
        environment variable for RGB support indicators.
        
        Returns:
            True if terminal supports RGB color, False otherwise
        """
        import os
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Check COLORTERM for truecolor/24bit indicators
            colorterm = os.environ.get("COLORTERM", "").lower()
            if "truecolor" in colorterm or "24bit" in colorterm:
                logger.debug(f"RGB support detected via COLORTERM: {colorterm}")
                return True
            
            # Check TERM for RGB support indicators
            term = os.environ.get("TERM", "").lower()
            rgb_indicators = ["truecolor", "24bit", "direct"]
            has_rgb = any(indicator in term for indicator in rgb_indicators)
            
            if has_rgb:
                logger.debug(f"RGB support detected via TERM: {term}")
            else:
                logger.debug(f"No RGB support detected (COLORTERM={colorterm}, TERM={term})")
            
            return has_rgb
        except Exception as e:
            logger.warning(f"Error detecting RGB support: {e}, assuming no RGB support")
            return False
    
    @staticmethod
    def supports_256_color() -> bool:
        """Check if terminal supports 256-color palette.
        
        Checks the TERM environment variable for 256-color indicators.
        
        Returns:
            True if terminal supports 256 colors, False otherwise
        """
        import os
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            term = os.environ.get("TERM", "").lower()
            has_256 = "256color" in term or "256" in term
            
            logger.debug(f"256-color support: {has_256} (TERM={term})")
            return has_256
        except Exception as e:
            logger.warning(f"Error detecting 256-color support: {e}, assuming no 256-color support")
            return False
    
    @staticmethod
    def get_dimensions() -> tuple[int, int]:
        """Return terminal dimensions (width, height).
        
        Uses Rich Console to get current terminal size, with fallback
        to standard 80x24 if size cannot be determined or is invalid.
        
        Returns:
            Tuple of (width, height) in characters, defaults to (80, 24)
        """
        from rich.console import Console
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            console = Console()
            width, height = console.size
            
            # Validate dimensions - if invalid, use fallback
            if width <= 0 or height <= 0:
                logger.warning(f"Invalid terminal dimensions ({width}x{height}), using fallback 80x24")
                return (80, 24)
            
            logger.debug(f"Terminal dimensions: {width}x{height}")
            return (width, height)
        except Exception as e:
            # Fallback to standard terminal size
            logger.warning(f"Failed to get terminal dimensions: {e}, using fallback 80x24")
            return (80, 24)
    
    @staticmethod
    def get_fallback_palette(theme: Theme) -> ColorPalette:
        """Return ANSI fallback colors for limited terminals.
        
        Maps RGB hex colors to closest ANSI color codes for terminals
        that don't support true color. Uses a comprehensive color mapping
        that covers all theme colors.
        
        Args:
            theme: Theme to generate fallback palette for
            
        Returns:
            ColorPalette with ANSI color codes instead of RGB hex
        """
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            def rgb_to_ansi(hex_color: str) -> str:
                """Convert RGB hex color to closest ANSI color name.
                
                Uses a comprehensive mapping from RGB hex codes to ANSI color names.
                Falls back to white for unmapped colors.
                """
                # Comprehensive mapping of RGB colors to ANSI color names
                color_map = {
                    # Cyan theme colors
                    "#00d7d7": "cyan",
                    "#5fffff": "bright_cyan",
                    
                    # Amber theme colors
                    "#ffb000": "yellow",
                    "#ffd700": "yellow",
                    "#ff8c00": "bright_yellow",
                    "#ffedd5": "white",
                    
                    # Green theme colors
                    "#00ff00": "green",
                    "#7fff00": "bright_green",
                    "#e0ffe0": "white",
                    
                    # Synthwave theme colors
                    "#ff00ff": "magenta",
                    "#ff6ec7": "bright_magenta",
                    
                    # Common colors across themes
                    "#00ff87": "bright_green",  # Success
                    "#ff005f": "bright_red",    # Error
                    "#6c6c6c": "bright_black",  # Dim
                    "#ffffff": "white",         # Text
                    "#999999": "bright_black",  # Gray
                }
                
                return color_map.get(hex_color.lower(), "white")
            
            original = theme.palette
            
            fallback = ColorPalette(
                primary=rgb_to_ansi(original.primary),
                highlight=rgb_to_ansi(original.highlight),
                success=rgb_to_ansi(original.success),
                error=rgb_to_ansi(original.error),
                warning=rgb_to_ansi(original.warning),
                dim=rgb_to_ansi(original.dim),
                text=rgb_to_ansi(original.text),
            )
            
            logger.debug(f"Generated ANSI fallback palette for theme {theme.name}")
            return fallback
            
        except Exception as e:
            logger.error(f"Failed to generate fallback palette: {e}, using default ANSI colors")
            # Return a safe default palette
            return ColorPalette(
                primary="cyan",
                highlight="bright_cyan",
                success="bright_green",
                error="bright_red",
                warning="yellow",
                dim="bright_black",
                text="white",
            )
