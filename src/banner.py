"""Banner system for peepBeefy ASCII art display.

This module provides data models and functionality for managing ASCII art banners,
including parsing, selection, and rendering with theme support.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
from pathlib import Path
from enum import Enum, auto
import logging

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
    
    def load_banners(self, force_reload: bool = False) -> Dict[str, List[Banner]]:
        """Load all banners from ASCII database files.
        
        Parses the ASCII database file using a state machine approach to handle
        the format with delimiters, definitions, headers, and content sections.
        
        Args:
            force_reload: If True, bypass cache and re-parse from source
        
        Returns:
            Dictionary mapping category names to lists of banners
        """
        ascii_file = self._assets_dir / "ASCII-Full-Logo.txt"
        
        if not ascii_file.exists():
            logger.error(f"ASCII database not found: {ascii_file}")
            return {}
        
        try:
            with open(ascii_file, 'r', encoding='utf-8') as f:
                return self._parse_database(f)
        except Exception as e:
            logger.error(f"Failed to parse ASCII database: {e}")
            return {}
    
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
                if line.strip() == "---":
                    # Empty banner, skip it
                    state = ParserState.DELIMITER
                elif line.strip().startswith("-"):
                    # This is the separator line under the header, skip it
                    continue
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
