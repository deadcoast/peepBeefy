"""
Memory usage tests for hyfetch integration components.

Tests verify that memory footprint of gradients, caches, and other
components remains within acceptable bounds.

Requirements tested: 13.7
"""

import sys
import gc
from typing import Any

import pytest

from src.color_util import RGB
from src.color_scale import Scale, create_gradient
from src.color_presets import ColorPreset, load_presets
from src.banner import Banner, BannerMetadata


def get_size_bytes(obj: Any) -> int:
    """
    Recursively calculate the size of an object in bytes.
    
    This includes the object itself and all objects it references.
    """
    seen = set()
    
    def sizeof(o: Any) -> int:
        if id(o) in seen:
            return 0
        seen.add(id(o))
        
        size = sys.getsizeof(o)
        
        if isinstance(o, dict):
            size += sum(sizeof(k) + sizeof(v) for k, v in o.items())
        elif isinstance(o, (list, tuple, set, frozenset)):
            size += sum(sizeof(item) for item in o)
        elif hasattr(o, '__dict__'):
            size += sizeof(o.__dict__)
        elif hasattr(o, '__slots__'):
            size += sum(sizeof(getattr(o, slot)) for slot in o.__slots__ if hasattr(o, slot))
        
        return size
    
    return sizeof(obj)


def format_bytes(bytes_size: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


class TestGradientMemoryFootprint:
    """Test memory usage of gradient system."""
    
    def test_single_gradient_memory(self):
        """
        Test that a single gradient with default resolution uses acceptable memory.
        
        A gradient with 2 colors and resolution 300 should use < 60KB.
        """
        gc.collect()  # Clean up before measurement
        
        colors = ["#FF0000", "#0000FF"]
        gradient = Scale(colors, resolution=300)
        
        size = get_size_bytes(gradient)
        size_kb = size / 1024
        
        print(f"\nSingle gradient memory: {format_bytes(size)}")
        
        # Gradient should use less than 60KB (measured ~53KB)
        assert size_kb < 60, f"Gradient uses {size_kb:.2f}KB, expected < 60KB"
    
    def test_multiple_gradients_memory(self):
        """
        Test memory usage with multiple gradients (typical use case).
        
        10 gradients should use < 1MB total.
        """
        gc.collect()
        
        gradients = []
        color_sets = [
            ["#FF0000", "#00FF00", "#0000FF"],
            ["#FFFF00", "#FF00FF", "#00FFFF"],
            ["#FF8800", "#8800FF", "#00FF88"],
            ["#FF0088", "#88FF00", "#0088FF"],
            ["#880088", "#008888", "#888800"],
            ["#FF4444", "#44FF44", "#4444FF"],
            ["#FFAA00", "#00FFAA", "#AA00FF"],
            ["#FF6600", "#66FF00", "#0066FF"],
            ["#CC0000", "#00CC00", "#0000CC"],
            ["#FF9900", "#99FF00", "#0099FF"],
        ]
        
        for colors in color_sets:
            gradients.append(Scale(colors, resolution=300))
        
        total_size = sum(get_size_bytes(g) for g in gradients)
        size_kb = total_size / 1024
        
        print(f"\n10 gradients total memory: {format_bytes(total_size)}")
        
        # 10 gradients should use less than 1MB (measured ~970KB)
        assert size_kb < 1024, f"10 gradients use {size_kb:.2f}KB, expected < 1MB"
    
    def test_high_resolution_gradient_memory(self):
        """
        Test memory usage of high-resolution gradient.
        
        A gradient with resolution 1000 should still use < 500KB.
        """
        gc.collect()
        
        colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
        gradient = Scale(colors, resolution=1000)
        
        size = get_size_bytes(gradient)
        size_kb = size / 1024
        
        print(f"\nHigh-resolution gradient memory: {format_bytes(size)}")
        
        # High-res gradient should use less than 500KB (measured ~455KB)
        assert size_kb < 500, f"High-res gradient uses {size_kb:.2f}KB, expected < 500KB"
    
    def test_gradient_rgb_array_memory(self):
        """
        Test that pre-computed RGB array is the main memory consumer.
        
        The RGB array should account for > 80% of gradient memory.
        """
        gc.collect()
        
        colors = ["#FF0000", "#0000FF"]
        gradient = Scale(colors, resolution=300)
        
        total_size = get_size_bytes(gradient)
        rgb_array_size = get_size_bytes(gradient.rgb)
        
        percentage = (rgb_array_size / total_size) * 100
        
        print(f"\nRGB array: {format_bytes(rgb_array_size)} ({percentage:.1f}% of total)")
        
        # RGB array should be the dominant memory consumer
        assert percentage > 80, f"RGB array is only {percentage:.1f}% of memory, expected > 80%"


class TestBannerCacheMemory:
    """Test memory usage of banner caching system."""
    
    def test_single_banner_memory(self):
        """
        Test memory footprint of a single banner.
        
        A typical banner should use < 10KB.
        """
        gc.collect()
        
        banner = Banner(
            metadata=BannerMetadata(
                category="TEST",
                name="test_banner",
                dimensions=(7, 5),
            ),
            lines=["  ___  ", " / _ \\ ", "| | | |", "| |_| |", " \\___/ "]
        )
        
        size = get_size_bytes(banner)
        size_kb = size / 1024
        
        print(f"\nSingle banner memory: {format_bytes(size)}")
        
        # Single banner should use less than 10KB
        assert size_kb < 10, f"Banner uses {size_kb:.2f}KB, expected < 10KB"
    
    def test_banner_cache_memory(self):
        """
        Test memory usage of cached banners.
        
        A cache with 50 banners should use < 500KB.
        """
        gc.collect()
        
        # Create a realistic banner cache
        banners = []
        for i in range(50):
            banner = Banner(
                metadata=BannerMetadata(
                    category=f"CAT_{i % 5}",
                    name=f"banner_{i}",
                    dimensions=(20, 10),
                    author=f"Author {i}",
                    description=f"Test banner number {i}",
                ),
                lines=[f"Banner {i}" for _ in range(10)]  # 10 lines
            )
            banners.append(banner)
        
        cache = {"banners": banners}
        
        size = get_size_bytes(cache)
        size_kb = size / 1024
        
        print(f"\n50-banner cache memory: {format_bytes(size)}")
        
        # 50 banners should use less than 500KB
        assert size_kb < 500, f"Banner cache uses {size_kb:.2f}KB, expected < 500KB"
    
    def test_large_banner_memory(self):
        """
        Test memory usage of a large ASCII art banner.
        
        A large banner (50 lines, 100 chars wide) should use < 50KB.
        """
        gc.collect()
        
        # Create a large banner
        large_lines = ["X" * 100 for _ in range(50)]
        banner = Banner(
            metadata=BannerMetadata(
                category="LARGE",
                name="large_banner",
                dimensions=(100, 50),
            ),
            lines=large_lines
        )
        
        size = get_size_bytes(banner)
        size_kb = size / 1024
        
        print(f"\nLarge banner memory: {format_bytes(size)}")
        
        # Large banner should use less than 50KB
        assert size_kb < 50, f"Large banner uses {size_kb:.2f}KB, expected < 50KB"


class TestColorPresetMemory:
    """Test memory usage of color preset system."""
    
    def test_single_preset_memory(self):
        """
        Test memory footprint of a single color preset.
        
        A preset with 10 colors should use < 5KB.
        """
        gc.collect()
        
        preset = ColorPreset(
            name="test_preset",
            colors=["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF",
                   "#00FFFF", "#FF8800", "#8800FF", "#00FF88", "#880088"]
        )
        
        size = get_size_bytes(preset)
        size_kb = size / 1024
        
        print(f"\nSingle preset memory: {format_bytes(size)}")
        
        # Single preset should use less than 5KB
        assert size_kb < 5, f"Preset uses {size_kb:.2f}KB, expected < 5KB"
    
    def test_preset_collection_memory(self):
        """
        Test memory usage of a collection of presets.
        
        20 presets should use < 100KB.
        """
        gc.collect()
        
        presets = {}
        for i in range(20):
            presets[f"preset_{i}"] = ColorPreset(
                name=f"preset_{i}",
                colors=[f"#{j:02x}{(j*2)%256:02x}{(j*3)%256:02x}" for j in range(10)]
            )
        
        size = get_size_bytes(presets)
        size_kb = size / 1024
        
        print(f"\n20-preset collection memory: {format_bytes(size)}")
        
        # 20 presets should use less than 100KB
        assert size_kb < 100, f"Preset collection uses {size_kb:.2f}KB, expected < 100KB"
    
    def test_weighted_preset_memory(self):
        """
        Test memory usage of weighted presets.
        
        Weighted presets should not significantly increase memory usage.
        """
        gc.collect()
        
        preset_simple = ColorPreset(
            name="simple",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        preset_weighted = ColorPreset(
            name="weighted",
            colors=["#FF0000", "#00FF00", "#0000FF"],
            weights=[3, 2, 1]
        )
        
        size_simple = get_size_bytes(preset_simple)
        size_weighted = get_size_bytes(preset_weighted)
        
        overhead = size_weighted - size_simple
        
        print(f"\nSimple preset: {format_bytes(size_simple)}")
        print(f"Weighted preset: {format_bytes(size_weighted)}")
        print(f"Overhead: {format_bytes(overhead)}")
        
        # Weighted preset should add < 1KB overhead
        assert overhead < 1024, f"Weighted preset adds {overhead}B overhead, expected < 1KB"


class TestTotalMemoryOverhead:
    """Test total memory overhead of all hyfetch integration components."""
    
    def test_typical_usage_memory(self):
        """
        Test memory usage in a typical usage scenario.
        
        Total memory overhead should be < 3MB for:
        - 5 gradients
        - 20 banners in cache
        - 10 color presets
        """
        gc.collect()
        
        # Create typical usage scenario
        components = {}
        
        # 5 gradients
        components['gradients'] = [
            Scale(["#FF0000", "#00FF00", "#0000FF"], resolution=300)
            for _ in range(5)
        ]
        
        # 20 banners
        components['banners'] = [
            Banner(
                metadata=BannerMetadata(
                    category=f"CAT_{i % 5}",
                    name=f"banner_{i}",
                    dimensions=(20, 10),
                ),
                lines=[f"Banner {i}" for _ in range(10)]
            )
            for i in range(20)
        ]
        
        # 10 presets
        components['presets'] = {
            f"preset_{i}": ColorPreset(
                name=f"preset_{i}",
                colors=[f"#{j:02x}{(j*2)%256:02x}{(j*3)%256:02x}" for j in range(8)]
            )
            for i in range(10)
        }
        
        total_size = get_size_bytes(components)
        size_mb = total_size / (1024 * 1024)
        
        print(f"\nTypical usage total memory: {format_bytes(total_size)}")
        
        # Total should be less than 3MB
        assert size_mb < 3, f"Total memory is {size_mb:.2f}MB, expected < 3MB"
    
    def test_memory_per_component_breakdown(self):
        """
        Test and report memory breakdown by component type.
        
        This helps identify which components are the largest consumers.
        """
        gc.collect()
        
        # Create components
        gradients = [Scale(["#FF0000", "#0000FF"], resolution=300) for _ in range(5)]
        banners = [
            Banner(
                metadata=BannerMetadata(category="TEST", name=f"b{i}", dimensions=(10, 10)),
                lines=["Test" for _ in range(10)]
            )
            for i in range(20)
        ]
        presets = {
            f"p{i}": ColorPreset(name=f"p{i}", colors=[f"#{j:02x}0000" for j in range(8)])
            for i in range(10)
        }
        
        # Measure each component type
        gradient_size = sum(get_size_bytes(g) for g in gradients)
        banner_size = sum(get_size_bytes(b) for b in banners)
        preset_size = get_size_bytes(presets)
        
        total = gradient_size + banner_size + preset_size
        
        print(f"\nMemory breakdown:")
        print(f"  Gradients (5):  {format_bytes(gradient_size)} ({gradient_size/total*100:.1f}%)")
        print(f"  Banners (20):   {format_bytes(banner_size)} ({banner_size/total*100:.1f}%)")
        print(f"  Presets (10):   {format_bytes(preset_size)} ({preset_size/total*100:.1f}%)")
        print(f"  Total:          {format_bytes(total)}")
        
        # Verify total is reasonable (< 3MB)
        assert total < 3 * 1024 * 1024, f"Total memory {format_bytes(total)} exceeds 3MB"
    
    def test_memory_growth_with_scale(self):
        """
        Test that memory usage scales linearly with component count.
        
        Doubling components should roughly double memory usage.
        """
        gc.collect()
        
        # Baseline: 5 gradients
        gradients_5 = [Scale(["#FF0000", "#0000FF"], resolution=300) for _ in range(5)]
        size_5 = sum(get_size_bytes(g) for g in gradients_5)
        
        # Double: 10 gradients
        gradients_10 = [Scale(["#FF0000", "#0000FF"], resolution=300) for _ in range(10)]
        size_10 = sum(get_size_bytes(g) for g in gradients_10)
        
        ratio = size_10 / size_5
        
        print(f"\n5 gradients:  {format_bytes(size_5)}")
        print(f"10 gradients: {format_bytes(size_10)}")
        print(f"Ratio: {ratio:.2f}x")
        
        # Ratio should be close to 2.0 (within 20% tolerance)
        assert 1.8 < ratio < 2.2, f"Memory scaling ratio {ratio:.2f}x not close to 2.0x"


class TestMemoryLeaks:
    """Test for potential memory leaks in component lifecycle."""
    
    def test_gradient_cleanup(self):
        """
        Test that gradients are properly garbage collected.
        
        Creating and destroying gradients should not leak memory.
        """
        gc.collect()
        
        # Baseline memory
        baseline = len(gc.get_objects())
        
        # Create and destroy gradients
        for _ in range(100):
            gradient = Scale(["#FF0000", "#0000FF"], resolution=300)
            _ = gradient(0.5)  # Use the gradient
            del gradient
        
        gc.collect()
        
        # Check object count
        after = len(gc.get_objects())
        growth = after - baseline
        
        print(f"\nObject count growth: {growth}")
        
        # Object count should not grow significantly (< 50 objects)
        assert growth < 50, f"Object count grew by {growth}, possible memory leak"
    
    def test_preset_cleanup(self):
        """
        Test that presets are properly garbage collected.
        """
        gc.collect()
        
        baseline = len(gc.get_objects())
        
        # Create and destroy presets
        for i in range(100):
            preset = ColorPreset(
                name=f"temp_{i}",
                colors=["#FF0000", "#00FF00", "#0000FF"]
            )
            _ = preset.expand_colors()
            del preset
        
        gc.collect()
        
        after = len(gc.get_objects())
        growth = after - baseline
        
        print(f"\nObject count growth: {growth}")
        
        # Object count should not grow significantly
        assert growth < 50, f"Object count grew by {growth}, possible memory leak"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
