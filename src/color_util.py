"""
Color utility module for RGB/HSL conversion and manipulation.

This module provides comprehensive color handling including:
- RGB and HSL color representation
- Conversion between RGB and HSL color spaces
- Lightness adjustment and color blending
- ANSI color code generation for terminal output
"""

from dataclasses import dataclass
import colorsys
from typing import Optional, Literal


# Type definition for ANSI color modes
AnsiMode = Literal["rgb", "8bit", "ansi", "default"]


@dataclass
class HSL:
    """HSL color representation.
    
    Attributes:
        h: Hue in range [0.0, 1.0]
        s: Saturation in range [0.0, 1.0]
        l: Lightness in range [0.0, 1.0]
    """
    h: float  # 0.0-1.0 (hue)
    s: float  # 0.0-1.0 (saturation)
    l: float  # 0.0-1.0 (lightness)
    
    def __post_init__(self):
        """Validate HSL values are in valid range."""
        if not (0.0 <= self.h <= 1.0):
            raise ValueError(f"Hue must be in [0.0, 1.0], got {self.h}")
        if not (0.0 <= self.s <= 1.0):
            raise ValueError(f"Saturation must be in [0.0, 1.0], got {self.s}")
        if not (0.0 <= self.l <= 1.0):
            raise ValueError(f"Lightness must be in [0.0, 1.0], got {self.l}")
    
    def rgb(self) -> 'RGB':
        """Convert HSL to RGB using colorsys.
        
        Returns:
            RGB color equivalent to this HSL color
        """
        r, g, b = colorsys.hls_to_rgb(self.h, self.l, self.s)
        return RGB(
            r=round(r * 255),
            g=round(g * 255),
            b=round(b * 255)
        )


@dataclass
class RGB:
    """RGB color representation.
    
    Attributes:
        r: Red component in range [0, 255]
        g: Green component in range [0, 255]
        b: Blue component in range [0, 255]
    """
    r: int  # 0-255
    g: int  # 0-255
    b: int  # 0-255
    
    def __post_init__(self):
        """Validate RGB values are in valid range."""
        if not (0 <= self.r <= 255):
            raise ValueError(f"Red must be in [0, 255], got {self.r}")
        if not (0 <= self.g <= 255):
            raise ValueError(f"Green must be in [0, 255], got {self.g}")
        if not (0 <= self.b <= 255):
            raise ValueError(f"Blue must be in [0, 255], got {self.b}")
    
    @classmethod
    def from_hex(cls, hex_str: str) -> 'RGB':
        """Parse hex color string to RGB.
        
        Supports both 6-character (#RRGGBB) and 3-character (#RGB) formats.
        
        Args:
            hex_str: Hex color string (with or without # prefix)
            
        Returns:
            RGB color parsed from hex string
            
        Raises:
            ValueError: If hex string format is invalid
        """
        hex_str = hex_str.lstrip("#")
        
        if len(hex_str) == 3:
            # Expand 3-character format: #RGB -> #RRGGBB
            hex_str = ''.join([c * 2 for c in hex_str])
        
        if len(hex_str) != 6:
            raise ValueError(f"Invalid hex color length: {len(hex_str)}, expected 3 or 6")
        
        try:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return cls(r=r, g=g, b=b)
        except ValueError as e:
            raise ValueError(f"Invalid hex color format: {hex_str}") from e
    
    def hsl(self) -> HSL:
        """Convert RGB to HSL using colorsys.
        
        Returns:
            HSL color equivalent to this RGB color
        """
        r_norm = self.r / 255.0
        g_norm = self.g / 255.0
        b_norm = self.b / 255.0
        
        h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)
        return HSL(h=h, s=s, l=l)
    
    def set_light(
        self,
        light: float,
        at_least: Optional[bool] = None,
        at_most: Optional[bool] = None
    ) -> 'RGB':
        """Adjust lightness while preserving hue and saturation.
        
        Args:
            light: Target lightness value in [0.0, 1.0]
            at_least: If True, only increase lightness (don't decrease below current)
            at_most: If True, only decrease lightness (don't increase above current)
            
        Returns:
            New RGB color with adjusted lightness
        """
        hsl = self.hsl()
        
        if at_least and light < hsl.l:
            # Don't decrease lightness if at_least is True
            return self
        
        if at_most and light > hsl.l:
            # Don't increase lightness if at_most is True
            return self
        
        new_hsl = HSL(h=hsl.h, s=hsl.s, l=light)
        return new_hsl.rgb()
    
    def lighten(self, multiplier: float) -> 'RGB':
        """Lighten color by multiplying RGB components.
        
        If any component exceeds 255, redistributes proportionally.
        
        Args:
            multiplier: Factor to multiply RGB components by
            
        Returns:
            New RGB color with lightened components
        """
        new_r = self.r * multiplier
        new_g = self.g * multiplier
        new_b = self.b * multiplier
        
        # Check if any component exceeds 255
        if new_r > 255 or new_g > 255 or new_b > 255:
            new_r, new_g, new_b = redistribute_rgb(
                int(new_r),
                int(new_g),
                int(new_b)
            )
        
        return RGB(
            r=round(new_r),
            g=round(new_g),
            b=round(new_b)
        )
    
    def is_light(self) -> bool:
        """Determine if color is light or dark.
        
        Uses HSL lightness threshold of 0.5.
        
        Returns:
            True if lightness > 0.5, False otherwise
        """
        return self.hsl().l > 0.5
    
    def overlay(self, color: 'RGB', alpha: float) -> 'RGB':
        """Blend this color with another using alpha blending.
        
        Formula: result = (1 - alpha) * self + alpha * color
        
        Args:
            color: Color to overlay on top
            alpha: Blending factor in [0.0, 1.0]
                  0.0 = fully this color
                  1.0 = fully overlay color
                  
        Returns:
            New RGB color from blending
        """
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"Alpha must be in [0.0, 1.0], got {alpha}")
        
        r = round((1 - alpha) * self.r + alpha * color.r)
        g = round((1 - alpha) * self.g + alpha * color.g)
        b = round((1 - alpha) * self.b + alpha * color.b)
        
        return RGB(r=r, g=g, b=b)
    
    def to_ansi_rgb(self, foreground: bool = True) -> str:
        """Generate 24-bit RGB ANSI escape code.
        
        Args:
            foreground: If True, generate foreground color code (38;2)
                       If False, generate background color code (48;2)
                       
        Returns:
            ANSI escape sequence for 24-bit RGB color
            
        Example:
            >>> RGB(255, 0, 0).to_ansi_rgb(foreground=True)
            '\\033[38;2;255;0;0m'
            >>> RGB(0, 255, 0).to_ansi_rgb(foreground=False)
            '\\033[48;2;0;255;0m'
        """
        prefix = "38" if foreground else "48"
        return f"\033[{prefix};2;{self.r};{self.g};{self.b}m"
    
    def to_ansi_8bit(self, foreground: bool = True) -> str:
        """Generate 8-bit (256-color) ANSI escape code.
        
        Converts RGB to 8-bit color code using:
        - Grayscale mapping (codes 232-255) for low-saturation colors
        - Color cube algorithm (codes 16-231) for saturated colors
        
        Args:
            foreground: If True, generate foreground color code (38;5)
                       If False, generate background color code (48;5)
                       
        Returns:
            ANSI escape sequence for 8-bit color
            
        Example:
            >>> RGB(255, 0, 0).to_ansi_8bit(foreground=True)
            '\\033[38;5;196m'
            >>> RGB(128, 128, 128).to_ansi_8bit(foreground=False)
            '\\033[48;5;244m'
        """
        hsl = self.hsl()
        
        # Low saturation colors use grayscale mapping (codes 232-255)
        if hsl.s < 0.1:
            # Map lightness [0.0, 1.0] to grayscale codes [232, 255]
            gray_code = 232 + round(hsl.l * 23)
            gray_code = max(232, min(255, gray_code))
            prefix = "38" if foreground else "48"
            return f"\033[{prefix};5;{gray_code}m"
        
        # Saturated colors use color cube (codes 16-231)
        # Formula: 16 + 36*r + 6*g + b where r,g,b are in [0, 5]
        r_cube = round(self.r / 255.0 * 5)
        g_cube = round(self.g / 255.0 * 5)
        b_cube = round(self.b / 255.0 * 5)
        
        color_code = 16 + 36 * r_cube + 6 * g_cube + b_cube
        
        prefix = "38" if foreground else "48"
        return f"\033[{prefix};5;{color_code}m"
    
    def to_ansi(self, mode: AnsiMode = "default", foreground: bool = True) -> str:
        """Generate ANSI escape code using specified color mode.
        
        Unified interface for ANSI color code generation that delegates
        to mode-specific methods.
        
        Args:
            mode: Color mode to use:
                  - "rgb": 24-bit true color (calls to_ansi_rgb)
                  - "8bit": 256-color palette (calls to_ansi_8bit)
                  - "ansi": Basic 16-color ANSI (uses 8bit as fallback)
                  - "default": Uses 8bit as safe default
            foreground: If True, generate foreground color code
                       If False, generate background color code
                       
        Returns:
            ANSI escape sequence for the specified mode
            
        Example:
            >>> RGB(255, 0, 0).to_ansi(mode="rgb")
            '\\033[38;2;255;0;0m'
            >>> RGB(255, 0, 0).to_ansi(mode="8bit")
            '\\033[38;5;196m'
        """
        if mode == "rgb":
            return self.to_ansi_rgb(foreground=foreground)
        elif mode == "8bit":
            return self.to_ansi_8bit(foreground=foreground)
        elif mode == "ansi":
            # Basic ANSI mode - use 8bit as fallback for now
            return self.to_ansi_8bit(foreground=foreground)
        else:  # mode == "default"
            # Default to 8bit as safe fallback
            return self.to_ansi_8bit(foreground=foreground)

    def to_ansi_rgb(self, foreground: bool = True) -> str:
        """Generate 24-bit RGB ANSI escape code.

        Args:
            foreground: If True, generate foreground color code (38;2)
                       If False, generate background color code (48;2)

        Returns:
            ANSI escape sequence for 24-bit RGB color

        Example:
            >>> RGB(255, 0, 0).to_ansi_rgb(foreground=True)
            '\\033[38;2;255;0;0m'
            >>> RGB(0, 255, 0).to_ansi_rgb(foreground=False)
            '\\033[48;2;0;255;0m'
        """
        prefix = "38" if foreground else "48"
        return f"\033[{prefix};2;{self.r};{self.g};{self.b}m"



def redistribute_rgb(r: int, g: int, b: int) -> tuple[int, int, int]:
    """Redistribute RGB components when values exceed 255.
    
    Maintains proportional relationships between components while
    ensuring all values are in valid [0, 255] range.
    
    Args:
        r: Red component (may exceed 255)
        g: Green component (may exceed 255)
        b: Blue component (may exceed 255)
        
    Returns:
        Tuple of (r, g, b) with all components in [0, 255]
    """
    max_component = max(r, g, b)
    
    if max_component <= 255:
        return (r, g, b)
    
    # Scale down proportionally
    scale = 255.0 / max_component
    return (
        round(r * scale),
        round(g * scale),
        round(b * scale)
    )


# Minecraft color code mappings to 8-bit ANSI codes
_MINECRAFT_COLORS = {
    '0': 16,   # Black
    '1': 19,   # Dark Blue
    '2': 34,   # Dark Green
    '3': 37,   # Dark Aqua
    '4': 124,  # Dark Red
    '5': 127,  # Dark Purple
    '6': 214,  # Gold
    '7': 248,  # Gray
    '8': 240,  # Dark Gray
    '9': 63,   # Blue
    'a': 83,   # Green
    'b': 87,   # Aqua
    'c': 203,  # Red
    'd': 207,  # Light Purple
    'e': 227,  # Yellow
    'f': 231,  # White
}

# Formatting code mappings to ANSI escape sequences
_FORMATTING_CODES = {
    'l': '\033[1m',  # Bold
    'o': '\033[3m',  # Italic
    'n': '\033[4m',  # Underline
    'r': '\033[0m',  # Reset
}

# Extended code mappings
_EXTENDED_CODES = {
    '-': '\n',       # Newline
    '~': '\033[39m', # Reset foreground
    '*': '\033[49m', # Reset background
}


def color(msg: str) -> str:
    """Parse Minecraft-style color codes and convert to ANSI escape sequences.
    
    Supports the following color code formats:
    - &0-&f: Minecraft color codes (16 colors)
    - &l: Bold
    - &o: Italic
    - &n: Underline
    - &r: Reset all formatting
    - &-: Newline
    - &~: Reset foreground color
    - &*: Reset background color
    - &gf(#RRGGBB): RGB foreground color
    - &gb(#RRGGBB): RGB background color
    - &gf(R,G,B): RGB foreground color with comma-separated values
    - &gb(R,G,B): RGB background color with comma-separated values
    
    Args:
        msg: String containing Minecraft-style color codes
        
    Returns:
        String with color codes replaced by ANSI escape sequences
        
    Example:
        >>> color("&cRed text &aGreen text &r")
        '\\033[38;5;203mRed text \\033[38;5;83mGreen text \\033[0m'
        >>> color("&gf(#FF0000)Custom red")
        '\\033[38;2;255;0;0mCustom red'
    """
    import re
    
    result = msg
    
    # Process RGB color codes: &gf(#RRGGBB) or &gb(#RRGGBB)
    def replace_rgb_hex(match):
        fg_or_bg = match.group(1)  # 'f' for foreground, 'b' for background
        hex_color = match.group(2)
        try:
            rgb = RGB.from_hex(hex_color)
            return rgb.to_ansi_rgb(foreground=(fg_or_bg == 'f'))
        except ValueError:
            # Invalid hex color, leave as-is
            return match.group(0)
    
    result = re.sub(r'&g([fb])\(#([0-9A-Fa-f]{3,6})\)', replace_rgb_hex, result)
    
    # Process RGB color codes: &gf(R,G,B) or &gb(R,G,B)
    def replace_rgb_comma(match):
        fg_or_bg = match.group(1)  # 'f' for foreground, 'b' for background
        r_str = match.group(2)
        g_str = match.group(3)
        b_str = match.group(4)
        try:
            r = int(r_str)
            g = int(g_str)
            b = int(b_str)
            rgb = RGB(r=r, g=g, b=b)
            return rgb.to_ansi_rgb(foreground=(fg_or_bg == 'f'))
        except (ValueError, TypeError):
            # Invalid RGB values, leave as-is
            return match.group(0)
    
    result = re.sub(r'&g([fb])\((\d+),(\d+),(\d+)\)', replace_rgb_comma, result)
    
    # Process Minecraft color codes (&0-&f)
    for code, ansi_code in _MINECRAFT_COLORS.items():
        result = result.replace(f'&{code}', f'\033[38;5;{ansi_code}m')
    
    # Process formatting codes (&l, &o, &n, &r)
    for code, ansi_seq in _FORMATTING_CODES.items():
        result = result.replace(f'&{code}', ansi_seq)
    
    # Process extended codes (&-, &~, &*)
    for code, replacement in _EXTENDED_CODES.items():
        result = result.replace(f'&{code}', replacement)
    
    return result


def printc(msg: str) -> None:
    """Print string with Minecraft-style color codes.
    
    Automatically appends ANSI reset code at the end to prevent
    color bleeding into subsequent terminal output.
    
    Args:
        msg: String containing Minecraft-style color codes
        
    Example:
        >>> printc("&cRed text &aGreen text")
        # Prints colored text and resets formatting
    """
    colored_msg = color(msg)
    # Append reset code if not already present at the end
    if not colored_msg.endswith('\033[0m'):
        colored_msg += '\033[0m'
    print(colored_msg)
