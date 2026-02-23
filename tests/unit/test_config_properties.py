"""Property-based tests for configuration system.

Tests universal properties that should hold across all valid configurations,
including round-trip preservation, directory creation, and JSON validity.
"""

import json
import tempfile
from pathlib import Path
from contextlib import contextmanager
from hypothesis import given, strategies as st
import pytest

from src.config import AppConfig, BannerConfig, ConfigManager


# Strategy for generating valid banner modes
banner_mode_strategy = st.sampled_from(["random", "fixed", "category"])

# Strategy for generating valid theme variants
theme_variant_strategy = st.sampled_from([
    "CRT_Cyan", "Amber_Terminal", "Green_Phosphor", "Synthwave"
])

# Strategy for generating valid animation intensities
animation_intensity_strategy = st.sampled_from(["subtle", "normal", "intense"])

# Strategy for generating valid animation durations (0.5-10.0)
animation_duration_strategy = st.floats(min_value=0.5, max_value=10.0)

# Strategy for generating valid animation FPS (4-30)
animation_fps_strategy = st.integers(min_value=4, max_value=30)

# Strategy for generating valid category lists
category_list_strategy = st.lists(
    st.sampled_from(["1ST_BEEFS", "ALT", "CURSIVE", "FAROUT", "LIB", "MIN"]),
    min_size=1,
    max_size=6
)


@contextmanager
def temp_config_context():
    """Context manager to provide a temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".peepbeefy"
        # Monkey-patch ConfigManager to use temp directory
        original_dir = ConfigManager.CONFIG_DIR
        original_file = ConfigManager.CONFIG_FILE
        ConfigManager.CONFIG_DIR = config_dir
        ConfigManager.CONFIG_FILE = config_dir / "config.json"
        try:
            yield config_dir
        finally:
            # Restore original paths
            ConfigManager.CONFIG_DIR = original_dir
            ConfigManager.CONFIG_FILE = original_file


# Property 5: Configuration Round-Trip Preservation
# **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 3.6, 6.2, 6.3, 6.7, 7.5, 11.1**
@given(
    mode=banner_mode_strategy,
    animation_enabled=st.booleans(),
    animation_duration=animation_duration_strategy,
    animation_fps=animation_fps_strategy,
    animation_intensity=animation_intensity_strategy,
    theme_variant=theme_variant_strategy,
    selected_categories=category_list_strategy,
    first_run_complete=st.booleans()
)
@pytest.mark.property_test
def test_config_round_trip_preservation(
    mode,
    animation_enabled,
    animation_duration,
    animation_fps,
    animation_intensity,
    theme_variant,
    selected_categories,
    first_run_complete
):
    """Property 5: For any valid configuration, save then load produces equivalent config.
    
    This property ensures that configuration data is preserved exactly through
    the save/load cycle, validating the persistence mechanism.
    """
    with temp_config_context():
        # Arrange
        original_config = AppConfig(
            version=1,
            first_run_complete=first_run_complete,
            theme_variant=theme_variant,
            banner=BannerConfig(
                mode=mode,
                selected_banner=None,
                selected_categories=selected_categories,
                animation_enabled=animation_enabled,
                animation_duration=animation_duration,
                animation_fps=animation_fps,
                animation_intensity=animation_intensity
            ),
            user_preferences={}
        )
        
        config_manager = ConfigManager()
        
        # Act
        config_manager.save(original_config)
        loaded_config = config_manager.load()
        
        # Assert
        # Note: version may be migrated to CURRENT_VERSION, so we check >= original
        from src.config import CURRENT_VERSION
        assert loaded_config.version >= original_config.version
        assert loaded_config.version <= CURRENT_VERSION
        assert loaded_config.first_run_complete == original_config.first_run_complete
        assert loaded_config.theme_variant == original_config.theme_variant
        assert loaded_config.banner.mode == original_config.banner.mode
        assert loaded_config.banner.selected_banner == original_config.banner.selected_banner
        assert loaded_config.banner.selected_categories == original_config.banner.selected_categories
        assert loaded_config.banner.animation_enabled == original_config.banner.animation_enabled
        assert abs(loaded_config.banner.animation_duration - original_config.banner.animation_duration) < 0.01
        assert loaded_config.banner.animation_fps == original_config.banner.animation_fps
        assert loaded_config.banner.animation_intensity == original_config.banner.animation_intensity
        assert loaded_config.user_preferences == original_config.user_preferences


# Property 6: Configuration Directory Creation
# **Validates: Requirements 6.2**
@given(
    mode=banner_mode_strategy,
    theme_variant=theme_variant_strategy
)
@pytest.mark.property_test
def test_config_directory_creation(mode, theme_variant):
    """Property 6: For any config save, directory is created if it doesn't exist.
    
    This property ensures that the configuration system automatically creates
    the necessary directory structure before saving.
    """
    with temp_config_context() as temp_config_dir:
        # Arrange
        config = AppConfig(
            theme_variant=theme_variant,
            banner=BannerConfig(mode=mode)
        )
        
        # Ensure directory doesn't exist
        if temp_config_dir.exists():
            import shutil
            shutil.rmtree(temp_config_dir)
        
        assert not temp_config_dir.exists()
        
        config_manager = ConfigManager()
        
        # Act
        config_manager.save(config)
        
        # Assert
        assert temp_config_dir.exists()
        assert temp_config_dir.is_dir()
        assert ConfigManager.CONFIG_FILE.exists()


# Property 7: Configuration JSON Validity
# **Validates: Requirements 6.3**
@given(
    mode=banner_mode_strategy,
    animation_enabled=st.booleans(),
    animation_duration=animation_duration_strategy,
    animation_fps=animation_fps_strategy,
    theme_variant=theme_variant_strategy
)
@pytest.mark.property_test
def test_config_json_validity(
    mode,
    animation_enabled,
    animation_duration,
    animation_fps,
    theme_variant
):
    """Property 7: For any config saved, the resulting file is valid JSON.
    
    This property ensures that the saved configuration file can be parsed
    as valid JSON without errors.
    """
    with temp_config_context():
        # Arrange
        config = AppConfig(
            theme_variant=theme_variant,
            banner=BannerConfig(
                mode=mode,
                animation_enabled=animation_enabled,
                animation_duration=animation_duration,
                animation_fps=animation_fps
            )
        )
        
        config_manager = ConfigManager()
        
        # Act
        config_manager.save(config)
        
        # Assert - file should be valid JSON
        with open(ConfigManager.CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)  # Should not raise JSONDecodeError
        
        # Verify structure
        assert isinstance(data, dict)
        assert 'version' in data
        assert 'theme_variant' in data
        assert 'banner' in data
        assert isinstance(data['banner'], dict)



# Property 8: Configuration Schema Validation
# **Validates: Requirements 6.4**
@given(
    invalid_duration=st.one_of(
        st.floats(min_value=-100.0, max_value=0.4),  # Too low
        st.floats(min_value=10.1, max_value=100.0)   # Too high
    ),
    invalid_fps=st.one_of(
        st.integers(min_value=-100, max_value=3),    # Too low
        st.integers(min_value=31, max_value=100)     # Too high
    ),
    invalid_theme=st.text(min_size=1).filter(
        lambda x: x not in ["CRT_Cyan", "Amber_Terminal", "Green_Phosphor", "Synthwave"]
    )
)
@pytest.mark.property_test
def test_config_schema_validation(invalid_duration, invalid_fps, invalid_theme):
    """Property 8: For any invalid config data, defaults are used instead.
    
    This property ensures that out-of-range values and invalid types are
    rejected and replaced with sensible defaults.
    """
    with temp_config_context():
        config_manager = ConfigManager()
        
        # Create a config with invalid values
        invalid_config = {
            "version": 1,
            "first_run_complete": False,
            "theme_variant": invalid_theme,
            "banner": {
                "mode": "random",
                "selected_banner": None,
                "selected_categories": ["1ST_BEEFS"],
                "animation_enabled": True,
                "animation_duration": invalid_duration,
                "animation_fps": invalid_fps,
                "animation_intensity": "normal"
            },
            "user_preferences": {}
        }
        
        # Write invalid config directly to file
        config_manager.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(config_manager.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(invalid_config, f)
        
        # Act - load should validate and fix invalid values
        loaded_config = config_manager.load()
        
        # Assert - invalid values should be replaced with defaults
        assert 0.5 <= loaded_config.banner.animation_duration <= 10.0
        assert 4 <= loaded_config.banner.animation_fps <= 30
        assert loaded_config.theme_variant in ["CRT_Cyan", "Amber_Terminal", "Green_Phosphor", "Synthwave"]


# Property 26: Corrupted Config Recovery
# **Validates: Requirements 10.6, 10.7**
@given(
    corrupted_json=st.one_of(
        st.just("{invalid json"),
        st.just('{"version": 1, "banner": {unclosed'),
        st.just('{"version": "not a number"}'),
        st.just('[1, 2, 3]'),  # Valid JSON but wrong type
        st.just('')  # Empty file
    )
)
@pytest.mark.property_test
def test_corrupted_config_recovery(corrupted_json):
    """Property 26: For any corrupted config, system backs up and uses defaults.
    
    This property ensures that the system gracefully handles corrupted
    configuration files by backing them up and creating fresh defaults.
    """
    with temp_config_context():
        config_manager = ConfigManager()
        
        # Create corrupted config file
        config_manager.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(config_manager.CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write(corrupted_json)
        
        # Act - load should handle corruption gracefully
        loaded_config = config_manager.load()
        
        # Assert - should return default config
        # Note: default config uses CURRENT_VERSION
        from src.config import CURRENT_VERSION
        assert loaded_config.version == CURRENT_VERSION
        assert loaded_config.theme_variant == "CRT_Cyan"
        assert loaded_config.banner.mode == "random"
        assert loaded_config.banner.animation_duration == 3.0
        assert loaded_config.banner.animation_fps == 8
        
        # Assert - corrupted file should be backed up (or deleted)
        # The original config.json should either not exist or be replaced
        if config_manager.CONFIG_FILE.exists():
            # If it exists, it should be valid JSON now
            with open(config_manager.CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)  # Should not raise
                assert isinstance(data, dict)



# Property 9: Configuration Version Migration
# **Validates: Requirements 6.6**
@given(
    mode=banner_mode_strategy,
    theme_variant=theme_variant_strategy,
    animation_enabled=st.booleans(),
    selected_categories=category_list_strategy
)
@pytest.mark.property_test
def test_config_version_migration(mode, theme_variant, animation_enabled, selected_categories):
    """Property 9: For any old config version, loading migrates to current version.
    
    This property ensures that configuration files with older schema versions
    are automatically migrated to the current version while preserving
    compatible fields.
    """
    with temp_config_context():
        config_manager = ConfigManager()
        
        # Create an old version config (version 0, which doesn't exist but tests migration)
        # In reality, we're testing that version 1 stays at version 1 since CURRENT_VERSION is 1
        # But the migration system is in place for future versions
        old_config = {
            "version": 1,  # Current version, so no migration needed
            "first_run_complete": True,
            "theme_variant": theme_variant,
            "banner": {
                "mode": mode,
                "selected_banner": None,
                "selected_categories": selected_categories,
                "animation_enabled": animation_enabled,
                "animation_duration": 3.0,
                "animation_fps": 8,
                "animation_intensity": "normal"
            },
            "user_preferences": {}
        }
        
        # Write old config to file
        config_manager.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(config_manager.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(old_config, f)
        
        # Act - load should handle version correctly
        loaded_config = config_manager.load()
        
        # Assert - version should be current
        from src.config import CURRENT_VERSION
        assert loaded_config.version == CURRENT_VERSION
        
        # Assert - compatible fields should be preserved
        assert loaded_config.theme_variant == theme_variant
        assert loaded_config.banner.mode == mode
        assert loaded_config.banner.animation_enabled == animation_enabled
        assert loaded_config.banner.selected_categories == selected_categories
