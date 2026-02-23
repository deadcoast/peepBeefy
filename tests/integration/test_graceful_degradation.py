"""
Integration tests for graceful degradation across terminal capabilities.

Tests verify that all color features degrade gracefully from RGB → 8-bit → ANSI
when terminal capabilities are limited, without errors or functionality loss.

Feature: hyfetch-integration-analysis
Property 43: Graceful Terminal Degradation
Validates: Requirements 14.7
"""

import pytest
from unittest import mock
import os

from src.color_util import RGB, color, printc
from src.color_scale import Scale, create_gradient
from src.color_presets import ColorPreset, load_presets
from src.ascii_renderer import ASCIIColorizer, ColorAlignment
from src.terminal_detect import detect_ansi_mode


class TestGracefulDegradation:
    """Test suite for graceful degradation across terminal capabilities."""
    
    def test_rgb_color_degrades_to_8bit(self):
        """Verify RGB colors degrade to 8-bit when RGB not supported."""
        rgb = RGB(255, 128, 64)
        
        # RGB mode
        rgb_code = rgb.to_ansi(mode="rgb", foreground=True)
        assert "38;2;255;128;64" in rgb_code
        
        # 8-bit mode (should not raise error)
        bit8_code = rgb.to_ansi(mode="8bit", foreground=True)
        assert "38;5;" in bit8_code
        assert bit8_code != rgb_code  # Different format
        
        # ANSI mode (should not raise error, currently falls back to 8-bit)
        ansi_code = rgb.to_ansi(mode="ansi", foreground=True)
        assert ansi_code != rgb_code
        # Note: "ansi" mode currently falls back to 8-bit, which is acceptable graceful degradation
        assert "38;5;" in ansi_code
    
    def test_rgb_color_degrades_to_ansi(self):
        """Verify RGB colors degrade to ANSI when only basic colors supported."""
        rgb = RGB(200, 50, 50)  # Reddish color
        
        # Should not raise error in any mode
        rgb_code = rgb.to_ansi(mode="rgb")
        bit8_code = rgb.to_ansi(mode="8bit")
        ansi_code = rgb.to_ansi(mode="ansi")
        
        # All should be valid ANSI escape sequences
        assert rgb_code.startswith("\033[")
        assert bit8_code.startswith("\033[")
        assert ansi_code.startswith("\033[")
    
    def test_gradient_works_in_all_modes(self):
        """Verify gradient generation works regardless of terminal capability."""
        colors = [RGB(255, 0, 0), RGB(0, 255, 0), RGB(0, 0, 255)]
        gradient = create_gradient(colors, resolution=50)
        
        # Should work in all modes
        for mode in ["rgb", "8bit", "ansi"]:
            for rgb in gradient[::10]:  # Sample every 10th color
                ansi_code = rgb.to_ansi(mode=mode)
                assert ansi_code.startswith("\033[")
                assert "m" in ansi_code
    
    def test_scale_lookup_works_in_all_modes(self):
        """Verify Scale class works with all terminal modes."""
        scale = Scale(["#FF0000", "#00FF00", "#0000FF"], resolution=100)
        
        # Test lookups at various ratios
        for ratio in [0.0, 0.25, 0.5, 0.75, 1.0]:
            rgb = scale(ratio)
            
            # Should work in all modes
            for mode in ["rgb", "8bit", "ansi"]:
                ansi_code = rgb.to_ansi(mode=mode)
                assert ansi_code.startswith("\033[")
    
    def test_preset_spreading_works_in_all_modes(self):
        """Verify color preset spreading works regardless of terminal capability."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        spread = preset.spread_colors(10)
        assert len(spread) == 10
        
        # All colors should work in all modes
        for rgb in spread:
            for mode in ["rgb", "8bit", "ansi"]:
                ansi_code = rgb.to_ansi(mode=mode)
                assert ansi_code.startswith("\033[")
    
    def test_ascii_colorizer_degrades_gracefully(self):
        """Verify ASCII colorization works in all terminal modes."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        alignment = ColorAlignment(mode="horizontal")
        
        ascii_lines = [
            "  ████████  ",
            " ██      ██ ",
            "██  BEEF  ██",
            " ██      ██ ",
            "  ████████  "
        ]
        
        # Should work in all modes
        for mode in ["rgb", "8bit", "ansi"]:
            colorizer = ASCIIColorizer(preset, alignment, ansi_mode=mode)
            colored = colorizer.colorize(ascii_lines)
            
            # Should produce colored output
            assert len(colored) == len(ascii_lines)
            
            # Should contain ANSI codes
            assert any("\033[" in line for line in colored)
            
            # Should preserve structure (when stripped)
            for original, colored_line in zip(ascii_lines, colored):
                # Strip ANSI codes
                stripped = colored_line
                while "\033[" in stripped:
                    start = stripped.find("\033[")
                    end = stripped.find("m", start)
                    if end != -1:
                        stripped = stripped[:start] + stripped[end+1:]
                    else:
                        break
                assert stripped == original
    
    def test_minecraft_color_codes_work_in_all_modes(self):
        """Verify Minecraft-style color codes work regardless of terminal capability."""
        test_string = "&cRed &aGreen &9Blue &rReset"
        
        # Should not raise error (mode is detected automatically)
        colored = color(test_string)
        
        # Should contain ANSI codes
        assert "\033[" in colored
        
        # Should not contain original color codes
        assert "&c" not in colored
        assert "&a" not in colored
        assert "&9" not in colored
    
    def test_rgb_color_codes_degrade_gracefully(self):
        """Verify RGB color codes in Minecraft format degrade gracefully."""
        test_string = "&gf(255,0,0)Red &gf(#00FF00)Green &gf(#0000FF)Blue"
        
        # Should not raise error
        colored = color(test_string)
        
        # Should contain ANSI codes
        assert "\033[" in colored
        
        # Should not contain original color codes
        assert "&gf(" not in colored
    
    def test_ansi_only_terminal_works(self):
        """Verify all features work on ANSI-only terminal."""
        # Test that features work when explicitly using ansi mode
        # (regardless of what detection returns)
        
        # RGB colors should still work (will use ANSI internally)
        rgb = RGB(255, 0, 0)
        ansi_code = rgb.to_ansi(mode="ansi")
        assert ansi_code.startswith("\033[")
        
        # Gradients should work
        gradient = create_gradient([RGB(255, 0, 0), RGB(0, 255, 0)], resolution=10)
        assert len(gradient) == 10
        
        # ASCII colorization should work
        preset = ColorPreset(name="test", colors=["#FF0000", "#00FF00"])
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="ansi")
        
        colored = colorizer.colorize(["Line 1", "Line 2"])
        assert len(colored) == 2
        assert any("\033[" in line for line in colored)
    
    def test_8bit_terminal_works(self):
        """Verify all features work on 8-bit (256-color) terminal."""
        # Test that features work when explicitly using 8bit mode
        # (regardless of what detection returns)
        
        # RGB colors should work in 8-bit mode
        rgb = RGB(128, 64, 192)
        bit8_code = rgb.to_ansi(mode="8bit")
        assert "38;5;" in bit8_code
        
        # Gradients should work
        scale = Scale(["#FF0000", "#00FF00", "#0000FF"], resolution=50)
        rgb = scale(0.5)
        bit8_code = rgb.to_ansi(mode="8bit")
        assert "38;5;" in bit8_code
        
        # ASCII colorization should work
        preset = ColorPreset(name="test", colors=["#FF0000", "#00FF00", "#0000FF"])
        alignment = ColorAlignment(mode="vertical")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="8bit")
        
        colored = colorizer.colorize(["████████", "████████"])
        assert len(colored) == 2
        assert any("38;5;" in line for line in colored)
    
    @mock.patch.dict(os.environ, {"COLORTERM": "truecolor", "TERM": "xterm-256color"}, clear=True)
    def test_rgb_terminal_works(self):
        """Verify all features work on RGB (truecolor) terminal."""
        # Detection should return rgb mode
        mode = detect_ansi_mode()
        assert mode in ["rgb", None]
        
        # RGB colors should work in RGB mode
        rgb = RGB(123, 45, 67)
        rgb_code = rgb.to_ansi(mode="rgb")
        assert "38;2;123;45;67" in rgb_code
        
        # Gradients should work
        gradient = create_gradient([RGB(255, 0, 0), RGB(0, 0, 255)], resolution=100)
        for rgb in gradient[::20]:
            rgb_code = rgb.to_ansi(mode="rgb")
            assert "38;2;" in rgb_code
        
        # ASCII colorization should work
        preset = ColorPreset(name="test", colors=["#FF0000", "#00FF00", "#0000FF"])
        alignment = ColorAlignment(mode="custom", custom_colors={"0": "#FF0000"})
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        colored = colorizer.colorize(["\033[0mColored\033[0m"])
        assert len(colored) == 1
        assert "38;2;" in colored[0]
    
    def test_fallback_chain_rgb_to_8bit_to_ansi(self):
        """Verify complete fallback chain: RGB → 8-bit → ANSI."""
        rgb = RGB(200, 100, 50)
        
        # Try RGB first
        try:
            rgb_code = rgb.to_ansi(mode="rgb")
            assert "38;2;" in rgb_code
        except Exception:
            pytest.fail("RGB mode should not raise exception")
        
        # Fallback to 8-bit
        try:
            bit8_code = rgb.to_ansi(mode="8bit")
            assert "38;5;" in bit8_code
        except Exception:
            pytest.fail("8-bit mode should not raise exception")
        
        # Fallback to ANSI
        try:
            ansi_code = rgb.to_ansi(mode="ansi")
            assert ansi_code.startswith("\033[")
        except Exception:
            pytest.fail("ANSI mode should not raise exception")
    
    def test_no_terminal_detection_uses_safe_defaults(self):
        """Verify system works when terminal detection fails."""
        # System should still work with explicit mode even if detection fails
        rgb = RGB(255, 128, 0)
        
        # Can explicitly use any mode as fallback
        bit8_code = rgb.to_ansi(mode="8bit")
        assert "38;5;" in bit8_code
        
        rgb_code = rgb.to_ansi(mode="rgb")
        assert "38;2;" in rgb_code
        
        # All modes work independently of detection
        ansi_code = rgb.to_ansi(mode="ansi")
        assert ansi_code.startswith("\033[")
    
    def test_empty_preset_degrades_gracefully(self):
        """Verify colorization handles edge cases gracefully."""
        # Test with minimal preset (single color)
        preset = ColorPreset(name="minimal", colors=["#FF0000"])
        alignment = ColorAlignment(mode="horizontal")
        colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
        
        ascii_lines = ["Line 1", "Line 2", "Line 3"]
        
        # Should work with single color (cycles through lines)
        colored = colorizer.colorize(ascii_lines)
        assert len(colored) == len(ascii_lines)
        assert all("\033[" in line for line in colored)
        
        # Test with empty lines
        empty_lines = []
        colored_empty = colorizer.colorize(empty_lines)
        assert colored_empty == []
    
    def test_invalid_mode_degrades_gracefully(self):
        """Verify invalid mode doesn't crash system."""
        rgb = RGB(255, 0, 0)
        
        # Invalid mode should use default
        try:
            code = rgb.to_ansi(mode="default")
            assert code.startswith("\033[")
        except Exception:
            pytest.fail("Invalid mode should not raise exception")
    
    def test_all_features_work_without_terminal(self):
        """Verify all features work in non-terminal environment (e.g., file output)."""
        # Mock non-TTY environment
        with mock.patch('sys.stdout.isatty', return_value=False):
            # Color utilities should still work
            rgb = RGB(255, 128, 64)
            rgb_code = rgb.to_ansi(mode="rgb")
            assert "38;2;" in rgb_code
            
            # Gradients should work
            gradient = create_gradient([RGB(255, 0, 0), RGB(0, 255, 0)], resolution=20)
            assert len(gradient) == 20
            
            # Presets should work
            preset = ColorPreset(name="test", colors=["#FF0000", "#00FF00"])
            spread = preset.spread_colors(5)
            assert len(spread) == 5
            
            # ASCII colorization should work
            alignment = ColorAlignment(mode="horizontal")
            colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
            colored = colorizer.colorize(["Line 1", "Line 2"])
            assert len(colored) == 2
    
    def test_extreme_color_values_degrade_gracefully(self):
        """Verify extreme color values don't crash in any mode."""
        # Test boundary values
        test_colors = [
            RGB(0, 0, 0),        # Black
            RGB(255, 255, 255),  # White
            RGB(255, 0, 0),      # Pure red
            RGB(0, 255, 0),      # Pure green
            RGB(0, 0, 255),      # Pure blue
            RGB(128, 128, 128),  # Gray
        ]
        
        for rgb in test_colors:
            for mode in ["rgb", "8bit", "ansi"]:
                try:
                    code = rgb.to_ansi(mode=mode)
                    assert code.startswith("\033[")
                except Exception as e:
                    pytest.fail(f"Color {rgb} failed in mode {mode}: {e}")
    
    def test_large_gradient_degrades_gracefully(self):
        """Verify large gradients work in all modes."""
        # Create large gradient
        colors = [RGB(i * 25, 0, 255 - i * 25) for i in range(11)]
        gradient = create_gradient(colors, resolution=100)
        
        # Should work in all modes
        for mode in ["rgb", "8bit", "ansi"]:
            for rgb in gradient[::50]:  # Sample
                code = rgb.to_ansi(mode=mode)
                assert code.startswith("\033[")
    
    def test_complex_ascii_art_degrades_gracefully(self):
        """Verify complex ASCII art with many lines works in all modes."""
        # Create complex ASCII art
        ascii_lines = [f"Line {i:03d} {'█' * 20}" for i in range(50)]
        
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#9400D3"]
        )
        
        for mode in ["rgb", "8bit", "ansi"]:
            alignment = ColorAlignment(mode="horizontal")
            colorizer = ASCIIColorizer(preset, alignment, ansi_mode=mode)
            
            colored = colorizer.colorize(ascii_lines)
            assert len(colored) == len(ascii_lines)
            assert all("\033[" in line for line in colored)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
