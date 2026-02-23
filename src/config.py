"""Configuration system for peepBeefy user preferences.

This module provides data models and management for persistent user configuration,
including banner preferences, animation settings, and theme variants.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Literal
from pathlib import Path
import json
import logging
import pickle
import os

logger = logging.getLogger(__name__)

# Type definitions for configuration
LightDark = Literal["light", "dark"]
ColorAlignMode = Literal["horizontal", "vertical", "custom"]
AnsiMode = Literal["default", "ansi", "8bit", "rgb"]

# Current schema version
CURRENT_VERSION = 2


@dataclass
class BannerConfig:
    """Banner-related configuration.
    
    Attributes:
        mode: Banner selection mode - "random", "fixed", or "category"
        selected_banner: Specific banner ID in format "CATEGORY:NAME" (for fixed mode)
        selected_categories: List of categories to select from (for category/random mode)
        animation_enabled: Whether to enable fire animation on banners
        animation_duration: Duration of animation in seconds (0.5-10.0)
        animation_fps: Frames per second for animation (4-30)
        animation_intensity: Animation intensity level - "subtle", "normal", or "intense"
        color_preset: Optional preset name from color_presets.json for banner coloring
        color_alignment: Color alignment mode - "horizontal", "vertical", or "custom"
        custom_color_map: Optional custom color mapping for custom alignment mode
    """
    mode: str = "random"
    selected_banner: Optional[str] = None
    selected_categories: List[str] = field(default_factory=lambda: ["1ST_BEEFS"])
    animation_enabled: bool = True
    animation_duration: float = 3.0
    animation_fps: int = 8
    animation_intensity: str = "normal"
    color_preset: Optional[str] = None
    color_alignment: ColorAlignMode = "horizontal"
    custom_color_map: Optional[Dict[str, str]] = None


@dataclass
class DisplayConfig:
    """Display and color-related configuration.
    
    Attributes:
        color_mode: ANSI color mode - "default" (auto-detect), "rgb", "8bit", or "ansi"
        auto_detect_background: Whether to automatically detect terminal background color
        force_light_dark: Override background detection with "light" or "dark"
        lightness_adjustment: Lightness threshold for dark backgrounds (0.0-1.0)
        use_gradients: Whether to enable gradient effects in rendering
    """
    color_mode: AnsiMode = "default"
    auto_detect_background: bool = True
    force_light_dark: Optional[LightDark] = None
    lightness_adjustment: float = 0.65
    use_gradients: bool = False


@dataclass
class AppConfig:
    """Complete application configuration.
    
    Attributes:
        version: Schema version for migration support
        first_run_complete: Whether the first-run setup wizard has been completed
        theme_variant: Selected theme name (e.g., "CRT_Cyan", "Amber_Terminal")
        banner: Banner-related configuration
        display: Display and color-related configuration
        user_preferences: Dictionary for future expansion and custom preferences
    """
    version: int = CURRENT_VERSION
    first_run_complete: bool = False
    theme_variant: str = "CRT_Cyan"
    banner: BannerConfig = field(default_factory=BannerConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    user_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheEntry:
    """Generic cache entry with timestamp and data.
    
    Attributes:
        timestamp: Unix timestamp when the cache entry was created
        data: The cached data (can be any picklable type)
    """
    timestamp: float
    data: Any


@dataclass
class BannerCache:
    """Cache for banner database.
    
    Attributes:
        banners: Dictionary mapping category names to lists of banners
        last_modified: Unix timestamp of when the cache was last modified
    """
    banners: Dict[str, List[Any]]
    last_modified: float


@dataclass
class TerminalCache:
    """Cache for terminal detection results.
    
    Attributes:
        ansi_mode: Detected ANSI color mode
        background_color: Detected background color (RGB tuple or None)
        supports_rgb: Whether terminal supports RGB colors
        supports_256: Whether terminal supports 256 colors
        detected_at: Unix timestamp when detection was performed
        ttl: Time-to-live in seconds (default 1 hour)
    """
    ansi_mode: str
    background_color: Optional[tuple]
    supports_rgb: bool
    supports_256: bool
    detected_at: float
    ttl: float = 3600.0



class ConfigManager:
    """Manages application configuration persistence.
    
    Handles loading and saving configuration to disk with atomic writes,
    schema validation, and migration support.
    
    Performance optimizations:
    - In-memory cache for loaded configuration
    - Lazy cache directory creation
    - Optimized cache read/write operations
    
    Attributes:
        CONFIG_DIR: Path to the configuration directory (~/.peepbeefy)
        CONFIG_FILE: Path to the configuration file (~/.peepbeefy/config.json)
        CACHE_DIR: Path to the cache directory (~/.cache/hyfetch or $XDG_CACHE_HOME/hyfetch)
    """
    
    CONFIG_DIR = Path.home() / ".peepbeefy"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    
    # Cache directory follows XDG Base Directory specification
    _xdg_cache_home = os.environ.get('XDG_CACHE_HOME')
    if _xdg_cache_home:
        CACHE_DIR = Path(_xdg_cache_home) / "hyfetch"
    else:
        CACHE_DIR = Path.home() / ".cache" / "hyfetch"
    
    # Class-level cache directory existence flag to avoid repeated checks
    _cache_dir_checked: bool = False
    _cache_dir_exists: bool = False
    
    def __init__(self):
        """Initialize the ConfigManager."""
        self._config: Optional[AppConfig] = None
        # Defer cache directory creation until actually needed
    
    def load(self) -> AppConfig:
        """Load configuration from disk, creating defaults if missing.
        
        Validates the configuration schema and handles corrupted files by
        backing them up and creating fresh defaults.
        
        Returns:
            AppConfig object with loaded or default configuration
        """
        if not self.CONFIG_FILE.exists():
            logger.info("Config file not found, using defaults")
            return AppConfig()
        
        try:
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate that data is a dictionary
            if not isinstance(data, dict):
                logger.error(f"Invalid config format: expected dict, got {type(data).__name__}")
                self._backup_corrupted()
                return AppConfig()
            
            logger.info(f"Loaded configuration from {self.CONFIG_FILE}")
            
            # Validate version field type
            if 'version' in data and not isinstance(data['version'], int):
                logger.error(f"Invalid version type: expected int, got {type(data['version']).__name__}")
                self._backup_corrupted()
                return AppConfig()
            
            # Check if migration is needed
            old_version = data.get('version', 1)
            if old_version < CURRENT_VERSION:
                logger.info(f"Config version {old_version} is older than current {CURRENT_VERSION}, migrating...")
                config = self.migrate(old_version, data)
                # Save migrated config
                self.save(config)
                self._config = config
                return config
            
            # Validate and convert nested dictionaries to dataclass instances
            if 'banner' in data:
                if not isinstance(data['banner'], dict):
                    logger.error(f"Invalid banner type: expected dict, got {type(data['banner']).__name__}")
                    self._backup_corrupted()
                    return AppConfig()
                
                banner_data = data['banner']
                
                # Validate animation_duration range (0.5-10.0)
                if 'animation_duration' in banner_data:
                    duration = banner_data['animation_duration']
                    if not isinstance(duration, (int, float)):
                        logger.warning(f"Invalid animation_duration type {type(duration).__name__}, using default 3.0")
                        banner_data['animation_duration'] = 3.0
                    elif duration < 0.5 or duration > 10.0:
                        logger.warning(f"Invalid animation_duration {duration} (must be 0.5-10.0), using default 3.0")
                        banner_data['animation_duration'] = 3.0
                
                # Validate animation_fps range (4-30)
                if 'animation_fps' in banner_data:
                    fps = banner_data['animation_fps']
                    if not isinstance(fps, int):
                        logger.warning(f"Invalid animation_fps type {type(fps).__name__}, using default 8")
                        banner_data['animation_fps'] = 8
                    elif fps < 4 or fps > 30:
                        logger.warning(f"Invalid animation_fps {fps} (must be 4-30), using default 8")
                        banner_data['animation_fps'] = 8
                
                data['banner'] = BannerConfig(**banner_data)
            
            # Validate and convert display config
            if 'display' in data:
                if not isinstance(data['display'], dict):
                    logger.error(f"Invalid display type: expected dict, got {type(data['display']).__name__}")
                    self._backup_corrupted()
                    return AppConfig()
                
                display_data = data['display']
                
                # Validate lightness_adjustment range (0.0-1.0)
                if 'lightness_adjustment' in display_data:
                    adjustment = display_data['lightness_adjustment']
                    if not isinstance(adjustment, (int, float)):
                        logger.warning(f"Invalid lightness_adjustment type {type(adjustment).__name__}, using default 0.65")
                        display_data['lightness_adjustment'] = 0.65
                    elif adjustment < 0.0 or adjustment > 1.0:
                        logger.warning(f"Invalid lightness_adjustment {adjustment} (must be 0.0-1.0), using default 0.65")
                        display_data['lightness_adjustment'] = 0.65
                
                data['display'] = DisplayConfig(**display_data)
            
            # Validate theme_variant against available themes
            if 'theme_variant' in data:
                valid_themes = ["CRT_Cyan", "Amber_Terminal", "Green_Phosphor", "Synthwave"]
                if data['theme_variant'] not in valid_themes:
                    logger.warning(f"Invalid theme_variant {data['theme_variant']}, using default CRT_Cyan")
                    data['theme_variant'] = "CRT_Cyan"
            
            config = AppConfig(**data)
            self._config = config
            return config
            
        except FileNotFoundError:
            logger.info("Config file not found, using defaults")
            return AppConfig()
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted config file (invalid JSON): {e}")
            self._backup_corrupted()
            return AppConfig()
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid config schema: {e}")
            self._backup_corrupted()
            return AppConfig()
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")
            self._backup_corrupted()
            return AppConfig()
    
    def save(self, config: AppConfig) -> None:
        """Save configuration to disk with atomic write.
        
        Uses a temporary file and rename operation to ensure atomic writes,
        preventing corruption if the write is interrupted.
        
        Args:
            config: AppConfig object to save
        """
        # Create config directory if it doesn't exist
        try:
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create config directory: {e}")
            logger.warning("Configuration will not be persisted")
            return
        
        # Write to temporary file first
        temp_file = self.CONFIG_FILE.with_suffix('.tmp')
        try:
            # Convert dataclasses to dictionaries for JSON serialization
            data = asdict(config)
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename
            temp_file.replace(self.CONFIG_FILE)
            
            logger.info(f"Saved configuration to {self.CONFIG_FILE}")
            self._config = config
            
        except OSError as e:
            logger.error(f"Failed to save config: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Unexpected error saving config: {e}")
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
    
    def is_first_run(self) -> bool:
        """Check if this is the first time running peepBeefy.
        
        Returns:
            True if config file doesn't exist, False otherwise
        """
        return not self.CONFIG_FILE.exists()
    
    def mark_first_run_complete(self) -> None:
        """Mark the first-run setup wizard as complete.
        
        Sets the first_run_complete flag to True in the current configuration
        and saves it to disk. If no configuration is loaded, loads the default
        configuration first.
        """
        # Load current config if not already loaded
        if self._config is None:
            self._config = self.load()
        
        # Set first_run_complete flag
        self._config.first_run_complete = True
        
        # Save the updated configuration
        self.save(self._config)
        
        logger.info("Marked first-run setup as complete")
    
    def _backup_corrupted(self) -> None:
        """Backup corrupted config file before creating fresh config.
        
        Renames the corrupted file with a .corrupted suffix and timestamp.
        """
        if not self.CONFIG_FILE.exists():
            return
        
        try:
            import time
            timestamp = int(time.time())
            backup_path = self.CONFIG_FILE.with_suffix(f'.corrupted.{timestamp}')
            self.CONFIG_FILE.rename(backup_path)
            logger.info(f"Backed up corrupted config to {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup corrupted config: {e}")
            # Try to delete the corrupted file if we can't rename it
            try:
                self.CONFIG_FILE.unlink()
                logger.info("Deleted corrupted config file")
            except Exception:
                pass
    
    def migrate(self, old_version: int, data: Dict[str, Any]) -> AppConfig:
        """Migrate configuration from older schema versions.
        
        Applies migration functions sequentially from old_version to CURRENT_VERSION.
        Each migration function transforms the data dictionary in place.
        
        Args:
            old_version: The version number of the old schema
            data: The configuration data dictionary to migrate
        
        Returns:
            AppConfig object with migrated data
        """
        current = data.copy()
        
        # Apply migrations sequentially
        for version in range(old_version, CURRENT_VERSION):
            migration_func_name = f"_migrate_v{version}_to_v{version+1}"
            if hasattr(self, migration_func_name):
                migration_func = getattr(self, migration_func_name)
                current = migration_func(current)
                logger.info(f"Migrated config from v{version} to v{version+1}")
            else:
                logger.warning(f"No migration function found: {migration_func_name}")
        
        # Convert to AppConfig
        if 'banner' in current and isinstance(current['banner'], dict):
            banner_data = current['banner']
            
            # Validate animation_duration range (0.5-10.0)
            if 'animation_duration' in banner_data:
                duration = banner_data['animation_duration']
                if not isinstance(duration, (int, float)):
                    logger.warning(f"Invalid animation_duration type {type(duration).__name__}, using default 3.0")
                    banner_data['animation_duration'] = 3.0
                elif duration < 0.5 or duration > 10.0:
                    logger.warning(f"Invalid animation_duration {duration} (must be 0.5-10.0), using default 3.0")
                    banner_data['animation_duration'] = 3.0
            
            # Validate animation_fps range (4-30)
            if 'animation_fps' in banner_data:
                fps = banner_data['animation_fps']
                if not isinstance(fps, int):
                    logger.warning(f"Invalid animation_fps type {type(fps).__name__}, using default 8")
                    banner_data['animation_fps'] = 8
                elif fps < 4 or fps > 30:
                    logger.warning(f"Invalid animation_fps {fps} (must be 4-30), using default 8")
                    banner_data['animation_fps'] = 8
            
            current['banner'] = BannerConfig(**banner_data)
        
        if 'display' in current and isinstance(current['display'], dict):
            display_data = current['display']
            
            # Validate lightness_adjustment range (0.0-1.0)
            if 'lightness_adjustment' in display_data:
                adjustment = display_data['lightness_adjustment']
                if not isinstance(adjustment, (int, float)):
                    logger.warning(f"Invalid lightness_adjustment type {type(adjustment).__name__}, using default 0.65")
                    display_data['lightness_adjustment'] = 0.65
                elif adjustment < 0.0 or adjustment > 1.0:
                    logger.warning(f"Invalid lightness_adjustment {adjustment} (must be 0.0-1.0), using default 0.65")
                    display_data['lightness_adjustment'] = 0.65
            
            current['display'] = DisplayConfig(**display_data)
        
        # Validate theme_variant against available themes
        if 'theme_variant' in current:
            valid_themes = ["CRT_Cyan", "Amber_Terminal", "Green_Phosphor", "Synthwave"]
            if current['theme_variant'] not in valid_themes:
                logger.warning(f"Invalid theme_variant {current['theme_variant']}, using default CRT_Cyan")
                current['theme_variant'] = "CRT_Cyan"
        
        return AppConfig(**current)
    
    def _migrate_v1_to_v2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate configuration from v1 to v2.
        
        Adds new display configuration section and extends banner configuration
        with color preset and alignment fields.
        
        Args:
            data: Configuration data dictionary from v1 schema
        
        Returns:
            Updated configuration data dictionary for v2 schema
        """
        data["version"] = 2
        
        # Add display section with defaults if not present
        if "display" not in data:
            data["display"] = {
                "color_mode": "default",
                "auto_detect_background": True,
                "force_light_dark": None,
                "lightness_adjustment": 0.65,
                "use_gradients": False
            }
        
        # Extend banner configuration with new fields
        if "banner" in data:
            banner = data["banner"]
            if "color_preset" not in banner:
                banner["color_preset"] = None
            if "color_alignment" not in banner:
                banner["color_alignment"] = "horizontal"
            if "custom_color_map" not in banner:
                banner["custom_color_map"] = None
        
        return data
    
    def _ensure_cache_dir(self) -> bool:
        """Ensure cache directory exists, creating it if necessary.
        
        Handles cache directory creation failures gracefully by logging
        warnings but not raising exceptions.
        
        Uses class-level caching to avoid repeated filesystem checks.
        
        Returns:
            True if cache directory exists or was created successfully,
            False if creation failed
        """
        # Use class-level cache to avoid repeated checks
        if ConfigManager._cache_dir_checked:
            return ConfigManager._cache_dir_exists
        
        try:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache directory ready: {self.CACHE_DIR}")
            ConfigManager._cache_dir_checked = True
            ConfigManager._cache_dir_exists = True
            return True
        except OSError as e:
            logger.warning(f"Failed to create cache directory {self.CACHE_DIR}: {e}")
            logger.warning("Caching will be disabled")
            ConfigManager._cache_dir_checked = True
            ConfigManager._cache_dir_exists = False
            return False
        except Exception as e:
            logger.warning(f"Unexpected error creating cache directory: {e}")
            logger.warning("Caching will be disabled")
            ConfigManager._cache_dir_checked = True
            ConfigManager._cache_dir_exists = False
            return False
    
    def write_cache(self, cache_name: str, data: Any) -> bool:
        """Write data to cache file using pickle serialization.
        
        Args:
            cache_name: Name of the cache file (without extension)
            data: Data to cache (must be picklable)
        
        Returns:
            True if cache was written successfully, False otherwise
        """
        if not self._ensure_cache_dir():
            return False
        
        cache_file = self.CACHE_DIR / f"{cache_name}.pkl"
        temp_file = cache_file.with_suffix('.tmp')
        
        try:
            # Create cache entry with timestamp
            import time
            entry = CacheEntry(timestamp=time.time(), data=data)
            
            # Write to temporary file first
            with open(temp_file, 'wb') as f:
                pickle.dump(entry, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Atomic rename
            temp_file.replace(cache_file)
            
            logger.debug(f"Wrote cache: {cache_name}")
            return True
            
        except (OSError, pickle.PickleError) as e:
            logger.warning(f"Failed to write cache {cache_name}: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False
        except Exception as e:
            logger.warning(f"Unexpected error writing cache {cache_name}: {e}")
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False
    
    def read_cache(self, cache_name: str, max_age: Optional[float] = None) -> Optional[Any]:
        """Read data from cache file with freshness validation.
        
        Args:
            cache_name: Name of the cache file (without extension)
            max_age: Maximum age in seconds (None = no age check)
        
        Returns:
            Cached data if valid and fresh, None otherwise
        """
        cache_file = self.CACHE_DIR / f"{cache_name}.pkl"
        
        if not cache_file.exists():
            logger.debug(f"Cache miss: {cache_name} (file not found)")
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                entry = pickle.load(f)
            
            # Validate cache entry structure
            if not isinstance(entry, CacheEntry):
                logger.warning(f"Invalid cache entry format for {cache_name}")
                return None
            
            # Check cache freshness if max_age is specified
            if max_age is not None:
                import time
                age = time.time() - entry.timestamp
                if age > max_age:
                    logger.debug(f"Cache expired: {cache_name} (age: {age:.1f}s, max: {max_age}s)")
                    return None
            
            logger.debug(f"Cache hit: {cache_name}")
            return entry.data
            
        except (OSError, pickle.PickleError) as e:
            logger.warning(f"Failed to read cache {cache_name}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error reading cache {cache_name}: {e}")
            return None
    
    def invalidate_cache(self, cache_name: str) -> bool:
        """Invalidate (delete) a cache file.
        
        Args:
            cache_name: Name of the cache file (without extension)
        
        Returns:
            True if cache was deleted or didn't exist, False on error
        """
        cache_file = self.CACHE_DIR / f"{cache_name}.pkl"
        
        if not cache_file.exists():
            return True
        
        try:
            cache_file.unlink()
            logger.debug(f"Invalidated cache: {cache_name}")
            return True
        except OSError as e:
            logger.warning(f"Failed to invalidate cache {cache_name}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error invalidating cache {cache_name}: {e}")
            return False
    
    def validate_cache_freshness(self, cache_name: str, source_file: Path) -> bool:
        """Validate cache freshness using file modification timestamps.
        
        Compares the cache timestamp with the source file's modification time.
        If the source file is newer than the cache, the cache is stale.
        
        Args:
            cache_name: Name of the cache file (without extension)
            source_file: Path to the source file to compare against
        
        Returns:
            True if cache is fresh (newer than source), False if stale or invalid
        """
        cache_file = self.CACHE_DIR / f"{cache_name}.pkl"
        
        if not cache_file.exists():
            logger.debug(f"Cache validation failed: {cache_name} (not found)")
            return False
        
        if not source_file.exists():
            logger.debug(f"Cache validation failed: source file {source_file} not found")
            return False
        
        try:
            # Get cache timestamp
            cache_data = self.read_cache(cache_name)
            if cache_data is None:
                return False
            
            # Get source file modification time
            source_mtime = source_file.stat().st_mtime
            
            # Get cache file modification time
            cache_mtime = cache_file.stat().st_mtime
            
            # Cache is fresh if it's newer than the source file
            is_fresh = cache_mtime >= source_mtime
            
            if not is_fresh:
                logger.debug(f"Cache stale: {cache_name} (source modified after cache)")
            
            return is_fresh
            
        except OSError as e:
            logger.warning(f"Failed to validate cache freshness for {cache_name}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error validating cache freshness: {e}")
            return False
