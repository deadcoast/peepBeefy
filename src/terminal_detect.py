"""
Terminal capability detection module.

This module provides functions to detect terminal color capabilities
across different platforms (Unix/Windows) and return the appropriate
ANSI color mode.
"""

import os
import sys
import platform
import re
from typing import Literal, Optional

# Unix-specific imports (not available on Windows)
try:
    import select
    import termios
    import tty
    _UNIX_MODULES_AVAILABLE = True
except ImportError:
    _UNIX_MODULES_AVAILABLE = False

# Type definition for ANSI modes
AnsiMode = Literal["rgb", "8bit", "ansi", "default"]


def unix_detect_ansi_mode() -> Optional[AnsiMode]:
    """
    Detect ANSI color mode on Unix-like systems.
    
    Checks environment variables COLORTERM and TERM to determine
    the terminal's color capabilities.
    
    Returns:
        AnsiMode: Detected color mode ("rgb", "8bit", "ansi"), or None if detection fails
    
    Requirements: 3.1, 3.2, 3.7, 3.8
    """
    try:
        # Check COLORTERM for truecolor/24-bit support
        colorterm = os.environ.get("COLORTERM", "").lower()
        if "truecolor" in colorterm or "24bit" in colorterm:
            return "rgb"
        
        # Check TERM environment variable
        term = os.environ.get("TERM", "").lower()
        
        # Special case: xterm-kitty supports RGB
        if "xterm-kitty" in term:
            return "rgb"
        
        # Special case: linux console supports ANSI only
        if term == "linux":
            return "ansi"
        
        # Check for 256-color support
        if "256color" in term:
            return "8bit"
        
        # Check for basic color support
        if "color" in term:
            return "8bit"
        
        # Check for ANSI support
        if "ansi" in term:
            return "ansi"
        
        # Unable to determine - return None for graceful fallback
        return None
        
    except Exception:
        # Graceful failure - return None
        return None


def windows_detect_ansi_mode() -> Optional[AnsiMode]:
    """
    Detect ANSI color mode on Windows systems.
    
    Checks ConEmuANSI environment variable and Windows build version
    to determine color capabilities.
    
    Returns:
        AnsiMode: Detected color mode ("rgb", "8bit", "ansi"), or None if detection fails
    
    Requirements: 3.3, 3.4, 3.5
    """
    try:
        # Check ConEmuANSI environment variable
        conemu_ansi = os.environ.get("ConEmuANSI", "").upper()
        if conemu_ansi == "ON":
            return "rgb"
        
        # Check Windows build version
        # platform.version() returns something like "10.0.19041"
        try:
            version_str = platform.version()
            # Extract build number (third component)
            parts = version_str.split(".")
            if len(parts) >= 3:
                build = int(parts[2])
                
                # Windows 10 build 14931+ supports RGB
                if build >= 14931:
                    return "rgb"
                
                # Windows 10 build 10586+ supports ANSI
                if build >= 10586:
                    return "8bit"
                
                # Older builds - ANSI only
                return "ansi"
        except (ValueError, IndexError):
            # Failed to parse version - return None
            return None
        
        # Unable to determine
        return None
        
    except Exception:
        # Graceful failure - return None
        return None


def detect_ansi_mode() -> Optional[AnsiMode]:
    """
    Platform-agnostic terminal capability detection.
    
    Automatically detects the platform and calls the appropriate
    detection function (Unix or Windows).
    
    Returns:
        AnsiMode: Detected color mode ("rgb", "8bit", "ansi"), or None if detection fails
    
    Requirements: 3.6
    """
    try:
        # Detect platform
        system = platform.system().lower()
        
        if system in ("linux", "darwin", "freebsd", "openbsd", "netbsd"):
            # Unix-like systems
            return unix_detect_ansi_mode()
        elif system == "windows":
            # Windows systems
            return windows_detect_ansi_mode()
        else:
            # Unknown platform - graceful fallback
            return None
            
    except Exception:
        # Graceful failure - return None for fallback
        return None



def unix_read_osc(seq: int, timeout_ms: int = 50) -> Optional[str]:
    """
    Read OSC (Operating System Command) response from terminal.
    
    Sends an OSC query sequence and waits for the terminal response.
    This is used for querying terminal properties like background color.
    
    Args:
        seq: OSC sequence number (e.g., 11 for background color)
        timeout_ms: Timeout in milliseconds (default 50ms for local, 500ms for SSH)
        
    Returns:
        OSC response string, or None if timeout or error occurs
        
    Requirements: 10.1, 10.2, 10.3, 10.5, 10.6
    """
    # Only works on Unix-like systems with required modules
    if not _UNIX_MODULES_AVAILABLE:
        return None
    
    # Only works on Unix-like systems with TTY
    if not sys.stdout.isatty():
        return None
    
    # Skip detection for screen/tmux terminals (not supported)
    term = os.environ.get("TERM", "").lower()
    if "screen" in term or "tmux" in term:
        return None
    
    try:
        # Get file descriptor for stdout
        fd = sys.stdout.fileno()
        
        # Save original terminal settings
        old_settings = termios.tcgetattr(fd)
        
        try:
            # Set terminal to raw mode for reading response
            tty.setraw(fd)
            
            # Send OSC query: ESC ] seq ; ? BEL
            query = f"\033]{seq};?\007"
            sys.stdout.write(query)
            sys.stdout.flush()
            
            # Wait for response with timeout
            timeout_sec = timeout_ms / 1000.0
            ready, _, _ = select.select([sys.stdin], [], [], timeout_sec)
            
            if not ready:
                # Timeout - no response
                return None
            
            # Read response (OSC responses typically end with ESC \ or BEL)
            response = ""
            while True:
                char = sys.stdin.read(1)
                response += char
                
                # Check for terminator: BEL (\007) or ESC \ (\033\\)
                if char == "\007":
                    break
                if len(response) >= 2 and response[-2:] == "\033\\":
                    break
                
                # Safety limit to prevent infinite loop
                if len(response) > 1000:
                    return None
            
            return response
            
        finally:
            # Always restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
    except (OSError, termios.error, ValueError):
        # Graceful failure - terminal doesn't support OSC or other error
        return None


def parse_osc_rgb_response(response: str) -> Optional['RGB']:
    """
    Parse RGB values from OSC 11 response.
    
    OSC 11 returns background color in format: ESC ] 11 ; rgb:RRRR/GGGG/BBBB BEL
    where RRRR, GGGG, BBBB are 16-bit hex values (0000-FFFF).
    
    Args:
        response: OSC response string from terminal
        
    Returns:
        RGB color object, or None if parsing fails
        
    Requirements: 10.4
    """
    try:
        # Match pattern: rgb:RRRR/GGGG/BBBB
        # The response may have various prefixes/suffixes, so we search for the pattern
        match = re.search(r'rgb:([0-9a-fA-F]{4})/([0-9a-fA-F]{4})/([0-9a-fA-F]{4})', response)
        
        if not match:
            return None
        
        # Extract 16-bit hex values
        r_16bit = int(match.group(1), 16)
        g_16bit = int(match.group(2), 16)
        b_16bit = int(match.group(3), 16)
        
        # Convert 16-bit (0-65535) to 8-bit (0-255)
        r_8bit = round(r_16bit / 65535.0 * 255)
        g_8bit = round(g_16bit / 65535.0 * 255)
        b_8bit = round(b_16bit / 65535.0 * 255)
        
        # Import RGB here to avoid circular dependency
        from color_util import RGB
        
        return RGB(r=r_8bit, g=g_8bit, b=b_8bit)
        
    except (ValueError, IndexError, AttributeError):
        # Parsing failed - return None
        return None


def get_background_color() -> Optional['RGB']:
    """
    Detect terminal background color using OSC 11 query.
    
    Sends an OSC 11 query to the terminal and parses the RGB response.
    This only works on Unix-like systems with terminals that support OSC.
    
    The timeout is set based on whether we're in an SSH session:
    - Local: 50ms timeout (fast response expected)
    - SSH: 500ms timeout (network latency)
    
    Returns:
        RGB color of terminal background, or None if detection fails
        
    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
    """
    # Only works on Unix-like systems
    system = platform.system().lower()
    if system not in ("linux", "darwin", "freebsd", "openbsd", "netbsd"):
        return None
    
    # Determine timeout based on SSH session
    # SSH_CONNECTION or SSH_CLIENT indicate SSH session
    is_ssh = bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_CLIENT"))
    timeout_ms = 500 if is_ssh else 50
    
    # Send OSC 11 query and read response
    response = unix_read_osc(seq=11, timeout_ms=timeout_ms)
    
    if response is None:
        return None
    
    # Parse RGB values from response
    return parse_osc_rgb_response(response)
