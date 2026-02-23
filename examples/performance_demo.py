"""Demonstration of performance optimizations.

This script shows the performance benefits of lazy loading,
caching, and efficient data structures.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.color_presets import load_presets, get_presets_lazy, clear_preset_cache
from src.color_scale import create_gradient, clear_gradient_cache, get_gradient_cache_stats
from src.color_util import RGB


def demo_lazy_loading():
    """Demonstrate lazy loading benefits."""
    print("=" * 60)
    print("Lazy Loading Demo")
    print("=" * 60)
    print()
    
    # Clear cache to start fresh
    clear_preset_cache()
    
    preset_file = Path("data/color_presets.json")
    
    # Eager loading (traditional approach)
    print("1. Eager loading (load immediately):")
    start = time.perf_counter()
    presets_eager = load_presets(preset_file)
    eager_time = (time.perf_counter() - start) * 1000
    print(f"   Time: {eager_time:.2f}ms")
    print(f"   Loaded: {len(presets_eager)} presets")
    print()
    
    # Lazy loading (first call)
    print("2. Lazy loading (first call - loads from disk):")
    clear_preset_cache()
    start = time.perf_counter()
    presets_lazy1 = get_presets_lazy(preset_file)
    lazy_time1 = (time.perf_counter() - start) * 1000
    print(f"   Time: {lazy_time1:.2f}ms")
    print(f"   Loaded: {len(presets_lazy1)} presets")
    print()
    
    # Lazy loading (second call - uses cache)
    print("3. Lazy loading (second call - uses cache):")
    start = time.perf_counter()
    presets_lazy2 = get_presets_lazy(preset_file)
    lazy_time2 = (time.perf_counter() - start) * 1000
    print(f"   Time: {lazy_time2:.2f}ms")
    print(f"   Speedup: {lazy_time1 / lazy_time2:.1f}x faster")
    print()
    
    print(f"✓ Lazy loading with cache is {lazy_time1 / lazy_time2:.1f}x faster on subsequent calls")
    print()


def demo_gradient_caching():
    """Demonstrate gradient caching benefits."""
    print("=" * 60)
    print("Gradient Caching Demo")
    print("=" * 60)
    print()
    
    # Clear cache to start fresh
    clear_gradient_cache()
    
    colors = [
        RGB(255, 0, 0),    # Red
        RGB(255, 165, 0),  # Orange
        RGB(255, 255, 0),  # Yellow
        RGB(0, 255, 0),    # Green
        RGB(0, 0, 255),    # Blue
    ]
    resolution = 300
    
    # First gradient creation (no cache)
    print("1. First gradient creation (no cache):")
    start = time.perf_counter()
    gradient1 = create_gradient(colors, resolution)
    time1 = (time.perf_counter() - start) * 1000
    print(f"   Time: {time1:.2f}ms")
    print(f"   Length: {len(gradient1)} colors")
    stats = get_gradient_cache_stats()
    print(f"   Cache size: {stats['size']} gradients")
    print()
    
    # Second gradient creation (uses cache)
    print("2. Second gradient creation (uses cache):")
    start = time.perf_counter()
    gradient2 = create_gradient(colors, resolution)
    time2 = (time.perf_counter() - start) * 1000
    print(f"   Time: {time2:.2f}ms")
    print(f"   Speedup: {time1 / time2:.1f}x faster")
    print(f"   Same object: {gradient1 is gradient2}")
    print()
    
    # Create multiple different gradients
    print("3. Creating 10 different gradients:")
    start = time.perf_counter()
    for i in range(10):
        # Create slightly different gradients
        test_colors = [
            RGB(255, i * 10, 0),
            RGB(0, 255, i * 10),
            RGB(0, 0, 255)
        ]
        create_gradient(test_colors, 100)
    time3 = (time.perf_counter() - start) * 1000
    stats = get_gradient_cache_stats()
    print(f"   Time: {time3:.2f}ms")
    print(f"   Cache size: {stats['size']} gradients")
    print(f"   Memory usage: {stats['memory_mb']:.2f} MB")
    print()
    
    # Reuse cached gradients
    print("4. Reusing 10 cached gradients:")
    start = time.perf_counter()
    for i in range(10):
        test_colors = [
            RGB(255, i * 10, 0),
            RGB(0, 255, i * 10),
            RGB(0, 0, 255)
        ]
        create_gradient(test_colors, 100)
    time4 = (time.perf_counter() - start) * 1000
    print(f"   Time: {time4:.2f}ms")
    print(f"   Speedup: {time3 / time4:.1f}x faster")
    print()
    
    print(f"✓ Gradient caching provides {time3 / time4:.1f}x speedup for repeated gradients")
    print()


def demo_startup_simulation():
    """Simulate startup with and without optimizations."""
    print("=" * 60)
    print("Startup Simulation")
    print("=" * 60)
    print()
    
    # Scenario 1: Without optimizations (eager loading)
    print("1. Without optimizations (eager loading):")
    clear_preset_cache()
    clear_gradient_cache()
    
    start = time.perf_counter()
    
    # Load presets eagerly
    presets = load_presets(Path("data/color_presets.json"))
    
    # Create some gradients
    for preset_name in list(presets.keys())[:5]:
        preset = presets[preset_name]
        colors = [RGB.from_hex(c) for c in preset.colors[:3]]
        create_gradient(colors, 300)
    
    time_without = (time.perf_counter() - start) * 1000
    print(f"   Time: {time_without:.2f}ms")
    print()
    
    # Scenario 2: With optimizations (lazy loading + caching)
    print("2. With optimizations (lazy loading + caching):")
    clear_preset_cache()
    clear_gradient_cache()
    
    start = time.perf_counter()
    
    # Presets not loaded yet (lazy)
    # Gradients will be cached
    
    # Simulate actual usage (only load what's needed)
    presets = get_presets_lazy()
    preset = presets["fire"]
    colors = [RGB.from_hex(c) for c in preset.colors[:3]]
    gradient = create_gradient(colors, 300)
    
    time_with = (time.perf_counter() - start) * 1000
    print(f"   Time: {time_with:.2f}ms")
    print(f"   Speedup: {time_without / time_with:.1f}x faster")
    print()
    
    print(f"✓ Optimizations provide {time_without / time_with:.1f}x speedup at startup")
    print()


def main():
    """Run all performance demos."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "Performance Optimization Demo" + " " * 14 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    demo_lazy_loading()
    demo_gradient_caching()
    demo_startup_simulation()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print()
    print("Key optimizations demonstrated:")
    print("  1. Lazy loading: Load data only when needed")
    print("  2. Caching: Reuse computed results")
    print("  3. Efficient data structures: Pre-computed gradients")
    print()
    print("These optimizations help achieve the <200ms startup target")
    print("while maintaining full functionality.")
    print()


if __name__ == "__main__":
    main()
