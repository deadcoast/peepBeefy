"""Profile startup performance for peepBeefy banner system.

This script measures the time taken for various startup operations
to ensure we meet the <200ms target for banner display.
"""

import time
import cProfile
import pstats
from pathlib import Path
from io import StringIO

# Setup logging
from src.logging_config import setup_logging
setup_logging(debug=False)

from src.config import ConfigManager
from src.themes import ThemeRegistry
from src.banner import BannerDatabase, BannerRenderer
from rich.console import Console


def profile_startup():
    """Profile the complete startup sequence."""
    console = Console()
    
    print("=" * 60)
    print("peepBeefy Startup Performance Profile")
    print("=" * 60)
    print()
    
    # 1. Config loading
    start = time.perf_counter()
    config_manager = ConfigManager()
    config = config_manager.load()
    config_time = (time.perf_counter() - start) * 1000
    print(f"✓ Config loading: {config_time:.2f}ms")
    
    # 2. Theme loading
    start = time.perf_counter()
    theme = ThemeRegistry.get_theme(config.theme_variant)
    theme_time = (time.perf_counter() - start) * 1000
    print(f"✓ Theme loading: {theme_time:.2f}ms")
    
    # 3. Banner database initialization
    start = time.perf_counter()
    assets_dir = Path(".assets")
    banner_db = BannerDatabase(assets_dir)
    db_init_time = (time.perf_counter() - start) * 1000
    print(f"✓ Banner DB init: {db_init_time:.2f}ms")
    
    # 4. Banner loading (first time - no cache)
    start = time.perf_counter()
    banners = banner_db.load_banners(force_reload=True)
    load_time = (time.perf_counter() - start) * 1000
    print(f"✓ Banner loading (no cache): {load_time:.2f}ms")
    
    # 5. Banner loading (with cache)
    start = time.perf_counter()
    banners = banner_db.load_banners(force_reload=False)
    cache_time = (time.perf_counter() - start) * 1000
    print(f"✓ Banner loading (cached): {cache_time:.2f}ms")
    
    # 6. Banner selection
    start = time.perf_counter()
    renderer = BannerRenderer(theme)
    banner = renderer.select_banner_with_adaptation(banner_db, console, config)
    select_time = (time.perf_counter() - start) * 1000
    print(f"✓ Banner selection: {select_time:.2f}ms")
    
    # 7. Static rendering
    start = time.perf_counter()
    panel = renderer.render_static(banner, console)
    render_time = (time.perf_counter() - start) * 1000
    print(f"✓ Static rendering: {render_time:.2f}ms")
    
    # Calculate totals
    print()
    print("-" * 60)
    total_first_run = config_time + theme_time + db_init_time + load_time + select_time + render_time
    total_cached = config_time + theme_time + db_init_time + cache_time + select_time + render_time
    
    print(f"Total (first run):  {total_first_run:.2f}ms")
    print(f"Total (cached):     {total_cached:.2f}ms")
    print()
    
    # Check against target
    target = 200.0
    if total_cached <= target:
        print(f"✓ PASS: Cached startup is within {target}ms target")
    else:
        print(f"✗ FAIL: Cached startup exceeds {target}ms target by {total_cached - target:.2f}ms")
    
    print()
    print("=" * 60)
    
    return total_cached <= target


def detailed_profile():
    """Run detailed cProfile analysis."""
    print()
    print("Running detailed cProfile analysis...")
    print()
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run the startup sequence
    console = Console()
    config_manager = ConfigManager()
    config = config_manager.load()
    theme = ThemeRegistry.get_theme(config.theme_variant)
    assets_dir = Path(".assets")
    banner_db = BannerDatabase(assets_dir)
    banners = banner_db.load_banners()
    renderer = BannerRenderer(theme)
    banner = renderer.select_banner_with_adaptation(banner_db, console, config)
    panel = renderer.render_static(banner, console)
    
    profiler.disable()
    
    # Print stats
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    print(s.getvalue())


if __name__ == "__main__":
    # Run basic profiling
    passed = profile_startup()
    
    # Run detailed profiling if requested
    import sys
    if "--detailed" in sys.argv:
        detailed_profile()
    
    sys.exit(0 if passed else 1)
