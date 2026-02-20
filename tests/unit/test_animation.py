"""Unit tests for the animation module."""

import pytest
from rich.console import Console
from rich.text import Text

from src.animation import FirePalette, FireAnimator
from src.banner import Banner, BannerMetadata


def test_fire_palette_has_12_colors():
    """Verify FirePalette has exactly 12 colors."""
    assert len(FirePalette.COLORS) == 12
    assert len(FirePalette.STYLES) == 12


def test_fire_palette_colors_are_hex():
    """Verify all palette colors are valid hex codes."""
    for color in FirePalette.COLORS:
        assert color.startswith("#")
        assert len(color) == 7
        # Verify it's a valid hex string
        int(color[1:], 16)


def test_fire_animator_initialization():
    """Test FireAnimator can be initialized with different intensities."""
    animator_normal = FireAnimator("normal")
    assert animator_normal._intensity == "normal"
    assert animator_normal._intensity_multiplier == 1.0
    
    animator_subtle = FireAnimator("subtle")
    assert animator_subtle._intensity == "subtle"
    assert animator_subtle._intensity_multiplier == 0.5
    
    animator_intense = FireAnimator("intense")
    assert animator_intense._intensity == "intense"
    assert animator_intense._intensity_multiplier == 1.5


def test_fire_animator_default_intensity():
    """Test FireAnimator defaults to normal intensity."""
    animator = FireAnimator()
    assert animator._intensity == "normal"
    assert animator._intensity_multiplier == 1.0


def test_detect_zones_60_40_split():
    """Test flame zone detection uses 60/40 split by default."""
    animator = FireAnimator()
    
    # Create a 10-line banner
    banner = Banner(
        metadata=BannerMetadata(category="TEST", name="TEST"),
        lines=["Line " + str(i) for i in range(10)]
    )
    
    flame_lines, text_lines = animator._detect_zones(banner)
    
    # 60% of 10 = 6 lines for flame
    assert flame_lines == [0, 1, 2, 3, 4, 5]
    # Remaining 40% for text
    assert text_lines == [6, 7, 8, 9]


def test_detect_zones_with_metadata_override():
    """Test flame zone detection respects metadata override."""
    animator = FireAnimator()
    
    # Create a banner with explicit flame_lines metadata
    metadata = BannerMetadata(category="TEST", name="TEST")
    metadata.flame_lines = [0, 1, 2]  # Only first 3 lines are flame
    
    banner = Banner(
        metadata=metadata,
        lines=["Line " + str(i) for i in range(10)]
    )
    
    flame_lines, text_lines = animator._detect_zones(banner)
    
    assert flame_lines == [0, 1, 2]
    assert text_lines == [3, 4, 5, 6, 7, 8, 9]


def test_apply_flame_coloring_preserves_spaces():
    """Test flame coloring preserves space characters."""
    import random
    animator = FireAnimator()
    
    line = "  test  line  "
    rng = random.Random(42)
    result = animator._apply_flame_coloring(line, 0, 5, rng)
    
    # Convert to string to check content
    result_str = result.plain
    assert result_str == line
    assert "  " in result_str  # Spaces preserved


def test_apply_text_coloring_preserves_spaces():
    """Test text coloring preserves space characters."""
    import random
    animator = FireAnimator()
    
    line = "  test  line  "
    rng = random.Random(42)
    result = animator._apply_text_coloring(line, 0, rng)
    
    # Convert to string to check content
    result_str = result.plain
    assert result_str == line
    assert "  " in result_str  # Spaces preserved


def test_build_frame_returns_text():
    """Test _build_frame returns a Rich Text object."""
    animator = FireAnimator()
    
    banner = Banner(
        metadata=BannerMetadata(category="TEST", name="TEST"),
        lines=["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"]
    )
    
    flame_lines = [0, 1, 2]
    text_lines = [3, 4]
    
    import random
    rng = random.Random(42)
    
    result = animator._build_frame(banner, flame_lines, text_lines, rng)
    
    assert isinstance(result, Text)
    # Check that all lines are present
    assert "Line 1" in result.plain
    assert "Line 5" in result.plain


def test_animate_banner_basic():
    """Test animate_banner runs without errors (smoke test)."""
    animator = FireAnimator()
    console = Console()
    
    banner = Banner(
        metadata=BannerMetadata(category="TEST", name="TEST"),
        lines=["Test", "Banner", "Lines"]
    )
    
    # Run a very short animation (0.1 seconds)
    # This is just a smoke test to ensure no exceptions
    try:
        animator.animate_banner(banner, console, duration=0.1, fps=8)
    except Exception as e:
        pytest.fail(f"animate_banner raised an exception: {e}")


def test_intensity_affects_multiplier():
    """Test that different intensities produce different multipliers."""
    subtle = FireAnimator("subtle")
    normal = FireAnimator("normal")
    intense = FireAnimator("intense")
    
    assert subtle._intensity_multiplier < normal._intensity_multiplier
    assert normal._intensity_multiplier < intense._intensity_multiplier
    assert subtle._intensity_multiplier == 0.5
    assert normal._intensity_multiplier == 1.0
    assert intense._intensity_multiplier == 1.5
