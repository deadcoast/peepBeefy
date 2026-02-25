# Caching System Documentation

## Overview

The caching system provides infrastructure for caching expensive operations like distro detection and banner lookups. It uses pickle serialization, validates cache freshness, and handles failures gracefully without crashing the application.

## Features

- **Pickle Serialization**: Fast binary serialization for complex data structures
- **Freshness Validation**: Automatic cache invalidation based on file modification timestamps
- **Graceful Error Handling**: All cache operations fail gracefully without raising exceptions
- **XDG Compliance**: Follows XDG Base Directory specification for cache location
- **TTL Support**: Time-to-live validation for time-sensitive cached data

## Cache Location

The cache directory follows the XDG Base Directory specification:

- **Linux/macOS**: `$XDG_CACHE_HOME/hyfetch` or `~/.cache/hyfetch`
- **Windows**: `%LOCALAPPDATA%\.cache\hyfetch` or `~/.cache/hyfetch`

## Data Models

### CacheEntry

Generic cache entry with timestamp and data.

```python
@dataclass
class CacheEntry:
    timestamp: float  # Unix timestamp when created
    data: Any         # The cached data (any picklable type)
```

### BannerCache

Cache for banner database.

```python
@dataclass
class BannerCache:
    banners: Dict[str, List[Any]]  # Category -> banners mapping
    last_modified: float            # Unix timestamp
```

### TerminalCache

Cache for terminal detection results with TTL.

```python
@dataclass
class TerminalCache:
    ansi_mode: str                    # Detected ANSI color mode
    background_color: Optional[tuple] # RGB tuple or None
    supports_rgb: bool                # RGB support flag
    supports_256: bool                # 256-color support flag
    detected_at: float                # Detection timestamp
    ttl: float = 3600.0              # Time-to-live (default 1 hour)
```

## API Reference

### ConfigManager.write_cache()

Write data to cache file using pickle serialization.

```python
def write_cache(self, cache_name: str, data: Any) -> bool:
    """
    Args:
        cache_name: Name of the cache file (without extension)
        data: Data to cache (must be picklable)
    
    Returns:
        True if cache was written successfully, False otherwise
    """
```

**Example:**
```python
cm = ConfigManager()
terminal_data = TerminalCache(
    ansi_mode="rgb",
    background_color=(30, 30, 30),
    supports_rgb=True,
    supports_256=True,
    detected_at=time.time()
)
success = cm.write_cache("terminal_detection", terminal_data)
```

### ConfigManager.read_cache()

Read data from cache file with freshness validation.

```python
def read_cache(self, cache_name: str, max_age: Optional[float] = None) -> Optional[Any]:
    """
    Args:
        cache_name: Name of the cache file (without extension)
        max_age: Maximum age in seconds (None = no age check)
    
    Returns:
        Cached data if valid and fresh, None otherwise
    """
```

**Example:**
```python
# Read without age check
cached_data = cm.read_cache("terminal_detection")

# Read with 1-hour TTL
cached_data = cm.read_cache("terminal_detection", max_age=3600.0)
```

### ConfigManager.invalidate_cache()

Invalidate (delete) a cache file.

```python
def invalidate_cache(self, cache_name: str) -> bool:
    """
    Args:
        cache_name: Name of the cache file (without extension)
    
    Returns:
        True if cache was deleted or didn't exist, False on error
    """
```

**Example:**
```python
cm.invalidate_cache("terminal_detection")
```

### ConfigManager.validate_cache_freshness()

Validate cache freshness using file modification timestamps.

```python
def validate_cache_freshness(self, cache_name: str, source_file: Path) -> bool:
    """
    Args:
        cache_name: Name of the cache file (without extension)
        source_file: Path to the source file to compare against
    
    Returns:
        True if cache is fresh (newer than source), False if stale
    """
```

**Example:**
```python
source_file = Path("assets/banners/1ST_BEEFS/CLASSIC.txt")
is_fresh = cm.validate_cache_freshness("banner_cache", source_file)

if not is_fresh:
    # Regenerate cache
    banner_data = load_banners()
    cm.write_cache("banner_cache", banner_data)
```

## Usage Patterns

### Pattern 1: Simple Cache with TTL

```python
from src.config import ConfigManager
import time

cm = ConfigManager()

# Try to read from cache
cached_data = cm.read_cache("expensive_operation", max_age=3600.0)

if cached_data is None:
    # Cache miss or expired - perform expensive operation
    data = perform_expensive_operation()
    cm.write_cache("expensive_operation", data)
else:
    # Cache hit - use cached data
    data = cached_data
```

### Pattern 2: Cache with Source File Validation

```python
from src.config import ConfigManager
from pathlib import Path

cm = ConfigManager()
source_file = Path("data/source.json")

# Check if cache is fresh
if cm.validate_cache_freshness("processed_data", source_file):
    # Cache is fresh - use it
    data = cm.read_cache("processed_data")
else:
    # Cache is stale - regenerate
    data = process_source_file(source_file)
    cm.write_cache("processed_data", data)
```

### Pattern 3: Automatic Cache Regeneration

```python
from src.config import ConfigManager
from pathlib import Path

def get_banner_database(cm: ConfigManager) -> dict:
    """Get banner database with automatic cache regeneration."""
    banner_dir = Path("assets/banners")
    
    # Check cache freshness
    if cm.validate_cache_freshness("banner_db", banner_dir):
        cached = cm.read_cache("banner_db")
        if cached is not None:
            return cached
    
    # Cache miss or stale - regenerate
    banner_db = load_all_banners(banner_dir)
    cm.write_cache("banner_db", banner_db)
    return banner_db
```

## Error Handling

All cache operations handle errors gracefully:

- **Directory Creation Failure**: Logs warning, caching disabled
- **Write Failure**: Returns False, logs warning
- **Read Failure**: Returns None, logs warning
- **Corrupted Cache**: Returns None, logs warning
- **Permission Errors**: Returns False/None, logs warning

No exceptions are raised to the caller - the application continues with degraded performance (no caching).

## Performance Considerations

### Startup Time Impact

- Cache directory creation: ~1ms
- Cache read (hit): ~5-10ms
- Cache read (miss): ~1ms
- Cache write: ~10-20ms

### Memory Usage

- CacheEntry overhead: ~100 bytes
- Typical terminal cache: ~500 bytes
- Typical banner cache: ~50-100KB

### Disk Usage

Cache files are stored in pickle format:
- Terminal detection: ~1KB
- Banner database: ~100KB
- Total cache size: ~200KB (typical)

## Best Practices

1. **Use Descriptive Cache Names**: Use clear, descriptive names like "terminal_detection" not "cache1"

2. **Set Appropriate TTLs**: Choose TTL based on data volatility:
   - Terminal detection: 1 hour (3600s)
   - Banner database: Until source files change
   - Distro detection: 24 hours (86400s)

3. **Validate Freshness**: For file-based data, use `validate_cache_freshness()` instead of TTL

4. **Handle Cache Misses**: Always have fallback logic for cache misses

5. **Clean Up**: Invalidate caches when source data changes

6. **Don't Cache Everything**: Only cache expensive operations (>50ms)

## Testing

The caching system includes comprehensive unit tests:

```bash
# Run caching system tests
pytest tests/unit/test_caching_system.py -v

# Run with coverage
pytest tests/unit/test_caching_system.py --cov=src.config --cov-report=term
```

## Requirements Satisfied

- **Requirement 13.1**: Cache directory at `~/.cache/hyfetch` or `$XDG_CACHE_HOME/hyfetch` ✓
- **Requirement 13.2**: Cache distro detection results ✓
- **Requirement 13.3**: Cache font logo lookups ✓
- **Requirement 13.4**: Validate cache freshness using file timestamps ✓
- **Requirement 13.5**: Automatic cache regeneration when stale ✓
- **Requirement 13.6**: Graceful handling of cache failures ✓
- **Requirement 13.7**: Pickle format for serialization ✓

## Future Enhancements

Potential improvements for future versions:

1. **Cache Size Limits**: Implement LRU eviction when cache exceeds size limit
2. **Compression**: Add optional gzip compression for large caches
3. **Cache Statistics**: Track hit/miss rates for performance monitoring
4. **Async Cache Operations**: Non-blocking cache writes for better performance
5. **Cache Warming**: Pre-populate caches on first run
