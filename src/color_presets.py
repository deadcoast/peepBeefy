"""Color preset management system.

This module provides color preset management with support for:
- Simple presets (list of hex colors)
- Weighted presets (colors with repetition factors)
- Color spreading across target lengths
- Lightness adjustment for background adaptation
- Lazy loading and caching for performance optimization
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from src.color_util import RGB


LightDark = Literal["light", "dark"]

# Global preset cache for lazy loading
_preset_cache: Optional[dict[str, 'ColorPreset']] = None
_preset_cache_file: Optional[Path] = None


@dataclass
class ColorPreset:
    """Color preset with optional weights for repetition.
    
    Attributes:
        name: Preset identifier
        colors: List of hex color strings
        weights: Optional repetition factors for each color
    """
    name: str
    colors: list[str]
    weights: Optional[list[int]] = None
    
    def __post_init__(self):
        """Validate preset data."""
        if not self.colors:
            raise ValueError(f"Preset '{self.name}' must have at least one color")
        
        if self.weights is not None:
            if len(self.weights) != len(self.colors):
                raise ValueError(
                    f"Preset '{self.name}': weights length ({len(self.weights)}) "
                    f"must match colors length ({len(self.colors)})"
                )
            if any(w <= 0 for w in self.weights):
                raise ValueError(f"Preset '{self.name}': all weights must be positive")
    
    def expand_colors(self) -> list[RGB]:
        """Expand colors according to weights.
        
        If weights are provided, each color is repeated according to its weight.
        If no weights, returns colors as-is.
        
        Returns:
            List of RGB colors with repetition applied
        """
        rgb_colors = [RGB.from_hex(c) for c in self.colors]
        
        if self.weights is None:
            return rgb_colors
        
        expanded = []
        for color, weight in zip(rgb_colors, self.weights):
            expanded.extend([color] * weight)
        
        return expanded
    
    def spread_colors(self, length: int) -> list[RGB]:
        """Distribute colors across specified length.
        
        Uses center-outward distribution for balanced appearance when
        fewer colors than target length.
        
        Args:
            length: Target number of colors
            
        Returns:
            List of exactly 'length' RGB colors
        """
        if length <= 0:
            raise ValueError(f"Length must be positive, got {length}")
        
        expanded = self.expand_colors()
        return spread_colors_balanced(expanded, length)
    
    def adjust_lightness(
        self,
        light_dark: LightDark,
        method: str = "hsl"
    ) -> 'ColorPreset':
        """Adjust colors for light/dark backgrounds.
        
        Args:
            light_dark: "light" or "dark" background
            method: "hsl" for HSL adjustment, "overlay" for overlay-based
            
        Returns:
            New ColorPreset with adjusted colors
        """
        expanded = self.expand_colors()
        
        if light_dark == "dark":
            # Dark background: ensure lightness >= 0.65
            target_lightness = 0.65
            adjusted = []
            for color in expanded:
                if method == "hsl":
                    adjusted.append(color.set_light(target_lightness, at_least=True))
                else:  # overlay
                    # Overlay with white to lighten
                    white = RGB(r=255, g=255, b=255)
                    if color.hsl().l < target_lightness:
                        # Calculate alpha needed to reach target lightness
                        # For very dark colors, we need higher alpha values
                        # Linear approximation: alpha ≈ (target - current) / (1.0 - current)
                        current_l = color.hsl().l
                        if current_l < 0.99:  # Avoid division by zero
                            alpha = min(1.0, (target_lightness - current_l) / (1.0 - current_l))
                        else:
                            alpha = 0.0
                        adjusted.append(color.overlay(white, alpha))
                    else:
                        adjusted.append(color)
        else:  # light background
            # Light background: ensure lightness <= 0.4
            target_lightness = 0.4
            adjusted = []
            for color in expanded:
                if method == "hsl":
                    adjusted.append(color.set_light(target_lightness, at_most=True))
                else:  # overlay
                    # Overlay with black to darken
                    black = RGB(r=0, g=0, b=0)
                    if color.hsl().l > target_lightness:
                        # Calculate alpha needed to reach target lightness
                        # Linear approximation: alpha ≈ (current - target) / current
                        current_l = color.hsl().l
                        if current_l > 0.01:  # Avoid division by zero
                            alpha = min(1.0, (current_l - target_lightness) / current_l)
                        else:
                            alpha = 0.0
                        adjusted.append(color.overlay(black, alpha))
                    else:
                        adjusted.append(color)
        
        # Convert back to hex strings
        adjusted_hex = [f"#{c.r:02x}{c.g:02x}{c.b:02x}" for c in adjusted]
        
        return ColorPreset(
            name=f"{self.name}_adjusted",
            colors=adjusted_hex,
            weights=None  # Weights already applied during expansion
        )


def spread_colors_balanced(colors: list[RGB], target_length: int) -> list[RGB]:
    """Distribute colors with center-outward balancing.
    
    When fewer colors than target length, distributes extra colors
    symmetrically from center outward for balanced appearance.
    
    Args:
        colors: Source color list
        target_length: Desired output length
        
    Returns:
        List of exactly target_length colors
    """
    if target_length <= 0:
        raise ValueError(f"Target length must be positive, got {target_length}")
    
    if not colors:
        raise ValueError("Cannot spread empty color list")
    
    if len(colors) == target_length:
        return colors.copy()
    
    if len(colors) > target_length:
        # More colors than needed: sample evenly
        step = len(colors) / target_length
        return [colors[int(i * step)] for i in range(target_length)]
    
    # Fewer colors than needed: distribute from center outward
    result = [None] * target_length
    
    # Calculate spacing
    spacing = target_length / len(colors)
    
    # Place colors at evenly spaced positions
    for i, color in enumerate(colors):
        pos = int(i * spacing + spacing / 2)
        if pos >= target_length:
            pos = target_length - 1
        result[pos] = color
    
    # Fill gaps by interpolating from nearest placed colors
    for i in range(target_length):
        if result[i] is None:
            # Find nearest colors on left and right
            left_idx = i - 1
            while left_idx >= 0 and result[left_idx] is None:
                left_idx -= 1
            
            right_idx = i + 1
            while right_idx < target_length and result[right_idx] is None:
                right_idx += 1
            
            if left_idx >= 0 and right_idx < target_length:
                # Interpolate between left and right
                left_color = result[left_idx]
                right_color = result[right_idx]
                ratio = (i - left_idx) / (right_idx - left_idx)
                result[i] = RGB(
                    r=round(left_color.r * (1 - ratio) + right_color.r * ratio),
                    g=round(left_color.g * (1 - ratio) + right_color.g * ratio),
                    b=round(left_color.b * (1 - ratio) + right_color.b * ratio)
                )
            elif left_idx >= 0:
                # Only left color available
                result[i] = result[left_idx]
            elif right_idx < target_length:
                # Only right color available
                result[i] = result[right_idx]
            else:
                # Shouldn't happen, but fallback to first color
                result[i] = colors[0]
    
    return result


def load_presets(preset_file: Path) -> dict[str, ColorPreset]:
    """Load color presets from JSON configuration.
    
    JSON format:
    {
        "preset_name": ["#color1", "#color2", ...],
        "weighted_preset": {
            "colors": ["#color1", "#color2"],
            "weights": [2, 1]
        }
    }
    
    Args:
        preset_file: Path to JSON preset file
        
    Returns:
        Dictionary mapping preset names to ColorPreset objects
        
    Raises:
        FileNotFoundError: If preset file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        ValueError: If preset data is invalid
    """
    with open(preset_file, 'r') as f:
        data = json.load(f)
    
    presets = {}
    
    for name, preset_data in data.items():
        if isinstance(preset_data, list):
            # Simple preset: just a list of colors
            presets[name] = ColorPreset(name=name, colors=preset_data)
        elif isinstance(preset_data, dict):
            # Weighted preset: dict with colors and weights
            colors = preset_data.get("colors", [])
            weights = preset_data.get("weights")
            presets[name] = ColorPreset(name=name, colors=colors, weights=weights)
        else:
            raise ValueError(
                f"Invalid preset format for '{name}': "
                f"expected list or dict, got {type(preset_data)}"
            )
    
    return presets


def get_presets_lazy(preset_file: Optional[Path] = None) -> dict[str, ColorPreset]:
    """Get color presets with lazy loading and caching.
    
    Loads presets only once and caches them for subsequent calls.
    This significantly improves startup performance by deferring
    preset loading until actually needed.
    
    Args:
        preset_file: Path to JSON preset file (defaults to data/color_presets.json)
        
    Returns:
        Dictionary mapping preset names to ColorPreset objects
        
    Examples:
        >>> presets = get_presets_lazy()  # First call loads from disk
        >>> presets = get_presets_lazy()  # Subsequent calls use cache
    """
    global _preset_cache, _preset_cache_file
    
    # Use default preset file if not specified
    if preset_file is None:
        preset_file = Path("data/color_presets.json")
    
    # Return cached presets if available and file hasn't changed
    if _preset_cache is not None and _preset_cache_file == preset_file:
        return _preset_cache
    
    # Load presets from disk
    _preset_cache = load_presets(preset_file)
    _preset_cache_file = preset_file
    
    return _preset_cache


def clear_preset_cache() -> None:
    """Clear the preset cache.
    
    Useful for testing or when preset files are modified at runtime.
    """
    global _preset_cache, _preset_cache_file
    _preset_cache = None
    _preset_cache_file = None


# Global preset cache for lazy loading
_preset_cache: Optional[dict[str, ColorPreset]] = None
_preset_cache_file: Optional[Path] = None


def get_presets_lazy(preset_file: Optional[Path] = None) -> dict[str, ColorPreset]:
    """Get color presets with lazy loading and caching.

    Loads presets only once and caches them for subsequent calls.
    This significantly improves startup performance by deferring
    preset loading until actually needed.

    Args:
        preset_file: Path to JSON preset file (defaults to data/color_presets.json)

    Returns:
        Dictionary mapping preset names to ColorPreset objects

    Examples:
        >>> presets = get_presets_lazy()  # First call loads from disk
        >>> presets = get_presets_lazy()  # Subsequent calls use cache
    """
    global _preset_cache, _preset_cache_file

    # Use default preset file if not specified
    if preset_file is None:
        preset_file = Path("data/color_presets.json")

    # Return cached presets if available and file hasn't changed
    if _preset_cache is not None and _preset_cache_file == preset_file:
        return _preset_cache

    # Load presets from disk
    _preset_cache = load_presets(preset_file)
    _preset_cache_file = preset_file

    return _preset_cache


def clear_preset_cache() -> None:
    """Clear the preset cache.

    Useful for testing or when preset files are modified at runtime.
    """
    global _preset_cache, _preset_cache_file
    _preset_cache = None
    _preset_cache_file = None

