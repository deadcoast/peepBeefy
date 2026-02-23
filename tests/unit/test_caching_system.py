"""Unit tests for caching system in config.py.

Tests cache infrastructure, data models, and cache operations including
write, read, freshness validation, and invalidation.
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
from src.config import ConfigManager, CacheEntry, BannerCache, TerminalCache


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory for testing."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def config_manager(temp_cache_dir):
    """Create a ConfigManager with temporary cache directory."""
    with patch.object(ConfigManager, 'CACHE_DIR', temp_cache_dir):
        manager = ConfigManager()
        yield manager


class TestCacheDataModels:
    """Test cache data model structures."""
    
    def test_cache_entry_creation(self):
        """Test CacheEntry dataclass creation."""
        entry = CacheEntry(timestamp=123456.789, data={"key": "value"})
        assert entry.timestamp == 123456.789
        assert entry.data == {"key": "value"}
    
    def test_banner_cache_creation(self):
        """Test BannerCache dataclass creation."""
        banners = {"category1": ["banner1", "banner2"]}
        cache = BannerCache(banners=banners, last_modified=123456.789)
        assert cache.banners == banners
        assert cache.last_modified == 123456.789
    
    def test_terminal_cache_creation(self):
        """Test TerminalCache dataclass creation."""
        cache = TerminalCache(
            ansi_mode="rgb",
            background_color=(30, 30, 30),
            supports_rgb=True,
            supports_256=True,
            detected_at=123456.789
        )
        assert cache.ansi_mode == "rgb"
        assert cache.background_color == (30, 30, 30)
        assert cache.supports_rgb is True
        assert cache.supports_256 is True
        assert cache.detected_at == 123456.789
        assert cache.ttl == 3600.0  # Default TTL
    
    def test_terminal_cache_custom_ttl(self):
        """Test TerminalCache with custom TTL."""
        cache = TerminalCache(
            ansi_mode="8bit",
            background_color=None,
            supports_rgb=False,
            supports_256=True,
            detected_at=123456.789,
            ttl=7200.0
        )
        assert cache.ttl == 7200.0


class TestCacheInfrastructure:
    """Test cache directory creation and management."""
    
    def test_ensure_cache_dir_creates_directory(self, temp_cache_dir):
        """Test that _ensure_cache_dir creates the cache directory."""
        # Remove the directory first
        temp_cache_dir.rmdir()
        assert not temp_cache_dir.exists()
        
        with patch.object(ConfigManager, 'CACHE_DIR', temp_cache_dir):
            manager = ConfigManager()
            result = manager._ensure_cache_dir()
        
        assert result is True
        assert temp_cache_dir.exists()
    
    def test_ensure_cache_dir_handles_existing_directory(self, config_manager):
        """Test that _ensure_cache_dir handles existing directory."""
        result = config_manager._ensure_cache_dir()
        assert result is True
    
    def test_ensure_cache_dir_handles_permission_error(self, temp_cache_dir):
        """Test graceful handling of permission errors."""
        import sys
        
        # Skip on Windows as permission handling is different
        if sys.platform == "win32":
            pytest.skip("Permission tests not reliable on Windows")
        
        # Create a read-only parent directory
        parent = temp_cache_dir / "readonly"
        parent.mkdir()
        parent.chmod(0o444)  # Read-only
        
        restricted_cache = parent / "cache"
        
        with patch.object(ConfigManager, 'CACHE_DIR', restricted_cache):
            manager = ConfigManager()
            result = manager._ensure_cache_dir()
        
        # Should return False but not raise exception
        assert result is False
        
        # Cleanup
        parent.chmod(0o755)


class TestCacheOperations:
    """Test cache write, read, and invalidation operations."""
    
    def test_write_and_read_cache(self, config_manager):
        """Test writing and reading cache data."""
        test_data = {"key": "value", "number": 42}
        
        # Write cache
        result = config_manager.write_cache("test_cache", test_data)
        assert result is True
        
        # Read cache
        cached_data = config_manager.read_cache("test_cache")
        assert cached_data == test_data
    
    def test_read_nonexistent_cache(self, config_manager):
        """Test reading cache that doesn't exist."""
        cached_data = config_manager.read_cache("nonexistent")
        assert cached_data is None
    
    def test_cache_with_max_age(self, config_manager):
        """Test cache freshness validation with max_age."""
        test_data = {"key": "value"}
        
        # Write cache
        config_manager.write_cache("test_cache", test_data)
        
        # Read immediately (should succeed)
        cached_data = config_manager.read_cache("test_cache", max_age=10.0)
        assert cached_data == test_data
        
        # Simulate old cache by waiting
        time.sleep(0.1)
        
        # Read with very short max_age (should fail)
        cached_data = config_manager.read_cache("test_cache", max_age=0.05)
        assert cached_data is None
    
    def test_invalidate_cache(self, config_manager):
        """Test cache invalidation."""
        test_data = {"key": "value"}
        
        # Write cache
        config_manager.write_cache("test_cache", test_data)
        
        # Verify it exists
        cached_data = config_manager.read_cache("test_cache")
        assert cached_data == test_data
        
        # Invalidate
        result = config_manager.invalidate_cache("test_cache")
        assert result is True
        
        # Verify it's gone
        cached_data = config_manager.read_cache("test_cache")
        assert cached_data is None
    
    def test_invalidate_nonexistent_cache(self, config_manager):
        """Test invalidating cache that doesn't exist."""
        result = config_manager.invalidate_cache("nonexistent")
        assert result is True  # Should succeed (idempotent)
    
    def test_write_cache_complex_data(self, config_manager):
        """Test caching complex data structures."""
        complex_data = {
            "nested": {
                "list": [1, 2, 3],
                "dict": {"a": "b"}
            },
            "tuple": (1, 2, 3),
            "set": {1, 2, 3}
        }
        
        # Write cache
        result = config_manager.write_cache("complex_cache", complex_data)
        assert result is True
        
        # Read cache
        cached_data = config_manager.read_cache("complex_cache")
        assert cached_data["nested"]["list"] == [1, 2, 3]
        assert cached_data["nested"]["dict"] == {"a": "b"}
        assert cached_data["tuple"] == (1, 2, 3)
        assert cached_data["set"] == {1, 2, 3}


class TestCacheFreshnessValidation:
    """Test cache freshness validation using file modification timestamps."""
    
    def test_validate_cache_freshness_fresh_cache(self, config_manager, temp_cache_dir):
        """Test validation when cache is fresh (newer than source)."""
        # Create source file
        source_file = temp_cache_dir / "source.txt"
        source_file.write_text("original content")
        
        # Wait a bit to ensure different timestamps
        time.sleep(0.1)
        
        # Write cache (will be newer than source)
        config_manager.write_cache("test_cache", {"data": "cached"})
        
        # Validate freshness
        is_fresh = config_manager.validate_cache_freshness("test_cache", source_file)
        assert is_fresh is True
    
    def test_validate_cache_freshness_stale_cache(self, config_manager, temp_cache_dir):
        """Test validation when cache is stale (older than source)."""
        # Create source file
        source_file = temp_cache_dir / "source.txt"
        source_file.write_text("original content")
        
        # Write cache
        config_manager.write_cache("test_cache", {"data": "cached"})
        
        # Wait a bit
        time.sleep(0.1)
        
        # Modify source file (make it newer than cache)
        source_file.write_text("modified content")
        
        # Validate freshness
        is_fresh = config_manager.validate_cache_freshness("test_cache", source_file)
        assert is_fresh is False
    
    def test_validate_cache_freshness_nonexistent_cache(self, config_manager, temp_cache_dir):
        """Test validation when cache doesn't exist."""
        source_file = temp_cache_dir / "source.txt"
        source_file.write_text("content")
        
        is_fresh = config_manager.validate_cache_freshness("nonexistent", source_file)
        assert is_fresh is False
    
    def test_validate_cache_freshness_nonexistent_source(self, config_manager, temp_cache_dir):
        """Test validation when source file doesn't exist."""
        config_manager.write_cache("test_cache", {"data": "cached"})
        
        nonexistent_source = temp_cache_dir / "nonexistent.txt"
        is_fresh = config_manager.validate_cache_freshness("test_cache", nonexistent_source)
        assert is_fresh is False


class TestCacheErrorHandling:
    """Test graceful error handling in cache operations."""
    
    def test_write_cache_without_directory(self, temp_cache_dir):
        """Test write_cache when cache directory cannot be created."""
        import sys
        
        # Skip on Windows as permission handling is different
        if sys.platform == "win32":
            pytest.skip("Permission tests not reliable on Windows")
        
        # Use a path that cannot be created
        invalid_cache_dir = Path("/invalid/path/that/does/not/exist")
        
        with patch.object(ConfigManager, 'CACHE_DIR', invalid_cache_dir):
            manager = ConfigManager()
            result = manager.write_cache("test_cache", {"data": "value"})
        
        # Should return False but not raise exception
        assert result is False
    
    def test_read_corrupted_cache(self, config_manager, temp_cache_dir):
        """Test reading corrupted cache file."""
        # Create a corrupted cache file
        cache_file = temp_cache_dir / "corrupted_cache.pkl"
        cache_file.write_text("This is not valid pickle data")
        
        # Try to read it
        cached_data = config_manager.read_cache("corrupted_cache")
        assert cached_data is None


class TestCacheIntegration:
    """Integration tests for caching system."""
    
    def test_cache_workflow(self, config_manager, temp_cache_dir):
        """Test complete cache workflow: write, read, validate, invalidate."""
        # Create source file
        source_file = temp_cache_dir / "source.txt"
        source_file.write_text("original")
        
        # Write cache
        test_data = {"key": "value"}
        assert config_manager.write_cache("workflow_cache", test_data) is True
        
        # Read cache
        cached = config_manager.read_cache("workflow_cache")
        assert cached == test_data
        
        # Validate freshness (should be fresh)
        time.sleep(0.1)
        assert config_manager.validate_cache_freshness("workflow_cache", source_file) is True
        
        # Modify source (make cache stale)
        time.sleep(0.1)
        source_file.write_text("modified")
        assert config_manager.validate_cache_freshness("workflow_cache", source_file) is False
        
        # Invalidate cache
        assert config_manager.invalidate_cache("workflow_cache") is True
        
        # Verify cache is gone
        assert config_manager.read_cache("workflow_cache") is None
