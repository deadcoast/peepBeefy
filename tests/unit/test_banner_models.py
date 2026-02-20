"""Unit tests for banner data models."""

import pytest
from src.banner import BannerMetadata, Banner


def test_banner_metadata_creation():
    """Test creating BannerMetadata with required fields."""
    metadata = BannerMetadata(category="1ST_BEEFS", name="BIGBEEF")
    
    assert metadata.category == "1ST_BEEFS"
    assert metadata.name == "BIGBEEF"
    assert metadata.author is None
    assert metadata.description is None
    assert metadata.dimensions == (0, 0)
    assert metadata.animation_compatible is True


def test_banner_metadata_with_optional_fields():
    """Test creating BannerMetadata with all optional fields."""
    metadata = BannerMetadata(
        category="ALT",
        name="COOL",
        author="Test Author",
        description="A cool banner",
        dimensions=(80, 10),
        animation_compatible=False
    )
    
    assert metadata.category == "ALT"
    assert metadata.name == "COOL"
    assert metadata.author == "Test Author"
    assert metadata.description == "A cool banner"
    assert metadata.dimensions == (80, 10)
    assert metadata.animation_compatible is False


def test_banner_width_property():
    """Test Banner.width property calculates correctly."""
    metadata = BannerMetadata(category="TEST", name="TEST")
    lines = [
        "Short",
        "Medium line",
        "This is the longest line here"
    ]
    banner = Banner(metadata=metadata, lines=lines)
    
    assert banner.width == 29  # Length of longest line


def test_banner_height_property():
    """Test Banner.height property calculates correctly."""
    metadata = BannerMetadata(category="TEST", name="TEST")
    lines = ["Line 1", "Line 2", "Line 3", "Line 4"]
    banner = Banner(metadata=metadata, lines=lines)
    
    assert banner.height == 4


def test_banner_empty_lines():
    """Test Banner with empty lines list."""
    metadata = BannerMetadata(category="TEST", name="EMPTY")
    banner = Banner(metadata=metadata, lines=[])
    
    assert banner.width == 0
    assert banner.height == 0


def test_banner_preserves_whitespace():
    """Test Banner preserves whitespace in lines."""
    metadata = BannerMetadata(category="TEST", name="SPACES")
    lines = [
        "  Indented",
        "Normal",
        "    More indent"
    ]
    banner = Banner(metadata=metadata, lines=lines)
    
    assert banner.lines[0] == "  Indented"
    assert banner.lines[2] == "    More indent"
    assert banner.width == 15  # "    More indent" is longest
