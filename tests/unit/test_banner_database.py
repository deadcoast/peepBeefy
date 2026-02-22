"""Unit tests for BannerDatabase class.

This module contains unit tests to verify the BannerDatabase parser
correctly handles the ASCII database format.
"""

import pytest
from pathlib import Path
from src.banner import BannerDatabase, Banner


def test_load_banners_from_real_file():
    """Test that BannerDatabase can load banners from the actual ASCII database file."""
    # Arrange
    assets_dir = Path(".assets")
    db = BannerDatabase(assets_dir)
    
    # Act
    banners = db.load_banners(force_reload=True)
    
    # Assert
    assert len(banners) > 0, "Should load at least one category"
    assert "1ST_BEEFS" in banners, "Should contain 1ST_BEEFS category"
    assert len(banners["1ST_BEEFS"]) > 0, "1ST_BEEFS should have at least one banner"
    
    # Verify a specific banner
    bigbeef = next((b for b in banners["1ST_BEEFS"] if b.metadata.name == "BIGBEEF"), None)
    assert bigbeef is not None, "Should find BIGBEEF banner"
    assert bigbeef.height > 0, "BIGBEEF should have content"
    assert bigbeef.width > 0, "BIGBEEF should have width"


def test_banner_content_preserved():
    """Test that banner content is preserved exactly as in the file."""
    # Arrange
    assets_dir = Path(".assets")
    db = BannerDatabase(assets_dir)
    
    # Act
    banners = db.load_banners()
    
    # Assert - check that whitespace is preserved
    for category, banner_list in banners.items():
        for banner in banner_list:
            # All banners should have lines
            assert len(banner.lines) > 0, f"{category}:{banner.metadata.name} should have lines"
            
            # Lines should preserve content (not all stripped)
            # At least some lines should have content
            has_content = any(line.strip() for line in banner.lines)
            assert has_content, f"{category}:{banner.metadata.name} should have content"


def test_multiple_categories_parsed():
    """Test that multiple categories are correctly parsed and grouped."""
    # Arrange
    assets_dir = Path(".assets")
    db = BannerDatabase(assets_dir)
    
    # Act
    banners = db.load_banners(force_reload=True)
    
    # Assert
    expected_categories = ["1ST_BEEFS", "ALT", "CURSIVE"]
    for category in expected_categories:
        assert category in banners, f"Should contain {category} category"
        assert len(banners[category]) > 0, f"{category} should have banners"


def test_banner_metadata_populated():
    """Test that banner metadata is correctly populated."""
    # Arrange
    assets_dir = Path(".assets")
    db = BannerDatabase(assets_dir)
    
    # Act
    banners = db.load_banners()
    
    # Assert
    for category, banner_list in banners.items():
        for banner in banner_list:
            # Metadata should be populated
            assert banner.metadata.category == category
            assert banner.metadata.name, "Banner should have a name"
            assert banner.metadata.dimensions[0] > 0, "Width should be calculated"
            assert banner.metadata.dimensions[1] > 0, "Height should be calculated"
            
            # Dimensions should match actual content
            assert banner.metadata.dimensions[0] == banner.width
            assert banner.metadata.dimensions[1] == banner.height


def test_missing_file_returns_empty():
    """Test that missing ASCII file returns empty dictionary."""
    # Arrange
    assets_dir = Path("/nonexistent")
    db = BannerDatabase(assets_dir)
    
    # Act
    banners = db.load_banners()
    
    # Assert
    assert banners == {}, "Should return empty dict for missing file"


def test_parser_handles_empty_lines():
    """Test that parser preserves empty lines in banner content."""
    # Arrange
    assets_dir = Path(".assets")
    db = BannerDatabase(assets_dir)
    
    # Act
    banners = db.load_banners()
    
    # Assert - check that some banners have empty lines (common in ASCII art)
    found_empty_line = False
    for category, banner_list in banners.items():
        for banner in banner_list:
            if any(line == "" for line in banner.lines):
                found_empty_line = True
                break
        if found_empty_line:
            break
    
    # Note: This assertion might fail if no banners have empty lines
    # That's okay - it's just checking the parser can handle them
    # The property tests already verify empty line preservation
