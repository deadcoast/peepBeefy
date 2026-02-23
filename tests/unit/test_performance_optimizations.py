"""Tests for performance optimization features.

This module tests lazy loading, caching, and other performance
optimizations added to meet the <200ms startup target.
"""

import pytest
from pathlib import Path
import json

from src.color_presets import (
    load_presets,
    get_presets_lazy,
    clear_preset_cache,
    ColorPreset
)
from src.color_scale import (
    create_gradient,
    clear_gradient_cache,
    get_gradient_cache_stats,
    Scale
)
from src.color_util import RGB


class TestLazyPresetLoading:
    """Test lazy loading of color presets."""
    
    def test_get_presets_lazy_loads_on_first_call(self, tmp_path):
        """Test that get_presets_lazy loads presets on first call."""
        clear_preset_cache()
        
        # Create test preset file
        preset_file = tmp_path / "test_presets.json"
        preset_data = {
            "test": ["#FF0000", "#00FF00", "#0000FF"]
        }
        preset_file.write_text(json.dumps(preset_data))
        
        # First call should load from disk
        presets = get_presets_lazy(preset_file)
        
        assert len(presets) == 1
        assert "test" in presets
        assert len(presets["test"].colors) == 3
    
    def test_get_presets_lazy_uses_cache_on_second_call(self, tmp_path):
        """Test that get_presets_lazy uses cache on subsequent calls."""
        clear_preset_cache()
        
        # Create test preset file
        preset_file = tmp_path / "test_presets.json"
        preset_data = {
            "test": ["#FF0000", "#00FF00", "#0000FF"]
        }
        preset_file.write_text(json.dumps(preset_data))
        
        # First call
        presets1 = get_presets_lazy(preset_file)
        
        # Second call should return same object (cached)
        presets2 = get_presets_lazy(preset_file)
        
        assert presets1 is presets2
    
    def test_get_presets_lazy_uses_default_file(self):
        """Test that get_presets_lazy uses default file when not specified."""
        clear_preset_cache()
        
        # Should load from data/color_presets.json
        presets = get_presets_lazy()
        
        assert len(presets) > 0
        assert "rainbow" in presets
    
    def test_clear_preset_cache_clears_cache(self, tmp_path):
        """Test that clear_preset_cache clears the cache."""
        clear_preset_cache()
        
        # Create test preset file
        preset_file = tmp_path / "test_presets.json"
        preset_data = {
            "test": ["#FF0000", "#00FF00", "#0000FF"]
        }
        preset_file.write_text(json.dumps(preset_data))
        
        # Load presets
        presets1 = get_presets_lazy(preset_file)
        
        # Clear cache
        clear_preset_cache()
        
        # Load again - should be different object
        presets2 = get_presets_lazy(preset_file)
        
        assert presets1 is not presets2
        assert len(presets1) == len(presets2)


class TestGradientCaching:
    """Test gradient caching functionality."""
    
    def test_create_gradient_caches_result(self):
        """Test that create_gradient caches the result."""
        clear_gradient_cache()
        
        colors = [RGB(255, 0, 0), RGB(0, 0, 255)]
        resolution = 100
        
        # First call
        gradient1 = create_gradient(colors, resolution)
        
        # Second call with same parameters
        gradient2 = create_gradient(colors, resolution)
        
        # Should return same cached object
        assert gradient1 is gradient2
    
    def test_create_gradient_different_params_creates_new(self):
        """Test that different parameters create new gradients."""
        clear_gradient_cache()
        
        colors = [RGB(255, 0, 0), RGB(0, 0, 255)]
        
        # Create with different resolutions
        gradient1 = create_gradient(colors, 100)
        gradient2 = create_gradient(colors, 200)
        
        # Should be different objects
        assert gradient1 is not gradient2
        assert len(gradient1) != len(gradient2)
    
    def test_clear_gradient_cache_clears_cache(self):
        """Test that clear_gradient_cache clears the cache."""
        clear_gradient_cache()
        
        colors = [RGB(255, 0, 0), RGB(0, 0, 255)]
        resolution = 100
        
        # Create gradient
        gradient1 = create_gradient(colors, resolution)
        
        # Clear cache
        clear_gradient_cache()
        
        # Create again - should be different object
        gradient2 = create_gradient(colors, resolution)
        
        assert gradient1 is not gradient2
        assert len(gradient1) == len(gradient2)
    
    def test_get_gradient_cache_stats_returns_stats(self):
        """Test that get_gradient_cache_stats returns correct statistics."""
        clear_gradient_cache()
        
        # Create some gradients
        colors1 = [RGB(255, 0, 0), RGB(0, 0, 255)]
        colors2 = [RGB(0, 255, 0), RGB(255, 255, 0)]
        
        create_gradient(colors1, 100)
        create_gradient(colors2, 100)
        
        stats = get_gradient_cache_stats()
        
        assert stats["size"] == 2
        assert stats["memory_estimate"] > 0
        assert stats["memory_mb"] > 0
    
    def test_gradient_cache_with_scale_class(self):
        """Test that Scale class benefits from gradient caching."""
        clear_gradient_cache()
        
        colors = ["#FF0000", "#00FF00", "#0000FF"]
        resolution = 300
        
        # Create first scale
        scale1 = Scale(colors, resolution)
        
        # Create second scale with same parameters
        scale2 = Scale(colors, resolution)
        
        # Internal gradients should be cached (same object)
        assert scale1.rgb is scale2.rgb


class TestCacheMemoryUsage:
    """Test that caching doesn't use excessive memory."""
    
    def test_gradient_cache_memory_reasonable(self):
        """Test that gradient cache memory usage is reasonable."""
        clear_gradient_cache()
        
        # Create 100 different gradients
        for i in range(100):
            colors = [
                RGB(i * 2, 0, 0),
                RGB(0, i * 2, 0),
                RGB(0, 0, i * 2)
            ]
            create_gradient(colors, 100)
        
        stats = get_gradient_cache_stats()
        
        # Should be less than 10MB for 100 gradients
        assert stats["memory_mb"] < 10.0
        assert stats["size"] == 100


class TestBackwardCompatibility:
    """Test that optimizations maintain backward compatibility."""
    
    def test_load_presets_still_works(self, tmp_path):
        """Test that original load_presets function still works."""
        preset_file = tmp_path / "test_presets.json"
        preset_data = {
            "test": ["#FF0000", "#00FF00", "#0000FF"]
        }
        preset_file.write_text(json.dumps(preset_data))
        
        # Original function should still work
        presets = load_presets(preset_file)
        
        assert len(presets) == 1
        assert "test" in presets
    
    def test_create_gradient_still_works(self):
        """Test that create_gradient still works as before."""
        colors = [RGB(255, 0, 0), RGB(0, 0, 255)]
        resolution = 100
        
        gradient = create_gradient(colors, resolution)
        
        assert len(gradient) == 100
        assert gradient[0] == RGB(255, 0, 0)
        # Last color is close to target (interpolation doesn't include final point)
        assert gradient[-1].b > 250  # Very close to blue
    
    def test_scale_class_still_works(self):
        """Test that Scale class still works as before."""
        colors = ["#FF0000", "#00FF00", "#0000FF"]
        
        scale = Scale(colors, resolution=300)
        
        # Test ratio lookup
        red = scale(0.0)
        blue = scale(1.0)
        
        assert red.r == 255
        # Blue component should be very close to 255 (within rounding tolerance)
        assert blue.b >= 254


class TestPerformanceImprovements:
    """Test that optimizations actually improve performance."""
    
    def test_lazy_loading_faster_on_second_call(self, tmp_path):
        """Test that lazy loading is faster on second call."""
        import time
        
        clear_preset_cache()
        
        preset_file = tmp_path / "test_presets.json"
        preset_data = {
            f"preset{i}": [f"#{i:02x}0000", f"#00{i:02x}00", f"#0000{i:02x}"]
            for i in range(20)
        }
        preset_file.write_text(json.dumps(preset_data))
        
        # First call
        start1 = time.perf_counter()
        presets1 = get_presets_lazy(preset_file)
        time1 = time.perf_counter() - start1
        
        # Second call
        start2 = time.perf_counter()
        presets2 = get_presets_lazy(preset_file)
        time2 = time.perf_counter() - start2
        
        # Second call should be significantly faster
        assert time2 < time1 * 0.5  # At least 2x faster
    
    def test_gradient_caching_faster_on_second_call(self):
        """Test that gradient caching is faster on second call."""
        import time
        
        clear_gradient_cache()
        
        colors = [RGB(255, 0, 0), RGB(0, 255, 0), RGB(0, 0, 255)]
        resolution = 1000
        
        # First call
        start1 = time.perf_counter()
        gradient1 = create_gradient(colors, resolution)
        time1 = time.perf_counter() - start1
        
        # Second call
        start2 = time.perf_counter()
        gradient2 = create_gradient(colors, resolution)
        time2 = time.perf_counter() - start2
        
        # Second call should be significantly faster
        assert time2 < time1 * 0.1  # At least 10x faster
