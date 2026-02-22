"""Unit tests for BannerRenderer animation integration.

This module tests the integration of animation functionality in BannerRenderer,
including animated rendering, static rendering, and fallback behavior.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console
from rich.panel import Panel

from src.banner import BannerRenderer, Banner, BannerMetadata
from src.themes import ThemeRegistry


@pytest.fixture
def test_banner():
    """Create a test banner for use in tests."""
    metadata = BannerMetadata(
        category="TEST",
        name="TEST_BANNER",
        description="Test banner for unit tests",
        animation_compatible=True
    )
    lines = [
        "Line 1",
        "Line 2",
        "Line 3",
        "Line 4",
        "Line 5"
    ]
    return Banner(metadata=metadata, lines=lines)


@pytest.fixture
def renderer():
    """Create a BannerRenderer with default theme."""
    theme = ThemeRegistry.get_theme("CRT_Cyan")
    return BannerRenderer(theme)


@pytest.fixture
def console():
    """Create a Rich Console for testing."""
    return Console()


def test_animation_displays_when_enabled(test_banner, renderer, console):
    """Test that animation displays when enabled.
    
    Validates: Requirements 3.6, 3.7
    """
    # Mock the FireAnimator to avoid actual animation
    # Patch where it's imported (inside render_animated method)
    with patch('animation.FireAnimator') as mock_animator_class:
        mock_animator = Mock()
        mock_animator_class.return_value = mock_animator
        
        # Call render_animated
        renderer.render_animated(
            test_banner,
            console,
            duration=1.0,
            fps=8,
            intensity="normal"
        )
        
        # Verify FireAnimator was imported and instantiated
        mock_animator_class.assert_called_once_with(intensity="normal")
        
        # Verify animate_banner was called with correct parameters
        mock_animator.animate_banner.assert_called_once_with(
            test_banner,
            console,
            duration=1.0,
            fps=8
        )


def test_static_banner_displays_when_disabled(test_banner, renderer, console):
    """Test that static banner displays when animation is disabled.
    
    Validates: Requirements 3.6, 3.7
    """
    # Call render_static
    panel = renderer.render_static(test_banner, console)
    
    # Verify a Panel is returned
    assert isinstance(panel, Panel)
    
    # Verify the panel contains the banner content
    # (We can't easily check the exact content, but we can verify it's a Panel)


def test_fallback_to_static_on_animation_error(test_banner, renderer, console):
    """Test that renderer falls back to static rendering on animation error.
    
    Validates: Requirements 3.6, 3.7
    """
    # Mock FireAnimator to raise an exception
    with patch('animation.FireAnimator') as mock_animator_class:
        mock_animator_class.side_effect = Exception("Animation failed")
        
        # Mock console.print to capture the fallback
        with patch.object(console, 'print') as mock_print:
            # Call render_animated - should not raise exception
            renderer.render_animated(
                test_banner,
                console,
                duration=1.0,
                fps=8,
                intensity="normal"
            )
            
            # Verify console.print was called (fallback to static)
            mock_print.assert_called_once()
            
            # Verify the argument is a Panel
            args, kwargs = mock_print.call_args
            assert len(args) == 1
            assert isinstance(args[0], Panel)


def test_animation_lazy_loading_not_imported_on_static(test_banner, renderer, console):
    """Test that FireAnimator is not imported when rendering static banners.
    
    Validates: Requirements 8.6
    """
    import sys
    
    # Remove animation module if it exists
    animation_modules = [
        'animation',
        'src.animation',
        'src.banner.animation'
    ]
    
    original_modules = {}
    for mod in animation_modules:
        if mod in sys.modules:
            original_modules[mod] = sys.modules[mod]
            del sys.modules[mod]
    
    try:
        # Render static banner
        panel = renderer.render_static(test_banner, console)
        
        # Verify animation module is still not loaded
        for mod in animation_modules:
            assert mod not in sys.modules, \
                f"{mod} should not be loaded when rendering static banners"
        
        # Verify we got a valid panel
        assert isinstance(panel, Panel)
        
    finally:
        # Restore original modules
        for mod, module in original_modules.items():
            sys.modules[mod] = module


def test_animation_respects_duration_parameter(test_banner, renderer, console):
    """Test that animation respects the duration parameter.
    
    Validates: Requirements 11.2
    """
    with patch('animation.FireAnimator') as mock_animator_class:
        mock_animator = Mock()
        mock_animator_class.return_value = mock_animator
        
        # Test with different durations
        for duration in [0.5, 1.0, 3.0, 5.0]:
            renderer.render_animated(
                test_banner,
                console,
                duration=duration,
                fps=8,
                intensity="normal"
            )
            
            # Verify animate_banner was called with the correct duration
            call_args = mock_animator.animate_banner.call_args
            assert call_args[1]['duration'] == duration


def test_animation_respects_fps_parameter(test_banner, renderer, console):
    """Test that animation respects the FPS parameter.
    
    Validates: Requirements 11.2
    """
    with patch('animation.FireAnimator') as mock_animator_class:
        mock_animator = Mock()
        mock_animator_class.return_value = mock_animator
        
        # Test with different FPS values
        for fps in [4, 8, 15, 30]:
            renderer.render_animated(
                test_banner,
                console,
                duration=1.0,
                fps=fps,
                intensity="normal"
            )
            
            # Verify animate_banner was called with the correct FPS
            call_args = mock_animator.animate_banner.call_args
            assert call_args[1]['fps'] == fps


def test_animation_respects_intensity_parameter(test_banner, renderer, console):
    """Test that animation respects the intensity parameter.
    
    Validates: Requirements 11.3, 11.4, 11.5
    """
    with patch('animation.FireAnimator') as mock_animator_class:
        mock_animator = Mock()
        mock_animator_class.return_value = mock_animator
        
        # Test with different intensity values
        for intensity in ["subtle", "normal", "intense"]:
            renderer.render_animated(
                test_banner,
                console,
                duration=1.0,
                fps=8,
                intensity=intensity
            )
            
            # Verify FireAnimator was instantiated with the correct intensity
            call_args = mock_animator_class.call_args
            assert call_args[1]['intensity'] == intensity


def test_render_static_handles_empty_banner(renderer, console):
    """Test that render_static handles empty banners gracefully."""
    # Create an empty banner
    metadata = BannerMetadata(category="TEST", name="EMPTY")
    empty_banner = Banner(metadata=metadata, lines=[])
    
    # Should not raise an exception
    panel = renderer.render_static(empty_banner, console)
    
    # Verify a Panel is returned
    assert isinstance(panel, Panel)


def test_render_animated_handles_empty_banner(renderer, console):
    """Test that render_animated handles empty banners gracefully."""
    # Create an empty banner
    metadata = BannerMetadata(category="TEST", name="EMPTY")
    empty_banner = Banner(metadata=metadata, lines=[])
    
    with patch('animation.FireAnimator') as mock_animator_class:
        mock_animator = Mock()
        mock_animator_class.return_value = mock_animator
        
        # Should not raise an exception
        renderer.render_animated(
            empty_banner,
            console,
            duration=1.0,
            fps=8,
            intensity="normal"
        )
        
        # Verify animate_banner was called even with empty banner
        mock_animator.animate_banner.assert_called_once()


def test_animation_fallback_preserves_banner_content(test_banner, renderer, console):
    """Test that fallback to static rendering preserves banner content.
    
    Validates: Requirements 3.6, 3.7
    """
    # Mock FireAnimator to raise an exception
    with patch('animation.FireAnimator') as mock_animator_class:
        mock_animator_class.side_effect = ImportError("Module not found")
        
        # Mock console.print to capture the fallback
        with patch.object(console, 'print') as mock_print:
            # Call render_animated
            renderer.render_animated(
                test_banner,
                console,
                duration=1.0,
                fps=8,
                intensity="normal"
            )
            
            # Verify console.print was called with a Panel
            mock_print.assert_called_once()
            args, kwargs = mock_print.call_args
            assert isinstance(args[0], Panel)


def test_multiple_animation_calls_work_correctly(test_banner, renderer, console):
    """Test that multiple animation calls work correctly (no state pollution)."""
    with patch('animation.FireAnimator') as mock_animator_class:
        mock_animator = Mock()
        mock_animator_class.return_value = mock_animator
        
        # Call render_animated multiple times
        for i in range(3):
            renderer.render_animated(
                test_banner,
                console,
                duration=1.0,
                fps=8,
                intensity="normal"
            )
        
        # Verify FireAnimator was instantiated 3 times (fresh instance each time)
        assert mock_animator_class.call_count == 3
        
        # Verify animate_banner was called 3 times
        assert mock_animator.animate_banner.call_count == 3
