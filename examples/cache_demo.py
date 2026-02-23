#!/usr/bin/env python3
"""Demo script showing the caching system in action.

This script demonstrates:
1. Writing data to cache
2. Reading data from cache
3. Cache freshness validation
4. Cache invalidation
"""

import time
from pathlib import Path
from src.config import ConfigManager, TerminalCache

def main():
    print("=== Caching System Demo ===\n")
    
    # Initialize config manager
    cm = ConfigManager()
    print(f"Cache directory: {cm.CACHE_DIR}\n")
    
    # Demo 1: Write and read cache
    print("1. Writing terminal detection results to cache...")
    terminal_data = TerminalCache(
        ansi_mode="rgb",
        background_color=(30, 30, 30),
        supports_rgb=True,
        supports_256=True,
        detected_at=time.time(),
        ttl=3600.0
    )
    
    success = cm.write_cache("terminal_detection", terminal_data)
    print(f"   Write successful: {success}")
    
    # Demo 2: Read from cache
    print("\n2. Reading from cache...")
    cached_data = cm.read_cache("terminal_detection")
    if cached_data:
        print(f"   Cache hit!")
        print(f"   ANSI mode: {cached_data.ansi_mode}")
        print(f"   Supports RGB: {cached_data.supports_rgb}")
        print(f"   Background: {cached_data.background_color}")
    else:
        print("   Cache miss!")
    
    # Demo 3: Cache with max_age
    print("\n3. Testing cache freshness with max_age...")
    fresh_data = cm.read_cache("terminal_detection", max_age=10.0)
    print(f"   Fresh cache (max_age=10s): {fresh_data is not None}")
    
    # Demo 4: Cache invalidation
    print("\n4. Invalidating cache...")
    cm.invalidate_cache("terminal_detection")
    cached_data = cm.read_cache("terminal_detection")
    print(f"   Cache after invalidation: {cached_data}")
    
    # Demo 5: Complex data caching
    print("\n5. Caching complex data structures...")
    banner_data = {
        "categories": {
            "1ST_BEEFS": ["CLASSIC", "MODERN"],
            "FOOD": ["BURGER", "PIZZA"]
        },
        "metadata": {
            "total_banners": 4,
            "last_updated": time.time()
        }
    }
    
    cm.write_cache("banner_database", banner_data)
    cached_banners = cm.read_cache("banner_database")
    print(f"   Cached categories: {list(cached_banners['categories'].keys())}")
    print(f"   Total banners: {cached_banners['metadata']['total_banners']}")
    
    # Demo 6: Cache freshness validation
    print("\n6. Testing cache freshness validation...")
    
    # Create a temporary source file
    source_file = Path("temp_source.txt")
    source_file.write_text("original content")
    
    # Write cache (will be newer than source)
    time.sleep(0.1)
    cm.write_cache("test_freshness", {"data": "cached"})
    
    # Validate freshness
    is_fresh = cm.validate_cache_freshness("test_freshness", source_file)
    print(f"   Cache is fresh: {is_fresh}")
    
    # Modify source file
    time.sleep(0.1)
    source_file.write_text("modified content")
    
    # Validate again
    is_fresh = cm.validate_cache_freshness("test_freshness", source_file)
    print(f"   Cache after source modification: {is_fresh}")
    
    # Cleanup
    source_file.unlink()
    cm.invalidate_cache("test_freshness")
    cm.invalidate_cache("banner_database")
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()
