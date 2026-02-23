"""
Color gradient generation and scaling system.

This module provides functionality for creating smooth color gradients
between multiple RGB colors using linear interpolation. It supports
pre-computed gradient arrays for efficient O(1) lookup operations.

Performance optimizations:
- Gradient caching to avoid recomputation
- Lazy gradient generation for Scale objects
"""

from dataclasses import dataclass, field
from typing import List, Optional
from src.color_util import RGB

# Global gradient cache for performance optimization
_gradient_cache: dict[tuple, List[RGB]] = {}


def create_gradient(colors: List[RGB], resolution: int) -> List[RGB]:
    """
    Create a gradient array using linear interpolation between colors.
    
    For a list of N colors, generates (N-1) * resolution interpolated colors,
    creating smooth transitions between each consecutive color pair.
    
    Uses caching to avoid recomputing identical gradients.
    
    Args:
        colors: List of RGB colors to interpolate between
        resolution: Number of interpolation steps per color pair
        
    Returns:
        List of interpolated RGB colors
        
    Raises:
        ValueError: If colors list is empty or resolution < 1
        
    Examples:
        >>> red = RGB(255, 0, 0)
        >>> blue = RGB(0, 0, 255)
        >>> gradient = create_gradient([red, blue], resolution=10)
        >>> len(gradient)
        10
    """
    if not colors:
        raise ValueError("Cannot create gradient from empty color list")
    
    if len(colors) == 1:
        # Single color "gradient" - just repeat the color
        return [colors[0]] * resolution
    
    if resolution < 1:
        raise ValueError(f"Resolution must be >= 1, got {resolution}")
    
    # Create cache key from colors and resolution
    cache_key = (tuple((c.r, c.g, c.b) for c in colors), resolution)
    
    # Check cache first
    if cache_key in _gradient_cache:
        return _gradient_cache[cache_key]
    
    gradient = []
    
    # Interpolate between each consecutive pair of colors
    for i in range(len(colors) - 1):
        c1 = colors[i]
        c2 = colors[i + 1]
        
        # Generate 'resolution' steps between c1 and c2
        for step in range(resolution):
            ratio = step / resolution
            
            # Linear interpolation: c2 * ratio + c1 * (1 - ratio)
            r = round(c2.r * ratio + c1.r * (1 - ratio))
            g = round(c2.g * ratio + c1.g * (1 - ratio))
            b = round(c2.b * ratio + c1.b * (1 - ratio))
            
            gradient.append(RGB(r, g, b))
    
    # Cache the result
    _gradient_cache[cache_key] = gradient
    
    return gradient


def create_gradient_hex(colors: List[str], resolution: int = 300) -> List[RGB]:
    """
    Create a gradient from hex color strings.
    
    Convenience function that converts hex strings to RGB objects
    and then creates a gradient.
    
    Args:
        colors: List of hex color strings (e.g., ["#FF0000", "#0000FF"])
        resolution: Number of interpolation steps per color pair (default: 300)
        
    Returns:
        List of interpolated RGB colors
        
    Raises:
        ValueError: If any hex string is invalid or colors list is empty
        
    Examples:
        >>> gradient = create_gradient_hex(["#FF0000", "#00FF00", "#0000FF"])
        >>> len(gradient)
        600
    """
    rgb_colors = [RGB.from_hex(hex_str) for hex_str in colors]
    return create_gradient(rgb_colors, resolution)


def get_raw(gradient: List[RGB], ratio: float) -> RGB:
    """
    Get color at specific ratio in pre-computed gradient.
    
    Helper function for array indexing with ratio-based lookup.
    
    Args:
        gradient: Pre-computed gradient array
        ratio: Position in gradient (0.0 = start, 1.0 = end)
        
    Returns:
        RGB color at the specified ratio
        
    Raises:
        ValueError: If gradient is empty
        IndexError: Should not occur due to clamping
        
    Examples:
        >>> gradient = create_gradient_hex(["#FF0000", "#0000FF"], 100)
        >>> color = get_raw(gradient, 0.5)  # Middle color
    """
    if not gradient:
        raise ValueError("Cannot lookup color in empty gradient")
    
    if ratio <= 0.0:
        return gradient[0]
    if ratio >= 1.0:
        return gradient[-1]
    
    # Map ratio to array index
    index = int(ratio * (len(gradient) - 1))
    return gradient[index]


@dataclass
class Scale:
    """
    Color scale with pre-computed gradient for efficient lookup.
    
    Provides O(1) color lookup by ratio using a pre-computed gradient array.
    Supports initialization from hex color strings.
    
    Attributes:
        colors: Original list of RGB colors
        rgb: Pre-computed gradient array for fast lookup
        
    Examples:
        >>> scale = Scale(["#FF0000", "#00FF00", "#0000FF"], resolution=300)
        >>> red = scale(0.0)
        >>> green = scale(0.5)
        >>> blue = scale(1.0)
    """
    colors: List[RGB] = field(default_factory=list)
    rgb: List[RGB] = field(default_factory=list)
    
    def __init__(self, scale: List[str], resolution: int = 300):
        """
        Initialize Scale from hex color strings.
        
        Args:
            scale: List of hex color strings
            resolution: Number of interpolation steps per color pair
            
        Raises:
            ValueError: If scale is empty or contains invalid hex strings
        """
        if not scale:
            raise ValueError("Cannot create Scale from empty color list")
        
        # Convert hex strings to RGB objects
        self.colors = [RGB.from_hex(hex_str) for hex_str in scale]
        
        # Pre-compute gradient array (uses caching internally)
        self.rgb = create_gradient(self.colors, resolution)
    
    def __call__(self, ratio: float) -> RGB:
        """
        Get color at ratio (0.0-1.0) in gradient.
        
        Args:
            ratio: Position in gradient (0.0 = start, 1.0 = end)
            
        Returns:
            RGB color at the specified ratio
            
        Examples:
            >>> scale = Scale(["#FF0000", "#0000FF"])
            >>> color = scale(0.5)  # Middle color between red and blue
        """
        return get_raw(self.rgb, ratio)
    
    def get_raw(self, ratio: float) -> RGB:
        """
        Get color at ratio using internal gradient array.
        
        Convenience method that calls the module-level get_raw function.
        
        Args:
            ratio: Position in gradient (0.0-1.0)
            
        Returns:
            RGB color at the specified ratio
        """
        return get_raw(self.rgb, ratio)


def clear_gradient_cache() -> None:
    """Clear the gradient cache.
    
    Useful for testing or when memory needs to be freed.
    """
    global _gradient_cache
    _gradient_cache.clear()


def get_gradient_cache_stats() -> dict:
    """Get gradient cache statistics.
    
    Returns:
        Dictionary with cache statistics:
        - size: Number of cached gradients
        - memory_estimate: Estimated memory usage in bytes
    """
    size = len(_gradient_cache)
    
    # Estimate memory: each RGB is ~24 bytes (3 ints + overhead)
    memory_estimate = sum(len(gradient) * 24 for gradient in _gradient_cache.values())
    
    return {
        "size": size,
        "memory_estimate": memory_estimate,
        "memory_mb": memory_estimate / (1024 * 1024)
    }
