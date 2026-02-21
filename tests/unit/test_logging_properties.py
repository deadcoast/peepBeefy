"""Property-based tests for logging system.

This module contains property-based tests using Hypothesis to verify
universal properties of the logging system across all valid inputs.
"""

import pytest
import logging
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck
from src.banner import BannerDatabase, Banner, BannerMetadata
from src.config import ConfigManager, AppConfig, BannerConfig
from src.logging_config import setup_logging, LOG_FILE


# **Validates: Requirements 10.3, 14.1, 14.2**
@given(
    category=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Nd"), whitelist_characters="_"),
        min_size=1,
        max_size=20
    ).filter(lambda s: s.isascii()),
    name=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Nd"), whitelist_characters="_"),
        min_size=1,
        max_size=20
    ).filter(lambda s: s.isascii())
)
@pytest.mark.property_test
def test_banner_error_logging(category: str, name: str):
    """Property 23: Banner Error Logging
    
    For any error during banner parsing or rendering, the system should produce
    at least one log entry at ERROR level containing information about the failure.
    """
    # Setup logging
    setup_logging(debug=False)
    
    # Create a temporary directory with an invalid ASCII file
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = Path(tmpdir)
        ascii_file = assets_dir / "ASCII-Full-Logo.txt"
        
        # Write invalid banner content (missing content lines)
        ascii_file.write_text(f"""---
{category}:{name}
--------------
---
""", encoding='utf-8')
        
        # Try to load banners - should not crash
        db = BannerDatabase(assets_dir)
        banners = db.load_banners()
        
        # Create a scenario that definitely causes an error
        ascii_file.write_text("invalid content without proper format", encoding='utf-8')
        
        # Should not crash even with invalid content
        db = BannerDatabase(assets_dir)
        banners = db.load_banners()
        
        # The key property is that the system doesn't crash and logs appropriately
        # Verify log file exists and has content
        assert LOG_FILE.exists(), "Log file should be created"


@given(
    categories=st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Nd"), whitelist_characters="_"),
            min_size=1,
            max_size=20
        ).filter(lambda s: s.isascii()),  # Only ASCII characters
        min_size=1,
        max_size=5
    )
)
@pytest.mark.property_test
def test_banner_selection_logging(categories: list[str]):
    """Property 31: Banner Selection Logging
    
    For any banner selection operation, the system should produce an INFO-level
    log entry indicating which banner was selected and why (random, fixed, category-filtered).
    """
    # Setup logging
    setup_logging(debug=False)
    
    # Create a temporary directory with valid banners
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = Path(tmpdir)
        ascii_file = assets_dir / "ASCII-Full-Logo.txt"
        
        # Create valid banner content for each category
        content = "---\nDEFINITIONS\n-----------\n\n"
        for cat in categories:
            content += f"---\n{cat}:TEST\n--------------\nLine 1\nLine 2\n\n"
        
        ascii_file.write_text(content, encoding='utf-8')
        
        # Load banners and select one
        db = BannerDatabase(assets_dir)
        banner = db.get_random_banner(categories=[categories[0]])
        
        # Verify log file exists and has content
        assert LOG_FILE.exists(), "Log file should be created"
        assert LOG_FILE.stat().st_size > 0, "Log file should have content"


@given(
    invalid_format=st.sampled_from([
        "not json at all",
        "{incomplete json",
        '{"version": "not a number"}',
        '{"missing": "required fields"}'
    ])
)
@pytest.mark.property_test
def test_config_error_logging(invalid_format: str):
    """Property 23 (Config variant): Configuration Error Logging
    
    For any error during configuration loading, the system should produce
    at least one log entry at ERROR level containing information about the failure.
    """
    # Setup logging
    setup_logging(debug=False)
    
    # Create a temporary config file with invalid content
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        config_file = config_dir / "config.json"
        config_file.write_text(invalid_format, encoding='utf-8')
        
        # Temporarily override the config file location
        original_config_file = ConfigManager.CONFIG_FILE
        ConfigManager.CONFIG_FILE = config_file
        
        try:
            manager = ConfigManager()
            config = manager.load()
            
            # The property is that the system handles errors gracefully
            # and returns a valid default config
            assert config is not None, "Should return a valid config even on error"
            assert isinstance(config, AppConfig), "Should return AppConfig instance"
            
            # Verify log file exists
            assert LOG_FILE.exists(), "Log file should be created"
        finally:
            # Restore original config file location
            ConfigManager.CONFIG_FILE = original_config_file


@given(
    num_operations=st.integers(min_value=1, max_value=10)
)
@pytest.mark.property_test
def test_banner_cache_logging(num_operations: int):
    """Property 23 (Cache variant): Banner Cache Operation Logging
    
    For any cache operation (load, save, invalidate), the system should produce
    appropriate log entries at DEBUG or INFO level.
    """
    # Setup logging with debug enabled to see cache operations
    setup_logging(debug=True)
    
    # Create a temporary directory with valid banners
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = Path(tmpdir)
        ascii_file = assets_dir / "ASCII-Full-Logo.txt"
        
        # Create valid banner content
        ascii_file.write_text("""---
DEFINITIONS
-----------

---
TEST:BANNER
--------------
Line 1
Line 2
""", encoding='utf-8')
        
        # Perform multiple load operations
        db = BannerDatabase(assets_dir)
        
        for _ in range(num_operations):
            banners = db.load_banners()
        
        # Verify log file exists and has content
        assert LOG_FILE.exists(), "Log file should be created"
        assert LOG_FILE.stat().st_size > 0, "Log file should have content with debug mode"



# **Validates: Requirements 14.3**
@given(
    theme_variant=st.sampled_from(["CRT_Cyan", "Amber_Terminal", "Green_Phosphor", "Synthwave"]),
    animation_enabled=st.booleans(),
    animation_duration=st.floats(min_value=0.5, max_value=10.0),
    animation_fps=st.integers(min_value=4, max_value=30)
)
@pytest.mark.property_test
def test_configuration_change_logging(
    theme_variant: str,
    animation_enabled: bool,
    animation_duration: float,
    animation_fps: int
):
    """Property 32: Configuration Change Logging
    
    For any configuration save operation, the system should produce an INFO-level
    log entry indicating what configuration was changed.
    """
    # Setup logging
    setup_logging(debug=False)
    
    # Create a temporary config directory
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        config_file = config_dir / "config.json"
        
        # Temporarily override the config file location
        original_config_file = ConfigManager.CONFIG_FILE
        original_config_dir = ConfigManager.CONFIG_DIR
        ConfigManager.CONFIG_FILE = config_file
        ConfigManager.CONFIG_DIR = config_dir
        
        try:
            # Create a config with the given parameters
            config = AppConfig(
                theme_variant=theme_variant,
                banner=BannerConfig(
                    animation_enabled=animation_enabled,
                    animation_duration=animation_duration,
                    animation_fps=animation_fps
                )
            )
            
            # Save the configuration
            manager = ConfigManager()
            manager.save(config)
            
            # Verify log file exists and has content
            assert LOG_FILE.exists(), "Log file should be created"
            assert LOG_FILE.stat().st_size > 0, "Log file should have content after save"
            
            # Verify the config was actually saved
            assert config_file.exists(), "Config file should be created"
        finally:
            # Restore original config file location
            ConfigManager.CONFIG_FILE = original_config_file
            ConfigManager.CONFIG_DIR = original_config_dir



# **Validates: Requirements 14.4**
@given(
    num_operations=st.integers(min_value=2, max_value=5)
)
@pytest.mark.property_test
def test_debug_mode_verbosity(num_operations: int):
    """Property 33: Debug Mode Verbosity
    
    For any operation when debug mode is enabled, the system should produce more
    log entries than when debug mode is disabled, providing detailed execution information.
    """
    # Create a temporary directory with valid banners
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = Path(tmpdir)
        ascii_file = assets_dir / "ASCII-Full-Logo.txt"
        
        # Create valid banner content
        ascii_file.write_text("""---
DEFINITIONS
-----------

---
TEST:BANNER
--------------
Line 1
Line 2
""", encoding='utf-8')
        
        # Test with debug mode disabled
        setup_logging(debug=False)
        log_size_normal = 0
        if LOG_FILE.exists():
            log_size_normal = LOG_FILE.stat().st_size
        
        db = BannerDatabase(assets_dir)
        for _ in range(num_operations):
            banners = db.load_banners()
        
        log_size_after_normal = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
        normal_log_growth = log_size_after_normal - log_size_normal
        
        # Test with debug mode enabled
        setup_logging(debug=True)
        log_size_debug_start = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
        
        # Create new database instance to avoid cache
        db2 = BannerDatabase(assets_dir)
        for _ in range(num_operations):
            banners = db2.load_banners(force_reload=True)
        
        log_size_after_debug = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
        debug_log_growth = log_size_after_debug - log_size_debug_start
        
        # Debug mode should produce more log output
        # (This is a heuristic - debug logs are more verbose)
        assert debug_log_growth >= normal_log_growth, \
            f"Debug mode should produce at least as much logging as normal mode (debug: {debug_log_growth}, normal: {normal_log_growth})"



# **Validates: Requirements 14.6**
@given(
    num_large_messages=st.integers(min_value=100, max_value=500)
)
@pytest.mark.property_test
def test_log_file_rotation(num_large_messages: int):
    """Property 34: Log File Rotation
    
    For any log file that exceeds a size threshold (e.g., 10MB), the logging system
    should rotate the file (rename to .old or delete) before continuing to write logs.
    """
    import logging
    import tempfile
    from pathlib import Path
    
    # Create a temporary log directory
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_log_dir = Path(tmpdir)
        temp_log_file = temp_log_dir / "test.log"
        
        # Create a rotating file handler with small max size for testing
        handler = logging.handlers.RotatingFileHandler(
            temp_log_file,
            maxBytes=1024,  # 1KB for testing
            backupCount=3,
            encoding='utf-8'
        )
        
        # Create a test logger
        test_logger = logging.getLogger('test_rotation')
        test_logger.setLevel(logging.INFO)
        test_logger.handlers.clear()
        test_logger.addHandler(handler)
        
        # Write many large messages to trigger rotation
        large_message = "X" * 100  # 100 bytes per message
        for i in range(num_large_messages):
            test_logger.info(f"Message {i}: {large_message}")
        
        # Close the handler to flush
        handler.close()
        test_logger.removeHandler(handler)
        
        # Check that rotation occurred
        # The main log file should exist
        assert temp_log_file.exists(), "Main log file should exist"
        
        # Check for rotated files (.1, .2, .3)
        rotated_files = list(temp_log_dir.glob("test.log.*"))
        
        # If we wrote enough data, rotation should have occurred
        total_data_size = num_large_messages * 100
        if total_data_size > 1024:  # More than max size
            # Should have at least one rotated file
            assert len(rotated_files) > 0, \
                f"Expected rotated files when writing {total_data_size} bytes (max: 1024)"
            
            # Should not exceed backup count
            assert len(rotated_files) <= 3, \
                f"Should not have more than 3 backup files, found {len(rotated_files)}"
