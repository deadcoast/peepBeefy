"""
Fire Animation Engine for peepBeefy

Implements DOOM PSX-inspired fire animation with per-character coloring,
flame zone detection, and configurable intensity levels.

Design: Extracted and generalized from install.py fire animation system.
"""

import random
import time
from typing import List, Tuple, Optional

from rich.console import Console
from rich.text import Text
from rich.style import Style
from rich.live import Live


class FirePalette:
    """12-step DOOM PSX fire color palette.
    
    The palette progresses from barely visible embers (index 0) to near-white
    flame tips (index 11). This creates smooth color transitions for the
    flicker effect.
    
    Palette structure:
    - Indices 0-3: Embers (dark red to red-orange)
    - Indices 4-7: Flame core (red to orange)
    - Indices 8-11: Flame tips (orange to yellow-white)
    """
    
    COLORS = (
        "#4F0F07", "#6D1504", "#8B1A00", "#AB1E00",  # embers
        "#CC2200", "#E53400", "#FF4500", "#FF6800",  # flame core
        "#FF8C00", "#FFB400", "#FFD700", "#FFE55C",  # tips
    )
    
    STYLES = tuple(Style(color=c) for c in COLORS)


class FireAnimator:
    """Applies DOOM PSX fire effect to ASCII art banners.
    
    The animator detects flame zones vs text zones in the banner and applies
    appropriate coloring:
    - Flame zones: Fire palette with flicker effect
    - Text zones: White/gray gradient with ember crack effect
    
    Attributes:
        intensity: Animation intensity level ("subtle", "normal", "intense")
    """
    
    # Pre-weighted flicker offsets for natural flame movement
    # Distribution: 0(40%) +1(18%) -1(17%) +2(13%) -2(12%)
    # Slight warm bias (31% warm vs 29% cool) — flames push energy upward
    _FLICKER_OFFSETS = (0,)*40 + (1,)*18 + (-1,)*17 + (2,)*13 + (-2,)*12
    
    # Text styles for text zone lines (white → gray → dim)
    _TEXT_STYLES = (
        Style(color="#FFFFFF", bold=True),   # Line 0: white-hot text
        Style(color="#CCCCCC"),              # Line 1: cooling glow
        Style(color="#999999", dim=True),    # Line 2: dim base
    )
    
    def __init__(self, intensity: str = "normal"):
        """Initialize the fire animator.
        
        Args:
            intensity: Animation intensity level ("subtle", "normal", "intense")
        """
        self._intensity = intensity
        self._intensity_multiplier = self._get_intensity_multiplier()
    
    def _get_intensity_multiplier(self) -> float:
        """Get the intensity multiplier for flicker and crack probabilities.
        
        Returns:
            Multiplier value: 0.5 for subtle, 1.0 for normal, 1.5 for intense
        """
        multipliers = {
            "subtle": 0.5,
            "normal": 1.0,
            "intense": 1.5,
        }
        return multipliers.get(self._intensity, 1.0)
    
    def animate_banner(
        self,
        banner,  # Banner type from banner.py
        console: Console,
        duration: float = 3.0,
        fps: int = 8
    ) -> None:
        """Run fire animation on banner for specified duration.
        
        Args:
            banner: Banner object with lines and metadata
            console: Rich Console for rendering
            duration: Animation duration in seconds
            fps: Frames per second
        """
        # Detect flame and text zones
        flame_lines, text_lines = self._detect_zones(banner)
        
        # Pre-compute all frames for smooth playback
        # Ensure at least 1 frame
        num_frames = max(1, int(duration * fps))
        frames = []
        rng = random.Random()
        
        for frame_idx in range(num_frames):
            frame = self._build_frame(banner, flame_lines, text_lines, rng)
            frames.append(frame)
        
        # Animate with Live context
        interval = 1.0 / fps
        start = time.monotonic()
        
        with Live(frames[0], console=console, refresh_per_second=fps) as live:
            frame_idx = 0
            while time.monotonic() - start < duration:
                live.update(frames[frame_idx % len(frames)])
                frame_idx += 1
                time.sleep(interval)
    
    def _detect_zones(self, banner) -> Tuple[List[int], List[int]]:
        """Detect which lines are flame vs text zones.
        
        Uses a 60/40 split heuristic: top 60% of banner is flame zone,
        bottom 40% is text zone. Can be overridden by banner metadata.
        
        Args:
            banner: Banner object with lines and metadata
            
        Returns:
            Tuple of (flame_line_indices, text_line_indices)
        """
        total_lines = len(banner.lines)
        
        # Check for explicit metadata override
        if hasattr(banner.metadata, 'flame_lines') and banner.metadata.flame_lines is not None:
            flame_lines = banner.metadata.flame_lines
            text_lines = [i for i in range(total_lines) if i not in flame_lines]
            return flame_lines, text_lines
        
        # Heuristic: 60/40 split
        flame_cutoff = int(total_lines * 0.6)
        flame_lines = list(range(flame_cutoff))
        text_lines = list(range(flame_cutoff, total_lines))
        
        return flame_lines, text_lines
    
    def _build_frame(
        self,
        banner,
        flame_lines: List[int],
        text_lines: List[int],
        rng: random.Random
    ) -> Text:
        """Build a single animation frame with per-character coloring.
        
        Args:
            banner: Banner object with lines
            flame_lines: Indices of lines in flame zone
            text_lines: Indices of lines in text zone
            rng: Random number generator for flicker
            
        Returns:
            Rich Text object with colored frame
        """
        result = Text()
        
        for i, line in enumerate(banner.lines):
            if i > 0:
                result.append("\n")
            
            if i in flame_lines:
                result.append(self._apply_flame_coloring(line, i, len(flame_lines), rng))
            elif i in text_lines:
                text_line_idx = text_lines.index(i)
                result.append(self._apply_text_coloring(line, text_line_idx, rng))
            else:
                # No coloring for lines outside zones
                result.append(line)
        
        return result
    
    def _apply_flame_coloring(
        self,
        line: str,
        line_idx: int,
        num_flame_lines: int,
        rng: random.Random
    ) -> Text:
        """Apply fire palette coloring to a flame zone line.
        
        Hotter colors at the top, cooler at the bottom. Flicker probability
        decreases toward the bottom.
        
        Args:
            line: Text line to color
            line_idx: Index of this line in the banner
            num_flame_lines: Total number of flame lines
            rng: Random number generator
            
        Returns:
            Rich Text with fire coloring
        """
        result = Text()
        
        # Determine base palette index based on line position
        # Top lines = hotter (higher index), bottom lines = cooler (lower index)
        normalized_pos = line_idx / max(1, num_flame_lines - 1) if num_flame_lines > 1 else 0
        base_idx = int(2 + normalized_pos * 8)  # Range: 2-10
        
        # Flicker probability decreases toward bottom
        flicker_prob = (1.0 - (normalized_pos * 0.5)) * self._intensity_multiplier
        
        # Min/max palette indices for this line
        lo = max(0, base_idx - 2)
        hi = min(11, base_idx + 2)
        
        for char in line:
            if char == ' ':
                result.append(char)
            else:
                if rng.random() < flicker_prob:
                    # Apply flicker offset
                    offset = rng.choice(self._FLICKER_OFFSETS)
                    idx = max(lo, min(hi, base_idx + offset))
                else:
                    idx = base_idx
                
                result.append(char, style=FirePalette.STYLES[idx])
        
        return result
    
    def _apply_text_coloring(
        self,
        line: str,
        text_line_idx: int,
        rng: random.Random
    ) -> Text:
        """Apply text coloring with ember crack effect.
        
        Uses white → gray → dim gradient based on line position.
        Randomly applies hot ember colors to simulate cracks.
        
        Args:
            line: Text line to color
            text_line_idx: Index within text zone (0 = first text line)
            rng: Random number generator
            
        Returns:
            Rich Text with text coloring and ember cracks
        """
        result = Text()
        
        # Determine base text style and crack parameters
        # Clamp to available text styles
        style_idx = min(text_line_idx, len(self._TEXT_STYLES) - 1)
        base_style = self._TEXT_STYLES[style_idx]
        
        # Crack probability and palette indices based on line position
        if text_line_idx == 0:
            crack_prob = 0.20 * self._intensity_multiplier
            crack_palette = (10, 11)  # Hot yellow
        elif text_line_idx == 1:
            crack_prob = 0.12 * self._intensity_multiplier
            crack_palette = (8, 9)  # Orange
        else:
            crack_prob = 0.06 * self._intensity_multiplier
            crack_palette = (2, 4)  # Ember
        
        for char in line:
            if char == ' ':
                result.append(char)
            else:
                if rng.random() < crack_prob:
                    # Ember crack effect
                    idx = rng.choice(crack_palette)
                    result.append(char, style=FirePalette.STYLES[idx])
                else:
                    result.append(char, style=base_style)
        
        return result
