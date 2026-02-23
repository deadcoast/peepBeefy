"""ASCII art color alignment and rendering system.

This module provides flexible color application to ASCII art with support for:
- Horizontal alignment (one color per line)
- Vertical alignment (gradient across character positions)
- Custom alignment (per-ASCII-color-index mapping)
- Neofetch color code stripping
"""

import re
from dataclasses import dataclass
from typing import Literal, Optional

from src.color_util import RGB, AnsiMode
from src.color_presets import ColorPreset


ColorAlignMode = Literal["horizontal", "vertical", "custom"]


@dataclass
class ColorAlignment:
    """Color alignment configuration for ASCII art.
    
    Attributes:
        mode: Alignment mode ("horizontal", "vertical", "custom")
        custom_colors: Optional color mapping for custom mode
                      Maps ASCII color codes to preset color indices
    """
    mode: ColorAlignMode
    custom_colors: Optional[dict[str, str]] = None
    
    def __post_init__(self):
        """Validate alignment configuration."""
        if self.mode == "custom" and self.custom_colors is None:
            raise ValueError("custom_colors required when mode is 'custom'")
        
        if self.mode != "custom" and self.custom_colors is not None:
            raise ValueError(
                f"custom_colors should only be provided for 'custom' mode, "
                f"got mode='{self.mode}'"
            )
    
    @classmethod
    def from_dict(cls, d: dict) -> 'ColorAlignment':
        """Construct ColorAlignment from dictionary.
        
        Args:
            d: Dictionary with 'mode' and optional 'custom_colors' keys
            
        Returns:
            ColorAlignment instance
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        mode = d.get('mode')
        if mode is None:
            raise ValueError("Missing required field: 'mode'")
        
        if mode not in ("horizontal", "vertical", "custom"):
            raise ValueError(
                f"Invalid mode '{mode}', expected 'horizontal', 'vertical', or 'custom'"
            )
        
        custom_colors = d.get('custom_colors')
        
        return cls(mode=mode, custom_colors=custom_colors)


class ASCIIColorizer:
    """Apply colors to ASCII art with flexible alignment modes.
    
    Attributes:
        preset: Color preset to use for coloring
        alignment: Color alignment configuration
        ansi_mode: ANSI color mode for terminal output
    """
    
    def __init__(
        self,
        preset: ColorPreset,
        alignment: ColorAlignment,
        ansi_mode: AnsiMode = "8bit"
    ):
        """Initialize ASCII colorizer.
        
        Args:
            preset: Color preset to use
            alignment: Alignment configuration
            ansi_mode: ANSI color mode ("rgb", "8bit", "ansi", "default")
        """
        self.preset = preset
        self.alignment = alignment
        self.ansi_mode = ansi_mode
    
    def colorize(self, lines: list[str]) -> list[str]:
        """Apply colors to ASCII art lines.
        
        Dispatcher method that delegates to mode-specific colorization.
        
        Args:
            lines: ASCII art lines to colorize
            
        Returns:
            Colorized ASCII art lines
        """
        if not lines:
            return []
        
        if not self.preset.colors:
            return lines
        
        # Strip existing color codes first
        stripped_lines = [self.strip_neofetch_codes(line) for line in lines]
        
        # Dispatch to mode-specific method
        if self.alignment.mode == "horizontal":
            return self.colorize_horizontal(stripped_lines)
        elif self.alignment.mode == "vertical":
            return self.colorize_vertical(stripped_lines)
        elif self.alignment.mode == "custom":
            return self.colorize_custom(stripped_lines)
        else:
            # Should never happen due to validation, but fallback
            return stripped_lines
    
    def strip_neofetch_codes(self, line: str) -> str:
        """Remove existing neofetch/ANSI color codes from line.
        
        Removes ANSI escape sequences while preserving text content.
        
        Args:
            line: Line potentially containing ANSI codes
            
        Returns:
            Line with ANSI codes removed
        """
        # Pattern matches ANSI escape sequences: \033[...m or \x1b[...m
        ansi_pattern = r'\033\[[0-9;]*m|\x1b\[[0-9;]*m'
        return re.sub(ansi_pattern, '', line)
    
    def colorize_horizontal(self, lines: list[str]) -> list[str]:
        """Apply horizontal color alignment (one color per line).
        
        Each line gets a single color from the preset. If there are more
        lines than colors, cycles through the color list.
        
        Args:
            lines: ASCII art lines to colorize
            
        Returns:
            Colorized lines with one color per line
        """
        colors = self.preset.expand_colors()
        if not colors:
            return lines
        
        colored_lines = []
        reset_code = '\033[0m'
        
        for i, line in enumerate(lines):
            # Cycle through colors if more lines than colors
            color = colors[i % len(colors)]
            ansi_code = color.to_ansi(mode=self.ansi_mode, foreground=True)
            colored_lines.append(f"{ansi_code}{line}{reset_code}")
        
        return colored_lines
    
    def colorize_vertical(self, lines: list[str]) -> list[str]:
        """Apply vertical color alignment (gradient across width).
        
        Creates a horizontal gradient effect by spreading colors across
        character positions within each line.
        
        Args:
            lines: ASCII art lines to colorize
            
        Returns:
            Colorized lines with gradient across width
        """
        if not lines:
            return []
        
        # Find maximum line width
        max_width = max(len(line) for line in lines)
        if max_width == 0:
            return lines
        
        # Spread colors across width
        colors = self.preset.spread_colors(max_width)
        reset_code = '\033[0m'
        
        colored_lines = []
        for line in lines:
            if not line:
                colored_lines.append(line)
                continue
            
            # Apply color to each character based on position
            colored_chars = []
            for i, char in enumerate(line):
                if i < len(colors):
                    color = colors[i]
                    ansi_code = color.to_ansi(mode=self.ansi_mode, foreground=True)
                    colored_chars.append(f"{ansi_code}{char}")
                else:
                    colored_chars.append(char)
            
            colored_lines.append(''.join(colored_chars) + reset_code)
        
        return colored_lines
    
    def colorize_custom(self, lines: list[str]) -> list[str]:
        """Apply custom color alignment using color code mapping.
        
        Maps ASCII color codes (e.g., from neofetch) to preset colors
        using the custom_colors mapping.
        
        Args:
            lines: ASCII art lines to colorize
            
        Returns:
            Colorized lines with custom color mapping
        """
        if self.alignment.custom_colors is None:
            # Should not happen due to validation, but fallback
            return lines
        
        colors = self.preset.expand_colors()
        if not colors:
            return lines
        
        # Build mapping from ASCII color codes to RGB colors
        color_map = {}
        for ascii_code, preset_idx in self.alignment.custom_colors.items():
            try:
                # preset_idx could be numeric string or color name
                if preset_idx.isdigit():
                    idx = int(preset_idx)
                    if 0 <= idx < len(colors):
                        color_map[ascii_code] = colors[idx]
                else:
                    # Try to find color by name in preset
                    # For now, just use modulo to wrap around
                    idx = hash(preset_idx) % len(colors)
                    color_map[ascii_code] = colors[idx]
            except (ValueError, IndexError):
                # Invalid mapping, skip
                continue
        
        # Apply custom color mapping
        # This is a simplified implementation - in practice, you'd need to
        # parse the original ASCII art format to understand its color codes
        colored_lines = []
        reset_code = '\033[0m'
        
        for line in lines:
            # For custom mode, we assume the line might have markers or
            # we apply a default color. This is a placeholder implementation.
            # Real implementation would parse original format's color codes.
            
            # Default: apply first color to entire line
            if colors:
                color = colors[0]
                ansi_code = color.to_ansi(mode=self.ansi_mode, foreground=True)
                colored_lines.append(f"{ansi_code}{line}{reset_code}")
            else:
                colored_lines.append(line)
        
        return colored_lines
