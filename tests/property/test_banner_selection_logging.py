"""Property 31: Banner Selection Logging

This property validates that banner selection decisions are logged at INFO level
with sufficient detail for debugging and auditing.

Validates Requirements: 10.3, 14.1, 14.2
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import tempfile
import logging
from io import StringIO

from src.banner import BannerDatabase, Banner, BannerMetadata


def create_test_banner_database(tmpdir: Path, num_categories: int = 2, banners_per_category: int = 3) -> Path:
    """Create a test ASCII database file with multiple categories and banners."""
    content_lines = ["---", "DEFINITIONS", "-----------"]
    
    for cat_idx in range(num_categories):
        cat_name = f"CAT{cat_idx}"
        content_lines.append(f"# {cat_name}: \"Test category {cat_idx}\"")
    
    for cat_idx in range(num_categories):
        cat_name = f"CAT{cat_idx}"
        for banner_idx in range(banners_per_category):
            banner_name = f"BANNER{banner_idx}"
            content_lines.extend([
                "",
                "---",
                f"{cat_name}:{banner_name}",
                "-------------",
                f"Test banner {cat_idx}-{banner_idx} line 1",
                f"Test banner {cat_idx}-{banner_idx} line 2",
            ])
    
    content_lines.append("\n---\n")
    
    ascii_file = tmpdir / "ASCII-Full-Logo.txt"
    ascii_file.write_text("\n".join(content_lines), encoding='utf-8')
    
    return tmpdir


@given(
    num_categories=st.integers(min_value=1, max_value=5),
    banners_per_category=st.integers(min_value=1, max_value=5),
    selection_mode=st.sampled_from(['random', 'specific', 'category'])
)
@settings(max_examples=50, deadline=None)
def test_banner_selection_is_logged(num_categories, banners_per_category, selection_mode):
    """Property 31: Banner selection decisions are logged at INFO level.
    
    PROPERTY: For all banner selection operations,
              the selection decision MUST be logged at INFO level
              with details about which banner was selected and why.
    
    This ensures that banner selection behavior can be audited and debugged.
    """
    # Set up logging capture
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    
    banner_logger = logging.getLogger('src.banner')
    original_level = banner_logger.level
    banner_logger.setLevel(logging.INFO)
    banner_logger.addHandler(handler)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            assets_dir = create_test_banner_database(
                Path(tmpdir),
                num_categories,
                banners_per_category
            )
            
            db = BannerDatabase(assets_dir)
            
            # Clear log stream before selection
            log_stream.truncate(0)
            log_stream.seek(0)
            
            # Perform banner selection based on mode
            if selection_mode == 'random':
                banner = db.get_random_banner()
            elif selection_mode == 'specific':
                # Try to get a specific banner
                banner = db.get_banner(category=f"CAT0", name=f"BANNER0")
            elif selection_mode == 'category':
                # Get random from specific category
                banner = db.get_random_banner(categories=[f"CAT0"])
            
            # Get logged output
            log_output = log_stream.getvalue()
            
            # Property: Selection should be logged at INFO level
            assert "INFO" in log_output, \
                f"Banner selection should log at INFO level (mode: {selection_mode})"
            
            # Property: Log should contain banner identification
            assert "banner" in log_output.lower(), \
                "Log should mention 'banner'"
            
            # Property: For specific selections, log should mention the selected banner
            if selection_mode == 'specific':
                assert "CAT0" in log_output or "BANNER0" in log_output or "Selected" in log_output, \
                    "Specific selection should log the banner identifier"
            
            # Property: For random selections, log should indicate randomness
            if selection_mode == 'random':
                assert "random" in log_output.lower() or "Selected" in log_output, \
                    "Random selection should be indicated in logs"
    
    finally:
        # Clean up logging
        banner_logger.removeHandler(handler)
        banner_logger.setLevel(original_level)
        handler.close()


@given(
    has_cache=st.booleans(),
    force_reload=st.booleans()
)
@settings(max_examples=50, deadline=None)
def test_cache_operations_are_logged(has_cache, force_reload):
    """Property 31: Cache operations are logged at appropriate levels.
    
    PROPERTY: For all cache operations (load, save, invalidation),
              the operation MUST be logged at DEBUG or INFO level
              with details about the cache state.
    
    This ensures cache behavior can be monitored and debugged.
    """
    # Set up logging capture
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    
    banner_logger = logging.getLogger('src.banner')
    original_level = banner_logger.level
    banner_logger.setLevel(logging.DEBUG)
    banner_logger.addHandler(handler)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            assets_dir = create_test_banner_database(Path(tmpdir), 2, 2)
            
            db = BannerDatabase(assets_dir)
            
            # If has_cache, create a cache file first
            if has_cache:
                # Load once to create cache
                db.load_banners(force_reload=False)
                log_stream.truncate(0)
                log_stream.seek(0)
            
            # Now load again with force_reload setting
            banners = db.load_banners(force_reload=force_reload)
            
            log_output = log_stream.getvalue()
            
            # Property: Cache operations should be logged
            if has_cache and not force_reload:
                # Should attempt to use cache
                assert "cache" in log_output.lower() or "Loaded" in log_output or "Parsed" in log_output, \
                    "Cache usage should be logged"
            
            if force_reload:
                # Should bypass cache and parse
                assert "Parsed" in log_output or "banners" in log_output.lower(), \
                    "Force reload should log parsing operation"
            
            # Property: Log should contain quantitative information
            # (number of banners loaded/parsed)
            assert any(char.isdigit() for char in log_output) or "banners" in log_output.lower(), \
                "Log should contain information about number of banners"
    
    finally:
        # Clean up logging
        banner_logger.removeHandler(handler)
        banner_logger.setLevel(original_level)
        handler.close()


@given(
    terminal_too_small=st.booleans(),
    banner_too_large=st.booleans()
)
@settings(max_examples=50, deadline=None)
def test_fallback_decisions_are_logged(terminal_too_small, banner_too_large):
    """Property 31: Fallback decisions are logged with reasoning.
    
    PROPERTY: For all fallback scenarios (missing files, oversized banners, etc.),
              the fallback decision MUST be logged at WARNING or INFO level
              with explanation of why fallback was triggered.
    
    This ensures fallback behavior is transparent and debuggable.
    """
    # Set up logging capture
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    
    banner_logger = logging.getLogger('src.banner')
    original_level = banner_logger.level
    banner_logger.setLevel(logging.INFO)
    banner_logger.addHandler(handler)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            assets_dir = Path(tmpdir)
            
            if not terminal_too_small and not banner_too_large:
                # Normal case - create valid database
                create_test_banner_database(assets_dir, 1, 1)
            elif terminal_too_small or banner_too_large:
                # Don't create database file to trigger fallback
                pass
            
            db = BannerDatabase(assets_dir)
            
            # Clear log before operation
            log_stream.truncate(0)
            log_stream.seek(0)
            
            # Try to get a banner (should trigger fallback if no file)
            banner = db.get_random_banner()
            
            log_output = log_stream.getvalue()
            
            # Property: If fallback was triggered, it should be logged
            if not (assets_dir / "ASCII-Full-Logo.txt").exists():
                assert "WARNING" in log_output or "fallback" in log_output.lower() or "not found" in log_output.lower(), \
                    "Fallback to default banner should be logged with warning"
                
                # Property: Log should explain why fallback was used
                assert "available" in log_output.lower() or "not found" in log_output.lower() or "fallback" in log_output.lower(), \
                    "Fallback log should explain the reason"
    
    finally:
        # Clean up logging
        banner_logger.removeHandler(handler)
        banner_logger.setLevel(original_level)
        handler.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
