"""
Property-based tests for configuration validation and backward compatibility.

Tests:
- Property 24: Configuration Type Validation
- Property 42: Backward Compatible Config Loading

Validates Requirements 7.7, 14.5
"""

import json
import pytest
import tempfile
from pathlib import Path
from typing import Any, Dict
from hypothesis import given, strategies as st, assume, settings
from src.config import (
    AppConfig, BannerConfig, DisplayConfig, ConfigManager,
    AnsiMode, LightDark, ColorAlignMode, CURRENT_VERSION
)


# --- Hypothesis Strategies ---

# Strategy for valid AnsiMode values
ansi_mode_strategy = st.sampled_from(["default", "ansi", "8bit", "rgb"])

# Strategy for valid LightDark values
light_dark_strategy = st.sampled_from(["light", "dark"])

# Strategy for valid ColorAlignMode values
color_align_mode_strategy = st.sampled_from(["horizontal", "vertical", "custom"])

# Strategy for valid theme variants
theme_variant_strategy = st.sampled_from([
    "CRT_Cyan", "Amber_Terminal", "Green_Phosphor", "Synthwave"
])

# Strategy for valid banner modes
banner_mode_strategy = st.sampled_from(["random", "fixed", "category"])

# Strategy for valid animation intensity
animation_intensity_strategy = st.sampled_from(["subtle", "normal", "intense"])

# Strategy for valid animation duration (0.5-10.0)
animation_duration_strategy = st.floats(
    min_value=0.5, max_value=10.0,
    allow_nan=False, allow_infinity=False
)

# Strategy for valid animation FPS (4-30)
animation_fps_strategy = st.integers(min_value=4, max_value=30)

# Strategy for valid lightness adjustment (0.0-1.0)
lightness_adjustment_strategy = st.floats(
    min_value=0.0, max_value=1.0,
    allow_nan=False, allow_infinity=False
)

# Strategy for valid BannerConfig
banner_config_strategy = st.builds(
    BannerConfig,
    mode=banner_mode_strategy,
    selected_banner=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    selected_categories=st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=5),
    animation_enabled=st.booleans(),
    animation_duration=animation_duration_strategy,
    animation_fps=animation_fps_strategy,
    animation_intensity=animation_intensity_strategy,
    color_preset=st.one_of(st.none(), st.text(min_size=1, max_size=30)),
    color_alignment=color_align_mode_strategy,
    custom_color_map=st.one_of(
        st.none(),
        st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.text(min_size=1, max_size=20),
            max_size=5
        )
    )
)

# Strategy for valid DisplayConfig
display_config_strategy = st.builds(
    DisplayConfig,
    color_mode=ansi_mode_strategy,
    auto_detect_background=st.booleans(),
    force_light_dark=st.one_of(st.none(), light_dark_strategy),
    lightness_adjustment=lightness_adjustment_strategy,
    use_gradients=st.booleans()
)

# Strategy for valid AppConfig
app_config_strategy = st.builds(
    AppConfig,
    version=st.just(CURRENT_VERSION),
    first_run_complete=st.booleans(),
    theme_variant=theme_variant_strategy,
    banner=banner_config_strategy,
    display=display_config_strategy,
    user_preferences=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(
            st.text(max_size=50),
            st.integers(min_value=-100, max_value=100),
            st.booleans()
        ),
        max_size=5
    )
)


class TestConfigurationTypeValidation:
    """Property 24: Configuration Type Validation
    
    For any configuration data with invalid types (e.g., string where int expected),
    the Config_Manager load operation should either coerce to valid types or raise
    an appropriate error.
    
    Validates: Requirement 7.7
    """
    
    @given(st.text(min_size=1, max_size=50))
    def test_invalid_animation_duration_type_uses_default(self, invalid_value: str):
        """Invalid animation_duration type should use default value."""
        config_data = {
            "version": CURRENT_VERSION,
            "banner": {
                "animation_duration": invalid_value  # String instead of float
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default value (3.0) instead of invalid string
            assert config.banner.animation_duration == 3.0
    
    @given(st.floats(min_value=-100.0, max_value=0.4, allow_nan=False, allow_infinity=False))
    def test_animation_duration_below_minimum_uses_default(self, invalid_duration: float):
        """animation_duration below 0.5 should use default value."""
        config_data = {
            "version": CURRENT_VERSION,
            "banner": {
                "animation_duration": invalid_duration
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default value (3.0)
            assert config.banner.animation_duration == 3.0
    
    @given(st.floats(min_value=10.1, max_value=100.0, allow_nan=False, allow_infinity=False))
    def test_animation_duration_above_maximum_uses_default(self, invalid_duration: float):
        """animation_duration above 10.0 should use default value."""
        config_data = {
            "version": CURRENT_VERSION,
            "banner": {
                "animation_duration": invalid_duration
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default value (3.0)
            assert config.banner.animation_duration == 3.0
    
    @given(st.text(min_size=1, max_size=50))
    def test_invalid_animation_fps_type_uses_default(self, invalid_value: str):
        """Invalid animation_fps type should use default value."""
        config_data = {
            "version": CURRENT_VERSION,
            "banner": {
                "animation_fps": invalid_value  # String instead of int
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default value (8)
            assert config.banner.animation_fps == 8
    
    @given(st.integers(min_value=-100, max_value=3))
    def test_animation_fps_below_minimum_uses_default(self, invalid_fps: int):
        """animation_fps below 4 should use default value."""
        config_data = {
            "version": CURRENT_VERSION,
            "banner": {
                "animation_fps": invalid_fps
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default value (8)
            assert config.banner.animation_fps == 8
    
    @given(st.integers(min_value=31, max_value=100))
    def test_animation_fps_above_maximum_uses_default(self, invalid_fps: int):
        """animation_fps above 30 should use default value."""
        config_data = {
            "version": CURRENT_VERSION,
            "banner": {
                "animation_fps": invalid_fps
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default value (8)
            assert config.banner.animation_fps == 8
    
    @given(st.text(min_size=1, max_size=50))
    def test_invalid_lightness_adjustment_type_uses_default(self, invalid_value: str):
        """Invalid lightness_adjustment type should use default value."""
        config_data = {
            "version": CURRENT_VERSION,
            "display": {
                "lightness_adjustment": invalid_value  # String instead of float
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default value (0.65)
            assert config.display.lightness_adjustment == 0.65
    
    @given(st.floats(min_value=-10.0, max_value=-0.01, allow_nan=False, allow_infinity=False))
    def test_lightness_adjustment_below_minimum_uses_default(self, invalid_adjustment: float):
        """lightness_adjustment below 0.0 should use default value."""
        config_data = {
            "version": CURRENT_VERSION,
            "display": {
                "lightness_adjustment": invalid_adjustment
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default value (0.65)
            assert config.display.lightness_adjustment == 0.65
    
    @given(st.floats(min_value=1.01, max_value=10.0, allow_nan=False, allow_infinity=False))
    def test_lightness_adjustment_above_maximum_uses_default(self, invalid_adjustment: float):
        """lightness_adjustment above 1.0 should use default value."""
        config_data = {
            "version": CURRENT_VERSION,
            "display": {
                "lightness_adjustment": invalid_adjustment
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default value (0.65)
            assert config.display.lightness_adjustment == 0.65
    
    @given(st.text(min_size=1, max_size=50).filter(
        lambda x: x not in ["CRT_Cyan", "Amber_Terminal", "Green_Phosphor", "Synthwave"]
    ))
    def test_invalid_theme_variant_uses_default(self, invalid_theme: str):
        """Invalid theme_variant should use default value."""
        config_data = {
            "version": CURRENT_VERSION,
            "theme_variant": invalid_theme
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default value (CRT_Cyan)
            assert config.theme_variant == "CRT_Cyan"
    
    @given(st.text(min_size=1, max_size=50))
    def test_invalid_version_type_uses_default_config(self, invalid_version: str):
        """Invalid version type should trigger default config."""
        config_data = {
            "version": invalid_version,  # String instead of int
            "theme_variant": "Amber_Terminal"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default config
            assert config.version == CURRENT_VERSION
            assert config.theme_variant == "CRT_Cyan"  # Default, not Amber_Terminal
    
    @given(st.lists(st.integers(), min_size=1, max_size=5))
    def test_non_dict_config_uses_default(self, invalid_config: list):
        """Non-dict config should trigger default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(invalid_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default config
            assert config.version == CURRENT_VERSION
            assert config.theme_variant == "CRT_Cyan"


class TestBackwardCompatibleConfigLoading:
    """Property 42: Backward Compatible Config Loading
    
    For any configuration file from an older schema version, the Config_Manager
    should load it successfully, applying migrations and using defaults for new fields.
    
    Validates: Requirement 14.5
    """
    
    def test_v1_config_loads_with_defaults(self):
        """Version 1 config should load and migrate to version 2."""
        v1_config = {
            "version": 1,
            "first_run_complete": True,
            "theme_variant": "Amber_Terminal",
            "banner": {
                "mode": "fixed",
                "selected_banner": "1ST_BEEFS:classic",
                "selected_categories": ["1ST_BEEFS"],
                "animation_enabled": True,
                "animation_duration": 5.0,
                "animation_fps": 12,
                "animation_intensity": "intense"
            },
            "user_preferences": {
                "custom_key": "custom_value"
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v1_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should migrate to version 2
            assert config.version == 2
            
            # Existing fields should be preserved
            assert config.first_run_complete is True
            assert config.theme_variant == "Amber_Terminal"
            assert config.banner.mode == "fixed"
            assert config.banner.selected_banner == "1ST_BEEFS:classic"
            assert config.banner.animation_duration == 5.0
            assert config.banner.animation_fps == 12
            assert config.banner.animation_intensity == "intense"
            assert config.user_preferences["custom_key"] == "custom_value"
            
            # New banner fields should have defaults
            assert config.banner.color_preset is None
            assert config.banner.color_alignment == "horizontal"
            assert config.banner.custom_color_map is None
            
            # New display section should have defaults
            assert config.display.color_mode == "default"
            assert config.display.auto_detect_background is True
            assert config.display.force_light_dark is None
            assert config.display.lightness_adjustment == 0.65
            assert config.display.use_gradients is False
    
    @given(
        st.booleans(),
        theme_variant_strategy,
        banner_mode_strategy,
        st.text(min_size=1, max_size=50),
        animation_duration_strategy,
        animation_fps_strategy,
        animation_intensity_strategy
    )
    def test_v1_config_preserves_all_original_fields(
        self,
        first_run: bool,
        theme: str,
        banner_mode: str,
        selected_banner: str,
        duration: float,
        fps: int,
        intensity: str
    ):
        """V1 config migration should preserve all original field values."""
        v1_config = {
            "version": 1,
            "first_run_complete": first_run,
            "theme_variant": theme,
            "banner": {
                "mode": banner_mode,
                "selected_banner": selected_banner,
                "selected_categories": ["1ST_BEEFS", "CUSTOM"],
                "animation_enabled": True,
                "animation_duration": duration,
                "animation_fps": fps,
                "animation_intensity": intensity
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v1_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # All original fields should be preserved
            assert config.first_run_complete == first_run
            assert config.theme_variant == theme
            assert config.banner.mode == banner_mode
            assert config.banner.selected_banner == selected_banner
            assert config.banner.animation_duration == duration
            assert config.banner.animation_fps == fps
            assert config.banner.animation_intensity == intensity
    
    def test_v1_config_without_banner_section(self):
        """V1 config without banner section should use defaults."""
        v1_config = {
            "version": 1,
            "first_run_complete": False,
            "theme_variant": "CRT_Cyan"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v1_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should have default banner config
            assert config.banner.mode == "random"
            assert config.banner.animation_enabled is True
            assert config.banner.animation_duration == 3.0
            assert config.banner.animation_fps == 8
    
    def test_config_without_version_field_assumes_v1(self):
        """Config without version field should be treated as v1."""
        old_config = {
            # No version field
            "first_run_complete": True,
            "theme_variant": "Green_Phosphor",
            "banner": {
                "mode": "category",
                "selected_categories": ["1ST_BEEFS"]
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(old_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should migrate to current version
            assert config.version == CURRENT_VERSION
            
            # Original fields should be preserved
            assert config.first_run_complete is True
            assert config.theme_variant == "Green_Phosphor"
            assert config.banner.mode == "category"
            
            # New fields should have defaults
            assert config.display.color_mode == "default"
    
    @given(app_config_strategy)
    def test_current_version_config_loads_without_migration(self, config: AppConfig):
        """Current version config should load without migration."""
        # Convert to dict for saving
        from dataclasses import asdict
        config_data = asdict(config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            loaded_config = manager.load()
            
            # Should load without migration
            assert loaded_config.version == CURRENT_VERSION
            assert loaded_config.theme_variant == config.theme_variant
            assert loaded_config.first_run_complete == config.first_run_complete
    
    def test_corrupted_json_uses_default_config(self):
        """Corrupted JSON should trigger default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                f.write("{invalid json content")
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default config
            assert config.version == CURRENT_VERSION
            assert config.theme_variant == "CRT_Cyan"
            assert config.first_run_complete is False
    
    def test_missing_config_file_uses_default(self):
        """Missing config file should use default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "nonexistent.json"
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default config
            assert config.version == CURRENT_VERSION
            assert config.theme_variant == "CRT_Cyan"
            assert config.first_run_complete is False
    
    @given(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.text(max_size=50), st.integers(), st.booleans()),
            min_size=1,
            max_size=5
        )
    )
    def test_user_preferences_preserved_during_migration(self, preferences: Dict[str, Any]):
        """User preferences should be preserved during migration."""
        v1_config = {
            "version": 1,
            "theme_variant": "CRT_Cyan",
            "user_preferences": preferences
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(v1_config, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # User preferences should be preserved
            assert config.user_preferences == preferences


class TestConfigurationEdgeCases:
    """Test edge cases for configuration loading."""
    
    def test_empty_config_file_uses_default(self):
        """Empty config file should use default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_file.write_text("")
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should use default config
            assert config.version == CURRENT_VERSION
    
    def test_config_with_extra_fields_loads_successfully(self):
        """Config with extra unknown fields should load successfully."""
        config_data = {
            "version": CURRENT_VERSION,
            "theme_variant": "CRT_Cyan",
            "unknown_field": "unknown_value",
            "banner": {
                "mode": "random",
                "extra_banner_field": "extra_value"
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            config = manager.load()
            
            # Should load successfully, ignoring extra fields
            assert config.version == CURRENT_VERSION
            assert config.theme_variant == "CRT_Cyan"
    
    def test_config_save_and_load_round_trip(self):
        """Saving and loading config should preserve all values."""
        original_config = AppConfig(
            version=CURRENT_VERSION,
            first_run_complete=True,
            theme_variant="Synthwave",
            banner=BannerConfig(
                mode="fixed",
                selected_banner="TEST:banner",
                animation_duration=7.5,
                animation_fps=20,
                color_preset="rainbow",
                color_alignment="vertical"
            ),
            display=DisplayConfig(
                color_mode="rgb",
                auto_detect_background=False,
                force_light_dark="dark",
                lightness_adjustment=0.8,
                use_gradients=True
            )
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            
            manager = ConfigManager()
            manager.CONFIG_FILE = config_file
            
            # Save
            manager.save(original_config)
            
            # Load
            loaded_config = manager.load()
            
            # All values should be preserved
            assert loaded_config.version == original_config.version
            assert loaded_config.first_run_complete == original_config.first_run_complete
            assert loaded_config.theme_variant == original_config.theme_variant
            assert loaded_config.banner.mode == original_config.banner.mode
            assert loaded_config.banner.selected_banner == original_config.banner.selected_banner
            assert loaded_config.banner.animation_duration == original_config.banner.animation_duration
            assert loaded_config.banner.animation_fps == original_config.banner.animation_fps
            assert loaded_config.banner.color_preset == original_config.banner.color_preset
            assert loaded_config.banner.color_alignment == original_config.banner.color_alignment
            assert loaded_config.display.color_mode == original_config.display.color_mode
            assert loaded_config.display.auto_detect_background == original_config.display.auto_detect_background
            assert loaded_config.display.force_light_dark == original_config.display.force_light_dark
            assert loaded_config.display.lightness_adjustment == original_config.display.lightness_adjustment
            assert loaded_config.display.use_gradients == original_config.display.use_gradients
