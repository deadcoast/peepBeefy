"""Configuration system for peepBeefy user preferences.

This module provides data models and management for persistent user configuration,
including banner preferences, animation settings, and theme variants.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# Current schema version
CURRENT_VERSION = 1


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
    """
    mode: str = "random"
    selected_banner: Optional[str] = None
    selected_categories: List[str] = field(default_factory=lambda: ["1ST_BEEFS"])
    animation_enabled: bool = True
    animation_duration: float = 3.0
    animation_fps: int = 8
    animation_intensity: str = "normal"


@dataclass
class AppConfig:
    """Complete application configuration.
    
    Attributes:
        version: Schema version for migration support
        first_run_complete: Whether the first-run setup wizard has been completed
        theme_variant: Selected theme name (e.g., "CRT_Cyan", "Amber_Terminal")
        banner: Banner-related configuration
        user_preferences: Dictionary for future expansion and custom preferences
    """
    version: int = 1
    first_run_complete: bool = False
    theme_variant: str = "CRT_Cyan"
    banner: BannerConfig = field(default_factory=BannerConfig)
    user_preferences: Dict[str, Any] = field(default_factory=dict)



class ConfigManager:
    """Manages application configuration persistence.
    
    Handles loading and saving configuration to disk with atomic writes,
    schema validation, and migration support.
    
    Attributes:
        CONFIG_DIR: Path to the configuration directory (~/.peepbeefy)
        CONFIG_FILE: Path to the configuration file (~/.peepbeefy/config.json)
    """
    
    CONFIG_DIR = Path.home() / ".peepbeefy"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    
    def __init__(self):
        """Initialize the ConfigManager."""
        self._config: Optional[AppConfig] = None
    
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
            if 'banner' in data and isinstance(data['banner'], dict):
                banner_data = data['banner']
                
                # Validate animation_duration range (0.5-10.0)
                if 'animation_duration' in banner_data:
                    duration = banner_data['animation_duration']
                    if not isinstance(duration, (int, float)) or not (0.5 <= duration <= 10.0):
                        logger.warning(f"Invalid animation_duration {duration}, using default 3.0")
                        banner_data['animation_duration'] = 3.0
                
                # Validate animation_fps range (4-30)
                if 'animation_fps' in banner_data:
                    fps = banner_data['animation_fps']
                    if not isinstance(fps, int) or not (4 <= fps <= 30):
                        logger.warning(f"Invalid animation_fps {fps}, using default 8")
                        banner_data['animation_fps'] = 8
                
                data['banner'] = BannerConfig(**banner_data)
            
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
            current['banner'] = BannerConfig(**current['banner'])
        
        return AppConfig(**current)
    
    # Migration function template for future schema changes
    # def _migrate_v1_to_v2(self, data: Dict[str, Any]) -> Dict[str, Any]:
    #     """Migrate configuration from v1 to v2.
    #     
    #     Example migration that adds new fields or transforms existing ones.
    #     """
    #     data["version"] = 2
    #     
    #     # Add new fields with defaults
    #     if "new_field" not in data:
    #         data["new_field"] = "default_value"
    #     
    #     # Rename fields
    #     if "old_field_name" in data:
    #         data["new_field_name"] = data.pop("old_field_name")
    #     
    #     # Transform values
    #     if "banner" in data and "mode" in data["banner"]:
    #         # Convert old mode values to new format
    #         mode_map = {"rand": "random", "fix": "fixed"}
    #         old_mode = data["banner"]["mode"]
    #         data["banner"]["mode"] = mode_map.get(old_mode, old_mode)
    #     
    #     return data
