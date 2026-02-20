"""Banner system for peepBeefy ASCII art display.

This module provides data models and functionality for managing ASCII art banners,
including parsing, selection, and rendering with theme support.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
from pathlib import Path
from enum import Enum, auto
import logging
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich.style import Style

logger = logging.getLogger(__name__)


@dataclass
class BannerMetadata:
    """Metadata for a single ASCII art banner.
    
    Attributes:
        category: The category this banner belongs to (e.g., "1ST_BEEFS", "ALT")
        name: The unique name of the banner within its category
        author: Optional author attribution for the banner
        description: Optional description of the banner
        dimensions: Tuple of (width, height) for the banner, defaults to (0, 0)
        animation_compatible: Whether this banner works well with fire animation
    """
    category: str
    name: str
    author: Optional[str] = None
    description: Optional[str] = None
    dimensions: Tuple[int, int] = (0, 0)
    animation_compatible: bool = True


@dataclass
class Banner:
    """A parsed ASCII art banner with metadata.
    
    Attributes:
        metadata: The BannerMetadata containing category, name, and other info
        lines: List of strings representing each line of the ASCII art
    """
    metadata: BannerMetadata
    lines: List[str]
    
    @property
    def width(self) -> int:
        """Calculate the width of the banner (longest line).
        
        Returns:
            The width in characters of the longest line, or 0 if no lines exist
        """
        return max(len(line) for line in self.lines) if self.lines else 0
    
    @property
    def height(self) -> int:
        """Calculate the height of the banner (number of lines).
        
        Returns:
            The number of lines in the banner
        """
        return len(self.lines)


class ParserState(Enum):
    """States for the ASCII database parser state machine."""
    INITIAL = auto()
    DELIMITER = auto()
    DEFINITIONS = auto()
    HEADER = auto()
    CONTENT = auto()


class BannerDatabase:
    """Manages loading and caching of ASCII art banners.
    
    This class implements a state machine parser for the ASCII database format,
    which uses "---" delimiters to separate sections and "CATEGORY:NAME" headers
    to identify individual banners.
    
    Attributes:
        _assets_dir: Path to the directory containing ASCII database files
        _cache: Dictionary mapping category names to lists of banners
        _cache_timestamp: Timestamp of when the cache was last updated
    """
    
    def __init__(self, assets_dir: Path):
        """Initialize the BannerDatabase.
        
        Args:
            assets_dir: Path to the directory containing ASCII database files
        """
        self._assets_dir = assets_dir
        self._cache: Dict[str, List[Banner]] = {}
        self._cache_timestamp: Optional[float] = None
        self._cache_file = Path.home() / ".peepbeefy" / "banner_cache.pkl"
    
    def load_banners(self, force_reload: bool = False) -> Dict[str, List[Banner]]:
        """Load all banners from ASCII database files.
        
        Parses the ASCII database file using a state machine approach to handle
        the format with delimiters, definitions, headers, and content sections.
        Uses caching to avoid re-parsing on subsequent loads.
        
        Args:
            force_reload: If True, bypass cache and re-parse from source
        
        Returns:
            Dictionary mapping category names to lists of banners
        """
        # Check if cache is valid and use it
        if not force_reload and self._is_cache_valid():
            logger.info("Loading banners from cache")
            return self._load_from_cache()
        
        # Parse from source
        ascii_file = self._assets_dir / "ASCII-Full-Logo.txt"
        
        if not ascii_file.exists():
            logger.error(f"ASCII database not found: {ascii_file}")
            return {}
        
        try:
            with open(ascii_file, 'r', encoding='utf-8') as f:
                banners = self._parse_database(f)
            
            # Save to cache
            self._save_to_cache(banners)
            
            return banners
        except Exception as e:
            logger.error(f"Failed to parse ASCII database: {e}")
            return {}
    
    def _is_cache_valid(self) -> bool:
        """Check if the banner cache is valid.
        
        Cache is valid if:
        1. Cache file exists
        2. Source ASCII file exists
        3. Cache is newer than source file
        
        Returns:
            True if cache is valid, False otherwise
        """
        if not self._cache_file.exists():
            logger.debug("Cache file does not exist")
            return False
        
        ascii_file = self._assets_dir / "ASCII-Full-Logo.txt"
        if not ascii_file.exists():
            logger.debug("Source ASCII file does not exist")
            return False
        
        try:
            cache_mtime = self._cache_file.stat().st_mtime
            source_mtime = ascii_file.stat().st_mtime
            
            is_valid = cache_mtime > source_mtime
            logger.debug(f"Cache validation: cache_mtime={cache_mtime}, source_mtime={source_mtime}, valid={is_valid}")
            return is_valid
        except Exception as e:
            logger.warning(f"Failed to check cache validity: {e}")
            return False
    
    def _load_from_cache(self) -> Dict[str, List[Banner]]:
        """Load banners from cache file.
        
        Returns:
            Dictionary mapping category names to lists of banners
        """
        import pickle
        
        try:
            with open(self._cache_file, 'rb') as f:
                banners = pickle.load(f)
            logger.info(f"Loaded {sum(len(b) for b in banners.values())} banners from cache")
            return banners
        except Exception as e:
            logger.warning(f"Failed to load from cache: {e}, will re-parse")
            return {}
    
    def _save_to_cache(self, banners: Dict[str, List[Banner]]) -> None:
        """Save banners to cache file.
        
        Args:
            banners: Dictionary mapping category names to lists of banners
        """
        import pickle
        
        try:
            # Create cache directory if it doesn't exist
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file first, then rename (atomic operation)
            temp_file = self._cache_file.with_suffix('.tmp')
            with open(temp_file, 'wb') as f:
                pickle.dump(banners, f)
            
            # Atomic rename
            temp_file.replace(self._cache_file)
            
            logger.info(f"Saved {sum(len(b) for b in banners.values())} banners to cache")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
    
    def _parse_database(self, file) -> Dict[str, List[Banner]]:
        """Parse the ASCII database file using a state machine.
        
        State transitions:
        - INITIAL → DELIMITER (on "---")
        - DELIMITER → DEFINITIONS (on "DEFINITIONS")
        - DELIMITER → HEADER (on "CATEGORY:NAME")
        - DEFINITIONS → DELIMITER (on "---")
        - HEADER → CONTENT (on non-delimiter line)
        - CONTENT → DELIMITER (on "---")
        
        Args:
            file: File object to read from
        
        Returns:
            Dictionary mapping category names to lists of banners
        """
        state = ParserState.INITIAL
        banners: Dict[str, List[Banner]] = {}
        
        # Current banner being parsed
        current_category: Optional[str] = None
        current_name: Optional[str] = None
        current_lines: List[str] = []
        current_metadata: Dict[str, str] = {}
        
        for line_num, line in enumerate(file, start=1):
            # Remove newline but preserve other whitespace
            line = line.rstrip('\n\r')
            
            if state == ParserState.INITIAL:
                if line.strip() == "---":
                    state = ParserState.DELIMITER
                    
            elif state == ParserState.DELIMITER:
                if line.strip() == "DEFINITIONS":
                    state = ParserState.DEFINITIONS
                elif line.strip() == "---":
                    # Skip consecutive delimiters
                    continue
                elif ":" in line and not line.strip().startswith("#"):
                    # This is a banner header (CATEGORY:NAME)
                    try:
                        category, name = line.split(":", 1)
                        current_category = category.strip()
                        current_name = name.strip()
                        current_lines = []
                        current_metadata = {}
                        state = ParserState.HEADER
                    except ValueError:
                        logger.warning(f"Line {line_num}: Invalid header format: {line}")
                        
            elif state == ParserState.DEFINITIONS:
                if line.strip() == "---":
                    state = ParserState.DELIMITER
                # Skip definition lines (they start with #)
                
            elif state == ParserState.HEADER:
                if line.strip().startswith("-") and line.strip() != "---":
                    # This is the separator line under the header (but not a delimiter), skip it
                    continue
                elif line.strip() == "---":
                    # Empty banner, skip it
                    state = ParserState.DELIMITER
                elif line.strip().startswith("#") and ":" in line:
                    # This is a metadata comment (must have colon to be valid metadata)
                    self._parse_metadata_line(line, current_metadata)
                else:
                    # First content line (including lines starting with # that aren't metadata)
                    current_lines.append(line)
                    state = ParserState.CONTENT
                    
            elif state == ParserState.CONTENT:
                if line.strip() == "---":
                    # End of banner content, save the banner
                    if current_category and current_name and current_lines:
                        banner = self._create_banner(
                            current_category,
                            current_name,
                            current_lines,
                            current_metadata
                        )
                        if banner:
                            if current_category not in banners:
                                banners[current_category] = []
                            banners[current_category].append(banner)
                    
                    # Reset for next banner
                    current_category = None
                    current_name = None
                    current_lines = []
                    current_metadata = {}
                    state = ParserState.DELIMITER
                else:
                    # Add line to current banner content
                    current_lines.append(line)
        
        # Handle case where file doesn't end with delimiter
        if state == ParserState.CONTENT and current_category and current_name and current_lines:
            banner = self._create_banner(
                current_category,
                current_name,
                current_lines,
                current_metadata
            )
            if banner:
                if current_category not in banners:
                    banners[current_category] = []
                banners[current_category].append(banner)
        
        logger.info(f"Parsed {sum(len(b) for b in banners.values())} banners from {len(banners)} categories")
        return banners
    
    def _parse_metadata_line(self, line: str, metadata: Dict[str, str]) -> None:
        """Parse a metadata comment line and add to metadata dictionary.
        
        Metadata lines have the format: # key: value
        
        Args:
            line: The line to parse
            metadata: Dictionary to add parsed metadata to
        """
        # Remove leading # and whitespace
        line = line.lstrip('#').strip()
        
        # Split on first colon
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            # Store in metadata dictionary
            metadata[key] = value
            logger.debug(f"Parsed metadata: {key} = {value}")
    
    def _create_banner(
        self,
        category: str,
        name: str,
        lines: List[str],
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[Banner]:
        """Create a Banner object from parsed data.
        
        Args:
            category: The category name
            name: The banner name
            lines: List of ASCII art lines
            metadata: Optional dictionary of metadata key-value pairs
        
        Returns:
            Banner object, or None if invalid
        """
        if not lines:
            logger.warning(f"Empty banner: {category}:{name}")
            return None
        
        # Calculate dimensions
        width = max(len(line) for line in lines) if lines else 0
        height = len(lines)
        
        # Parse metadata fields
        metadata = metadata or {}
        author = metadata.get('author')
        description = metadata.get('description')
        
        # Use banner name as default description if not provided
        if not description:
            description = name
        
        # Parse animation_compatible (default to True)
        animation_compatible = True
        if 'animation_compatible' in metadata:
            anim_value = metadata['animation_compatible'].lower()
            animation_compatible = anim_value in ('true', 'yes', '1')
        
        # Parse flame_lines if present
        flame_lines = None
        if 'flame_lines' in metadata:
            try:
                flame_lines = [int(x.strip()) for x in metadata['flame_lines'].split(',')]
            except ValueError:
                logger.warning(f"Invalid flame_lines format for {category}:{name}")
        
        banner_metadata = BannerMetadata(
            category=category,
            name=name,
            author=author,
            description=description,
            dimensions=(width, height),
            animation_compatible=animation_compatible
        )
        
        return Banner(metadata=banner_metadata, lines=lines)
    
    def get_banner(
        self,
        category: Optional[str] = None,
        name: Optional[str] = None
    ) -> Banner:
        """Retrieve a specific banner or random selection.
        
        Args:
            category: Optional category to filter by
            name: Optional specific banner name to retrieve
        
        Returns:
            Banner object matching the criteria, or a random banner if not found,
            or the fallback banner if no banners are available
        """
        # Load banners if not already loaded
        if not self._cache:
            self._cache = self.load_banners()
        
        # If no banners loaded, return fallback
        if not self._cache:
            logger.warning("No banners available, using fallback")
            return self._get_fallback_banner()
        
        # If both category and name specified, try to find exact match
        if category and name:
            if category in self._cache:
                for banner in self._cache[category]:
                    if banner.metadata.name == name:
                        logger.info(f"Selected banner: {category}:{name}")
                        return banner
            logger.warning(f"Banner {category}:{name} not found, selecting random")
            return self.get_random_banner()
        
        # If only category specified, get random from that category
        if category:
            return self.get_random_banner(categories=[category])
        
        # Otherwise, get random from all categories
        return self.get_random_banner()
    
    def get_random_banner(
        self,
        categories: Optional[List[str]] = None
    ) -> Banner:
        """Select a random banner, optionally filtered by categories.
        
        Args:
            categories: Optional list of categories to select from
        
        Returns:
            Randomly selected banner, or fallback if no banners available
        """
        import random
        
        # Load banners if not already loaded
        if not self._cache:
            self._cache = self.load_banners()
        
        # If no banners loaded, return fallback
        if not self._cache:
            logger.warning("No banners available, using fallback")
            return self._get_fallback_banner()
        
        # Filter by categories if specified
        if categories:
            available_banners = []
            for cat in categories:
                if cat in self._cache:
                    available_banners.extend(self._cache[cat])
            
            if not available_banners:
                logger.warning(f"No banners found in categories {categories}, using all categories")
                available_banners = [
                    banner
                    for banners in self._cache.values()
                    for banner in banners
                ]
        else:
            # Get all banners from all categories
            available_banners = [
                banner
                for banners in self._cache.values()
                for banner in banners
            ]
        
        # If no banners available, return fallback
        if not available_banners:
            logger.warning("No banners available, using fallback")
            return self._get_fallback_banner()
        
        # Select random banner
        selected = random.choice(available_banners)
        logger.info(f"Selected random banner: {selected.metadata.category}:{selected.metadata.name}")
        return selected
    
    def list_categories(self) -> List[str]:
        """Return all available banner categories.
        
        Returns:
            List of category names
        """
        # Load banners if not already loaded
        if not self._cache:
            self._cache = self.load_banners()
        
        return list(self._cache.keys())
    
    def _get_fallback_banner(self) -> Banner:
        """Return hardcoded default banner for error recovery.
        
        Returns:
            A simple fallback banner that always works
        """
        fallback_lines = [
            "                          _______              ___       ",
            " .-----.-----.-----.-----|   _   .-----.-----.'  _.--.--.  ",
            " |  _  |  -__|  -__|  _  |.  1   |  -__|  -__|   _|  |  |  ",
            " |   __|_____|_____|   __|.  _   |_____|_____|__| |___  |  ",
            " |__|              |__|  |:  1    \\               |_____|  ",
            "                         |::.. .  /                        ",
            "                         `-------'                         "
        ]
        
        metadata = BannerMetadata(
            category="FALLBACK",
            name="DEFAULT",
            description="Default fallback banner",
            dimensions=(59, 7),
            animation_compatible=True
        )
        
        return Banner(metadata=metadata, lines=fallback_lines)



class BannerRenderer:
    """Renders banners with theme styling.
    
    Provides methods for rendering ASCII art banners with theme colors,
    terminal size validation, and fallback handling.
    
    Attributes:
        _theme: Theme instance for color styling
    """
    
    def __init__(self, theme):
        """Initialize the BannerRenderer with a theme.
        
        Args:
            theme: Theme instance from themes.py for color styling
        """
        self._theme = theme
    
    def render_static(self, banner: Banner, console: Console) -> Panel:
        """Render a static banner with theme colors.
        
        Creates a Rich Panel containing the banner ASCII art with theme
        colors applied. Uses DOUBLE box borders from the theme.
        
        Args:
            banner: Banner object to render
            console: Rich Console instance for rendering
        
        Returns:
            Rich Panel object with styled banner content
        """
        # Handle empty banners gracefully
        if not banner.lines:
            logger.warning("Attempted to render empty banner")
            content = Text("peepBeefy", style=Style(color=self._theme.palette.highlight, bold=True))
        else:
            # Apply theme colors to banner text
            content = Text()
            for i, line in enumerate(banner.lines):
                if i > 0:
                    content.append("\n")
                # Apply primary color to banner content
                content.append(line, style=Style(color=self._theme.palette.primary))
        
        # Create panel with DOUBLE box borders and theme colors
        panel = Panel(
            content,
            box=self._theme.get_box_style(),
            border_style=self._theme.get_border_style(),
            padding=(0, 1),
        )
        
        return panel
    
    def validate_terminal_size(self, banner: Banner, console: Console) -> bool:
        """Check if banner fits in current terminal dimensions.
        
        Validates that the banner width and height (plus panel padding/borders)
        will fit within the current terminal size.
        
        Args:
            banner: Banner object to validate
            console: Rich Console instance for terminal size
        
        Returns:
            True if banner fits, False otherwise
        """
        term_width, term_height = console.size
        
        # Account for panel borders and padding (4 chars width, 2 lines height)
        required_width = banner.width + 4
        required_height = banner.height + 2
        
        fits = required_width <= term_width and required_height <= term_height
        
        if not fits:
            logger.debug(
                f"Banner size check: {required_width}x{required_height} "
                f"vs terminal {term_width}x{term_height} = {fits}"
            )
        
        return fits
    
    def render_animated(
        self,
        banner: Banner,
        console: Console,
        duration: float = 3.0,
        fps: int = 8,
        intensity: str = "normal"
    ) -> None:
        """Render an animated banner using fire effect.
        
        Lazy-loads the FireAnimator only when animation is enabled.
        Falls back to static rendering if animation fails.
        
        Args:
            banner: Banner object to render
            console: Rich Console instance for rendering
            duration: Animation duration in seconds
            fps: Frames per second for animation
            intensity: Animation intensity level ("subtle", "normal", "intense")
        """
        try:
            # Lazy-load FireAnimator only when animation is enabled
            from animation import FireAnimator
            
            # Create animator with configured intensity
            animator = FireAnimator(intensity=intensity)
            
            # Run the animation
            animator.animate_banner(banner, console, duration=duration, fps=fps)
            
            logger.info(f"Animated banner {banner.metadata.category}:{banner.metadata.name} "
                       f"for {duration}s at {fps}fps with {intensity} intensity")
            
        except Exception as e:
            # Fallback to static rendering on any error
            logger.error(f"Animation failed: {e}, falling back to static rendering")
            panel = self.render_static(banner, console)
            console.print(panel)
    
    def get_fallback_banner(self) -> Banner:
        """Return hardcoded default banner for error recovery.
        
        Provides a simple fallback banner that always works when banner
        selection or loading fails.
        
        Returns:
            A minimal fallback Banner object
        """
        fallback_lines = [
            "                          _______              ___       ",
            " .-----.-----.-----.-----|   _   .-----.-----.'  _.--.--.  ",
            " |  _  |  -__|  -__|  _  |.  1   |  -__|  -__|   _|  |  |  ",
            " |   __|_____|_____|   __|.  _   |_____|_____|__| |___  |  ",
            " |__|              |__|  |:  1    \\               |_____|  ",
            "                         |::.. .  /                        ",
            "                         `-------'                         "
        ]
        
        metadata = BannerMetadata(
            category="FALLBACK",
            name="DEFAULT",
            description="Default fallback banner",
            dimensions=(59, 7),
            animation_compatible=True
        )
        
        return Banner(metadata=metadata, lines=fallback_lines)
    def render_animated(
        self,
        banner: Banner,
        console: Console,
        duration: float = 3.0,
        fps: int = 8,
        intensity: str = "normal"
    ) -> None:
        """Render an animated banner using fire effect.

        Lazy-loads the FireAnimator only when animation is enabled.
        Falls back to static rendering if animation fails.

        Args:
            banner: Banner object to render
            console: Rich Console instance for rendering
            duration: Animation duration in seconds
            fps: Frames per second for animation
            intensity: Animation intensity level ("subtle", "normal", "intense")
        """
        try:
            # Lazy-load FireAnimator only when animation is enabled
            from animation import FireAnimator

            # Create animator with configured intensity
            animator = FireAnimator(intensity=intensity)

            # Run the animation
            animator.animate_banner(banner, console, duration=duration, fps=fps)

            logger.info(f"Animated banner {banner.metadata.category}:{banner.metadata.name} "
                       f"for {duration}s at {fps}fps with {intensity} intensity")

        except Exception as e:
            # Fallback to static rendering on any error
            logger.error(f"Animation failed: {e}, falling back to static rendering")
            panel = self.render_static(banner, console)
            console.print(panel)

    
    def select_banner_with_adaptation(
        self,
        banner_db: BannerDatabase,
        console: Console,
        config
    ) -> Banner:
        """Select banner with terminal size adaptation and fallback chain.
        
        Implements the fallback chain: selected → category → random → fallback
        Filters banners by terminal size to ensure they fit.
        
        Args:
            banner_db: BannerDatabase instance to select from
            console: Rich Console instance for terminal size
            config: Configuration object with banner preferences
        
        Returns:
            Banner object that fits in the terminal
        """
        import random
        
        # Get terminal dimensions
        term_width, term_height = console.size
        
        # Step 1: Try to get the selected banner (if mode is "fixed")
        if config.banner.mode == "fixed" and config.banner.selected_banner:
            try:
                category, name = config.banner.selected_banner.split(":", 1)
                banner = banner_db.get_banner(category=category, name=name)
                
                if self.validate_terminal_size(banner, console):
                    logger.info(f"Selected fixed banner: {config.banner.selected_banner}")
                    return banner
                else:
                    logger.warning(
                        f"Fixed banner {config.banner.selected_banner} doesn't fit "
                        f"({banner.width}x{banner.height} vs {term_width}x{term_height}), "
                        "trying alternatives"
                    )
            except Exception as e:
                logger.error(f"Failed to load fixed banner: {e}")
        
        # Step 2: Try to get random banner from selected categories
        if config.banner.mode in ("category", "random"):
            categories = config.banner.selected_categories if config.banner.mode == "category" else None
            
            # Get all banners from the specified categories (or all categories)
            all_banners = []
            banner_dict = banner_db.load_banners()
            
            if categories:
                for cat in categories:
                    if cat in banner_dict:
                        all_banners.extend(banner_dict[cat])
            else:
                for banners in banner_dict.values():
                    all_banners.extend(banners)
            
            # Filter by terminal size
            fitting_banners = [
                b for b in all_banners
                if self.validate_terminal_size(b, console)
            ]
            
            if fitting_banners:
                selected = random.choice(fitting_banners)
                logger.info(
                    f"Selected random banner: {selected.metadata.category}:{selected.metadata.name} "
                    f"({selected.width}x{selected.height})"
                )
                return selected
            else:
                logger.warning(
                    f"No banners fit in terminal {term_width}x{term_height}, "
                    "using fallback"
                )
        
        # Step 3: Fallback to hardcoded banner
        fallback = self.get_fallback_banner()
        
        # Check if even the fallback fits
        if not self.validate_terminal_size(fallback, console):
            logger.warning(
                f"Terminal too small ({term_width}x{term_height}) even for fallback banner, "
                "will render anyway"
            )
        
        logger.info("Using fallback banner")
        return fallback
