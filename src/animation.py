"""
Fire Animation Engine for peepBeefy

Implements DOOM PSX-inspired fire effect for ASCII art banners.
Extracted and generalized from install.py.

Design:
- 12-step fire color palette (ember → flame → tips)
- Per-character coloring with flicker effect
- Adaptive flame zone detection
- Configurable intensity levels
- Terminal color capability detection with fallback
- Metadata-driven flame zone override
- Input validation and error handling
"""

import logging
import random
import time
from typing import List, Tuple, Optional

from rich.console import Console
from rich.live import Live
from rich.style import Style
from rich.text import Text

# Try to import TerminalCapabilities for RGB detection
# If not available, default to RGB mode
try:
    from themes import TerminalCapabilities
    _HAS_TERMINAL_CAPABILITIES = True
except ImportError:
    _HAS_TERMINAL_CAPABILITIES = False

logger = logging.getLogger(__name__)


class FirePalette:
    """12-step DOOM PSX fire color palette.
    
    Index 0 = barely visible ember
    Index 11 = near-white peak
    
    The palette progresses from deep embers through flame core to bright tips.
    Supports both RGB and 8-bit color fallback for terminal compatibility.
    """
    
    # RGB (24-bit) color palette
    COLORS = (
        "#4F0F07", "#6D1504", "#8B1A00", "#AB1E00",   # embers (0-3)
        "#CC2200", "#E53400", "#FF4500", "#FF6800",   # flame core (4-7)
        "#FF8C00", "#FFB400", "#FFD700", "#FFE55C",   # tips (8-11)
    )
    
    STYLES = tuple(Style(color=c) for c in COLORS)
    
    # 8-bit ANSI color fallback palette (for terminals without RGB support)
    # Maps to closest ANSI 256-color codes
    COLORS_8BIT = (
        "color(52)",   # dark red (ember)
        "color(88)",   # red
        "color(124)",  # bright red
        "color(160)",  # orange-red
        "color(196)",  # bright red
        "color(202)",  # orange
        "color(208)",  # bright orange
        "color(214)",  # yellow-orange
        "color(220)",  # yellow
        "color(226)",  # bright yellow
        "color(227)",  # pale yellow
        "color(229)",  # near-white yellow
    )
    
    STYLES_8BIT = tuple(Style(color=c) for c in COLORS_8BIT)


# Pre-weighted flicker offsets: 0(40%) +1(18%) -1(17%) +2(13%) -2(12%)
# Slight warm bias (31% warm vs 29% cool) — flames push energy upward.
FLICKER_OFFSETS = (0,)*40 + (1,)*18 + (-1,)*17 + (2,)*13 + (-2,)*12


class FireAnimator:
    """Applies DOOM PSX fire effect to ASCII art banners.
    
    The animator adapts to different ASCII art dimensions and applies
    per-character coloring with configurable intensity.
    
    Features:
    - RGB color support with 8-bit fallback
    - Metadata-driven flame zone override
    - Input validation and error handling
    - Configurable intensity levels
    """
    
    def __init__(self, intensity: str = "normal", use_rgb: Optional[bool] = None):
        """Initialize the fire animator.
        
        Args:
            intensity: Animation intensity level - "subtle", "normal", or "intense"
            use_rgb: Whether to use RGB colors. If None, auto-detect terminal capability.
        """
        self._intensity = intensity
        self._intensity_multiplier = self._get_intensity_multiplier()
        
        # Detect RGB support if not explicitly specified
        if use_rgb is None:
            if _HAS_TERMINAL_CAPABILITIES:
                self._use_rgb = TerminalCapabilities.supports_rgb()
            else:
                # Default to RGB if TerminalCapabilities not available
                self._use_rgb = True
        else:
            self._use_rgb = use_rgb
        
        # Select appropriate palette
        self._palette = FirePalette.STYLES if self._use_rgb else FirePalette.STYLES_8BIT
        
        logger.debug(f"FireAnimator initialized: intensity={intensity}, use_rgb={self._use_rgb}")
    
    def _get_intensity_multiplier(self) -> float:
        """Get the intensity multiplier for flicker and crack probabilities."""
        return {
            "subtle": 0.5,
            "normal": 1.0,
            "intense": 1.5,
        }.get(self._intensity, 1.0)
    
    def animate_banner(
        self,
        banner,
        console: Console,
        duration: float = 3.0,
        fps: int = 8,
        precompute_frames: bool = False
    ) -> None:
        """Run fire animation on banner for specified duration.
        
        Args:
            banner: Banner object or list of strings representing ASCII art lines
            console: Rich Console instance for rendering
            duration: Animation duration in seconds (clamped to 0.5-60.0)
            fps: Frames per second (clamped to 1-60)
            precompute_frames: If True, pre-compute all frames before animating
        """
        try:
            # Validate and clamp inputs
            duration = max(0.5, min(60.0, duration))
            fps = max(1, min(60, fps))
            
            # Handle both Banner objects and list of strings
            if hasattr(banner, 'lines'):
                lines = banner.lines
            else:
                lines = banner
            
            if not lines:
                logger.warning("Empty banner provided to animate_banner")
                return
            
            # Detect flame and text zones with metadata override support
            # Detect flame and text zones
            flame_lines, text_lines = self._detect_zones(banner)
            
            # Pre-compute all frames for smooth playback
            # Ensure at least 1 frame
            num_frames = max(1, int(duration * fps))
            frames = []
            rng = random.Random()
            
            logger.debug(f"Pre-computing {num_frames} animation frames")
            
            for frame_idx in range(num_frames):
                try:
                    frame = self._build_frame(banner, flame_lines, text_lines, rng)
                    frames.append(frame)
                except Exception as e:
                    logger.error(f"Error building frame {frame_idx}: {e}")
                    # Use a simple fallback frame
                    fallback_frame = Text("\n".join(banner.lines))
                    frames.append(fallback_frame)
            
            # Animate with Live context
            interval = 1.0 / fps
            start = time.monotonic()
            
            with Live(frames[0], console=console, refresh_per_second=fps) as live:
                frame_idx = 0
                while time.monotonic() - start < duration:
                    try:
                        live.update(frames[frame_idx % len(frames)])
                        frame_idx += 1
                        time.sleep(interval)
                    except KeyboardInterrupt:
                        logger.info("Animation interrupted by user")
                        break
                    except Exception as e:
                        logger.error(f"Error during animation playback: {e}")
                        break
            
            logger.debug(f"Animation completed: {frame_idx} frames displayed")
        except ValueError as e:
            logger.error(f"Invalid input to animate_banner: {e}")
            # Fallback to static display
            try:
                static_frame = self._build_static_frame(banner)
                console.print(static_frame)
            except Exception as fallback_error:
                logger.error(f"Fallback static frame failed: {fallback_error}")
    def _validate_inputs(self, banner, console: Console) -> bool:
        """Validate inputs for animation.

        Args:
            banner: Banner object or list of strings
            console: Rich Console instance

        Returns:
            True if inputs are valid, False otherwise
        """
        try:
            if not console:
                logger.error("Console is None")
                return False

            # Handle both Banner objects and list of strings
            if hasattr(banner, 'lines'):
                lines = banner.lines
            else:
                lines = banner

            if not isinstance(lines, (list, tuple)):
                logger.error("Banner lines must be a list or tuple")
                return False

            if not lines:
                logger.warning("Empty banner provided")
                return False

            # Validate each line is a string
            for i, line in enumerate(lines):
                if not isinstance(line, str):
                    logger.error(f"Line {i} is not a string: {type(line)}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Error validating inputs: {e}")
            return False
            
            if precompute_frames:
                # Pre-compute all frames for smoother playback
                self._animate_precomputed(lines, flame_lines, text_lines, console, duration, fps)
            else:
                # Build frames on-the-fly (lower memory usage)
                self._animate_realtime(lines, flame_lines, text_lines, console, duration, fps)
                
        except Exception as e:
            logger.error(f"Error during animation: {e}", exc_info=True)
            # Fallback: display static frame
            try:
                static_frame = self._build_static_frame(banner)
                console.print(static_frame)
            except Exception as fallback_error:
                logger.error(f"Fallback static frame failed: {fallback_error}")
    
    def _animate_realtime(
        self,
        lines: List[str],
        flame_lines: List[int],
        text_lines: List[int],
        console: Console,
        duration: float,
        fps: int
    ) -> None:
        """Animate by building frames in real-time."""
        rng = random.Random()
        frame = self._build_frame(lines, flame_lines, text_lines, rng)
        
        interval = 1.0 / fps
        start = time.monotonic()
        
        with Live(frame, console=console, refresh_per_second=fps, transient=False) as live:
            while time.monotonic() - start < duration:
                time.sleep(interval)
                frame = self._build_frame(lines, flame_lines, text_lines, rng)
                live.update(frame)
    
    def _animate_precomputed(
        self,
        lines: List[str],
        flame_lines: List[int],
        text_lines: List[int],
        console: Console,
        duration: float,
        fps: int
    ) -> None:
        """Animate using pre-computed frames for smoother playback."""
        import itertools
        
        # Pre-compute frames
        num_frames = max(8, int(fps * 1.0))  # At least 8 frames, or 1 second worth
        rng = random.Random()
        frames = []
        
        for _ in range(num_frames):
            frame = self._build_frame(lines, flame_lines, text_lines, rng)
            frames.append(frame)
        
        # Animate with pre-computed frames
        interval = 1.0 / fps
        start = time.monotonic()
        frame_cycle = itertools.cycle(frames)
        
        with Live(next(frame_cycle), console=console, refresh_per_second=fps, transient=False) as live:
            while time.monotonic() - start < duration:
                time.sleep(interval)
                live.update(next(frame_cycle))
    
    def _build_static_frame(self, banner) -> Text:
        """Build a static (non-animated) frame for error fallback."""
        if hasattr(banner, 'lines'):
            lines = banner.lines
        else:
            lines = banner
        
        result = Text()
        for i, line in enumerate(lines):
            if i > 0:
                result.append("\n")
            result.append(line, style=Style(color="#00d7d7"))  # Default cyan
        return result
    
    def _build_frame(
        self,
        banner,
        flame_lines: List[int],
        text_lines: List[int],
        rng: random.Random
    ) -> Text:
        """Build a single animation frame with per-character coloring.
        
        Args:
            banner: Banner object or list of ASCII art lines
            flame_lines: Indices of lines in the flame zone
            text_lines: Indices of lines in the text zone
            rng: Random number generator for flicker
            
        Returns:
            Rich Text object with colored characters
        """
        # Handle both Banner objects and list of strings
        if hasattr(banner, 'lines'):
            lines = banner.lines
        else:
            lines = banner
        
        result = Text()
        
        for i, line in enumerate(lines):
            if i > 0:
                result.append("\n")
            
            if i in flame_lines:
                result.append(self._apply_flame_coloring(line, i, len(flame_lines), rng))
            elif i in text_lines:
                text_line_idx = text_lines.index(i)
                result.append(self._apply_text_coloring(line, text_line_idx, rng))
            else:
                # Shouldn't happen, but handle gracefully
                result.append(line)
        
        return result

    
    def _detect_zones(self, banner) -> Tuple[List[int], List[int]]:
        """Detect which lines are flame vs text zones.
        
        Uses a 60/40 split heuristic: top 60% is flame zone, bottom 40% is text zone.
        Can be overridden with explicit flame_lines metadata from Banner object.
        
        Args:
            banner: Banner object (with optional metadata.flame_lines) or list of ASCII art lines
            
        Returns:
            Tuple of (flame_line_indices, text_line_indices)
        """
        # Handle both Banner objects and list of strings
        if hasattr(banner, 'lines'):
            lines = banner.lines
        else:
            lines = banner
        
        total_lines = len(lines)
        
        # Check for metadata override (defensive attribute checking)
        if hasattr(banner, 'metadata') and hasattr(banner.metadata, 'flame_lines'):
            flame_lines_override = banner.metadata.flame_lines
            if flame_lines_override is not None and isinstance(flame_lines_override, (list, tuple)):
                # Validate indices are within bounds
                flame_lines = [i for i in flame_lines_override if 0 <= i < total_lines]
                text_lines = [i for i in range(total_lines) if i not in flame_lines]
                logger.debug(f"Using metadata flame_lines override: {flame_lines}")
                return flame_lines, text_lines
        
        # Heuristic: 60/40 split
        flame_cutoff = int(total_lines * 0.6)
        flame_lines = list(range(flame_cutoff))
        text_lines = list(range(flame_cutoff, total_lines))
        
        logger.debug(f"Using heuristic flame zone: {flame_cutoff}/{total_lines} lines")
        return flame_lines, text_lines

    
    def _apply_flame_coloring(
        self,
        line: str,
        line_idx: int,
        num_flame_lines: int,
        rng: random.Random
    ) -> Text:
        """Apply fire palette coloring to a flame zone line.
        
        Calculates base palette index based on line position (hotter at top),
        applies flicker effect with random palette offsets, and adjusts
        flicker probability based on line position.
        
        Args:
            line: The ASCII art line to color
            line_idx: Index of this line within the flame zone (0 = top)
            num_flame_lines: Total number of lines in the flame zone
            rng: Random number generator for flicker
            
        Returns:
            Rich Text object with fire-colored characters
        """
        result = Text()
        
        # Determine base palette index based on line position
        # Top lines = hotter (higher index), bottom lines = cooler (lower index)
        normalized_pos = line_idx / max(1, num_flame_lines - 1) if num_flame_lines > 1 else 0
        base_idx = int(2 + normalized_pos * 8)  # Range: 2-10
        
        # Flicker probability decreases toward bottom
        flicker_prob = (1.0 - (normalized_pos * 0.5)) * self._intensity_multiplier  # Range: 1.0 to 0.5
        
        # Clamp palette indices
        lo = max(0, base_idx - 2)
        hi = min(11, base_idx + 2)
        
        for char in line:
            if char == ' ':
                result.append(char)
            else:
                if rng.random() < flicker_prob:
                    # Apply flicker offset
                    offset = rng.choice(FLICKER_OFFSETS)
                    idx = max(lo, min(hi, base_idx + offset))
                else:
                    idx = base_idx
                
                result.append(char, style=self._palette[idx])
        
        return result

    
    def _apply_text_coloring(
        self,
        line: str,
        text_line_idx: int,
        rng: random.Random
    ) -> Text:
        """Apply text coloring with ember crack effect to a text zone line.
        
        Uses white → gray → dim gradient based on line position, and applies
        ember crack effect with random hot color spots. Crack probability
        decreases with line position.
        
        Args:
            line: The ASCII art line to color
            text_line_idx: Index of this line within the text zone (0 = top of text zone)
            rng: Random number generator for ember cracks
            
        Returns:
            Rich Text object with text-colored characters and ember cracks
        """
        result = Text()
        
        # Determine base text style and crack effect based on line position
        if text_line_idx == 0:
            # First text line: white-hot with frequent yellow cracks
            base_style = Style(color="#FFFFFF", bold=True)
            crack_prob = 0.20 * self._intensity_multiplier
            crack_palette = (10, 11)  # Hot yellow
        elif text_line_idx == 1:
            # Second text line: cooling glow with orange cracks
            base_style = Style(color="#CCCCCC")
            crack_prob = 0.12 * self._intensity_multiplier
            crack_palette = (8, 9)  # Orange
        else:
            # Remaining text lines: dim base with ember cracks
            base_style = Style(color="#999999", dim=True)
            crack_prob = 0.06 * self._intensity_multiplier
            crack_palette = (2, 4)  # Ember
        
        for char in line:
            if char == ' ':
                result.append(char)
            else:
                if rng.random() < crack_prob:
                    # Ember crack effect
                    idx = rng.choice(crack_palette)
                    result.append(char, style=self._palette[idx])
                else:
                    result.append(char, style=base_style)
        
        return result
