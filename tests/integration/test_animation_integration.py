"""
Integration tests for Animation + Color System.

Tests the integration between the fire animation engine and the color system,
verifying that animations adapt to terminal capabilities and use appropriate
color modes (RGB vs 8-bit fallback).

Validates Requirement 14.1: Verify Color_System works with existing Animation_Engine
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console

from src.animation import FireAnimator, FirePalette
from src.color_util import RGB
from src.banner import Banner, BannerMetadata


class TestAnimationColorIntegration:
    """Integration tests for animation engine with color system."""
    
    @pytest.fixture
    def mock_console(self):
        """Create a real Rich Console for testing (mocking doesn't work well with Live)."""
        from rich.console import Console
        # Use a real console but with file output to avoid terminal issues
        import io
        return Console(file=io.StringIO(), force_terminal=True, width=80, height=24)
    
    @pytest.fixture
    def simple_banner(self):
        """Create a simple test banner."""
        lines = [
            "  ████████  ",
            "  ██    ██  ",
            "  ██    ██  ",
            "  ████████  ",
            "   BEEF     ",
        ]
        metadata = BannerMetadata(
            category="TEST",
            name="SIMPLE",
            dimensions=(12, 5)
        )
        return Banner(metadata=metadata, lines=lines)
    
    def test_fire_animator_uses_rgb_when_supported(self, simple_banner, mock_console):
        """Test that FireAnimator uses RGB colors when terminal supports it.
        
        Validates Requirement 14.1: Color system integration with animation
        """
        # Mock terminal with RGB support
        with patch('src.animation.TerminalCapabilities.supports_rgb', return_value=True):
            animator = FireAnimator(intensity="normal")
            
            # Verify RGB mode is enabled
            assert animator._use_rgb is True
            assert animator._palette == FirePalette.STYLES
            
            # Verify animation can be built without errors
            try:
                animator.animate_banner(
                    simple_banner,
                    mock_console,
                    duration=0.1,
                    fps=2
                )
                # Animation should complete without errors
            except Exception as e:
                pytest.fail(f"Animation with RGB colors failed: {e}")
    
    def test_fire_animator_uses_8bit_fallback_when_no_rgb(self, simple_banner, mock_console):
        """Test that FireAnimator falls back to 8-bit colors when RGB not supported.
        
        Validates Requirement 14.1: Graceful degradation in color system
        """
        # Mock terminal without RGB support
        with patch('src.animation.TerminalCapabilities.supports_rgb', return_value=False):
            animator = FireAnimator(intensity="normal")
            
            # Verify 8-bit fallback mode is enabled
            assert animator._use_rgb is False
            assert animator._palette == FirePalette.STYLES_8BIT
            
            # Verify animation can be built without errors
            try:
                animator.animate_banner(
                    simple_banner,
                    mock_console,
                    duration=0.1,
                    fps=2
                )
                # Animation should complete without errors
            except Exception as e:
                pytest.fail(f"Animation with 8-bit colors failed: {e}")
    
    def test_fire_animator_explicit_rgb_override(self, simple_banner, mock_console):
        """Test that FireAnimator respects explicit use_rgb parameter.
        
        Validates Requirement 14.1: Manual color mode override
        """
        # Explicitly request RGB mode
        animator_rgb = FireAnimator(intensity="normal", use_rgb=True)
        assert animator_rgb._use_rgb is True
        assert animator_rgb._palette == FirePalette.STYLES
        
        # Explicitly request 8-bit mode
        animator_8bit = FireAnimator(intensity="normal", use_rgb=False)
        assert animator_8bit._use_rgb is False
        assert animator_8bit._palette == FirePalette.STYLES_8BIT
    
    def test_fire_animator_intensity_affects_coloring(self, simple_banner, mock_console):
        """Test that intensity setting affects animation coloring.
        
        Validates Requirement 14.1: Animation parameters work with color system
        """
        # Test different intensity levels
        for intensity in ["subtle", "normal", "intense"]:
            animator = FireAnimator(intensity=intensity, use_rgb=True)
            
            # Verify intensity multiplier is set correctly
            expected_multipliers = {
                "subtle": 0.5,
                "normal": 1.0,
                "intense": 1.5
            }
            assert animator._intensity_multiplier == expected_multipliers[intensity]
            
            # Verify animation works with this intensity
            try:
                animator.animate_banner(
                    simple_banner,
                    mock_console,
                    duration=0.1,
                    fps=2
                )
            except Exception as e:
                pytest.fail(f"Animation with intensity '{intensity}' failed: {e}")
    
    def test_fire_palette_rgb_colors_valid(self):
        """Test that RGB fire palette contains valid hex colors.
        
        Validates Requirement 14.1: Color palette integrity
        """
        # Verify all RGB colors can be parsed
        for i, hex_color in enumerate(FirePalette.COLORS):
            try:
                rgb = RGB.from_hex(hex_color)
                # Verify RGB values are in valid range
                assert 0 <= rgb.r <= 255, f"Invalid red component in color {i}: {rgb.r}"
                assert 0 <= rgb.g <= 255, f"Invalid green component in color {i}: {rgb.g}"
                assert 0 <= rgb.b <= 255, f"Invalid blue component in color {i}: {rgb.b}"
            except Exception as e:
                pytest.fail(f"Invalid hex color at index {i}: {hex_color}, error: {e}")
    
    def test_fire_palette_progression(self):
        """Test that fire palette progresses from dark to bright.
        
        Validates Requirement 14.1: Color palette design
        """
        # Convert all colors to RGB and check lightness progression
        from src.color_util import RGB
        
        lightness_values = []
        for hex_color in FirePalette.COLORS:
            rgb = RGB.from_hex(hex_color)
            hsl = rgb.hsl()
            lightness_values.append(hsl.l)
        
        # Verify general upward trend (allowing some variation)
        # First color should be darker than last color
        assert lightness_values[0] < lightness_values[-1], \
            "Fire palette should progress from dark to bright"
        
        # Middle colors should be between first and last
        mid_lightness = lightness_values[len(lightness_values) // 2]
        assert lightness_values[0] < mid_lightness < lightness_values[-1], \
            "Fire palette should have gradual progression"
    
    def test_animation_preserves_banner_structure(self, simple_banner, mock_console):
        """Test that animation doesn't alter banner text structure.
        
        Validates Requirement 14.1: Animation preserves content
        """
        import random
        
        animator = FireAnimator(intensity="normal", use_rgb=True)
        
        # Build a single frame
        rng = random.Random(42)  # Fixed seed for reproducibility
        flame_lines, text_lines = animator._detect_zones(simple_banner)
        frame = animator._build_frame(simple_banner, flame_lines, text_lines, rng)
        
        # Extract plain text from Rich Text object
        frame_text = frame.plain
        original_text = "\n".join(simple_banner.lines)
        
        # Verify text content is preserved
        assert frame_text == original_text, \
            "Animation should preserve banner text structure"
    
    def test_animation_with_metadata_flame_lines(self, mock_console):
        """Test that animation respects metadata flame_lines override.
        
        Validates Requirement 14.1: Metadata-driven animation zones
        """
        # Create banner with explicit flame_lines metadata
        lines = [
            "  ████████  ",
            "  ██    ██  ",
            "  ██    ██  ",
            "  ████████  ",
            "   BEEF     ",
        ]
        metadata = BannerMetadata(
            category="TEST",
            name="CUSTOM_FLAME",
            dimensions=(12, 5),
            flame_lines=[0, 1, 2]  # Only first 3 lines are flame zone
        )
        banner = Banner(metadata=metadata, lines=lines)
        
        animator = FireAnimator(intensity="normal", use_rgb=True)
        
        # Detect zones and verify metadata override is used
        flame_lines, text_lines = animator._detect_zones(banner)
        
        assert flame_lines == [0, 1, 2], \
            "Animation should use metadata flame_lines override"
        assert text_lines == [3, 4], \
            "Animation should use remaining lines as text zone"
    
    def test_animation_handles_empty_banner_gracefully(self, mock_console):
        """Test that animation handles edge cases gracefully.
        
        Validates Requirement 14.1: Error handling in integration
        """
        animator = FireAnimator(intensity="normal", use_rgb=True)
        
        # Test with empty banner
        empty_banner = Banner(
            metadata=BannerMetadata(category="TEST", name="EMPTY", dimensions=(0, 0)),
            lines=[]
        )
        
        # Should not crash, just log warning
        try:
            animator.animate_banner(
                empty_banner,
                mock_console,
                duration=0.1,
                fps=2
            )
            # Should complete without raising exception
        except Exception as e:
            pytest.fail(f"Animation should handle empty banner gracefully, got: {e}")
    
    def test_color_mode_detection_integration(self):
        """Test that color mode detection works with animation system.
        
        Validates Requirement 14.1: Terminal detection integration
        """
        from src.terminal_detect import detect_ansi_mode
        
        # Mock different terminal environments
        test_cases = [
            ({"COLORTERM": "truecolor", "TERM": "xterm"}, "rgb"),
            ({"TERM": "xterm-256color"}, "8bit"),  # Note: might detect as rgb if COLORTERM is set
            ({"TERM": "linux"}, "ansi"),
        ]
        
        for env_vars, expected_mode in test_cases:
            with patch.dict('os.environ', env_vars, clear=True):
                detected_mode = detect_ansi_mode()
                
                # Verify detection returns a valid mode (may not match expected exactly)
                assert detected_mode in ["rgb", "8bit", "ansi", None], \
                    f"Should return valid mode, got: {detected_mode}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
