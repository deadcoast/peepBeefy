"""
Property-based tests for terminal detection graceful failure.

Tests:
- Property 10: Terminal Detection Graceful Failure

Validates Requirements 3.6
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings, assume
from src.terminal_detect import (
    detect_ansi_mode,
    unix_detect_ansi_mode,
    windows_detect_ansi_mode,
    unix_read_osc,
    get_background_color,
    AnsiMode
)


# Strategy for generating environment variable dictionaries
# Note: os.environ doesn't accept null characters, so we filter them out
env_vars = st.dictionaries(
    keys=st.sampled_from(["TERM", "COLORTERM", "ConEmuANSI", "SSH_CONNECTION", "SSH_CLIENT"]),
    values=st.text(
        alphabet=st.characters(blacklist_characters='\x00'),  # Exclude null characters
        min_size=0,
        max_size=50
    ),
    min_size=0,
    max_size=5
)

# Strategy for generating platform names
platform_names = st.sampled_from([
    "linux", "darwin", "windows", "freebsd", "openbsd", "netbsd",
    "unknown", "aix", "sunos", "cygwin", ""
])

# Strategy for generating Windows version strings
windows_versions = st.one_of(
    st.just("10.0.19041"),  # Valid version
    st.just("10.0.14931"),  # RGB threshold
    st.just("10.0.10586"),  # ANSI threshold
    st.just("10.0.9999"),   # Below ANSI threshold
    st.just("invalid"),     # Invalid format
    st.just("10.0"),        # Incomplete version
    st.just(""),            # Empty string
    st.text(min_size=0, max_size=20)  # Random text
)


class TestTerminalDetectionGracefulFailure:
    """Property 10: Terminal Detection Graceful Failure
    
    For any environment where terminal capabilities cannot be determined,
    detect_ansi_mode() should return None rather than raising an exception.
    
    Validates: Requirements 3.6
    """
    
    @given(env_vars)
    @settings(max_examples=200)
    def test_unix_detect_never_raises_exception(self, env: dict):
        """unix_detect_ansi_mode should never raise an exception, regardless of environment."""
        with patch.dict(os.environ, env, clear=True):
            try:
                result = unix_detect_ansi_mode()
                # Result should be either a valid AnsiMode or None
                assert result is None or result in ("rgb", "8bit", "ansi", "default"), \
                    f"Invalid result: {result}"
            except Exception as e:
                pytest.fail(f"unix_detect_ansi_mode raised exception: {e}")
    
    @given(env_vars, windows_versions)
    @settings(max_examples=200)
    def test_windows_detect_never_raises_exception(self, env: dict, version: str):
        """windows_detect_ansi_mode should never raise an exception, regardless of environment."""
        with patch.dict(os.environ, env, clear=True):
            with patch('platform.version', return_value=version):
                try:
                    result = windows_detect_ansi_mode()
                    # Result should be either a valid AnsiMode or None
                    assert result is None or result in ("rgb", "8bit", "ansi", "default"), \
                        f"Invalid result: {result}"
                except Exception as e:
                    pytest.fail(f"windows_detect_ansi_mode raised exception: {e}")
    
    @given(platform_names, env_vars)
    @settings(max_examples=200)
    def test_detect_ansi_mode_never_raises_exception(self, platform_name: str, env: dict):
        """detect_ansi_mode should never raise an exception, regardless of platform or environment."""
        with patch.dict(os.environ, env, clear=True):
            with patch('platform.system', return_value=platform_name):
                try:
                    result = detect_ansi_mode()
                    # Result should be either a valid AnsiMode or None
                    assert result is None or result in ("rgb", "8bit", "ansi", "default"), \
                        f"Invalid result: {result}"
                except Exception as e:
                    pytest.fail(f"detect_ansi_mode raised exception: {e}")
    
    @given(st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=100)
    def test_unix_read_osc_never_raises_exception(self, timeout_ms: int):
        """unix_read_osc should never raise an exception, even with invalid timeouts."""
        try:
            result = unix_read_osc(seq=11, timeout_ms=timeout_ms)
            # Result should be either a string or None
            assert result is None or isinstance(result, str), \
                f"Invalid result type: {type(result)}"
        except Exception as e:
            pytest.fail(f"unix_read_osc raised exception: {e}")
    
    def test_get_background_color_never_raises_exception(self):
        """get_background_color should never raise an exception."""
        try:
            result = get_background_color()
            # Result should be either an RGB object or None
            assert result is None or hasattr(result, 'r'), \
                f"Invalid result: {result}"
        except Exception as e:
            pytest.fail(f"get_background_color raised exception: {e}")
    
    @given(env_vars)
    @settings(max_examples=100)
    def test_detection_returns_none_on_missing_env_vars(self, env: dict):
        """Detection should return None when environment variables are missing or invalid."""
        # Clear all terminal-related environment variables
        with patch.dict(os.environ, {}, clear=True):
            result = unix_detect_ansi_mode()
            # With no environment variables, detection should fail gracefully
            assert result is None, \
                "Expected None when no environment variables are set"
    
    def test_detection_handles_corrupted_env_vars(self):
        """Detection should handle corrupted or malformed environment variables."""
        corrupted_envs = [
            {"TERM": "\x01\x02\x03"},  # Binary data (no null chars - os.environ doesn't accept them)
            {"COLORTERM": "a" * 10000},  # Very long string
            {"ConEmuANSI": "MAYBE"},  # Invalid value
            {"TERM": ""},  # Empty string
        ]
        
        for env in corrupted_envs:
            with patch.dict(os.environ, env, clear=True):
                try:
                    result = detect_ansi_mode()
                    assert result is None or result in ("rgb", "8bit", "ansi", "default")
                except Exception as e:
                    pytest.fail(f"Detection failed with corrupted env {env}: {e}")
    
    def test_detection_handles_platform_system_failure(self):
        """Detection should handle platform.system() failures gracefully."""
        with patch('platform.system', side_effect=Exception("Platform detection failed")):
            try:
                result = detect_ansi_mode()
                assert result is None, \
                    "Expected None when platform detection fails"
            except Exception as e:
                pytest.fail(f"detect_ansi_mode raised exception when platform.system failed: {e}")
    
    def test_windows_detection_handles_version_parsing_failure(self):
        """Windows detection should handle version parsing failures gracefully."""
        invalid_versions = [
            "not.a.version",
            "10",
            "10.0",
            "",
            "abc.def.ghi",
            None,
        ]
        
        for version in invalid_versions:
            with patch('platform.version', return_value=version):
                try:
                    result = windows_detect_ansi_mode()
                    assert result is None or result in ("rgb", "8bit", "ansi", "default")
                except Exception as e:
                    pytest.fail(f"windows_detect_ansi_mode failed with version {version}: {e}")
    
    def test_unix_read_osc_handles_non_tty(self):
        """unix_read_osc should return None when stdout is not a TTY."""
        with patch('sys.stdout.isatty', return_value=False):
            result = unix_read_osc(seq=11)
            assert result is None, \
                "Expected None when stdout is not a TTY"
    
    def test_unix_read_osc_handles_screen_tmux(self):
        """unix_read_osc should return None for screen/tmux terminals."""
        screen_terms = ["screen", "screen-256color", "tmux", "tmux-256color"]
        
        for term in screen_terms:
            with patch.dict(os.environ, {"TERM": term}):
                result = unix_read_osc(seq=11)
                assert result is None, \
                    f"Expected None for {term} terminal"
    
    def test_get_background_color_handles_non_unix_platforms(self):
        """get_background_color should return None on non-Unix platforms."""
        non_unix_platforms = ["windows", "unknown", "cygwin"]
        
        for platform_name in non_unix_platforms:
            with patch('platform.system', return_value=platform_name):
                result = get_background_color()
                assert result is None, \
                    f"Expected None for {platform_name} platform"


class TestGracefulFailureEdgeCases:
    """Test specific edge cases for graceful failure."""
    
    def test_empty_environment(self):
        """Detection should work with completely empty environment."""
        with patch.dict(os.environ, {}, clear=True):
            result = detect_ansi_mode()
            assert result is None or result in ("rgb", "8bit", "ansi", "default")
    
    def test_unicode_in_env_vars(self):
        """Detection should handle Unicode in environment variables."""
        unicode_envs = [
            {"TERM": "xterm-256color-🎨"},
            {"COLORTERM": "truecolor™"},
            {"ConEmuANSI": "ON™"},
        ]
        
        for env in unicode_envs:
            with patch.dict(os.environ, env, clear=True):
                try:
                    result = detect_ansi_mode()
                    assert result is None or result in ("rgb", "8bit", "ansi", "default")
                except Exception as e:
                    pytest.fail(f"Detection failed with Unicode env {env}: {e}")
    
    def test_case_sensitivity_handling(self):
        """Detection should handle case variations in environment variables."""
        case_variations = [
            {"TERM": "XTERM-256COLOR"},
            {"TERM": "XTerm-256Color"},
            {"COLORTERM": "TRUECOLOR"},
            {"COLORTERM": "TrueColor"},
            {"ConEmuANSI": "on"},
            {"ConEmuANSI": "On"},
        ]
        
        for env in case_variations:
            with patch.dict(os.environ, env, clear=True):
                try:
                    result = detect_ansi_mode()
                    assert result is None or result in ("rgb", "8bit", "ansi", "default")
                except Exception as e:
                    pytest.fail(f"Detection failed with case variation {env}: {e}")
    
    def test_whitespace_in_env_vars(self):
        """Detection should handle whitespace in environment variables."""
        whitespace_envs = [
            {"TERM": " xterm-256color "},
            {"COLORTERM": "  truecolor  "},
            {"ConEmuANSI": " ON "},
        ]
        
        for env in whitespace_envs:
            with patch.dict(os.environ, env, clear=True):
                try:
                    result = detect_ansi_mode()
                    assert result is None or result in ("rgb", "8bit", "ansi", "default")
                except Exception as e:
                    pytest.fail(f"Detection failed with whitespace env {env}: {e}")
    
    def test_negative_timeout(self):
        """unix_read_osc should handle negative timeouts gracefully."""
        result = unix_read_osc(seq=11, timeout_ms=-100)
        assert result is None or isinstance(result, str)
    
    def test_zero_timeout(self):
        """unix_read_osc should handle zero timeout gracefully."""
        result = unix_read_osc(seq=11, timeout_ms=0)
        assert result is None or isinstance(result, str)
    
    def test_very_large_timeout(self):
        """unix_read_osc should handle very large timeouts gracefully."""
        # Don't actually wait - just verify it doesn't crash
        with patch('select.select', return_value=([], [], [])):
            result = unix_read_osc(seq=11, timeout_ms=999999)
            assert result is None or isinstance(result, str)


class TestReturnValueConsistency:
    """Test that graceful failures return consistent None values."""
    
    def test_unix_detect_returns_none_or_valid_mode(self):
        """unix_detect_ansi_mode should only return None or valid AnsiMode."""
        # Test with various invalid environments
        invalid_envs = [
            {},
            {"TERM": "invalid"},
            {"COLORTERM": "invalid"},
            {"TERM": "", "COLORTERM": ""},
        ]
        
        for env in invalid_envs:
            with patch.dict(os.environ, env, clear=True):
                result = unix_detect_ansi_mode()
                assert result is None or result in ("rgb", "8bit", "ansi", "default"), \
                    f"Invalid return value: {result}"
    
    def test_windows_detect_returns_none_or_valid_mode(self):
        """windows_detect_ansi_mode should only return None or valid AnsiMode."""
        # Test with various invalid environments
        invalid_envs = [
            {},
            {"ConEmuANSI": "INVALID"},
        ]
        
        for env in invalid_envs:
            with patch.dict(os.environ, env, clear=True):
                with patch('platform.version', return_value="invalid"):
                    result = windows_detect_ansi_mode()
                    assert result is None or result in ("rgb", "8bit", "ansi", "default"), \
                        f"Invalid return value: {result}"
    
    def test_detect_ansi_mode_returns_none_or_valid_mode(self):
        """detect_ansi_mode should only return None or valid AnsiMode."""
        # Test with unknown platform
        with patch('platform.system', return_value="unknown"):
            result = detect_ansi_mode()
            assert result is None or result in ("rgb", "8bit", "ansi", "default"), \
                f"Invalid return value: {result}"
    
    def test_unix_read_osc_returns_none_or_string(self):
        """unix_read_osc should only return None or string."""
        result = unix_read_osc(seq=11)
        assert result is None or isinstance(result, str), \
            f"Invalid return type: {type(result)}"
    
    def test_get_background_color_returns_none_or_rgb(self):
        """get_background_color should only return None or RGB object."""
        result = get_background_color()
        assert result is None or (hasattr(result, 'r') and hasattr(result, 'g') and hasattr(result, 'b')), \
            f"Invalid return value: {result}"
