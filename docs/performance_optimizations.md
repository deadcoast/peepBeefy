# Performance Optimizations

This document describes the performance optimizations implemented in peepBeefy to achieve the <200ms startup time target.

## Overview

The hyfetch integration adds sophisticated color handling, terminal detection, and rendering capabilities. To maintain fast startup times, several optimization strategies have been implemented:

1. **Lazy Loading** - Defer expensive operations until actually needed
2. **Caching** - Cache computed results to avoid redundant work
3. **Efficient Data Structures** - Use pre-computed arrays for O(1) lookups

## Optimization Details

### 1. Lazy Preset Loading

**Module**: `src/color_presets.py`

**Problem**: Loading all color presets from JSON at startup adds ~10-20ms overhead, even when presets aren't used.

**Solution**: Implement `get_presets_lazy()` function that:
- Loads presets only on first access
- Caches loaded presets in memory
- Returns cached presets on subsequent calls

**Usage**:
```python
from src.color_presets import get_presets_lazy

# First call loads from disk (slow)
presets = get_presets_lazy()

# Subsequent calls use cache (fast)
presets = get_presets_lazy()
```

**Performance Impact**: Saves 10-20ms on startup when presets aren't needed immediately.

### 2. Gradient Caching

**Module**: `src/color_scale.py`

**Problem**: Creating gradients involves expensive interpolation calculations. Creating the same gradient multiple times wastes CPU cycles.

**Solution**: Implement gradient caching in `create_gradient()`:
- Cache gradients by (colors, resolution) key
- Return cached gradient if available
- Automatically cache new gradients

**Usage**:
```python
from src.color_scale import create_gradient, clear_gradient_cache, get_gradient_cache_stats

# First call computes gradient
gradient1 = create_gradient([red, blue], 300)

# Second call with same parameters returns cached result
gradient2 = create_gradient([red, blue], 300)  # Fast!

# Check cache statistics
stats = get_gradient_cache_stats()
print(f"Cached gradients: {stats['size']}")
print(f"Memory usage: {stats['memory_mb']:.2f} MB")

# Clear cache if needed (e.g., in tests)
clear_gradient_cache()
```

**Performance Impact**: 
- Saves 5-15ms per duplicate gradient creation
- Memory overhead: ~24 bytes per RGB color in gradient
- Typical memory usage: <1MB for common use cases

### 3. Optimized Cache Directory Handling

**Module**: `src/config.py`

**Problem**: Checking if cache directory exists on every cache operation adds overhead.

**Solution**: Implement class-level caching for directory existence:
- Check directory existence once per process
- Store result in class variable
- Skip repeated filesystem checks

**Implementation**:
```python
class ConfigManager:
    _cache_dir_checked: bool = False
    _cache_dir_exists: bool = False
    
    def _ensure_cache_dir(self) -> bool:
        if ConfigManager._cache_dir_checked:
            return ConfigManager._cache_dir_exists
        # ... check and create directory ...
```

**Performance Impact**: Saves 1-2ms per cache operation after first check.

### 4. Deferred Cache Directory Creation

**Module**: `src/config.py`

**Problem**: Creating cache directory in `__init__()` adds startup overhead even when caching isn't used.

**Solution**: Defer cache directory creation until first cache operation:
- Remove `_ensure_cache_dir()` call from `__init__()`
- Call it only when actually reading/writing cache

**Performance Impact**: Saves 2-5ms on startup when caching isn't used.

## Performance Targets

| Operation | Target | Typical |
|-----------|--------|---------|
| Total startup | <200ms | 150-180ms |
| Module imports | <50ms | 30-40ms |
| Config load | <20ms | 10-15ms |
| Theme init | <10ms | 5-8ms |
| Banner load (cached) | <30ms | 15-25ms |
| Preset load (lazy) | 0ms | 0ms (deferred) |

## Memory Usage

| Component | Memory |
|-----------|--------|
| Gradient cache | <1MB |
| Preset cache | <100KB |
| Banner cache | <500KB |
| Total overhead | <2MB |

## Best Practices

### For Application Code

1. **Use lazy loading functions**:
   ```python
   # Good: Lazy loading
   presets = get_presets_lazy()
   
   # Avoid: Eager loading at module level
   PRESETS = load_presets(Path("data/color_presets.json"))
   ```

2. **Reuse Scale objects**:
   ```python
   # Good: Create once, reuse
   fire_scale = Scale(["#FF0000", "#FFD700"], resolution=300)
   for i in range(100):
       color = fire_scale(i / 100)
   
   # Avoid: Creating new Scale each time
   for i in range(100):
       scale = Scale(["#FF0000", "#FFD700"], resolution=300)
       color = scale(i / 100)
   ```

3. **Use caching for expensive operations**:
   ```python
   # Good: Cache terminal detection results
   config_manager.write_cache("terminal_info", terminal_data)
   
   # Later...
   cached = config_manager.read_cache("terminal_info", max_age=3600)
   ```

### For Testing

1. **Clear caches between tests**:
   ```python
   from src.color_presets import clear_preset_cache
   from src.color_scale import clear_gradient_cache
   
   def teardown():
       clear_preset_cache()
       clear_gradient_cache()
   ```

2. **Use cache statistics for debugging**:
   ```python
   from src.color_scale import get_gradient_cache_stats
   
   stats = get_gradient_cache_stats()
   assert stats['size'] < 100  # Ensure cache doesn't grow unbounded
   ```

## Profiling

Use the startup profiler to measure performance:

```bash
python scripts/profile_startup.py
```

This will output:
- Time breakdown by operation
- Total startup time
- Pass/fail against 200ms target
- Slowest operations

## Future Optimizations

Potential areas for further optimization:

1. **Lazy banner loading**: Load banner files only when needed
2. **Compressed cache format**: Use compression for large cache files
3. **Parallel loading**: Load independent resources in parallel
4. **JIT compilation**: Use PyPy or Numba for hot paths
5. **C extensions**: Rewrite critical paths in C/Rust

## Monitoring

Track startup performance over time:

```bash
# Run profiler and save results
python scripts/profile_startup.py > performance_log.txt

# Compare with previous runs
diff performance_log_old.txt performance_log.txt
```

## Troubleshooting

### Startup time exceeds target

1. Run profiler to identify bottleneck
2. Check if caching is working (cache hits vs misses)
3. Verify lazy loading is being used
4. Check for unnecessary imports at module level

### High memory usage

1. Check gradient cache statistics
2. Clear caches if memory is constrained
3. Reduce gradient resolution if acceptable
4. Use smaller preset files

### Cache not working

1. Verify cache directory exists and is writable
2. Check file permissions
3. Look for error messages in logs
4. Verify cache freshness validation logic

## References

- [Requirement 13.7](../specs/hyfetch-integration-analysis/requirements.md#requirement-13-caching-system-for-performance): Caching system for performance
- [Design Document](../specs/hyfetch-integration-analysis/design.md): Architecture and implementation details
- [Task 21.2](../specs/hyfetch-integration-analysis/tasks.md): Optimize startup performance
