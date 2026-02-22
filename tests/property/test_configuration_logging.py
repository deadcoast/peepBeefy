"""Property 32: Configuration Change Logging

This property validates that configuration changes are logged at INFO level
and validation errors are logged at WARNING level.

Validates Requirements: 14.3
"""

import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path
import tempfile
import logging
from io import StringIO
import json

from src.config import ConfigManager, AppConfig, BannerConfig


@given(
    theme_variant=st.sampled_from(["CRT_Cyan", "Amber_Terminal", "Green_Phosphor", "Synthwave"]),
    banner_mode=st.sampled_from(["random", "fixed", "category"]),
    animation_enabled=st.booleans()
)
@settings(max_examples=50, deadline=None)
def test_configuration_changes_are_logged(theme_variant, banner_mode, animation_enabled):
    """Property 32: Configuration changes are logged at INFO level.
    
    PROPERTY: For all configuration save operations,
              the save operation MUST be logged at INFO level
              with details about what was saved.
    
    This ensures configuration changes can be audited and tracked.
    """
    # Set up logging capture
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    
    config_logger = logging.getLogger('src.config')
    original_level = config_logger.level
    config_logger.setLevel(logging.INFO)
    config_logger.addHandler(handler)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override CONFIG_DIR for testing
            original_config_dir = ConfigManager.CONFIG_DIR
            original_config_file = ConfigManager.CONFIG_FILE
            
            ConfigManager.CONFIG_DIR = Path(tmpdir) / ".peepbeefy"
            ConfigManager.CONFIG_FILE = ConfigManager.CONFIG_DIR / "config.json"
            
            try:
                manager = ConfigManager()
                
                # Create a configuration
                config = AppConfig(
                    version=1,
                    first_run_complete=True,
                    theme_variant=theme_variant,
                    banner=BannerConfig(
                        mode=banner_mode,
                        animation_enabled=animation_enabled
                    )
                )
                
                # Clear log before save
                log_stream.truncate(0)
                log_stream.seek(0)
                
                # Save configuration
                manager.save(config)
                
                log_output = log_stream.getvalue()
                
                # Property: Save operation should be logged at INFO level
                assert "INFO" in log_output, \
                    "Configuration save should log at INFO level"
                
                # Property: Log should mention configuration or save operation
                assert "config" in log_output.lower() or "Saved" in log_output, \
                    "Log should mention configuration or save operation"
                
                # Property: Log should contain file path information
                assert "config.json" in log_output or str(ConfigManager.CONFIG_FILE) in log_output, \
                    "Log should contain configuration file path"
            
            finally:
                # Restore original paths
                ConfigManager.CONFIG_DIR = original_config_dir
                ConfigManager.CONFIG_FILE = original_config_file
    
    finally:
        # Clean up logging
        config_logger.removeHandler(handler)
        config_logger.setLevel(original_level)
        handler.close()


@given(
    old_version=st.integers(min_value=0, max_value=0),  # Currently only v1 exists, so test v0->v1
)
@settings(max_examples=20, deadline=None)
def test_migration_operations_are_logged(old_version):
    """Property 32: Migration operations are logged at INFO level.
    
    PROPERTY: For all configuration migration operations,
              the migration MUST be logged at INFO level
              with details about version transition.
    
    This ensures schema migrations can be tracked and debugged.
    """
    # Set up logging capture
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    
    config_logger = logging.getLogger('src.config')
    original_level = config_logger.level
    config_logger.setLevel(logging.INFO)
    config_logger.addHandler(handler)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override CONFIG_DIR for testing
            original_config_dir = ConfigManager.CONFIG_DIR
            original_config_file = ConfigManager.CONFIG_FILE
            
            ConfigManager.CONFIG_DIR = Path(tmpdir) / ".peepbeefy"
            ConfigManager.CONFIG_FILE = ConfigManager.CONFIG_DIR / "config.json"
            
            try:
                # Create old version config file
                ConfigManager.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                
                old_config_data = {
                    "version": old_version,
                    "first_run_complete": False,
                    "theme_variant": "CRT_Cyan",
                    "banner": {
                        "mode": "random",
                        "animation_enabled": True
                    }
                }
                
                with open(ConfigManager.CONFIG_FILE, 'w') as f:
                    json.dump(old_config_data, f)
                
                manager = ConfigManager()
                
                # Clear log before load (which triggers migration)
                log_stream.truncate(0)
                log_stream.seek(0)
                
                # Load configuration (should trigger migration if old_version < current)
                config = manager.load()
                
                log_output = log_stream.getvalue()
                
                # Property: If migration occurred, it should be logged
                if old_version < 1:  # Current version is 1
                    # Migration should be logged
                    assert "migrat" in log_output.lower() or "version" in log_output.lower(), \
                        "Migration operation should be logged"
                    
                    # Property: Log should mention version numbers
                    if "migrat" in log_output.lower():
                        assert str(old_version) in log_output or "v" in log_output.lower(), \
                            "Migration log should mention version numbers"
            
            finally:
                # Restore original paths
                ConfigManager.CONFIG_DIR = original_config_dir
                ConfigManager.CONFIG_FILE = original_config_file
    
    finally:
        # Clean up logging
        config_logger.removeHandler(handler)
        config_logger.setLevel(original_level)
        handler.close()


@given(
    invalid_type=st.sampled_from([
        'invalid_duration',
        'invalid_fps',
        'invalid_theme',
        'corrupted_json',
        'invalid_schema'
    ])
)
@settings(max_examples=50, deadline=None)
def test_validation_errors_are_logged(invalid_type):
    """Property 32: Validation errors are logged at WARNING or ERROR level.
    
    PROPERTY: For all configuration validation failures,
              the validation error MUST be logged at WARNING or ERROR level
              with details about what failed validation.
    
    This ensures configuration issues are visible and debuggable.
    """
    # Set up logging capture
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    
    config_logger = logging.getLogger('src.config')
    original_level = config_logger.level
    config_logger.setLevel(logging.WARNING)
    config_logger.addHandler(handler)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override CONFIG_DIR for testing
            original_config_dir = ConfigManager.CONFIG_DIR
            original_config_file = ConfigManager.CONFIG_FILE
            
            ConfigManager.CONFIG_DIR = Path(tmpdir) / ".peepbeefy"
            ConfigManager.CONFIG_FILE = ConfigManager.CONFIG_DIR / "config.json"
            
            try:
                ConfigManager.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                
                # Create invalid config based on type
                if invalid_type == 'invalid_duration':
                    config_data = {
                        "version": 1,
                        "banner": {
                            "animation_duration": 100.0  # Out of range (0.5-10.0)
                        }
                    }
                elif invalid_type == 'invalid_fps':
                    config_data = {
                        "version": 1,
                        "banner": {
                            "animation_fps": 100  # Out of range (4-30)
                        }
                    }
                elif invalid_type == 'invalid_theme':
                    config_data = {
                        "version": 1,
                        "theme_variant": "NonExistentTheme"
                    }
                elif invalid_type == 'corrupted_json':
                    # Write invalid JSON
                    with open(ConfigManager.CONFIG_FILE, 'w') as f:
                        f.write("{invalid json content")
                    config_data = None
                elif invalid_type == 'invalid_schema':
                    config_data = {
                        "version": "not_an_integer",  # Should be int
                        "banner": {}
                    }
                
                if config_data is not None:
                    with open(ConfigManager.CONFIG_FILE, 'w') as f:
                        json.dump(config_data, f)
                
                manager = ConfigManager()
                
                # Clear log before load
                log_stream.truncate(0)
                log_stream.seek(0)
                
                # Load configuration (should trigger validation)
                config = manager.load()
                
                log_output = log_stream.getvalue()
                
                # Property: Validation errors should be logged
                if invalid_type in ['invalid_duration', 'invalid_fps', 'invalid_theme']:
                    assert "WARNING" in log_output or "ERROR" in log_output, \
                        f"Validation error for {invalid_type} should be logged"
                    
                    # Property: Log should mention the invalid field
                    if invalid_type == 'invalid_duration':
                        assert "duration" in log_output.lower() or "Invalid" in log_output, \
                            "Log should mention the invalid duration"
                    elif invalid_type == 'invalid_fps':
                        assert "fps" in log_output.lower() or "Invalid" in log_output, \
                            "Log should mention the invalid FPS"
                    elif invalid_type == 'invalid_theme':
                        assert "theme" in log_output.lower() or "Invalid" in log_output, \
                            "Log should mention the invalid theme"
                
                elif invalid_type in ['corrupted_json', 'invalid_schema']:
                    assert "ERROR" in log_output, \
                        f"Corrupted config ({invalid_type}) should log error"
                    
                    # Property: Log should indicate the nature of the error
                    assert "config" in log_output.lower() or "Invalid" in log_output or "Corrupted" in log_output, \
                        "Log should indicate configuration error"
            
            finally:
                # Restore original paths
                ConfigManager.CONFIG_DIR = original_config_dir
                ConfigManager.CONFIG_FILE = original_config_file
    
    finally:
        # Clean up logging
        config_logger.removeHandler(handler)
        config_logger.setLevel(original_level)
        handler.close()


@given(
    operation=st.sampled_from(['load', 'save', 'mark_first_run'])
)
@settings(max_examples=50, deadline=None)
def test_all_config_operations_produce_logs(operation):
    """Property 32: All configuration operations produce appropriate logs.
    
    PROPERTY: For all configuration operations (load, save, mark_first_run),
              the operation MUST produce at least one log entry
              at INFO level or higher.
    
    This ensures all configuration activity is traceable.
    """
    # Set up logging capture
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    
    config_logger = logging.getLogger('src.config')
    original_level = config_logger.level
    config_logger.setLevel(logging.INFO)
    config_logger.addHandler(handler)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override CONFIG_DIR for testing
            original_config_dir = ConfigManager.CONFIG_DIR
            original_config_file = ConfigManager.CONFIG_FILE
            
            ConfigManager.CONFIG_DIR = Path(tmpdir) / ".peepbeefy"
            ConfigManager.CONFIG_FILE = ConfigManager.CONFIG_DIR / "config.json"
            
            try:
                manager = ConfigManager()
                
                # Clear log before operation
                log_stream.truncate(0)
                log_stream.seek(0)
                
                # Perform operation
                if operation == 'load':
                    config = manager.load()
                elif operation == 'save':
                    config = AppConfig()
                    manager.save(config)
                elif operation == 'mark_first_run':
                    manager.mark_first_run_complete()
                
                log_output = log_stream.getvalue()
                
                # Property: Operation should produce at least one log entry
                assert len(log_output) > 0, \
                    f"Operation '{operation}' should produce log output"
                
                # Property: Log should be at INFO level or higher
                assert "INFO" in log_output or "WARNING" in log_output or "ERROR" in log_output, \
                    f"Operation '{operation}' should log at INFO level or higher"
            
            finally:
                # Restore original paths
                ConfigManager.CONFIG_DIR = original_config_dir
                ConfigManager.CONFIG_FILE = original_config_file
    
    finally:
        # Clean up logging
        config_logger.removeHandler(handler)
        config_logger.setLevel(original_level)
        handler.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
