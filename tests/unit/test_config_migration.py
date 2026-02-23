"""Unit tests for configuration migration.

Tests specific migration scenarios:
- v1 config loads with defaults for new fields
- v2 config loads correctly
- Corrupted config handling

Requirements: 7.6, 14.5
"""

import json
import tempfile
from pathlib import Path
import pytest

from src.config import ConfigManager, AppConfig, BannerConfig, DisplayConfig, CURRENT_VERSION


class TestV1ConfigMigration:
    """Test v1 configuration migration to v2."""
    
    def test_v1_config_loads_with_display_defaults(self):
        """v1 config without display section should load with default display settings."""
        v1_config = {
            "version": 1,
            "first_run_complete": True,
            "theme_variant": "CRT_Cyan",
            "banner": {
                "mode": "random",
                "selected_banner": None,
                "selected_categories": ["1ST_BEEFS"],
                "animation_enabled": True,
                "animation_duration": 3.0,
                "animation_fps": 8,
                "animation_intensity": "normal"
            },
            "user_preferences": {}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v1_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should migrate to v2
            assert config.version == 2
            
            # Original fields preserved
            assert config.first_run_complete is True
            assert config.theme_variant == "CRT_Cyan"
            assert config.banner.mode == "random"
            assert config.banner.animation_enabled is True
            
            # Display section added with defaults
            assert config.display is not None
            assert config.display.color_mode == "default"
            assert config.display.auto_detect_background is True
            assert config.display.force_light_dark is None
            assert config.display.lightness_adjustment == 0.65
            assert config.display.use_gradients is False
    
    def test_v1_config_loads_with_banner_color_defaults(self):
        """v1 config without color fields should load with default color settings."""
        v1_config = {
            "version": 1,
            "theme_variant": "Amber_Terminal",
            "banner": {
                "mode": "specific",
                "selected_banner": "peep_beefy_logo"
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v1_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Banner color fields added with defaults
            assert config.banner.color_preset is None
            assert config.banner.color_alignment == "horizontal"
            assert config.banner.custom_color_map is None
    
    def test_v1_config_with_minimal_fields(self):
        """v1 config with only version field should load with all defaults."""
        v1_config = {
            "version": 1
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v1_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should migrate to v2 with all defaults
            assert config.version == 2
            assert config.first_run_complete is False
            assert config.theme_variant == "CRT_Cyan"
            assert config.banner is not None
            assert config.display is not None
    
    def test_v1_config_preserves_user_preferences(self):
        """v1 config user preferences should be preserved during migration."""
        v1_config = {
            "version": 1,
            "theme_variant": "Green_Phosphor",
            "user_preferences": {
                "custom_key": "custom_value",
                "nested": {
                    "data": [1, 2, 3]
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v1_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # User preferences preserved exactly
            assert config.user_preferences == v1_config["user_preferences"]
            assert config.user_preferences["custom_key"] == "custom_value"
            assert config.user_preferences["nested"]["data"] == [1, 2, 3]


class TestV2ConfigLoading:
    """Test v2 configuration loading."""
    
    def test_v2_config_loads_correctly(self):
        """v2 config with all fields should load without migration."""
        v2_config = {
            "version": 2,
            "first_run_complete": True,
            "theme_variant": "Synthwave",
            "banner": {
                "mode": "random",
                "selected_banner": None,
                "selected_categories": ["1ST_BEEFS", "RETRO"],
                "animation_enabled": True,
                "animation_duration": 5.0,
                "animation_fps": 12,
                "animation_intensity": "high",
                "color_preset": "rainbow",
                "color_alignment": "vertical",
                "custom_color_map": None
            },
            "display": {
                "color_mode": "rgb",
                "auto_detect_background": False,
                "force_light_dark": "dark",
                "lightness_adjustment": 0.7,
                "use_gradients": True
            },
            "user_preferences": {
                "last_used": "2024-01-01"
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v2_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # All fields loaded correctly
            assert config.version == 2
            assert config.first_run_complete is True
            assert config.theme_variant == "Synthwave"
            
            # Banner fields
            assert config.banner.mode == "random"
            assert config.banner.selected_categories == ["1ST_BEEFS", "RETRO"]
            assert config.banner.animation_duration == 5.0
            assert config.banner.animation_fps == 12
            assert config.banner.animation_intensity == "high"
            assert config.banner.color_preset == "rainbow"
            assert config.banner.color_alignment == "vertical"
            assert config.banner.custom_color_map is None
            
            # Display fields
            assert config.display.color_mode == "rgb"
            assert config.display.auto_detect_background is False
            assert config.display.force_light_dark == "dark"
            assert config.display.lightness_adjustment == 0.7
            assert config.display.use_gradients is True
            
            # User preferences
            assert config.user_preferences["last_used"] == "2024-01-01"
    
    def test_v2_config_with_custom_color_map(self):
        """v2 config with custom color map should load correctly."""
        v2_config = {
            "version": 2,
            "theme_variant": "CRT_Cyan",
            "banner": {
                "mode": "specific",
                "selected_banner": "custom_logo",
                "color_alignment": "custom",
                "custom_color_map": {
                    "0": "#FF0000",
                    "1": "#00FF00",
                    "2": "#0000FF"
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v2_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Custom color map loaded correctly
            assert config.banner.color_alignment == "custom"
            assert config.banner.custom_color_map is not None
            assert config.banner.custom_color_map["0"] == "#FF0000"
            assert config.banner.custom_color_map["1"] == "#00FF00"
            assert config.banner.custom_color_map["2"] == "#0000FF"
    
    def test_v2_config_with_partial_display_section(self):
        """v2 config with partial display section should use defaults for missing fields."""
        v2_config = {
            "version": 2,
            "theme_variant": "CRT_Cyan",
            "display": {
                "color_mode": "8bit"
                # Other fields missing
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v2_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Specified field loaded
            assert config.display.color_mode == "8bit"
            
            # Missing fields use defaults
            assert config.display.auto_detect_background is True
            assert config.display.force_light_dark is None
            assert config.display.lightness_adjustment == 0.65
            assert config.display.use_gradients is False


class TestCorruptedConfigHandling:
    """Test handling of corrupted configuration files."""
    
    def test_invalid_json_uses_defaults(self):
        """Corrupted JSON should use default config and backup the file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_file.write_text("{ invalid json }")
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default config
            assert config.version == CURRENT_VERSION
            assert config.theme_variant == "CRT_Cyan"
            assert config.first_run_complete is False
            
            # Backup file should be created (original file is renamed)
            backup_files = list(Path(tmpdir).glob("config.corrupted.*"))
            assert len(backup_files) == 1
            # Original config.json should no longer exist (it was renamed)
            assert not config_file.exists()
    
    def test_empty_json_object_uses_defaults(self):
        """Empty JSON object should use default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_file.write_text("{}")
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default config
            assert config.version == CURRENT_VERSION
            assert config.theme_variant == "CRT_Cyan"
    
    def test_invalid_type_for_banner_uses_defaults(self):
        """Invalid type for banner section should trigger error handling and use defaults."""
        config_data = {
            "version": 2,
            "theme_variant": "CRT_Cyan",
            "banner": "invalid_string_instead_of_dict"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default config due to invalid banner type
            assert config.version == CURRENT_VERSION
            assert config.theme_variant == "CRT_Cyan"
            assert config.banner is not None
            assert config.banner.mode == "random"
            
            # Backup file should be created
            backup_files = list(Path(tmpdir).glob("config.corrupted.*"))
            assert len(backup_files) == 1
    
    def test_invalid_animation_duration_uses_default(self):
        """Invalid animation_duration should be replaced with default."""
        config_data = {
            "version": 2,
            "theme_variant": "CRT_Cyan",
            "banner": {
                "animation_duration": 999.0  # Out of range (0.5-10.0)
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default animation_duration
            assert config.banner.animation_duration == 3.0
    
    def test_invalid_animation_fps_uses_default(self):
        """Invalid animation_fps should be replaced with default."""
        config_data = {
            "version": 2,
            "theme_variant": "CRT_Cyan",
            "banner": {
                "animation_fps": 100  # Out of range (4-30)
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default animation_fps
            assert config.banner.animation_fps == 8
    
    def test_invalid_lightness_adjustment_uses_default(self):
        """Invalid lightness_adjustment should be replaced with default."""
        config_data = {
            "version": 2,
            "theme_variant": "CRT_Cyan",
            "display": {
                "lightness_adjustment": 5.0  # Out of range (0.0-1.0)
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default lightness_adjustment
            assert config.display.lightness_adjustment == 0.65
    
    def test_invalid_theme_variant_uses_default(self):
        """Invalid theme_variant should be replaced with default."""
        config_data = {
            "version": 2,
            "theme_variant": "NonExistentTheme"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default theme_variant
            assert config.theme_variant == "CRT_Cyan"
    
    def test_missing_config_file_creates_default(self):
        """Missing config file should create default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            # Don't create the file
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default config
            assert config.version == CURRENT_VERSION
            assert config.theme_variant == "CRT_Cyan"
            assert config.first_run_complete is False
    
    def test_non_dict_json_uses_defaults(self):
        """JSON that's not a dictionary should use default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_file.write_text("[1, 2, 3]")  # Array instead of object
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default config
            assert config.version == CURRENT_VERSION
            assert config.theme_variant == "CRT_Cyan"


class TestMigrationEdgeCases:
    """Test edge cases in migration logic."""
    
    def test_config_with_extra_fields_preserved(self):
        """Config with extra unknown fields should preserve them in user_preferences."""
        v1_config = {
            "version": 1,
            "theme_variant": "CRT_Cyan",
            "unknown_field": "should_be_ignored"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v1_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should load successfully (extra fields ignored)
            assert config.version == 2
            assert config.theme_variant == "CRT_Cyan"
    
    def test_v1_config_with_existing_display_section(self):
        """v1 config with display section should preserve it during migration."""
        v1_config = {
            "version": 1,
            "theme_variant": "CRT_Cyan",
            "display": {
                "color_mode": "rgb",
                "use_gradients": True
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v1_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Existing display fields preserved
            assert config.display.color_mode == "rgb"
            assert config.display.use_gradients is True
            
            # Missing fields use defaults
            assert config.display.auto_detect_background is True
    
    def test_migration_preserves_all_banner_fields(self):
        """Migration should preserve all existing banner fields."""
        v1_config = {
            "version": 1,
            "theme_variant": "Amber_Terminal",
            "banner": {
                "mode": "specific",
                "selected_banner": "custom_banner",
                "selected_categories": ["CUSTOM"],
                "animation_enabled": False,
                "animation_duration": 7.5,
                "animation_fps": 15,
                "animation_intensity": "low"
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v1_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # All original banner fields preserved
            assert config.banner.mode == "specific"
            assert config.banner.selected_banner == "custom_banner"
            assert config.banner.selected_categories == ["CUSTOM"]
            assert config.banner.animation_enabled is False
            assert config.banner.animation_duration == 7.5
            assert config.banner.animation_fps == 15
            assert config.banner.animation_intensity == "low"
            
            # New fields added with defaults
            assert config.banner.color_preset is None
            assert config.banner.color_alignment == "horizontal"
            assert config.banner.custom_color_map is None
