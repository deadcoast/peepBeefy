"""
Unit tests for OSC (Operating System Command) detection.

Tests timeout handling, screen/tmux skip logic, and terminal mode restoration
for background color detection using OSC sequences.

Requirements: 10.1-10.7
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import sys
import os

# Import the module under test
from src.terminal_detect import (
    unix_read_osc,
    parse_osc_rgb_response,
    get_background_color,
    _UNIX_MODULES_AVAILABLE
)


class TestOSCTimeoutHandling(unittest.TestCase):
    """Test timeout handling for OSC queries."""
    
    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    def test_timeout_returns_none(self, mock_setraw, mock_tcsetattr, mock_tcgetattr, 
                                   mock_select, mock_fileno, mock_isatty):
        """Test that timeout returns None without blocking"""
        # Setup: select returns empty (timeout)
        mock_select.return_value = ([], [], [])
        mock_tcgetattr.return_value = ['mock', 'settings']
        
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        # Verify timeout occurred
        self.assertIsNone(result)
        
        # Verify select was called with correct timeout
        mock_select.assert_called_once()
        args = mock_select.call_args[0]
        timeout_arg = mock_select.call_args[0][3]
        self.assertAlmostEqual(timeout_arg, 0.05, places=3)  # 50ms = 0.05s

    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    def test_custom_timeout_respected(self, mock_setraw, mock_tcsetattr, mock_tcgetattr,
                                      mock_select, mock_fileno, mock_isatty):
        """Test that custom timeout values are respected"""
        # Setup: select returns empty (timeout)
        mock_select.return_value = ([], [], [])
        mock_tcgetattr.return_value = ['mock', 'settings']
        
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=500)
        
        # Verify custom timeout was used
        timeout_arg = mock_select.call_args[0][3]
        self.assertAlmostEqual(timeout_arg, 0.5, places=3)  # 500ms = 0.5s
    
    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('sys.stdin.read')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_successful_response_within_timeout(self, mock_flush, mock_write, mock_setraw,
                                                 mock_tcsetattr, mock_tcgetattr, mock_read,
                                                 mock_select, mock_fileno, mock_isatty):
        """Test successful OSC response received within timeout"""
        # Setup: select returns ready, stdin has response
        mock_select.return_value = ([sys.stdin], [], [])
        mock_tcgetattr.return_value = ['mock', 'settings']
        
        # Simulate OSC response: ESC ] 11 ; rgb:FFFF/0000/0000 BEL
        response_chars = list("\033]11;rgb:ffff/0000/0000\007")
        mock_read.side_effect = response_chars
        
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        # Verify response was received
        self.assertIsNotNone(result)
        self.assertIn("rgb:ffff/0000/0000", result)


class TestScreenTmuxSkipLogic(unittest.TestCase):
    """Test that OSC detection is skipped for screen/tmux terminals."""
    
    def test_screen_terminal_skipped(self):
        """Test that screen terminal skips OSC detection"""
        with patch.dict(os.environ, {"TERM": "screen"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        # Should return None without attempting OSC query
        self.assertIsNone(result)
    
    def test_screen_256color_terminal_skipped(self):
        """Test that screen-256color terminal skips OSC detection"""
        with patch.dict(os.environ, {"TERM": "screen-256color"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        self.assertIsNone(result)
    
    def test_tmux_terminal_skipped(self):
        """Test that tmux terminal skips OSC detection"""
        with patch.dict(os.environ, {"TERM": "tmux"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        self.assertIsNone(result)
    
    def test_tmux_256color_terminal_skipped(self):
        """Test that tmux-256color terminal skips OSC detection"""
        with patch.dict(os.environ, {"TERM": "tmux-256color"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        self.assertIsNone(result)
    
    def test_screen_in_term_name_skipped(self):
        """Test that any TERM containing 'screen' is skipped"""
        with patch.dict(os.environ, {"TERM": "my-screen-terminal"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        self.assertIsNone(result)
    
    def test_tmux_in_term_name_skipped(self):
        """Test that any TERM containing 'tmux' is skipped"""
        with patch.dict(os.environ, {"TERM": "custom-tmux-256"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        self.assertIsNone(result)
    
    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    def test_xterm_not_skipped(self, mock_setraw, mock_tcsetattr, mock_tcgetattr,
                                mock_select, mock_fileno, mock_isatty):
        """Test that regular xterm is NOT skipped"""
        # Setup: select returns empty (timeout) - we just want to verify it attempts the query
        mock_select.return_value = ([], [], [])
        mock_tcgetattr.return_value = ['mock', 'settings']
        
        with patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        # Should attempt the query (even if it times out)
        mock_setraw.assert_called_once()


class TestTerminalModeRestoration(unittest.TestCase):
    """Test that terminal mode is always restored after OSC query."""
    
    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    def test_terminal_mode_restored_on_timeout(self, mock_setraw, mock_tcsetattr,
                                                mock_tcgetattr, mock_select,
                                                mock_fileno, mock_isatty):
        """Test terminal mode is restored even when timeout occurs"""
        # Setup
        mock_select.return_value = ([], [], [])
        original_settings = ['original', 'terminal', 'settings']
        mock_tcgetattr.return_value = original_settings
        
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        # Verify terminal settings were saved
        mock_tcgetattr.assert_called_once_with(1)
        
        # Verify terminal was set to raw mode
        mock_setraw.assert_called_once_with(1)
        
        # Verify terminal settings were restored
        mock_tcsetattr.assert_called_once()
        restore_call = mock_tcsetattr.call_args
        self.assertEqual(restore_call[0][0], 1)  # fd
        self.assertEqual(restore_call[0][2], original_settings)  # settings
    
    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('sys.stdin.read')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_terminal_mode_restored_on_success(self, mock_flush, mock_write, mock_setraw,
                                                mock_tcsetattr, mock_tcgetattr, mock_read,
                                                mock_select, mock_fileno, mock_isatty):
        """Test terminal mode is restored after successful response"""
        # Setup
        mock_select.return_value = ([sys.stdin], [], [])
        original_settings = ['original', 'terminal', 'settings']
        mock_tcgetattr.return_value = original_settings
        
        # Simulate OSC response
        response_chars = list("\033]11;rgb:ffff/0000/0000\007")
        mock_read.side_effect = response_chars
        
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        # Verify terminal settings were restored
        mock_tcsetattr.assert_called_once()
        restore_call = mock_tcsetattr.call_args
        self.assertEqual(restore_call[0][2], original_settings)

    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw', side_effect=Exception("Test error"))
    def test_terminal_mode_restored_on_exception(self, mock_setraw, mock_tcsetattr,
                                                  mock_tcgetattr, mock_select,
                                                  mock_fileno, mock_isatty):
        """Test terminal mode is restored even when exception occurs"""
        # Setup
        original_settings = ['original', 'terminal', 'settings']
        mock_tcgetattr.return_value = original_settings
        
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        # Should return None due to exception
        self.assertIsNone(result)
        
        # Verify terminal settings were still restored (in finally block)
        mock_tcsetattr.assert_called_once()
        restore_call = mock_tcsetattr.call_args
        self.assertEqual(restore_call[0][2], original_settings)
    
    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('sys.stdin.read', side_effect=OSError("Read error"))
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_terminal_mode_restored_on_read_error(self, mock_flush, mock_write, mock_setraw,
                                                   mock_tcsetattr, mock_tcgetattr, mock_read,
                                                   mock_select, mock_fileno, mock_isatty):
        """Test terminal mode is restored when read operation fails"""
        # Setup
        mock_select.return_value = ([sys.stdin], [], [])
        original_settings = ['original', 'terminal', 'settings']
        mock_tcgetattr.return_value = original_settings
        
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        # Should return None due to read error
        self.assertIsNone(result)
        
        # Verify terminal settings were restored
        mock_tcsetattr.assert_called_once()
        restore_call = mock_tcsetattr.call_args
        self.assertEqual(restore_call[0][2], original_settings)


class TestOSCQuerySending(unittest.TestCase):
    """Test that OSC queries are sent correctly."""
    
    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_osc_11_query_format(self, mock_flush, mock_write, mock_setraw,
                                  mock_tcsetattr, mock_tcgetattr, mock_select,
                                  mock_fileno, mock_isatty):
        """Test that OSC 11 query is sent in correct format"""
        # Setup
        mock_select.return_value = ([], [], [])
        mock_tcgetattr.return_value = ['mock', 'settings']
        
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        # Verify OSC query was sent: ESC ] 11 ; ? BEL
        mock_write.assert_called_once_with("\033]11;?\007")
        mock_flush.assert_called_once()

    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_custom_osc_sequence_number(self, mock_flush, mock_write, mock_setraw,
                                         mock_tcsetattr, mock_tcgetattr, mock_select,
                                         mock_fileno, mock_isatty):
        """Test that custom OSC sequence numbers are supported"""
        # Setup
        mock_select.return_value = ([], [], [])
        mock_tcgetattr.return_value = ['mock', 'settings']
        
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=10, timeout_ms=50)
        
        # Verify OSC 10 query was sent (foreground color)
        mock_write.assert_called_once_with("\033]10;?\007")


class TestGetBackgroundColor(unittest.TestCase):
    """Test the high-level get_background_color function."""
    
    @patch('platform.system', return_value='Linux')
    @patch('src.terminal_detect.unix_read_osc')
    @patch('src.terminal_detect.parse_osc_rgb_response')
    def test_ssh_session_uses_longer_timeout(self, mock_parse, mock_read_osc, mock_system):
        """Test that SSH sessions use 500ms timeout"""
        from src.color_util import RGB
        
        # Setup: simulate SSH session
        with patch.dict(os.environ, {"SSH_CONNECTION": "192.168.1.1 12345 192.168.1.2 22"}, clear=True):
            mock_read_osc.return_value = "\033]11;rgb:ffff/0000/0000\007"
            mock_parse.return_value = RGB(255, 0, 0)
            
            result = get_background_color()
        
        # Verify 500ms timeout was used for SSH
        mock_read_osc.assert_called_once_with(seq=11, timeout_ms=500)
    
    @patch('platform.system', return_value='Linux')
    @patch('src.terminal_detect.unix_read_osc')
    @patch('src.terminal_detect.parse_osc_rgb_response')
    def test_local_session_uses_short_timeout(self, mock_parse, mock_read_osc, mock_system):
        """Test that local sessions use 50ms timeout"""
        from src.color_util import RGB
        
        # Setup: no SSH environment variables
        with patch.dict(os.environ, {}, clear=True):
            mock_read_osc.return_value = "\033]11;rgb:ffff/0000/0000\007"
            mock_parse.return_value = RGB(255, 0, 0)
            
            result = get_background_color()
        
        # Verify 50ms timeout was used for local
        mock_read_osc.assert_called_once_with(seq=11, timeout_ms=50)
    
    @patch('platform.system', return_value='Linux')
    @patch('src.terminal_detect.unix_read_osc')
    def test_ssh_client_env_var_detected(self, mock_read_osc, mock_system):
        """Test that SSH_CLIENT environment variable triggers SSH timeout"""
        # Setup: SSH_CLIENT instead of SSH_CONNECTION
        with patch.dict(os.environ, {"SSH_CLIENT": "192.168.1.1 12345 22"}, clear=True):
            mock_read_osc.return_value = None
            
            result = get_background_color()
        
        # Verify 500ms timeout was used
        mock_read_osc.assert_called_once_with(seq=11, timeout_ms=500)

    @patch('platform.system', return_value='Windows')
    def test_windows_returns_none(self, mock_system):
        """Test that Windows platform returns None (not supported)"""
        result = get_background_color()
        
        self.assertIsNone(result)
    
    @patch('platform.system', return_value='Linux')
    @patch('src.terminal_detect.unix_read_osc')
    def test_osc_timeout_returns_none(self, mock_read_osc, mock_system):
        """Test that OSC timeout results in None"""
        # Setup: unix_read_osc returns None (timeout)
        mock_read_osc.return_value = None
        
        with patch.dict(os.environ, {}, clear=True):
            result = get_background_color()
        
        self.assertIsNone(result)
    
    @patch('platform.system', return_value='Linux')
    @patch('src.terminal_detect.unix_read_osc')
    @patch('src.terminal_detect.parse_osc_rgb_response')
    def test_parse_failure_returns_none(self, mock_parse, mock_read_osc, mock_system):
        """Test that parse failure results in None"""
        # Setup: OSC response received but parsing fails
        mock_read_osc.return_value = "\033]11;invalid\007"
        mock_parse.return_value = None
        
        with patch.dict(os.environ, {}, clear=True):
            result = get_background_color()
        
        self.assertIsNone(result)
    
    @patch('platform.system', return_value='Linux')
    @patch('src.terminal_detect.unix_read_osc')
    @patch('src.terminal_detect.parse_osc_rgb_response')
    def test_successful_background_detection(self, mock_parse, mock_read_osc, mock_system):
        """Test successful background color detection"""
        from src.color_util import RGB
        
        # Setup: successful OSC response and parsing
        mock_read_osc.return_value = "\033]11;rgb:ffff/0000/0000\007"
        expected_rgb = RGB(255, 0, 0)
        mock_parse.return_value = expected_rgb
        
        with patch.dict(os.environ, {}, clear=True):
            result = get_background_color()
        
        self.assertEqual(result, expected_rgb)


class TestNonTTYHandling(unittest.TestCase):
    """Test handling of non-TTY environments."""
    
    @patch('sys.stdout.isatty', return_value=False)
    def test_non_tty_returns_none(self, mock_isatty):
        """Test that non-TTY stdout returns None"""
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        self.assertIsNone(result)
    
    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', side_effect=OSError("Not a file descriptor"))
    def test_fileno_error_returns_none(self, mock_fileno, mock_isatty):
        """Test that fileno() error returns None gracefully"""
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        self.assertIsNone(result)


class TestOSCResponseParsing(unittest.TestCase):
    """Test OSC response parsing edge cases."""
    
    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('sys.stdin.read')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_response_with_bel_terminator(self, mock_flush, mock_write, mock_setraw,
                                          mock_tcsetattr, mock_tcgetattr, mock_read,
                                          mock_select, mock_fileno, mock_isatty):
        """Test OSC response terminated with BEL (\\007)"""
        # Setup
        mock_select.return_value = ([sys.stdin], [], [])
        mock_tcgetattr.return_value = ['mock', 'settings']
        
        # Response with BEL terminator
        response_chars = list("\033]11;rgb:ffff/0000/0000\007")
        mock_read.side_effect = response_chars
        
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        self.assertIsNotNone(result)
        self.assertIn("rgb:ffff/0000/0000", result)
    
    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('sys.stdin.read')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_response_with_st_terminator(self, mock_flush, mock_write, mock_setraw,
                                         mock_tcsetattr, mock_tcgetattr, mock_read,
                                         mock_select, mock_fileno, mock_isatty):
        """Test OSC response terminated with ST (ESC \\)"""
        # Setup
        mock_select.return_value = ([sys.stdin], [], [])
        mock_tcgetattr.return_value = ['mock', 'settings']
        
        # Response with ST terminator (ESC \)
        response_chars = list("\033]11;rgb:ffff/0000/0000\033\\")
        mock_read.side_effect = response_chars
        
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        self.assertIsNotNone(result)
        self.assertIn("rgb:ffff/0000/0000", result)
    
    @unittest.skipIf(not _UNIX_MODULES_AVAILABLE, "Unix modules not available")
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdout.fileno', return_value=1)
    @patch('select.select')
    @patch('sys.stdin.read')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_response_safety_limit(self, mock_flush, mock_write, mock_setraw,
                                    mock_tcsetattr, mock_tcgetattr, mock_read,
                                    mock_select, mock_fileno, mock_isatty):
        """Test that response reading has safety limit to prevent infinite loop"""
        # Setup
        mock_select.return_value = ([sys.stdin], [], [])
        mock_tcgetattr.return_value = ['mock', 'settings']
        
        # Simulate infinite stream (no terminator)
        mock_read.return_value = 'x'
        
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        # Should return None due to safety limit
        self.assertIsNone(result)


class TestUnixModulesUnavailable(unittest.TestCase):
    """Test behavior when Unix modules are not available."""
    
    @unittest.skipIf(_UNIX_MODULES_AVAILABLE, "Unix modules are available")
    def test_unix_read_osc_returns_none_without_modules(self):
        """Test that unix_read_osc returns None when Unix modules unavailable"""
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            result = unix_read_osc(seq=11, timeout_ms=50)
        
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
