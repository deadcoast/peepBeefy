"""Integration tests for Banner Preview system.

This module tests the banner preview system's integration with other components
like BannerDatabase, Theme system, and animation.
"""

import pytest
from io import StringIO
from pathlib import Path

from src.banner import BannerDatabase, Banner, BannerMetadata
from src.banner_preview import BannerPreview
from src.themes import ThemeRegistry
from rich.console import Console


class TestBannerPreviewIntegration:
    """Integration tests for banner preview system."""
    
    def test_preview_displays_banners_from_database(self):
        """Test that preview can display banners loaded from database."""
        # Arrange
        assets_dir = Path(".assets")
        if not assets_dir.exists():
            pytest.skip("Assets directory not found")
        
        banner_db = BannerDatabase(assets_dir)
        banners_dict = banner_db.load_banners()
        
        if not banners_dict:
            pytest.skip("No banners available in database")
        
        # Get first few banners
        all_banners = []
        for category_banners in banners_dict.values():
            all_banners.extend(category_banners)
        
        test_banners = all_banners[:5]  # Test with first 5 banners
        
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        output = StringIO()
        console = Console(file=output, width=120, height=40)
        preview = BannerPreview(theme, console)
        
        # Act
        preview.display_grid(test_banners, page=1)
        
        # Assert
        result = output.getvalue()
        assert len(result) > 0, "Preview should produce output"
        assert "Banner Preview" in result, "Should show preview header"
        assert "Page 1/" in result, "Should show page indicator"
    
    def test_preview_pagination_with_multiple_pages(self):
        """Test that pagination works correctly with multiple pages."""
        # Arrange: Create 25 test banners
        banners = []
        for i in range(25):
            metadata = BannerMetadata(
                category=f"CAT{i % 3}",
                name=f"BANNER{i}",
                description=f"Test banner {i}"
            )
            banner = Banner(metadata=metadata, lines=[f"Line {i}"])
            banners.append(banner)
        
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        output = StringIO()
        console = Console(file=output, width=120, height=40)
        preview = BannerPreview(theme, console)
        
        # Act: Display page 1
        output.truncate(0)
        output.seek(0)
        preview.display_grid(banners, page=1)
        page1_output = output.getvalue()
        
        # Act: Display page 2
        output.truncate(0)
        output.seek(0)
        preview.display_grid(banners, page=2)
        page2_output = output.getvalue()
        
        # Assert
        assert "Page 1/" in page1_output, "Page 1 should show page indicator"
        assert "Page 2/" in page2_output, "Page 2 should show page indicator"
        assert page1_output != page2_output, "Different pages should show different content"
    
    def test_preview_filters_animated_banners(self):
        """Test that animation filtering works correctly."""
        # Arrange: Create mix of compatible and incompatible banners
        banners = []
        for i in range(10):
            metadata = BannerMetadata(
                category="TEST",
                name=f"BANNER{i}",
                animation_compatible=(i % 2 == 0)  # Even indices are compatible
            )
            banner = Banner(metadata=metadata, lines=[f"Line {i}"])
            banners.append(banner)
        
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        output = StringIO()
        console = Console(file=output, width=120, height=40)
        preview = BannerPreview(theme, console)
        
        # Act: Display with filtering
        preview.display_grid(banners, page=1, filter_animated=True)
        result = output.getvalue()
        
        # Assert: Should show only 5 compatible banners
        assert "(5 banners)" in result, "Should show 5 filtered banners"
    
    def test_preview_adapts_to_narrow_terminal(self):
        """Test that preview adapts layout for narrow terminals."""
        # Arrange
        banners = []
        for i in range(3):
            metadata = BannerMetadata(category="TEST", name=f"BANNER{i}")
            banner = Banner(metadata=metadata, lines=[f"Line {i}"])
            banners.append(banner)
        
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        
        # Test narrow terminal (< 80 columns)
        output = StringIO()
        console = Console(file=output, width=60, height=40)
        preview = BannerPreview(theme, console)
        
        # Act
        columns = preview._get_column_count()
        
        # Assert
        assert columns == 1, "Narrow terminal should use 1 column"
    
    def test_preview_adapts_to_wide_terminal(self):
        """Test that preview adapts layout for wide terminals."""
        # Arrange
        banners = []
        for i in range(3):
            metadata = BannerMetadata(category="TEST", name=f"BANNER{i}")
            banner = Banner(metadata=metadata, lines=[f"Line {i}"])
            banners.append(banner)
        
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        
        # Test wide terminal (>= 160 columns)
        output = StringIO()
        console = Console(file=output, width=180, height=40)
        preview = BannerPreview(theme, console)
        
        # Act
        columns = preview._get_column_count()
        
        # Assert
        assert columns == 3, "Wide terminal should use 3 columns"
    
    def test_preview_scales_large_banners(self):
        """Test that large banners are scaled to fit preview area."""
        # Arrange: Create a very large banner
        large_lines = ["X" * 150 for _ in range(50)]  # 150 chars wide, 50 lines tall
        metadata = BannerMetadata(category="TEST", name="LARGE")
        banner = Banner(metadata=metadata, lines=large_lines)
        
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        output = StringIO()
        console = Console(file=output, width=120, height=40)
        preview = BannerPreview(theme, console)
        
        # Act
        scaled_lines = preview._scale_banner(banner, max_width=60, max_height=10)
        
        # Assert
        assert all(len(line) <= 60 for line in scaled_lines), "All lines should fit max width"
        assert len(scaled_lines) <= 11, "Should not exceed max height + ellipsis"
        assert "..." in scaled_lines[-1], "Should add ellipsis for truncated content"
    
    def test_preview_displays_metadata(self):
        """Test that banner metadata is displayed in preview."""
        # Arrange
        metadata = BannerMetadata(
            category="TEST",
            name="SAMPLE",
            author="Test Author",
            description="A test banner",
            animation_compatible=True
        )
        banner = Banner(metadata=metadata, lines=["Test", "Banner"])
        
        theme = ThemeRegistry.get_theme("CRT_Cyan")
        output = StringIO()
        console = Console(file=output, width=120, height=40)
        preview = BannerPreview(theme, console)
        
        # Act
        panel = preview._render_banner_preview(banner, max_width=80, max_height=10)
        console.print(panel)
        result = output.getvalue()
        
        # Assert
        assert "Category" in result or "TEST" in result, "Should display category"
        assert "Name" in result or "SAMPLE" in result, "Should display name"
        assert "Author" in result or "Test Author" in result, "Should display author"
        assert "Description" in result or "A test banner" in result, "Should display description"
        assert "Animation" in result or "compatible" in result, "Should display animation compatibility"
    
    def test_preview_with_different_themes(self):
        """Test that preview works with different themes."""
        # Arrange
        metadata = BannerMetadata(category="TEST", name="SAMPLE")
        banner = Banner(metadata=metadata, lines=["Test"])
        
        themes = ["CRT_Cyan", "Amber_Terminal", "Green_Phosphor", "Synthwave"]
        
        for theme_name in themes:
            # Act
            theme = ThemeRegistry.get_theme(theme_name)
            output = StringIO()
            console = Console(file=output, width=120, height=40)
            preview = BannerPreview(theme, console)
            
            panel = preview._render_banner_preview(banner, max_width=80, max_height=10)
            console.print(panel)
            result = output.getvalue()
            
            # Assert
            assert len(result) > 0, f"Preview should work with {theme_name} theme"
            assert "TEST" in result, f"Should display banner with {theme_name} theme"
