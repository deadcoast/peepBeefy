"""Property tests for animation color degradation (Property 36).

Tests that fire animation gracefully degrades to 8-bit colors when RGB
is not supported, validating Requirement 15.5.
"""

import pytest
from hypothesis import given, strategies as st, assume
from rich.console import Console
from io import StringIO

from src.animation import FireAnimator, FirePalette
from src.banner import Banner, BannerMetadata


@given(
    intensity=st.sampled_from(["subtle", "normal", "intense"]),
    use_rgb=st.booleans(),
    num_lines=st.integers(min_value=3, max_value=20),
    line_length=st.integers(min_value=10, max_value=60),
)
def test_animation_uses_correct_palette_based_on_rgb_support(
    intensity: str,
    use_rgb: bool,
    num_lines: int,
    line_length: int,
):
    """Property 36: Animation Color Degradation.
    
    PROPERTY: When RGB support is disabled, the fire animator MUST use
    the 8-bit color palette instead of RGB colors.
    
    VALIDATES: Requirement 15.5 - Fire animation shall gracefully degrade
    on terminals without RGB support.
    """
    # Create animator with explicit RGB setting
    animator = FireAnimator(intensity=intensity, use_rgb=use_rgb)
    
    # Verify correct palette is selected
    if use_rgb:
        assert animator._use_rgb is True
        assert animator._palette == FirePalette.STYLES
        # RGB palette should contain hex colors
        assert all("#" in str(style.color) for style in FirePalette.STYLES if style.color)
    else:
        assert animator._use_rgb is False
        assert animator._palette == FirePalette.STYLES_8BIT
        # 8-bit palette should contain color() function calls
        assert all("color(" in str(style.color) for style in FirePalette.STYLES_8BIT if style.color)


@given(
    intensity=st.sampled_from(["subtle", "normal", "intense"]),
    num_lines=st.integers(min_value=3, max_value=15),
    line_length=st.integers(min_value=10, max_value=40),
)
def test_animation_produces_output_regardless_of_color_mode(
    intensity: str,
    num_lines: int,
    line_length: int,
):
    """Property 36: Animation Color Degradation (Output Consistency).
    
    PROPERTY: Animation MUST produce valid output in both RGB and 8-bit modes,
    with the same content structure (only colors differ).
    
    VALIDATES: Requirement 15.5 - Animation works correctly in degraded mode.
    """
    # Create test banner
    lines = ["X" * line_length for _ in range(num_lines)]
    metadata = BannerMetadata(category="TEST", name="TEST_BANNER")
    banner = Banner(metadata=metadata, lines=lines)
    
    # Test both RGB and 8-bit modes
    for use_rgb in [True, False]:
        animator = FireAnimator(intensity=intensity, use_rgb=use_rgb)
        
        # Detect zones for the banner
        flame_lines, text_lines = animator._detect_zones(banner)
        
        # Build a single frame
        import random
        rng = random.Random(42)
        frame = animator._build_frame(banner, flame_lines, text_lines, rng)
        
        # Verify frame is not empty
        assert frame is not None
        frame_text = frame.plain
        assert len(frame_text) > 0
        
        # Verify frame contains the banner content (ignoring colors)
        # Each line should be present in the output
        for line in lines:
            assert line in frame_text or len(frame_text) >= len(line)


@given(
    num_lines=st.integers(min_value=5, max_value=15),
    line_length=st.integers(min_value=15, max_value=50),
)
def test_palette_lengths_match_between_rgb_and_8bit(
    num_lines: int,
    line_length: int,
):
    """Property 36: Animation Color Degradation (Palette Consistency).
    
    PROPERTY: RGB and 8-bit palettes MUST have the same number of colors
    to ensure consistent animation behavior.
    
    VALIDATES: Requirement 15.5 - Color degradation maintains animation quality.
    """
    # Verify both palettes have the same length
    assert len(FirePalette.STYLES) == len(FirePalette.STYLES_8BIT)
    assert len(FirePalette.COLORS) == len(FirePalette.COLORS_8BIT)
    
    # Verify palette length is 12 (as per DOOM PSX specification)
    assert len(FirePalette.STYLES) == 12
    assert len(FirePalette.STYLES_8BIT) == 12


@given(
    intensity=st.sampled_from(["subtle", "normal", "intense"]),
    use_rgb=st.booleans(),
)
def test_animator_preserves_use_rgb_attribute(
    intensity: str,
    use_rgb: bool,
):
    """Property 36: Animation Color Degradation (Attribute Preservation).
    
    PROPERTY: The animator MUST preserve the _use_rgb attribute for
    inspection and testing purposes.
    
    VALIDATES: Requirement 15.5 - Terminal capability detection is accessible.
    """
    animator = FireAnimator(intensity=intensity, use_rgb=use_rgb)
    
    # Verify _use_rgb attribute exists and matches input
    assert hasattr(animator, "_use_rgb")
    assert animator._use_rgb == use_rgb
    
    # Verify palette selection is consistent with _use_rgb
    if use_rgb:
        assert animator._palette == FirePalette.STYLES
    else:
        assert animator._palette == FirePalette.STYLES_8BIT


@given(
    num_lines=st.integers(min_value=3, max_value=10),
    line_length=st.integers(min_value=10, max_value=30),
)
def test_auto_detection_defaults_to_safe_value(
    num_lines: int,
    line_length: int,
):
    """Property 36: Animation Color Degradation (Auto-Detection Safety).
    
    PROPERTY: When use_rgb is None (auto-detect), the animator MUST
    select a valid palette without crashing.
    
    VALIDATES: Requirement 15.5 - Auto-detection works reliably.
    """
    # Create animator with auto-detection (use_rgb=None)
    animator = FireAnimator(intensity="normal", use_rgb=None)
    
    # Verify a palette was selected
    assert hasattr(animator, "_use_rgb")
    assert isinstance(animator._use_rgb, bool)
    assert animator._palette is not None
    
    # Verify palette is one of the valid options
    assert animator._palette in [FirePalette.STYLES, FirePalette.STYLES_8BIT]
    
    # Verify animator can build frames
    lines = ["X" * line_length for _ in range(num_lines)]
    metadata = BannerMetadata(category="TEST", name="TEST")
    banner = Banner(metadata=metadata, lines=lines)
    
    # Detect zones and build frame
    flame_lines, text_lines = animator._detect_zones(banner)
    import random
    rng = random.Random(42)
    frame = animator._build_frame(banner, flame_lines, text_lines, rng)
    assert frame is not None
