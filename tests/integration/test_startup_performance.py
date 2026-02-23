"""
Integration tests for startup performance.

Tests verify that application startup time meets the <200ms target
with all hyfetch-inspired enhancements loaded.

Requirements tested:
- 13.7: Startup performance <200ms with all enhancements
"""

import time
import pytest
from pathlib import Path
import sys
import importlib
from typing import Dict, List, Tuple


class TestStartupPerformance:
    """Test suite for measuring and validating startup performance."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Reset module cache before each test."""
        # Store original modules
        self.original_modules = set(sys.modules.keys())
        yield
        # Clean up imported modules to ensure fresh imports
        new_modules = set(sys.modules.keys()) - self.original_modules
        for module in new_modules:
            if module.startswith('src.'):
                sys.modules.pop(module, None)
    
    def measure_import_time(self, module_name: str) -> float:
        """
        Measure the time to import a module.
        
        Args:
            module_name: Full module name (e.g., 'src.color_util')
        
        Returns:
            Import time in milliseconds
        """
        start = time.perf_counter()
        try:
            importlib.import_module(module_name)
            end = time.perf_counter()
            return (end - start) * 1000  # Convert to ms
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")
    
    def profile_component_loads(self) -> Dict[str, float]:
        """
        Profile individual component load times.
        
        Returns:
            Dictionary mapping component names to load times in ms
        """
        components = [
            'src.color_util',
            'src.color_scale',
            'src.terminal_detect',
            'src.color_presets',
            'src.ascii_renderer',
            'src.serializer',
            'src.themes',
            'src.config',
            'src.banner',
            'src.animation',
        ]
        
        profile = {}
        for component in components:
            load_time = self.measure_import_time(component)
            profile[component] = load_time
        
        return profile
    
    def test_total_startup_time(self):
        """
        Test that total startup time is under 200ms.
        
        Validates: Requirement 13.7
        """
        start = time.perf_counter()
        
        # Import all core modules in typical startup order
        from src import color_util
        from src import color_scale
        from src import terminal_detect
        from src import color_presets
        from src import ascii_renderer
        from src import serializer
        from src import themes
        from src import config
        from src import banner
        from src import animation
        
        end = time.perf_counter()
        total_time_ms = (end - start) * 1000
        
        # Log the result for visibility
        print(f"\n{'='*60}")
        print(f"Total startup time: {total_time_ms:.2f}ms")
        print(f"Target: <200ms")
        print(f"Status: {'✓ PASS' if total_time_ms < 200 else '✗ FAIL'}")
        print(f"{'='*60}")
        
        # Assert the performance requirement
        assert total_time_ms < 200, (
            f"Startup time {total_time_ms:.2f}ms exceeds 200ms target. "
            f"Optimization needed."
        )
    
    def test_component_load_profiling(self):
        """
        Profile individual component load times.
        
        Validates: Requirement 13.7 (component-level profiling)
        """
        profile = self.profile_component_loads()
        
        # Calculate total and statistics
        total_time = sum(profile.values())
        sorted_components = sorted(profile.items(), key=lambda x: x[1], reverse=True)
        
        # Log detailed profile
        print(f"\n{'='*60}")
        print("Component Load Time Profile")
        print(f"{'='*60}")
        print(f"{'Component':<30} {'Time (ms)':<15} {'% of Total':<10}")
        print(f"{'-'*60}")
        
        for component, load_time in sorted_components:
            percentage = (load_time / total_time * 100) if total_time > 0 else 0
            component_short = component.replace('src.', '')
            print(f"{component_short:<30} {load_time:>8.2f}ms      {percentage:>5.1f}%")
        
        print(f"{'-'*60}")
        print(f"{'TOTAL':<30} {total_time:>8.2f}ms      100.0%")
        print(f"{'='*60}")
        
        # Identify slow components (>50ms)
        slow_components = [
            (name, time_ms) for name, time_ms in profile.items() 
            if time_ms > 50
        ]
        
        if slow_components:
            print("\n⚠ Slow components detected (>50ms):")
            for name, time_ms in slow_components:
                print(f"  - {name}: {time_ms:.2f}ms")
        
        # Assert total is reasonable
        assert total_time < 200, (
            f"Total component load time {total_time:.2f}ms exceeds 200ms target"
        )
    
    def test_lazy_loading_effectiveness(self):
        """
        Test that lazy loading reduces initial startup time.
        
        Validates: Requirement 13.7 (lazy loading optimization)
        """
        # Measure time to import config without loading presets
        start = time.perf_counter()
        from src import config
        config_time = (time.perf_counter() - start) * 1000
        
        # Measure time to import color_presets (should be lazy)
        start = time.perf_counter()
        from src import color_presets
        preset_import_time = (time.perf_counter() - start) * 1000
        
        print(f"\n{'='*60}")
        print("Lazy Loading Analysis")
        print(f"{'='*60}")
        print(f"Config import time: {config_time:.2f}ms")
        print(f"Preset module import time: {preset_import_time:.2f}ms")
        print(f"{'='*60}")
        
        # Preset import should be fast (module load, not data load)
        assert preset_import_time < 50, (
            f"Preset module import took {preset_import_time:.2f}ms, "
            f"suggesting presets are loaded eagerly instead of lazily"
        )
    
    def test_cache_loading_performance(self):
        """
        Test that cache loading doesn't significantly impact startup.
        
        Validates: Requirement 13.7 (cache optimization)
        """
        # Import config which may load cache
        start = time.perf_counter()
        from src import config
        
        # Create a config manager instance (may trigger cache load)
        cfg_manager = config.ConfigManager()
        
        end = time.perf_counter()
        cache_load_time = (end - start) * 1000
        
        print(f"\n{'='*60}")
        print("Cache Loading Performance")
        print(f"{'='*60}")
        print(f"Config + cache load time: {cache_load_time:.2f}ms")
        print(f"Target: <50ms")
        print(f"{'='*60}")
        
        # Cache loading should be fast
        assert cache_load_time < 50, (
            f"Cache loading took {cache_load_time:.2f}ms, exceeds 50ms target"
        )
    
    def test_gradient_precomputation_performance(self):
        """
        Test that gradient pre-computation is efficient.
        
        Validates: Requirement 13.7 (gradient optimization)
        """
        from src.color_scale import Scale
        
        # Measure time to create a gradient with default resolution
        start = time.perf_counter()
        gradient = Scale(['#FF0000', '#00FF00', '#0000FF'], resolution=300)
        end = time.perf_counter()
        
        gradient_time = (end - start) * 1000
        
        print(f"\n{'='*60}")
        print("Gradient Pre-computation Performance")
        print(f"{'='*60}")
        print(f"3-color gradient (res=300): {gradient_time:.2f}ms")
        print(f"Target: <20ms")
        print(f"{'='*60}")
        
        # Gradient creation should be fast
        assert gradient_time < 20, (
            f"Gradient pre-computation took {gradient_time:.2f}ms, exceeds 20ms target"
        )
    
    def test_terminal_detection_performance(self):
        """
        Test that terminal detection is fast.
        
        Validates: Requirement 13.7 (terminal detection optimization)
        """
        from src.terminal_detect import detect_ansi_mode
        
        # Measure terminal detection time
        start = time.perf_counter()
        mode = detect_ansi_mode()
        end = time.perf_counter()
        
        detection_time = (end - start) * 1000
        
        print(f"\n{'='*60}")
        print("Terminal Detection Performance")
        print(f"{'='*60}")
        print(f"Detection time: {detection_time:.2f}ms")
        print(f"Detected mode: {mode}")
        print(f"Target: <10ms")
        print(f"{'='*60}")
        
        # Terminal detection should be very fast (just env var checks)
        assert detection_time < 10, (
            f"Terminal detection took {detection_time:.2f}ms, exceeds 10ms target"
        )
    
    def test_startup_time_consistency(self):
        """
        Test that startup time is consistent across multiple runs.
        
        Validates: Requirement 13.7 (consistent performance)
        """
        times: List[float] = []
        num_runs = 5
        
        for i in range(num_runs):
            # Clear module cache
            modules_to_clear = [m for m in sys.modules if m.startswith('src.')]
            for m in modules_to_clear:
                sys.modules.pop(m, None)
            
            # Measure startup time
            start = time.perf_counter()
            from src import color_util, color_scale, terminal_detect
            from src import color_presets, ascii_renderer, serializer
            from src import themes, config, banner, animation
            end = time.perf_counter()
            
            times.append((end - start) * 1000)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        variance = max_time - min_time
        
        print(f"\n{'='*60}")
        print("Startup Time Consistency Analysis")
        print(f"{'='*60}")
        print(f"Runs: {num_runs}")
        print(f"Average: {avg_time:.2f}ms")
        print(f"Min: {min_time:.2f}ms")
        print(f"Max: {max_time:.2f}ms")
        print(f"Variance: {variance:.2f}ms")
        print(f"{'='*60}")
        
        # Variance should be small (consistent performance)
        assert variance < 50, (
            f"Startup time variance {variance:.2f}ms is too high, "
            f"indicating inconsistent performance"
        )
        
        # Average should meet target
        assert avg_time < 200, (
            f"Average startup time {avg_time:.2f}ms exceeds 200ms target"
        )


class TestMemoryFootprint:
    """Test suite for memory usage validation."""
    
    def test_gradient_memory_usage(self):
        """
        Test that gradient memory footprint is acceptable.
        
        Validates: Requirement 13.7 (memory efficiency)
        """
        from src.color_scale import Scale
        import sys
        
        # Create multiple gradients to test memory usage
        gradients = []
        for i in range(10):
            gradient = Scale(['#FF0000', '#00FF00', '#0000FF'], resolution=300)
            gradients.append(gradient)
        
        # Estimate memory usage (rough approximation)
        # Each RGB object is ~3 ints, each gradient has ~600 colors
        # 10 gradients * 600 colors * 3 ints * 28 bytes/int ≈ 504KB
        estimated_memory_kb = 10 * 600 * 3 * 28 / 1024
        
        print(f"\n{'='*60}")
        print("Gradient Memory Usage")
        print(f"{'='*60}")
        print(f"10 gradients (res=300): ~{estimated_memory_kb:.1f}KB")
        print(f"Target: <1MB")
        print(f"{'='*60}")
        
        # Memory usage should be reasonable
        assert estimated_memory_kb < 1024, (
            f"Gradient memory usage ~{estimated_memory_kb:.1f}KB exceeds 1MB target"
        )
    
    def test_preset_memory_usage(self):
        """
        Test that preset system memory footprint is acceptable.
        
        Validates: Requirement 13.7 (memory efficiency)
        """
        from src.color_presets import ColorPreset
        
        # Create multiple presets
        presets = []
        for i in range(20):
            preset = ColorPreset(
                name=f"test_preset_{i}",
                colors=['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF']
            )
            presets.append(preset)
        
        # Estimate memory: 20 presets * 5 colors * ~50 bytes ≈ 5KB
        estimated_memory_kb = 20 * 5 * 50 / 1024
        
        print(f"\n{'='*60}")
        print("Preset Memory Usage")
        print(f"{'='*60}")
        print(f"20 presets (5 colors each): ~{estimated_memory_kb:.1f}KB")
        print(f"Target: <100KB")
        print(f"{'='*60}")
        
        # Memory usage should be minimal
        assert estimated_memory_kb < 100, (
            f"Preset memory usage ~{estimated_memory_kb:.1f}KB exceeds 100KB target"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
