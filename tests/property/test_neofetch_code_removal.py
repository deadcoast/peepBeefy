"""Property-based tests for neofetch code removal.

Property 28: Neofetch Code Removal
For any ASCII art line containing neofetch color codes (e.g., \033[...m),
strip_neofetch_codes() should remove all such codes while preserving the text content.

Validates: Requirements 8.6
"""

import re
from hypothesis import given, strategies as st

from src.ascii_renderer import ASCIIColorizer, ColorAlignment
from src.color_presets import ColorPreset


# Strategy for generating ANSI escape sequences
@st.composite
def ansi_escape_sequence(draw):
    """Generate valid ANSI escape sequences."""
    # Choose between \033 and \x1b prefix
    prefix = draw(st.sampled_from(['\033', '\x1b']))
    
    # Generate SGR parameters (0-9 and semicolons)
    # Common codes: 0 (reset), 1 (bold), 30-37 (fg colors), 40-47 (bg colors)
    # 38;2;R;G;B (RGB fg), 48;2;R;G;B (RGB bg), 38;5;N (8-bit)
    params = draw(st.one_of(
        st.just('0'),  # Reset
        st.just('1'),  # Bold
        st.integers(min_value=30, max_value=47).map(str),  # Basic colors
        st.just('38;2;' + ';'.join([str(draw(st.integers(0, 255))) for _ in range(3)])),  # RGB fg
        st.just('48;2;' + ';'.join([str(draw(st.integers(0, 255))) for _ in range(3)])),  # RGB bg
        st.just('38;5;' + str(draw(st.integers(0, 255)))),  # 8-bit fg
        st.just('48;5;' + str(draw(st.integers(0, 255)))),  # 8-bit bg
        # Multiple parameters
        st.lists(
            st.integers(min_value=0, max_value=107),
            min_size=1,
            max_size=5
        ).map(lambda lst: ';'.join(map(str, lst)))
    ))
    
    return f"{prefix}[{params}m"


@st.composite
def text_with_ansi_codes(draw):
    """Generate text with embedded ANSI codes."""
    # Generate base text (printable ASCII, no control characters)
    text_parts = draw(st.lists(
        st.text(
            alphabet=st.characters(
                min_codepoint=32,  # Space
                max_codepoint=126,  # ~
                blacklist_categories=('Cc', 'Cs')  # No control chars
            ),
            min_size=0,
            max_size=20
        ),
        min_size=1,
        max_size=10
    ))
    
    # Interleave with ANSI codes
    result_parts = []
    for i, text_part in enumerate(text_parts):
        # Optionally add ANSI code before text
        if draw(st.booleans()):
            result_parts.append(draw(ansi_escape_sequence()))
        result_parts.append(text_part)
        # Optionally add ANSI code after text
        if draw(st.booleans()):
            result_parts.append(draw(ansi_escape_sequence()))
    
    return ''.join(result_parts)


@given(line=text_with_ansi_codes())
def test_strip_neofetch_codes_removes_all_ansi(line):
    """Property: strip_neofetch_codes removes all ANSI escape sequences."""
    # Create a minimal colorizer instance
    preset = ColorPreset(name="test", colors=["#FF0000"])
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment)
    
    # Strip codes
    stripped = colorizer.strip_neofetch_codes(line)
    
    # Verify no ANSI codes remain
    ansi_pattern = r'\033\[[0-9;]*m|\x1b\[[0-9;]*m'
    assert not re.search(ansi_pattern, stripped), \
        f"ANSI codes still present in stripped output: {repr(stripped)}"


@given(line=text_with_ansi_codes())
def test_strip_neofetch_codes_preserves_text_content(line):
    """Property: strip_neofetch_codes preserves all non-ANSI text content."""
    # Create a minimal colorizer instance
    preset = ColorPreset(name="test", colors=["#FF0000"])
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment)
    
    # Extract expected text (remove ANSI codes manually)
    ansi_pattern = r'\033\[[0-9;]*m|\x1b\[[0-9;]*m'
    expected_text = re.sub(ansi_pattern, '', line)
    
    # Strip codes using the method
    stripped = colorizer.strip_neofetch_codes(line)
    
    # Verify text content is preserved
    assert stripped == expected_text, \
        f"Text content not preserved.\nOriginal: {repr(line)}\nExpected: {repr(expected_text)}\nGot: {repr(stripped)}"


@given(
    text=st.text(
        alphabet=st.characters(
            min_codepoint=32,
            max_codepoint=126,
            blacklist_categories=('Cc', 'Cs')
        ),
        min_size=0,
        max_size=100
    )
)
def test_strip_neofetch_codes_identity_on_plain_text(text):
    """Property: strip_neofetch_codes is identity function on text without ANSI codes."""
    # Create a minimal colorizer instance
    preset = ColorPreset(name="test", colors=["#FF0000"])
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment)
    
    # Strip codes (should be no-op)
    stripped = colorizer.strip_neofetch_codes(text)
    
    # Verify text is unchanged
    assert stripped == text, \
        f"Plain text was modified.\nOriginal: {repr(text)}\nGot: {repr(stripped)}"


@given(line=text_with_ansi_codes())
def test_strip_neofetch_codes_idempotent(line):
    """Property: strip_neofetch_codes is idempotent (applying twice = applying once)."""
    # Create a minimal colorizer instance
    preset = ColorPreset(name="test", colors=["#FF0000"])
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment)
    
    # Strip once
    stripped_once = colorizer.strip_neofetch_codes(line)
    
    # Strip again
    stripped_twice = colorizer.strip_neofetch_codes(stripped_once)
    
    # Verify idempotence
    assert stripped_once == stripped_twice, \
        f"strip_neofetch_codes is not idempotent.\nFirst: {repr(stripped_once)}\nSecond: {repr(stripped_twice)}"


@given(
    text_parts=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),
            min_size=1,
            max_size=10
        ),
        min_size=1,
        max_size=5
    ),
    ansi_codes=st.lists(ansi_escape_sequence(), min_size=1, max_size=10)
)
def test_strip_neofetch_codes_preserves_text_order(text_parts, ansi_codes):
    """Property: strip_neofetch_codes preserves the order of text segments."""
    # Create a minimal colorizer instance
    preset = ColorPreset(name="test", colors=["#FF0000"])
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment)
    
    # Build line with interleaved ANSI codes
    line_parts = []
    for i, text in enumerate(text_parts):
        if i < len(ansi_codes):
            line_parts.append(ansi_codes[i])
        line_parts.append(text)
    line = ''.join(line_parts)
    
    # Expected result is just the text parts concatenated
    expected = ''.join(text_parts)
    
    # Strip codes
    stripped = colorizer.strip_neofetch_codes(line)
    
    # Verify text order is preserved
    assert stripped == expected, \
        f"Text order not preserved.\nExpected: {repr(expected)}\nGot: {repr(stripped)}"


@given(
    line=st.text(
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        min_size=0,
        max_size=50
    )
)
def test_strip_neofetch_codes_preserves_length_or_reduces(line):
    """Property: strip_neofetch_codes never increases line length."""
    # Create a minimal colorizer instance
    preset = ColorPreset(name="test", colors=["#FF0000"])
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment)
    
    # Strip codes
    stripped = colorizer.strip_neofetch_codes(line)
    
    # Verify length is preserved or reduced (never increased)
    assert len(stripped) <= len(line), \
        f"Stripped line is longer than original.\nOriginal length: {len(line)}\nStripped length: {len(stripped)}"


# Edge case tests
def test_strip_neofetch_codes_empty_string():
    """Edge case: empty string should remain empty."""
    preset = ColorPreset(name="test", colors=["#FF0000"])
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment)
    
    assert colorizer.strip_neofetch_codes("") == ""


def test_strip_neofetch_codes_only_ansi():
    """Edge case: string with only ANSI codes should become empty."""
    preset = ColorPreset(name="test", colors=["#FF0000"])
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment)
    
    line = "\033[0m\033[1;31m\x1b[42m"
    assert colorizer.strip_neofetch_codes(line) == ""


def test_strip_neofetch_codes_complex_neofetch_example():
    """Real-world example: neofetch-style colored ASCII art."""
    preset = ColorPreset(name="test", colors=["#FF0000"])
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment)
    
    # Typical neofetch line with colors
    line = "\033[1;34m  .---.  \033[0m\033[1;36m user@host\033[0m"
    expected = "  .---.   user@host"
    
    assert colorizer.strip_neofetch_codes(line) == expected


def test_strip_neofetch_codes_rgb_colors():
    """Test stripping RGB (24-bit) ANSI codes."""
    preset = ColorPreset(name="test", colors=["#FF0000"])
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment)
    
    line = "\033[38;2;255;100;50mHello\033[0m \033[48;2;0;128;255mWorld\033[0m"
    expected = "Hello World"
    
    assert colorizer.strip_neofetch_codes(line) == expected


def test_strip_neofetch_codes_8bit_colors():
    """Test stripping 8-bit (256-color) ANSI codes."""
    preset = ColorPreset(name="test", colors=["#FF0000"])
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment)
    
    line = "\033[38;5;196mRed\033[0m \033[48;5;21mBlue BG\033[0m"
    expected = "Red Blue BG"
    
    assert colorizer.strip_neofetch_codes(line) == expected


def test_strip_neofetch_codes_mixed_prefixes():
    """Test stripping ANSI codes with both \033 and \x1b prefixes."""
    preset = ColorPreset(name="test", colors=["#FF0000"])
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment)
    
    line = "\033[31mRed\x1b[0m \x1b[1;32mGreen\033[0m"
    expected = "Red Green"
    
    assert colorizer.strip_neofetch_codes(line) == expected
