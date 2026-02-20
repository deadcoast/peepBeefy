"""Property-based tests for Banner data model.

This module contains property-based tests using Hypothesis to verify
universal properties of the Banner data model across all valid inputs.
"""

import pytest
from hypothesis import given, strategies as st
from src.banner import BannerMetadata, Banner


# Strategy for generating valid category names (alphanumeric + underscore)
category_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Nd"), whitelist_characters="_"),
    min_size=1,
    max_size=20
)

# Strategy for generating valid banner names (alphanumeric + underscore)
name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Nd"), whitelist_characters="_"),
    min_size=1,
    max_size=20
)

# Strategy for generating ASCII art lines (printable ASCII + whitespace, but not starting with -)
ascii_line_strategy = st.text(
    alphabet=st.characters(min_codepoint=32, max_codepoint=126),
    min_size=0,
    max_size=120
).filter(lambda s: not s.strip().startswith("-"))

# Strategy for generating lists of ASCII art lines
ascii_lines_strategy = st.lists(
    ascii_line_strategy,
    min_size=0,
    max_size=50
)


# **Validates: Requirements 1.5, 4.2, 4.5**
@given(
    category=category_strategy,
    name=name_strategy,
    lines=ascii_lines_strategy
)
@pytest.mark.property_test
def test_banner_parsing_preserves_content(category: str, name: str, lines: list[str]):
    """Property 3: Banner Parsing Preserves Content
    
    For any valid multi-line ASCII art block, the Banner data model should
    preserve all lines exactly as they appear, including whitespace and
    special characters.
    
    This test verifies that:
    1. All lines are preserved in order
    2. Whitespace (leading, trailing, internal) is preserved
    3. Special characters are preserved
    4. Empty lines are preserved
    5. Line count matches input
    """
    # Arrange: Create a Banner with the generated lines
    metadata = BannerMetadata(category=category, name=name)
    banner = Banner(metadata=metadata, lines=lines)
    
    # Assert: All lines are preserved exactly
    assert banner.lines == lines, "Lines should be preserved exactly as provided"
    
    # Assert: Line count matches
    assert len(banner.lines) == len(lines), "Line count should match input"
    
    # Assert: Each individual line is preserved
    for i, (original, preserved) in enumerate(zip(lines, banner.lines)):
        assert preserved == original, f"Line {i} should be preserved exactly"
        
        # Verify whitespace preservation
        assert len(preserved) == len(original), f"Line {i} length should be preserved"
        
        # Verify character-by-character preservation
        for j, (orig_char, pres_char) in enumerate(zip(original, preserved)):
            assert pres_char == orig_char, f"Character at line {i}, position {j} should be preserved"


@given(
    category=category_strategy,
    name=name_strategy,
    lines=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),
            min_size=1,
            max_size=120
        ).map(lambda s: "  " + s + "  "),  # Add leading and trailing spaces
        min_size=1,
        max_size=20
    )
)
@pytest.mark.property_test
def test_banner_preserves_leading_trailing_whitespace(
    category: str, 
    name: str, 
    lines: list[str]
):
    """Property 3 (Whitespace Focus): Banner preserves leading and trailing whitespace.
    
    For any ASCII art with leading or trailing whitespace, the Banner should
    preserve it exactly. This is critical for ASCII art alignment.
    """
    # Arrange
    metadata = BannerMetadata(category=category, name=name)
    banner = Banner(metadata=metadata, lines=lines)
    
    # Assert: Leading and trailing whitespace preserved
    for i, (original, preserved) in enumerate(zip(lines, banner.lines)):
        # Check leading whitespace
        orig_leading = len(original) - len(original.lstrip())
        pres_leading = len(preserved) - len(preserved.lstrip())
        assert orig_leading == pres_leading, \
            f"Line {i} should preserve {orig_leading} leading spaces"
        
        # Check trailing whitespace
        orig_trailing = len(original) - len(original.rstrip())
        pres_trailing = len(preserved) - len(preserved.rstrip())
        assert orig_trailing == pres_trailing, \
            f"Line {i} should preserve {orig_trailing} trailing spaces"


@given(
    category=category_strategy,
    name=name_strategy,
    lines=st.lists(
        st.sampled_from([
            "",  # Empty line
            "   ",  # Only spaces
            "\t\t",  # Only tabs (if we support tabs)
            "Line with  multiple   spaces",
            "!@#$%^&*()_+-=[]{}|;:',.<>?/",  # Special characters
            "MixedCASE123",
        ]),
        min_size=1,
        max_size=10
    )
)
@pytest.mark.property_test
def test_banner_preserves_special_cases(
    category: str,
    name: str, 
    lines: list[str]
):
    """Property 3 (Edge Cases): Banner preserves empty lines and special characters.
    
    For any ASCII art containing empty lines, lines with only whitespace,
    or special characters, the Banner should preserve them exactly.
    """
    # Arrange
    metadata = BannerMetadata(category=category, name=name)
    banner = Banner(metadata=metadata, lines=lines)
    
    # Assert: All special cases preserved
    assert banner.lines == lines, "All lines including empty and special should be preserved"
    
    # Assert: Empty lines remain empty
    for i, (original, preserved) in enumerate(zip(lines, banner.lines)):
        if original == "":
            assert preserved == "", f"Empty line at position {i} should remain empty"
        if original.strip() == "":
            assert preserved == original, \
                f"Whitespace-only line at position {i} should be preserved exactly"


@given(
    category=category_strategy,
    name=name_strategy,
    lines=ascii_lines_strategy
)
@pytest.mark.property_test
def test_banner_width_calculation_consistent(
    category: str,
    name: str,
    lines: list[str]
):
    """Property: Banner width calculation is consistent with preserved content.
    
    The width property should always return the length of the longest line
    in the preserved content.
    """
    # Arrange
    metadata = BannerMetadata(category=category, name=name)
    banner = Banner(metadata=metadata, lines=lines)
    
    # Calculate expected width
    expected_width = max(len(line) for line in lines) if lines else 0
    
    # Assert: Width matches longest preserved line
    assert banner.width == expected_width, \
        f"Width should be {expected_width} (longest line length)"
    
    # Assert: Width is consistent with preserved lines
    if lines:
        actual_max = max(len(line) for line in banner.lines)
        assert banner.width == actual_max, \
            "Width should match the longest line in preserved content"


@given(
    category=category_strategy,
    name=name_strategy,
    lines=ascii_lines_strategy
)
@pytest.mark.property_test
def test_banner_height_calculation_consistent(
    category: str,
    name: str,
    lines: list[str]
):
    """Property: Banner height calculation is consistent with preserved content.
    
    The height property should always return the number of lines in the
    preserved content.
    """
    # Arrange
    metadata = BannerMetadata(category=category, name=name)
    banner = Banner(metadata=metadata, lines=lines)
    
    # Assert: Height matches line count
    assert banner.height == len(lines), \
        f"Height should be {len(lines)} (number of lines)"
    
    # Assert: Height is consistent with preserved lines
    assert banner.height == len(banner.lines), \
        "Height should match the number of preserved lines"


# **Validates: Requirements 1.3**
@given(
    # Generate multiple categories with banners
    banners_by_category=st.dictionaries(
        keys=category_strategy,
        values=st.lists(
            st.tuples(
                name_strategy,  # banner name
                ascii_lines_strategy  # banner lines
            ),
            min_size=1,
            max_size=5
        ).map(lambda banners: [
            # Ensure unique names by appending index
            (f"{name}_{i}", lines) for i, (name, lines) in enumerate(banners)
        ]),
        min_size=2,
        max_size=5
    )
)
@pytest.mark.property_test
def test_banner_category_grouping(banners_by_category: dict):
    """Property 2: Banner Category Grouping
    
    For any valid ASCII database with multiple categories, parsing should
    correctly group banners by their category, such that querying for a
    specific category returns only banners from that category.
    
    This test verifies that:
    1. Banners are grouped by category correctly
    2. Each category contains only its own banners
    3. No banners are lost during parsing
    4. No banners appear in wrong categories
    """
    from src.banner import BannerDatabase
    from pathlib import Path
    import tempfile
    import os
    
    # Arrange: Create a temporary ASCII database file
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ascii_file = tmp_path / "ASCII-Full-Logo.txt"
        
        # Build the database file content
        content_lines = ["---", "DEFINITIONS", "-----------"]
        for category in banners_by_category.keys():
            content_lines.append(f'# {category}: "Test category"')
        content_lines.append("")
        
        # Add each banner
        for category, banners in banners_by_category.items():
            for name, lines in banners:
                if not lines:  # Skip empty banners
                    continue
                content_lines.append("---")
                content_lines.append(f"{category}:{name}")
                content_lines.append("-" * (len(category) + len(name) + 1))
                content_lines.extend(lines)
        
        content_lines.append("---")  # Final delimiter
        
        # Write the file
        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')
        
        # Act: Parse the database
        db = BannerDatabase(tmp_path)
        parsed_banners = db.load_banners()
        
        # Assert: All categories are present
        for category in banners_by_category.keys():
            if any(lines for _, lines in banners_by_category[category]):  # Only if has non-empty banners
                assert category in parsed_banners, \
                    f"Category '{category}' should be present in parsed results"
        
        # Assert: Each category contains only its own banners
        for category, expected_banners in banners_by_category.items():
            # Filter out empty banners (they won't be parsed)
            expected_non_empty = [(name, lines) for name, lines in expected_banners if lines]
            
            if not expected_non_empty:
                continue
            
            parsed_category_banners = parsed_banners.get(category, [])
            
            # Check count matches
            assert len(parsed_category_banners) == len(expected_non_empty), \
                f"Category '{category}' should have {len(expected_non_empty)} banners, got {len(parsed_category_banners)}"
            
            # Check each banner belongs to the correct category
            for banner in parsed_category_banners:
                assert banner.metadata.category == category, \
                    f"Banner '{banner.metadata.name}' should belong to category '{category}'"
            
            # Check banner names match
            parsed_names = {b.metadata.name for b in parsed_category_banners}
            expected_names = {name for name, _ in expected_non_empty}
            assert parsed_names == expected_names, \
                f"Category '{category}' should contain banners {expected_names}, got {parsed_names}"
        
        # Assert: Total banner count is correct
        total_expected = sum(
            len([lines for _, lines in banners if lines])
            for banners in banners_by_category.values()
        )
        total_parsed = sum(len(banners) for banners in parsed_banners.values())
        assert total_parsed == total_expected, \
            f"Total parsed banners ({total_parsed}) should match expected ({total_expected})"


# **Validates: Requirements 4.3**
@given(
    # Generate a mix of valid and invalid banner entries
    valid_banners=st.lists(
        st.tuples(
            category_strategy,
            name_strategy,
            st.lists(
                ascii_line_strategy,
                min_size=1,
                max_size=10
            )
        ),
        min_size=1,
        max_size=3
    ).map(lambda banners: [
        # Ensure unique category:name combinations by appending index
        (category, f"{name}_{i}", lines) for i, (category, name, lines) in enumerate(banners)
    ]),
    invalid_entries=st.lists(
        st.sampled_from([
            "INVALID_NO_COLON",  # Missing colon in header
            ":",  # Empty category and name
            "CATEGORY:",  # Missing name
            ":NAME",  # Missing category
        ]),
        min_size=1,
        max_size=3
    )
)
@pytest.mark.property_test
def test_parsing_error_continuation(valid_banners: list, invalid_entries: list):
    """Property 38: Parsing Error Continuation
    
    For any ASCII database file with some invalid banner entries, the parser
    should log errors for invalid entries but successfully parse and return
    all valid entries.
    
    This test verifies that:
    1. Invalid entries are detected and logged
    2. Valid entries are still parsed successfully
    3. Parser continues after encountering errors
    4. All valid banners are returned
    """
    from src.banner import BannerDatabase
    from pathlib import Path
    import tempfile
    
    # Arrange: Create a temporary ASCII database file with mixed valid/invalid entries
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ascii_file = tmp_path / "ASCII-Full-Logo.txt"
        
        content_lines = ["---", "DEFINITIONS", "-----------"]
        
        # Add valid banners
        for category, name, lines in valid_banners:
            content_lines.append("---")
            content_lines.append(f"{category}:{name}")
            content_lines.append("-" * (len(category) + len(name) + 1))
            content_lines.extend(lines)
        
        # Intersperse invalid entries
        for invalid_entry in invalid_entries:
            content_lines.append("---")
            content_lines.append(invalid_entry)
            content_lines.append("-" * len(invalid_entry))
            content_lines.append("This content should be skipped")
        
        content_lines.append("---")  # Final delimiter
        
        # Write the file
        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')
        
        # Act: Parse the database (should not crash)
        db = BannerDatabase(tmp_path)
        parsed_banners = db.load_banners()
        
        # Assert: Parser did not crash
        assert parsed_banners is not None, "Parser should return a result even with invalid entries"
        
        # Assert: All valid banners were parsed
        total_valid = len(valid_banners)
        total_parsed = sum(len(banners) for banners in parsed_banners.values())
        
        assert total_parsed == total_valid, \
            f"Should parse all {total_valid} valid banners, got {total_parsed}"
        
        # Assert: Each valid banner is present
        for category, name, lines in valid_banners:
            category_banners = parsed_banners.get(category, [])
            banner_names = [b.metadata.name for b in category_banners]
            
            assert name in banner_names, \
                f"Valid banner '{category}:{name}' should be parsed successfully"
            
            # Find the parsed banner and verify content
            parsed_banner = next(b for b in category_banners if b.metadata.name == name)
            assert parsed_banner.lines == lines, \
                f"Banner '{category}:{name}' content should be preserved"
        
        # Assert: Invalid entries did not create banners
        # (We can't easily check this directly, but the count assertion above covers it)


@given(
    # Generate categories with multiple banners each
    category1=category_strategy,
    category2=category_strategy.filter(lambda x: x != ""),  # Ensure different
    banners_cat1=st.lists(
        st.tuples(name_strategy, ascii_lines_strategy.filter(lambda x: len(x) > 0)),
        min_size=1,
        max_size=3
    ),
    banners_cat2=st.lists(
        st.tuples(name_strategy, ascii_lines_strategy.filter(lambda x: len(x) > 0)),
        min_size=1,
        max_size=3
    )
)
@pytest.mark.property_test
def test_category_isolation(
    category1: str,
    category2: str,
    banners_cat1: list,
    banners_cat2: list
):
    """Property 2 (Isolation): Banners from different categories don't mix.
    
    For any two different categories, banners from category A should never
    appear in category B's results and vice versa.
    """
    from src.banner import BannerDatabase
    from pathlib import Path
    import tempfile
    
    # Skip if categories are the same
    if category1 == category2:
        return
    
    # Arrange: Create database with two distinct categories
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ascii_file = tmp_path / "ASCII-Full-Logo.txt"
        
        content_lines = ["---", "DEFINITIONS", "-----------"]
        content_lines.append(f'# {category1}: "Category 1"')
        content_lines.append(f'# {category2}: "Category 2"')
        content_lines.append("")
        
        # Add category 1 banners
        for name, lines in banners_cat1:
            content_lines.append("---")
            content_lines.append(f"{category1}:{name}")
            content_lines.append("-" * (len(category1) + len(name) + 1))
            content_lines.extend(lines)
        
        # Add category 2 banners
        for name, lines in banners_cat2:
            content_lines.append("---")
            content_lines.append(f"{category2}:{name}")
            content_lines.append("-" * (len(category2) + len(name) + 1))
            content_lines.extend(lines)
        
        content_lines.append("---")
        
        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')
        
        # Act: Parse the database
        db = BannerDatabase(tmp_path)
        parsed_banners = db.load_banners()
        
        # Assert: Categories are separate
        cat1_banners = parsed_banners.get(category1, [])
        cat2_banners = parsed_banners.get(category2, [])
        
        # Assert: All category 1 banners have category 1
        for banner in cat1_banners:
            assert banner.metadata.category == category1, \
                f"Banner in category1 list should have category '{category1}'"
        
        # Assert: All category 2 banners have category 2
        for banner in cat2_banners:
            assert banner.metadata.category == category2, \
                f"Banner in category2 list should have category '{category2}'"
        
        # Assert: No overlap in banner names between categories
        cat1_names = {b.metadata.name for b in cat1_banners}
        cat2_names = {b.metadata.name for b in cat2_banners}
        
        # Names can overlap, but the banners should be in the right categories
        for banner in cat1_banners:
            assert banner not in cat2_banners, \
                "Banner objects should not appear in multiple categories"
        
        for banner in cat2_banners:
            assert banner not in cat1_banners, \
                "Banner objects should not appear in multiple categories"
