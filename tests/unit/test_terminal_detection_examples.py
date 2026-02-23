"""
Unit tests for terminal detection examples.

Tests specific environment variable combinations and platform scenarios
to verify correct ANSI mode detection.

Requirements: 3.1-3.8
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Import the module under test
from src.terminal_detect import (
    unix_detect_ansi_mode,
    windows_detect_ansi_mode,
    detect_ansi_mode,
    AnsiMode
)


class TestUnixTerminalDetection(unittest.TestCase):
    """Test Unix-specific terminal detection scenarios."""
    
    def test_colorterm_truecolor_returns_rgb(self):
        """Test COLORTERM="truecolor" → rgb"""
        with patch.dict(os.environ, {"COLORTERM": "truecolor", "TERM": "xterm"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "rgb")
    
    def test_colorterm_24bit_returns_rgb(self):
        """Test COLORTERM="24bit" → rgb"""
        with patch.dict(os.environ, {"COLORTERM": "24bit", "TERM": "xterm"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "rgb")
    
    def test_colorterm_case_insensitive(self):
        """Test COLORTERM is case-insensitive"""
        with patch.dict(os.environ, {"COLORTERM": "TrueColor", "TERM": "xterm"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "rgb")
    
    def test_term_xterm_256color_returns_8bit(self):
        """Test TERM="xterm-256color" → 8bit"""
        with patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "8bit")
    
    def test_term_screen_256color_returns_8bit(self):
        """Test TERM="screen-256color" → 8bit"""
        with patch.dict(os.environ, {"TERM": "screen-256color"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "8bit")
    
    def test_term_linux_returns_ansi(self):
        """Test TERM="linux" → ansi"""
        with patch.dict(os.environ, {"TERM": "linux"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "ansi")
    
    def test_term_xterm_kitty_returns_rgb(self):
        """Test TERM="xterm-kitty" → rgb (special case)"""
        with patch.dict(os.environ, {"TERM": "xterm-kitty"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "rgb")
    
    def test_term_xterm_color_returns_8bit(self):
        """Test TERM="xterm-color" → 8bit"""
        with patch.dict(os.environ, {"TERM": "xterm-color"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "8bit")
    
    def test_term_ansi_returns_ansi(self):
        """Test TERM="ansi" → ansi"""
        with patch.dict(os.environ, {"TERM": "ansi"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "ansi")
    
    def test_colorterm_overrides_term(self):
        """Test COLORTERM takes precedence over TERM"""
        with patch.dict(os.environ, {"COLORTERM": "truecolor", "TERM": "xterm-256color"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "rgb")
    
    def test_unknown_term_returns_none(self):
        """Test unknown TERM value returns None"""
        with patch.dict(os.environ, {"TERM": "unknown-terminal"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertIsNone(result)
    
    def test_no_env_vars_returns_none(self):
        """Test missing environment variables returns None"""
        with patch.dict(os.environ, {}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertIsNone(result)


class TestWindowsTerminalDetection(unittest.TestCase):
    """Test Windows-specific terminal detection scenarios."""
    
    def test_conemu_ansi_on_returns_rgb(self):
        """Test ConEmuANSI="ON" → rgb"""
        with patch.dict(os.environ, {"ConEmuANSI": "ON"}, clear=True):
            with patch('platform.version', return_value="10.0.19041"):
                result = windows_detect_ansi_mode()
                self.assertEqual(result, "rgb")
    
    def test_conemu_ansi_case_insensitive(self):
        """Test ConEmuANSI is case-insensitive"""
        with patch.dict(os.environ, {"ConEmuANSI": "on"}, clear=True):
            with patch('platform.version', return_value="10.0.19041"):
                result = windows_detect_ansi_mode()
                self.assertEqual(result, "rgb")
    
    def test_windows_build_14931_returns_rgb(self):
        """Test Windows build 14931+ → rgb"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('platform.version', return_value="10.0.14931"):
                result = windows_detect_ansi_mode()
                self.assertEqual(result, "rgb")
    
    def test_windows_build_19041_returns_rgb(self):
        """Test Windows build 19041 (Win10 20H1) → rgb"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('platform.version', return_value="10.0.19041"):
                result = windows_detect_ansi_mode()
                self.assertEqual(result, "rgb")
    
    def test_windows_build_10586_returns_8bit(self):
        """Test Windows build 10586-14930 → 8bit"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('platform.version', return_value="10.0.10586"):
                result = windows_detect_ansi_mode()
                self.assertEqual(result, "8bit")
    
    def test_windows_build_14930_returns_8bit(self):
        """Test Windows build 14930 (just below RGB threshold) → 8bit"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('platform.version', return_value="10.0.14930"):
                result = windows_detect_ansi_mode()
                self.assertEqual(result, "8bit")
    
    def test_windows_build_10585_returns_ansi(self):
        """Test Windows build < 10586 → ansi"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('platform.version', return_value="10.0.10585"):
                result = windows_detect_ansi_mode()
                self.assertEqual(result, "ansi")
    
    def test_windows_build_10240_returns_ansi(self):
        """Test Windows build 10240 (Win10 RTM) → ansi"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('platform.version', return_value="10.0.10240"):
                result = windows_detect_ansi_mode()
                self.assertEqual(result, "ansi")
    
    def test_conemu_overrides_build_version(self):
        """Test ConEmuANSI takes precedence over build version"""
        with patch.dict(os.environ, {"ConEmuANSI": "ON"}, clear=True):
            with patch('platform.version', return_value="10.0.10240"):
                result = windows_detect_ansi_mode()
                self.assertEqual(result, "rgb")
    
    def test_invalid_version_format_returns_none(self):
        """Test invalid version format returns None"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('platform.version', return_value="invalid"):
                result = windows_detect_ansi_mode()
                self.assertIsNone(result)
    
    def test_short_version_format_returns_none(self):
        """Test short version format (missing build) returns None"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('platform.version', return_value="10.0"):
                result = windows_detect_ansi_mode()
                self.assertIsNone(result)
    
    def test_version_exception_returns_none(self):
        """Test exception during version parsing returns None"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('platform.version', side_effect=Exception("Test error")):
                result = windows_detect_ansi_mode()
                self.assertIsNone(result)


class TestPlatformAgnosticDetection(unittest.TestCase):
    """Test platform-agnostic detection wrapper."""
    
    def test_linux_platform_calls_unix_detection(self):
        """Test Linux platform uses Unix detection"""
        with patch('platform.system', return_value="Linux"):
            with patch.dict(os.environ, {"COLORTERM": "truecolor"}, clear=True):
                result = detect_ansi_mode()
                self.assertEqual(result, "rgb")
    
    def test_darwin_platform_calls_unix_detection(self):
        """Test macOS (Darwin) platform uses Unix detection"""
        with patch('platform.system', return_value="Darwin"):
            with patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=True):
                result = detect_ansi_mode()
                self.assertEqual(result, "8bit")
    
    def test_freebsd_platform_calls_unix_detection(self):
        """Test FreeBSD platform uses Unix detection"""
        with patch('platform.system', return_value="FreeBSD"):
            with patch.dict(os.environ, {"TERM": "linux"}, clear=True):
                result = detect_ansi_mode()
                self.assertEqual(result, "ansi")
    
    def test_windows_platform_calls_windows_detection(self):
        """Test Windows platform uses Windows detection"""
        with patch('platform.system', return_value="Windows"):
            with patch.dict(os.environ, {"ConEmuANSI": "ON"}, clear=True):
                with patch('platform.version', return_value="10.0.19041"):
                    result = detect_ansi_mode()
                    self.assertEqual(result, "rgb")
    
    def test_unknown_platform_returns_none(self):
        """Test unknown platform returns None"""
        with patch('platform.system', return_value="UnknownOS"):
            result = detect_ansi_mode()
            self.assertIsNone(result)
    
    def test_platform_exception_returns_none(self):
        """Test exception during platform detection returns None"""
        with patch('platform.system', side_effect=Exception("Test error")):
            result = detect_ansi_mode()
            self.assertIsNone(result)
    
    def test_case_insensitive_platform_names(self):
        """Test platform names are case-insensitive"""
        with patch('platform.system', return_value="LINUX"):
            with patch.dict(os.environ, {"COLORTERM": "truecolor"}, clear=True):
                result = detect_ansi_mode()
                self.assertEqual(result, "rgb")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_empty_colorterm_value(self):
        """Test empty COLORTERM value"""
        with patch.dict(os.environ, {"COLORTERM": "", "TERM": "xterm-256color"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "8bit")
    
    def test_empty_term_value(self):
        """Test empty TERM value"""
        with patch.dict(os.environ, {"TERM": ""}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertIsNone(result)
    
    def test_whitespace_in_env_vars(self):
        """Test whitespace in environment variables"""
        with patch.dict(os.environ, {"COLORTERM": " truecolor ", "TERM": "xterm"}, clear=True):
            result = unix_detect_ansi_mode()
            # Should still detect truecolor (after lower())
            self.assertEqual(result, "rgb")
    
    def test_partial_match_in_term(self):
        """Test partial matches in TERM variable"""
        with patch.dict(os.environ, {"TERM": "my-custom-256color-terminal"}, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "8bit")
    
    def test_windows_build_boundary_14931(self):
        """Test exact boundary at build 14931"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('platform.version', return_value="10.0.14931"):
                result = windows_detect_ansi_mode()
                self.assertEqual(result, "rgb")
    
    def test_windows_build_boundary_10586(self):
        """Test exact boundary at build 10586"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('platform.version', return_value="10.0.10586"):
                result = windows_detect_ansi_mode()
                self.assertEqual(result, "8bit")


class TestRealWorldScenarios(unittest.TestCase):
    """Test real-world terminal configurations."""
    
    def test_gnome_terminal(self):
        """Test typical GNOME Terminal configuration"""
        with patch.dict(os.environ, {
            "COLORTERM": "truecolor",
            "TERM": "xterm-256color"
        }, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "rgb")
    
    def test_kitty_terminal(self):
        """Test Kitty terminal configuration"""
        with patch.dict(os.environ, {
            "TERM": "xterm-kitty"
        }, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "rgb")
    
    def test_tmux_session(self):
        """Test tmux session configuration"""
        with patch.dict(os.environ, {
            "TERM": "screen-256color"
        }, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "8bit")
    
    def test_linux_console(self):
        """Test Linux console (no X11)"""
        with patch.dict(os.environ, {
            "TERM": "linux"
        }, clear=True):
            result = unix_detect_ansi_mode()
            self.assertEqual(result, "ansi")
    
    def test_windows_terminal_modern(self):
        """Test modern Windows Terminal"""
        with patch('platform.system', return_value="Windows"):
            with patch.dict(os.environ, {}, clear=True):
                with patch('platform.version', return_value="10.0.22000"):
                    result = detect_ansi_mode()
                    self.assertEqual(result, "rgb")
    
    def test_conemu_terminal(self):
        """Test ConEmu terminal"""
        with patch('platform.system', return_value="Windows"):
            with patch.dict(os.environ, {"ConEmuANSI": "ON"}, clear=True):
                with patch('platform.version', return_value="10.0.19041"):
                    result = detect_ansi_mode()
                    self.assertEqual(result, "rgb")
    
    def test_old_windows_cmd(self):
        """Test old Windows CMD (pre-ANSI support)"""
        with patch('platform.system', return_value="Windows"):
            with patch.dict(os.environ, {}, clear=True):
                with patch('platform.version', return_value="10.0.10240"):
                    result = detect_ansi_mode()
                    self.assertEqual(result, "ansi")


if __name__ == "__main__":
    unittest.main()
