"""Profile peepBeefy startup performance.

This script measures the time taken for various startup operations
to identify bottlenecks and ensure the <200ms target is met.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def profile_startup():
    """Profile startup operations and report timings."""
    
    print("=" * 60)
    print("peepBeefy Startup Performance Profile")
    print("=" * 60)
    print()
    
    # Total startup timer
    total_start = time.perf_counter()
    
    # 1. Import modules
    import_start = time.perf_counter()
    from config import ConfigManager
    from banner import BannerDatabase, BannerRenderer
    from themes import ThemeRegistry
    import_time = (time.perf_counter() - import_start) * 1000
    print(f"✓ Module imports: {import_time:.2f}ms")
    
    # 2. Load configuration
    config_start = time.perf_counter()
    config_manager = ConfigManager()
    config = config_manager.load()
    config_time = (time.perf_counter() - config_start) * 1000
    print(f"✓ Configuration load: {config_time:.2f}ms")
    
    # 3. Initialize theme
    theme_start = time.perf_counter()
    theme = ThemeRegistry.get_theme(config.theme_variant)
    theme_time = (time.perf_counter() - theme_start) * 1000
    print(f"✓ Theme initialization: {theme_time:.2f}ms")
    
    # 4. Initialize banner database
    banner_db_start = time.perf_counter()
    assets_dir = Path(__file__).parent.parent / ".assets"
    banner_db = BannerDatabase(assets_dir)
    banner_db_time = (time.perf_counter() - banner_db_start) * 1000
    print(f"✓ Banner database init: {banner_db_time:.2f}ms")
    
    # 5. Load banners (with caching)
    banner_load_start = time.perf_counter()
    banners = banner_db.load_banners()
    banner_load_time = (time.perf_counter() - banner_load_start) * 1000
    print(f"✓ Banner loading: {banner_load_time:.2f}ms")
    
    # 6. Select banner
    banner_select_start = time.perf_counter()
    banner = banner_db.get_random_banner()
    banner_select_time = (time.perf_counter() - banner_select_start) * 1000
    print(f"✓ Banner selection: {banner_select_time:.2f}ms")
    
    # 7. Initialize renderer
    renderer_start = time.perf_counter()
    renderer = BannerRenderer(theme)
    renderer_time = (time.perf_counter() - renderer_start) * 1000
    print(f"✓ Renderer initialization: {renderer_time:.2f}ms")
    
    # Total time
    total_time = (time.perf_counter() - total_start) * 1000
    
    print()
    print("=" * 60)
    print(f"Total startup time: {total_time:.2f}ms")
    print()
    
    # Check against target
    target = 200.0
    if total_time < target:
        print(f"✓ PASS: Startup time is under {target}ms target")
        status_emoji = "✓"
        status_color = "\033[92m"  # Green
    else:
        print(f"✗ FAIL: Startup time exceeds {target}ms target")
        status_emoji = "✗"
        status_color = "\033[91m"  # Red
    
    print(f"{status_color}{status_emoji} Target: {target}ms | Actual: {total_time:.2f}ms | Margin: {target - total_time:.2f}ms\033[0m")
    print("=" * 60)
    print()
    
    # Breakdown percentages
    print("Time breakdown:")
    print(f"  Imports:        {import_time:>7.2f}ms ({import_time/total_time*100:>5.1f}%)")
    print(f"  Configuration:  {config_time:>7.2f}ms ({config_time/total_time*100:>5.1f}%)")
    print(f"  Theme:          {theme_time:>7.2f}ms ({theme_time/total_time*100:>5.1f}%)")
    print(f"  Banner DB init: {banner_db_time:>7.2f}ms ({banner_db_time/total_time*100:>5.1f}%)")
    print(f"  Banner loading: {banner_load_time:>7.2f}ms ({banner_load_time/total_time*100:>5.1f}%)")
    print(f"  Banner select:  {banner_select_time:>7.2f}ms ({banner_select_time/total_time*100:>5.1f}%)")
    print(f"  Renderer init:  {renderer_time:>7.2f}ms ({renderer_time/total_time*100:>5.1f}%)")
    print()
    
    # Identify bottlenecks
    operations = [
        ("Imports", import_time),
        ("Configuration", config_time),
        ("Theme", theme_time),
        ("Banner DB init", banner_db_time),
        ("Banner loading", banner_load_time),
        ("Banner select", banner_select_time),
        ("Renderer init", renderer_time),
    ]
    
    # Sort by time (descending)
    operations.sort(key=lambda x: x[1], reverse=True)
    
    print("Slowest operations:")
    for i, (name, duration) in enumerate(operations[:3], 1):
        print(f"  {i}. {name}: {duration:.2f}ms")
    print()
    
    return total_time < target


if __name__ == "__main__":
    success = profile_startup()
    sys.exit(0 if success else 1)
