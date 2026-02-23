"""Property-based tests for caching system.

Tests universal properties that should hold for all cache operations:
- Property 39: Cache Reuse on Repeated Access
- Property 40: Cache Freshness Validation
- Property 41: Cache Failure Graceful Handling

These tests use Hypothesis to generate random test data and verify
that caching behavior is correct across all possible inputs.
"""

import pytest
import time
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from src.config import ConfigManager, CacheEntry


# Strategy for generating cache names
cache_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=ord('a'), max_codepoint=ord('z')),
    min_size=1,
    max_size=20
).filter(lambda x: x.isalnum())

# Strategy for generating cacheable data (excluding None to avoid ambiguity)
cacheable_data_strategy = st.one_of(
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.lists(st.integers(), max_size=10),
    st.dictionaries(st.text(max_size=10), st.integers(), max_size=10),
)


class TestProperty39CacheReuseOnRepeatedAccess:
    """Property 39: Cache Reuse on Repeated Access
    
    For any cached data (distro detection, font logos), the second access
    should return the cached result without re-executing the expensive operation.
    
    Validates: Requirements 13.2, 13.3
    """
    
    @given(
        cache_name=cache_name_strategy,
        data=cacheable_data_strategy
    )
    @settings(max_examples=50, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_repeated_access_returns_same_data(self, cache_name, data):
        """Property: Repeated cache reads return identical data without re-execution.
        
        This property verifies that:
        1. Writing data to cache succeeds
        2. First read returns the cached data
        3. Second read returns identical data
        4. No re-execution occurs (data is reused from cache)
        """
        # Create temporary cache directory and config manager
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            
            # Reset class-level cache state
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', cache_dir):
                config_manager = ConfigManager()
                
                # Write data to cache
                write_result = config_manager.write_cache(cache_name, data)
                assume(write_result is True)  # Only test when write succeeds
                
                # First read
                first_read = config_manager.read_cache(cache_name)
                
                # Second read (should reuse cache)
                second_read = config_manager.read_cache(cache_name)
                
                # Property: Both reads return identical data
                assert first_read == data, "First read should return original data"
                assert second_read == data, "Second read should return original data"
                assert first_read == second_read, "Repeated reads should return identical data"
    
    @given(
        cache_name=cache_name_strategy,
        data=cacheable_data_strategy
    )
    @settings(max_examples=50, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_cache_reuse_without_recomputation(self, cache_name, data):
        """Property: Cache reuse avoids expensive recomputation.
        
        This property verifies that once data is cached, subsequent accesses
        do not trigger recomputation (simulated by tracking read operations).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', cache_dir):
                config_manager = ConfigManager()
                
                # Write data to cache
                write_result = config_manager.write_cache(cache_name, data)
                assume(write_result is True)
                
                # Track number of actual file reads
                original_open = open
                read_count = {'count': 0}
                
                def counting_open(*args, **kwargs):
                    if 'rb' in args or kwargs.get('mode') == 'rb':
                        read_count['count'] += 1
                    return original_open(*args, **kwargs)
                
                with patch('builtins.open', side_effect=counting_open):
                    # First read (will read from file)
                    first_read = config_manager.read_cache(cache_name)
                    first_count = read_count['count']
                    
                    # Second read (should also read from file, but data is reused)
                    second_read = config_manager.read_cache(cache_name)
                    second_count = read_count['count']
                
                # Property: Data is identical (reused)
                assert first_read == second_read
                
                # Property: Both reads access the cache file
                assert first_count >= 1, "First read should access cache file"
                assert second_count >= 2, "Second read should also access cache file"
    
    @given(
        cache_name=cache_name_strategy,
        data=cacheable_data_strategy,
        num_reads=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=30, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_repeated_accesses(self, cache_name, data, num_reads):
        """Property: Multiple repeated accesses all return identical cached data.
        
        This property verifies that any number of repeated cache accesses
        return the same data without corruption or modification.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', cache_dir):
                config_manager = ConfigManager()
                
                # Write data to cache
                write_result = config_manager.write_cache(cache_name, data)
                assume(write_result is True)
                
                # Perform multiple reads
                reads = []
                for _ in range(num_reads):
                    cached_data = config_manager.read_cache(cache_name)
                    reads.append(cached_data)
                
                # Property: All reads return identical data
                for i, read_data in enumerate(reads):
                    assert read_data == data, f"Read {i+1} should return original data"
                
                # Property: All reads are identical to each other
                for i in range(1, len(reads)):
                    assert reads[i] == reads[0], f"Read {i+1} should match first read"


class TestProperty40CacheFreshnessValidation:
    """Property 40: Cache Freshness Validation
    
    For any cached data, if the source file modification time is newer than
    the cache timestamp, the cache should be invalidated and regenerated.
    
    Validates: Requirements 13.4, 13.5
    """
    
    @given(
        cache_name=cache_name_strategy,
        data=cacheable_data_strategy
    )
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_fresh_cache_validates_as_fresh(self, cache_name, data):
        """Property: Cache created after source file is considered fresh.
        
        This property verifies that when cache is newer than source file,
        validate_cache_freshness returns True.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', cache_dir):
                config_manager = ConfigManager()
                
                # Create source file
                source_file = cache_dir / f"source_{cache_name}.txt"
                source_file.write_text("original content")
                
                # Wait to ensure different timestamps (longer on Windows)
                time.sleep(0.2)
                
                # Write cache (will be newer than source)
                write_result = config_manager.write_cache(cache_name, data)
                assume(write_result is True)
                
                # Wait to ensure cache file is fully written
                time.sleep(0.2)
                
                # Property: Cache should be considered fresh
                is_fresh = config_manager.validate_cache_freshness(cache_name, source_file)
                assert is_fresh is True, "Cache newer than source should be fresh"
    
    @given(
        cache_name=cache_name_strategy,
        data=cacheable_data_strategy
    )
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_stale_cache_validates_as_stale(self, cache_name, data):
        """Property: Cache older than source file is considered stale.
        
        This property verifies that when source file is modified after cache
        creation, validate_cache_freshness returns False.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', cache_dir):
                config_manager = ConfigManager()
                
                # Create source file
                source_file = cache_dir / f"source_{cache_name}.txt"
                source_file.write_text("original content")
                
                # Write cache
                write_result = config_manager.write_cache(cache_name, data)
                assume(write_result is True)
                
                # Wait to ensure different timestamps
                time.sleep(0.1)
                
                # Modify source file (make it newer than cache)
                source_file.write_text("modified content")
                
                # Property: Cache should be considered stale
                is_fresh = config_manager.validate_cache_freshness(cache_name, source_file)
                assert is_fresh is False, "Cache older than source should be stale"
    
    @given(
        cache_name=cache_name_strategy,
        data=cacheable_data_strategy,
        max_age=st.floats(min_value=0.01, max_value=1.0)
    )
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_max_age_validation(self, cache_name, data, max_age):
        """Property: Cache respects max_age parameter for freshness.
        
        This property verifies that cache read with max_age parameter
        correctly validates cache age and returns None for expired cache.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', cache_dir):
                config_manager = ConfigManager()
                
                # Write cache
                write_result = config_manager.write_cache(cache_name, data)
                assume(write_result is True)
                
                # Read immediately (should succeed)
                fresh_read = config_manager.read_cache(cache_name, max_age=max_age)
                assert fresh_read == data, "Fresh cache should return data"
                
                # Wait longer than max_age
                time.sleep(max_age + 0.1)
                
                # Read with same max_age (should fail due to age)
                stale_read = config_manager.read_cache(cache_name, max_age=max_age)
                
                # Property: Stale cache returns None
                assert stale_read is None, f"Cache older than {max_age}s should return None"
    
    @given(
        cache_name=cache_name_strategy
    )
    @settings(max_examples=30, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_nonexistent_cache_validates_as_stale(self, cache_name):
        """Property: Non-existent cache is always considered stale.
        
        This property verifies that validate_cache_freshness returns False
        when the cache file doesn't exist.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', cache_dir):
                config_manager = ConfigManager()
                
                # Create source file
                source_file = cache_dir / f"source_{cache_name}.txt"
                source_file.write_text("content")
                
                # Property: Non-existent cache is stale
                is_fresh = config_manager.validate_cache_freshness(cache_name, source_file)
                assert is_fresh is False, "Non-existent cache should be stale"
    
    @given(
        cache_name=cache_name_strategy,
        data=cacheable_data_strategy
    )
    @settings(max_examples=30, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_missing_source_file_validates_as_stale(self, cache_name, data):
        """Property: Cache with missing source file is considered stale.
        
        This property verifies that validate_cache_freshness returns False
        when the source file doesn't exist.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', cache_dir):
                config_manager = ConfigManager()
                
                # Write cache
                write_result = config_manager.write_cache(cache_name, data)
                assume(write_result is True)
                
                # Use non-existent source file
                nonexistent_source = cache_dir / f"nonexistent_{cache_name}.txt"
                
                # Property: Cache with missing source is stale
                is_fresh = config_manager.validate_cache_freshness(cache_name, nonexistent_source)
                assert is_fresh is False, "Cache with missing source should be stale"


class TestProperty41CacheFailureGracefulHandling:
    """Property 41: Cache Failure Graceful Handling
    
    For any cache directory creation or write failure, the system should
    continue operating without crashing, falling back to non-cached operation.
    
    Validates: Requirements 13.6
    """
    
    @given(
        cache_name=cache_name_strategy,
        data=cacheable_data_strategy
    )
    @settings(max_examples=50, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_write_failure_returns_false_not_exception(self, cache_name, data):
        """Property: Cache write failures return False, not exceptions.
        
        This property verifies that when cache directory cannot be created,
        write_cache returns False gracefully without raising exceptions.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a path that will fail when mkdir is called
            invalid_cache_dir = Path(tmpdir) / "invalid_cache"
            
            # Reset class-level cache state
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', invalid_cache_dir):
                # Mock mkdir to raise OSError
                with patch.object(Path, 'mkdir', side_effect=OSError("Permission denied")):
                    manager = ConfigManager()
                    
                    # Property: write_cache returns False, doesn't raise exception
                    try:
                        result = manager.write_cache(cache_name, data)
                        assert result is False, "Write to invalid directory should return False"
                    except Exception as e:
                        pytest.fail(f"write_cache should not raise exception, got: {e}")
    
    @given(
        cache_name=cache_name_strategy
    )
    @settings(max_examples=50, deadline=1000)
    def test_read_failure_returns_none_not_exception(self, cache_name):
        """Property: Cache read failures return None, not exceptions.
        
        This property verifies that when cache file is corrupted or unreadable,
        read_cache returns None gracefully without raising exceptions.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            
            # Create corrupted cache file
            cache_file = cache_dir / f"{cache_name}.pkl"
            cache_file.write_text("This is not valid pickle data")
            
            # Reset class-level cache state
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', cache_dir):
                manager = ConfigManager()
                
                # Property: read_cache returns None, doesn't raise exception
                try:
                    result = manager.read_cache(cache_name)
                    assert result is None, "Read of corrupted cache should return None"
                except Exception as e:
                    pytest.fail(f"read_cache should not raise exception, got: {e}")
    
    @given(
        cache_name=cache_name_strategy
    )
    @settings(max_examples=30, deadline=1000)
    def test_invalidate_failure_returns_false_not_exception(self, cache_name):
        """Property: Cache invalidation failures return False, not exceptions.
        
        This property verifies that when cache file cannot be deleted,
        invalidate_cache returns False gracefully without raising exceptions.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            
            # Reset class-level cache state
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', cache_dir):
                manager = ConfigManager()
                
                # Mock unlink to raise OSError
                with patch.object(Path, 'unlink', side_effect=OSError("Permission denied")):
                    # Create a cache file first
                    cache_file = cache_dir / f"{cache_name}.pkl"
                    cache_file.write_text("dummy")
                    
                    # Property: invalidate_cache returns False, doesn't raise exception
                    try:
                        result = manager.invalidate_cache(cache_name)
                        assert result is False, "Invalidate failure should return False"
                    except Exception as e:
                        pytest.fail(f"invalidate_cache should not raise exception, got: {e}")
    
    @given(
        cache_name=cache_name_strategy,
        data=cacheable_data_strategy
    )
    @settings(max_examples=30, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_cache_dir_creation_failure_graceful(self, cache_name, data):
        """Property: Cache directory creation failure is handled gracefully.
        
        This property verifies that when cache directory cannot be created,
        the system continues operating without crashing.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_cache_dir = Path(tmpdir) / "invalid_cache"
            
            # Reset class-level cache state
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', invalid_cache_dir):
                # Mock mkdir to raise OSError
                with patch.object(Path, 'mkdir', side_effect=OSError("Permission denied")):
                    manager = ConfigManager()
                    
                    # Property: All cache operations handle failure gracefully
                    try:
                        write_result = manager.write_cache(cache_name, data)
                        assert write_result is False, "Write should fail gracefully"
                        
                        read_result = manager.read_cache(cache_name)
                        assert read_result is None, "Read should return None gracefully"
                        
                        invalidate_result = manager.invalidate_cache(cache_name)
                        # Invalidate may return True (file doesn't exist) or False (error)
                        assert isinstance(invalidate_result, bool), "Invalidate should return bool"
                        
                    except Exception as e:
                        pytest.fail(f"Cache operations should not raise exceptions, got: {e}")
    
    @given(
        cache_name=cache_name_strategy,
        data=cacheable_data_strategy
    )
    @settings(max_examples=30, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_system_continues_after_cache_failure(self, cache_name, data):
        """Property: System continues operating after cache failures.
        
        This property verifies that cache failures don't prevent the system
        from continuing normal operation (fallback to non-cached mode).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_cache_dir = Path(tmpdir) / "invalid_cache"
            
            # Reset class-level cache state
            ConfigManager._cache_dir_checked = False
            ConfigManager._cache_dir_exists = False
            
            with patch.object(ConfigManager, 'CACHE_DIR', invalid_cache_dir):
                # Mock mkdir to raise OSError
                with patch.object(Path, 'mkdir', side_effect=OSError("Permission denied")):
                    manager = ConfigManager()
                    
                    # Attempt cache operations (should fail gracefully)
                    write_result = manager.write_cache(cache_name, data)
                    read_result = manager.read_cache(cache_name)
                    
                    # Property: System is still functional after cache failures
                    # (ConfigManager instance is still usable)
                    try:
                        # These operations should still work
                        assert hasattr(manager, 'CONFIG_DIR')
                        assert hasattr(manager, 'CACHE_DIR')
                        assert callable(manager.write_cache)
                        assert callable(manager.read_cache)
                        
                        # Can still attempt other cache operations
                        another_write = manager.write_cache(f"{cache_name}_2", {"other": "data"})
                        assert isinstance(another_write, bool)
                        
                    except Exception as e:
                        pytest.fail(f"System should remain functional after cache failure, got: {e}")
