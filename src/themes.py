"""Theme system for peepBeefy.

This module provides color palettes and styling for the banner system,
supporting multiple retro terminal themes while maintaining the DOUBLE
box border aesthetic.
"""

from dataclasses import dataclass
from rich.style import Style
from rich import box
from rich.text import Text


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
        true color support (truecolor, 24bit).
        
        Returns:
            True if terminal supports RGB color, False otherwise
        """
        import os
        
        colorterm = os.environ.get("COLORTERM", "").lower()
        return "truecolor" in colorterm or "24bit" in colorterm
    
    @staticmethod
    def supports_256_color() -> bool:
        """Check if terminal supports 256-color palette.
        
        Checks the TERM environment variable for 256-color indicators.
        
        Returns:
            True if terminal supports 256 colors, False otherwise
        """
        import os
        
        term = os.environ.get("TERM", "").lower()
        return "256color" in term or "256" in term
    
    @staticmethod
    def get_dimensions() -> tuple[int, int]:
        """Return terminal dimensions (width, height).
        
        Uses Rich Console to get current terminal size, with fallback
        to standard 80x24 if size cannot be determined.
        
        Returns:
            Tuple of (width, height) in characters
        """
        from rich.console import Console
        
        try:
            console = Console()
            return console.size
        except Exception:
            # Fallback to standard terminal size
            return (80, 24)
    
    @staticmethod
    def get_fallback_palette(theme: Theme) -> ColorPalette:
        """Return ANSI fallback colors for limited terminals.
        
        Maps RGB hex colors to closest ANSI color codes for terminals
        that don't support true color.
        
        Args:
            theme: Theme to generate fallback palette for
            
        Returns:
            ColorPalette with ANSI color codes instead of RGB hex
        """
        # Map common RGB colors to ANSI color names
        # This is a simplified mapping - in production, you'd use
        # a more sophisticated color distance algorithm
        
        def rgb_to_ansi(hex_color: str) -> str:
            """Convert RGB hex color to closest ANSI color name."""
            # Simple mapping based on common colors
            color_map = {
                "#00d7d7": "cyan",
                "#5fffff": "bright_cyan",
                "#00ff87": "bright_green",
                "#ff005f": "bright_red",
                "#ffd700": "yellow",
                "#6c6c6c": "bright_black",
                "#ffffff": "white",
                "#ffb000": "yellow",
                "#ff8c00": "bright_yellow",
                "#ffedd5": "white",
                "#00ff00": "green",
                "#7fff00": "bright_green",
                "#e0ffe0": "white",
                "#ff00ff": "magenta",
                "#ff6ec7": "bright_magenta",
                "#999999": "bright_black",
            }
            
            return color_map.get(hex_color.lower(), "white")
        
        original = theme.palette
        
        return ColorPalette(
            primary=rgb_to_ansi(original.primary),
            highlight=rgb_to_ansi(original.highlight),
            success=rgb_to_ansi(original.success),
            error=rgb_to_ansi(original.error),
            warning=rgb_to_ansi(original.warning),
            dim=rgb_to_ansi(original.dim),
            text=rgb_to_ansi(original.text),
        )
