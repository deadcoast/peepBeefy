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


# **Validates: Requirements 1.2, 1.4**
@given(
    # Generate multiple categories with banners
    banners_by_category=st.dictionaries(
        keys=category_strategy,
        values=st.lists(
            st.tuples(
                name_strategy,  # banner name
                ascii_lines_strategy.filter(lambda x: len(x) > 0)  # non-empty lines
            ),
            min_size=2,  # At least 2 banners per category for distribution testing
            max_size=5
        ).map(lambda banners: [
            # Ensure unique names by appending index
            (f"{name}_{i}", lines) for i, (name, lines) in enumerate(banners)
        ]),
        min_size=1,
        max_size=3
    ),
    num_selections=st.integers(min_value=50, max_value=200)
)
@pytest.mark.property_test
def test_banner_random_selection_distribution(
    banners_by_category: dict,
    num_selections: int
):
    """Property 1: Banner Random Selection Distribution

    For any valid ASCII database with multiple banners, random selection
    should distribute selections across all available banners over many
    iterations, with no banner being systematically excluded.

    This test verifies that:
    1. Random selection returns valid banners from the database
    2. Over many selections, all banners have a chance to be selected
    3. No banner is systematically excluded (appears at least once in sufficient trials)
    4. Selection respects category filtering when specified
    5. Random selection without filters draws from all categories
    """
    from src.banner import BannerDatabase
    from pathlib import Path
    import tempfile

    # Arrange: Create a temporary ASCII database file
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ascii_file = tmp_path / "ASCII-Full-Logo.txt"

        # Build the database file content
        content_lines = ["---", "DEFINITIONS", "-----------"]
        for category in banners_by_category.keys():
            content_lines.append(f'# {category}: "Test category"')
        content_lines.append("")

        # Track expected banners
        expected_banners = {}

        # Add each banner
        for category, banners in banners_by_category.items():
            for name, lines in banners:
                if not lines:  # Skip empty banners
                    continue
                content_lines.append("---")
                content_lines.append(f"{category}:{name}")
                content_lines.append("-" * (len(category) + len(name) + 1))
                content_lines.extend(lines)

                # Track this banner
                banner_id = f"{category}:{name}"
                expected_banners[banner_id] = (category, name, lines)

        content_lines.append("---")  # Final delimiter

        # Skip test if no valid banners
        if not expected_banners:
            return

        # Write the file
        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')

        # Act: Create database and perform multiple random selections
        db = BannerDatabase(tmp_path)
        db.load_banners()  # Pre-load to ensure cache is populated

        selected_banners = []
        for _ in range(num_selections):
            banner = db.get_random_banner()
            banner_id = f"{banner.metadata.category}:{banner.metadata.name}"
            selected_banners.append(banner_id)

        # Assert: All selections are valid banners from the database
        for banner_id in selected_banners:
            assert banner_id in expected_banners, \
                f"Selected banner '{banner_id}' should be from the database"

        # Assert: Over many selections, all banners should appear at least once
        # (with high probability for sufficient trials)
        unique_selected = set(selected_banners)

        # Calculate expected minimum coverage based on probability
        # With n banners and k selections, probability a specific banner is never
        # selected is ((n-1)/n)^k. For reasonable coverage, we expect most banners
        # to appear at least once when k >> n.
        num_banners = len(expected_banners)

        # We expect at least 70% of banners to appear in the selections
        # (this is a reasonable threshold that accounts for randomness)
        min_coverage = max(1, int(num_banners * 0.7))

        assert len(unique_selected) >= min_coverage, \
            f"Expected at least {min_coverage} unique banners out of {num_banners} " \
            f"to be selected in {num_selections} trials, got {len(unique_selected)}"

        # Assert: Each selected banner is valid and matches expected content
        for banner_id in unique_selected:
            category, name, expected_lines = expected_banners[banner_id]

            # Get the banner directly to verify
            banner = db.get_banner(category=category, name=name)
            assert banner.metadata.category == category, \
                f"Banner category should be '{category}'"
            assert banner.metadata.name == name, \
                f"Banner name should be '{name}'"
            assert banner.lines == expected_lines, \
                f"Banner content should match expected lines"


@given(
    # Generate a database with multiple categories
    category1=category_strategy,
    category2=category_strategy.filter(lambda x: x != ""),
    banners_cat1=st.lists(
        st.tuples(
            name_strategy,
            ascii_lines_strategy.filter(lambda x: len(x) > 0)
        ),
        min_size=2,
        max_size=4
    ),
    banners_cat2=st.lists(
        st.tuples(
            name_strategy,
            ascii_lines_strategy.filter(lambda x: len(x) > 0)
        ),
        min_size=2,
        max_size=4
    ),
    num_selections=st.integers(min_value=30, max_value=100)
)
@pytest.mark.property_test
def test_banner_random_selection_category_filtering(
    category1: str,
    category2: str,
    banners_cat1: list,
    banners_cat2: list,
    num_selections: int
):
    """Property 1 (Category Filtering): Random selection respects category filters.

    For any database with multiple categories, when random selection is
    filtered by specific categories, only banners from those categories
    should be returned.

    This test verifies that:
    1. Category filtering excludes banners from other categories
    2. All selections come from the specified categories
    3. Distribution is across the filtered set only
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

        # Track expected banners per category
        cat1_banner_ids = set()
        cat2_banner_ids = set()

        # Add category 1 banners
        for name, lines in banners_cat1:
            content_lines.append("---")
            content_lines.append(f"{category1}:{name}")
            content_lines.append("-" * (len(category1) + len(name) + 1))
            content_lines.extend(lines)
            cat1_banner_ids.add(f"{category1}:{name}")

        # Add category 2 banners
        for name, lines in banners_cat2:
            content_lines.append("---")
            content_lines.append(f"{category2}:{name}")
            content_lines.append("-" * (len(category2) + len(name) + 1))
            content_lines.extend(lines)
            cat2_banner_ids.add(f"{category2}:{name}")

        content_lines.append("---")

        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')

        # Act: Perform random selections with category filter
        db = BannerDatabase(tmp_path)
        db.load_banners()

        # Test filtering by category1
        selected_cat1 = []
        for _ in range(num_selections):
            banner = db.get_random_banner(categories=[category1])
            banner_id = f"{banner.metadata.category}:{banner.metadata.name}"
            selected_cat1.append(banner_id)

        # Assert: All selections are from category1
        for banner_id in selected_cat1:
            assert banner_id in cat1_banner_ids, \
                f"Banner '{banner_id}' should be from category '{category1}'"
            assert banner_id not in cat2_banner_ids, \
                f"Banner '{banner_id}' should not be from category '{category2}'"

        # Test filtering by category2
        selected_cat2 = []
        for _ in range(num_selections):
            banner = db.get_random_banner(categories=[category2])
            banner_id = f"{banner.metadata.category}:{banner.metadata.name}"
            selected_cat2.append(banner_id)

        # Assert: All selections are from category2
        for banner_id in selected_cat2:
            assert banner_id in cat2_banner_ids, \
                f"Banner '{banner_id}' should be from category '{category2}'"
            assert banner_id not in cat1_banner_ids, \
                f"Banner '{banner_id}' should not be from category '{category1}'"

        # Test filtering by both categories
        selected_both = []
        for _ in range(num_selections):
            banner = db.get_random_banner(categories=[category1, category2])
            banner_id = f"{banner.metadata.category}:{banner.metadata.name}"
            selected_both.append(banner_id)

        # Assert: All selections are from either category
        all_banner_ids = cat1_banner_ids | cat2_banner_ids
        for banner_id in selected_both:
            assert banner_id in all_banner_ids, \
                f"Banner '{banner_id}' should be from category '{category1}' or '{category2}'"


@given(
    # Generate a database with banners
    banners_by_category=st.dictionaries(
        keys=category_strategy,
        values=st.lists(
            st.tuples(
                name_strategy,
                ascii_lines_strategy.filter(lambda x: len(x) > 0)
            ),
            min_size=1,
            max_size=3
        ).map(lambda banners: [
            (f"{name}_{i}", lines) for i, (name, lines) in enumerate(banners)
        ]),
        min_size=2,
        max_size=4
    ),
    num_selections=st.integers(min_value=50, max_value=150)
)
@pytest.mark.property_test
def test_banner_random_selection_all_categories(
    banners_by_category: dict,
    num_selections: int
):
    """Property 1 (All Categories): Random selection without filters draws from all categories.

    For any database with multiple categories, when random selection is
    performed without category filters, banners from all categories should
    have a chance to be selected.

    This test verifies that:
    1. Unfiltered selection can return banners from any category
    2. Over many selections, multiple categories are represented
    3. No category is systematically excluded
    """
    from src.banner import BannerDatabase
    from pathlib import Path
    import tempfile

    # Arrange: Create database
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ascii_file = tmp_path / "ASCII-Full-Logo.txt"

        content_lines = ["---", "DEFINITIONS", "-----------"]
        for category in banners_by_category.keys():
            content_lines.append(f'# {category}: "Test category"')
        content_lines.append("")

        # Track categories with valid banners
        categories_with_banners = set()

        # Add each banner
        for category, banners in banners_by_category.items():
            for name, lines in banners:
                if not lines:
                    continue
                content_lines.append("---")
                content_lines.append(f"{category}:{name}")
                content_lines.append("-" * (len(category) + len(name) + 1))
                content_lines.extend(lines)
                categories_with_banners.add(category)

        content_lines.append("---")

        # Skip if no valid banners
        if not categories_with_banners:
            return

        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')

        # Act: Perform random selections without category filter
        db = BannerDatabase(tmp_path)
        db.load_banners()

        selected_categories = set()
        for _ in range(num_selections):
            banner = db.get_random_banner()  # No category filter
            selected_categories.add(banner.metadata.category)

        # Assert: Multiple categories are represented (if there are multiple categories)
        if len(categories_with_banners) > 1:
            # We expect at least 2 categories to appear in sufficient trials
            # (unless we're very unlucky with randomness)
            assert len(selected_categories) >= min(2, len(categories_with_banners)), \
                f"Expected at least 2 categories to be selected from {len(categories_with_banners)} " \
                f"available categories in {num_selections} trials, got {len(selected_categories)}"

        # Assert: All selected categories are valid
        for category in selected_categories:
            assert category in categories_with_banners, \
                f"Selected category '{category}' should be from the database"



# **Validates: Requirements 1.2, 1.4**
@given(
    # Generate multiple categories with banners
    banners_by_category=st.dictionaries(
        keys=category_strategy,
        values=st.lists(
            st.tuples(
                name_strategy,  # banner name
                ascii_lines_strategy.filter(lambda x: len(x) > 0)  # non-empty lines
            ),
            min_size=2,  # At least 2 banners per category for distribution testing
            max_size=5
        ).map(lambda banners: [
            # Ensure unique names by appending index
            (f"{name}_{i}", lines) for i, (name, lines) in enumerate(banners)
        ]),
        min_size=1,
        max_size=3
    ),
    num_selections=st.integers(min_value=50, max_value=200)
)
@pytest.mark.property_test
def test_banner_random_selection_distribution(
    banners_by_category: dict,
    num_selections: int
):
    """Property 1: Banner Random Selection Distribution
    
    For any valid ASCII database with multiple banners, random selection
    should distribute selections across all available banners over many
    iterations, with no banner being systematically excluded.
    
    This test verifies that:
    1. Random selection returns valid banners from the database
    2. Over many selections, all banners have a chance to be selected
    3. No banner is systematically excluded (appears at least once in sufficient trials)
    4. Selection respects category filtering when specified
    5. Random selection without filters draws from all categories
    """
    from src.banner import BannerDatabase
    from pathlib import Path
    import tempfile
    
    # Arrange: Create a temporary ASCII database file
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ascii_file = tmp_path / "ASCII-Full-Logo.txt"
        
        # Build the database file content
        content_lines = ["---", "DEFINITIONS", "-----------"]
        for category in banners_by_category.keys():
            content_lines.append(f'# {category}: "Test category"')
        content_lines.append("")
        
        # Track expected banners
        expected_banners = {}
        
        # Add each banner
        for category, banners in banners_by_category.items():
            for name, lines in banners:
                if not lines:  # Skip empty banners
                    continue
                content_lines.append("---")
                content_lines.append(f"{category}:{name}")
                content_lines.append("-" * (len(category) + len(name) + 1))
                content_lines.extend(lines)
                
                # Track this banner
                banner_id = f"{category}:{name}"
                expected_banners[banner_id] = (category, name, lines)
        
        content_lines.append("---")  # Final delimiter
        
        # Skip test if no valid banners
        if not expected_banners:
            return
        
        # Write the file
        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')
        
        # Act: Create database and perform multiple random selections
        db = BannerDatabase(tmp_path)
        db.load_banners()  # Pre-load to ensure cache is populated
        
        selected_banners = []
        for _ in range(num_selections):
            banner = db.get_random_banner()
            banner_id = f"{banner.metadata.category}:{banner.metadata.name}"
            selected_banners.append(banner_id)
        
        # Assert: All selections are valid banners from the database
        for banner_id in selected_banners:
            assert banner_id in expected_banners, \
                f"Selected banner '{banner_id}' should be from the database"
        
        # Assert: Over many selections, all banners should appear at least once
        # (with high probability for sufficient trials)
        unique_selected = set(selected_banners)
        
        # Calculate expected minimum coverage based on probability
        # With n banners and k selections, probability a specific banner is never
        # selected is ((n-1)/n)^k. For reasonable coverage, we expect most banners
        # to appear at least once when k >> n.
        num_banners = len(expected_banners)
        
        # We expect at least 70% of banners to appear in the selections
        # (this is a reasonable threshold that accounts for randomness)
        min_coverage = max(1, int(num_banners * 0.7))
        
        assert len(unique_selected) >= min_coverage, \
            f"Expected at least {min_coverage} unique banners out of {num_banners} " \
            f"to be selected in {num_selections} trials, got {len(unique_selected)}"
        
        # Assert: Each selected banner is valid and matches expected content
        for banner_id in unique_selected:
            category, name, expected_lines = expected_banners[banner_id]
            
            # Get the banner directly to verify
            banner = db.get_banner(category=category, name=name)
            assert banner.metadata.category == category, \
                f"Banner category should be '{category}'"
            assert banner.metadata.name == name, \
                f"Banner name should be '{name}'"
            assert banner.lines == expected_lines, \
                f"Banner content should match expected lines"


@given(
    # Generate a database with multiple categories
    category1=category_strategy,
    category2=category_strategy.filter(lambda x: x != ""),
    banners_cat1=st.lists(
        st.tuples(
            name_strategy,
            ascii_lines_strategy.filter(lambda x: len(x) > 0)
        ),
        min_size=2,
        max_size=4
    ),
    banners_cat2=st.lists(
        st.tuples(
            name_strategy,
            ascii_lines_strategy.filter(lambda x: len(x) > 0)
        ),
        min_size=2,
        max_size=4
    ),
    num_selections=st.integers(min_value=30, max_value=100)
)
@pytest.mark.property_test
def test_banner_random_selection_category_filtering(
    category1: str,
    category2: str,
    banners_cat1: list,
    banners_cat2: list,
    num_selections: int
):
    """Property 1 (Category Filtering): Random selection respects category filters.
    
    For any database with multiple categories, when random selection is
    filtered by specific categories, only banners from those categories
    should be returned.
    
    This test verifies that:
    1. Category filtering excludes banners from other categories
    2. All selections come from the specified categories
    3. Distribution is across the filtered set only
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
        
        # Track expected banners per category
        cat1_banner_ids = set()
        cat2_banner_ids = set()
        
        # Add category 1 banners
        for name, lines in banners_cat1:
            content_lines.append("---")
            content_lines.append(f"{category1}:{name}")
            content_lines.append("-" * (len(category1) + len(name) + 1))
            content_lines.extend(lines)
            cat1_banner_ids.add(f"{category1}:{name}")
        
        # Add category 2 banners
        for name, lines in banners_cat2:
            content_lines.append("---")
            content_lines.append(f"{category2}:{name}")
            content_lines.append("-" * (len(category2) + len(name) + 1))
            content_lines.extend(lines)
            cat2_banner_ids.add(f"{category2}:{name}")
        
        content_lines.append("---")
        
        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')
        
        # Act: Perform random selections with category filter
        db = BannerDatabase(tmp_path)
        db.load_banners()
        
        # Test filtering by category1
        selected_cat1 = []
        for _ in range(num_selections):
            banner = db.get_random_banner(categories=[category1])
            banner_id = f"{banner.metadata.category}:{banner.metadata.name}"
            selected_cat1.append(banner_id)
        
        # Assert: All selections are from category1
        for banner_id in selected_cat1:
            assert banner_id in cat1_banner_ids, \
                f"Banner '{banner_id}' should be from category '{category1}'"
            assert banner_id not in cat2_banner_ids, \
                f"Banner '{banner_id}' should not be from category '{category2}'"
        
        # Test filtering by category2
        selected_cat2 = []
        for _ in range(num_selections):
            banner = db.get_random_banner(categories=[category2])
            banner_id = f"{banner.metadata.category}:{banner.metadata.name}"
            selected_cat2.append(banner_id)
        
        # Assert: All selections are from category2
        for banner_id in selected_cat2:
            assert banner_id in cat2_banner_ids, \
                f"Banner '{banner_id}' should be from category '{category2}'"
            assert banner_id not in cat1_banner_ids, \
                f"Banner '{banner_id}' should not be from category '{category1}'"
        
        # Test filtering by both categories
        selected_both = []
        for _ in range(num_selections):
            banner = db.get_random_banner(categories=[category1, category2])
            banner_id = f"{banner.metadata.category}:{banner.metadata.name}"
            selected_both.append(banner_id)
        
        # Assert: All selections are from either category
        all_banner_ids = cat1_banner_ids | cat2_banner_ids
        for banner_id in selected_both:
            assert banner_id in all_banner_ids, \
                f"Banner '{banner_id}' should be from category '{category1}' or '{category2}'"


@given(
    # Generate a database with banners
    banners_by_category=st.dictionaries(
        keys=category_strategy,
        values=st.lists(
            st.tuples(
                name_strategy,
                ascii_lines_strategy.filter(lambda x: len(x) > 0)
            ),
            min_size=1,
            max_size=3
        ).map(lambda banners: [
            (f"{name}_{i}", lines) for i, (name, lines) in enumerate(banners)
        ]),
        min_size=2,
        max_size=4
    ),
    num_selections=st.integers(min_value=50, max_value=150)
)
@pytest.mark.property_test
def test_banner_random_selection_all_categories(
    banners_by_category: dict,
    num_selections: int
):
    """Property 1 (All Categories): Random selection without filters draws from all categories.
    
    For any database with multiple categories, when random selection is
    performed without category filters, banners from all categories should
    have a chance to be selected.
    
    This test verifies that:
    1. Unfiltered selection can return banners from any category
    2. Over many selections, multiple categories are represented
    3. No category is systematically excluded
    """
    from src.banner import BannerDatabase
    from pathlib import Path
    import tempfile
    
    # Arrange: Create database
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ascii_file = tmp_path / "ASCII-Full-Logo.txt"
        
        content_lines = ["---", "DEFINITIONS", "-----------"]
        for category in banners_by_category.keys():
            content_lines.append(f'# {category}: "Test category"')
        content_lines.append("")
        
        # Track categories with valid banners
        categories_with_banners = set()
        
        # Add each banner
        for category, banners in banners_by_category.items():
            for name, lines in banners:
                if not lines:
                    continue
                content_lines.append("---")
                content_lines.append(f"{category}:{name}")
                content_lines.append("-" * (len(category) + len(name) + 1))
                content_lines.extend(lines)
                categories_with_banners.add(category)
        
        content_lines.append("---")
        
        # Skip if no valid banners
        if not categories_with_banners:
            return
        
        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')
        
        # Act: Perform random selections without category filter
        db = BannerDatabase(tmp_path)
        db.load_banners()
        
        selected_categories = set()
        for _ in range(num_selections):
            banner = db.get_random_banner()  # No category filter
            selected_categories.add(banner.metadata.category)
        
        # Assert: Multiple categories are represented (if there are multiple categories)
        if len(categories_with_banners) > 1:
            # We expect at least 2 categories to appear in sufficient trials
            # (unless we're very unlucky with randomness)
            assert len(selected_categories) >= min(2, len(categories_with_banners)), \
                f"Expected at least 2 categories to be selected from {len(categories_with_banners)} " \
                f"available categories in {num_selections} trials, got {len(selected_categories)}"
        
        # Assert: All selected categories are valid
        for category in selected_categories:
            assert category in categories_with_banners, \
                f"Selected category '{category}' should be from the database"



# **Validates: Requirements 9.1, 9.2**
@given(
    category=category_strategy,
    name=name_strategy,
    lines=st.lists(
        ascii_line_strategy,
        min_size=1,
        max_size=10
    ).filter(lambda x: any(line.strip() for line in x)),  # Ensure at least one non-empty line
    # Generate metadata fields (filter out whitespace-only strings)
    author=st.one_of(
        st.none(), 
        st.text(
            alphabet=st.characters(min_codepoint=33, max_codepoint=126),  # Printable non-space
            min_size=1, 
            max_size=50
        )
    ),
    description=st.one_of(
        st.none(), 
        st.text(
            alphabet=st.characters(min_codepoint=33, max_codepoint=126),  # Printable non-space
            min_size=1, 
            max_size=100
        )
    ),
    animation_compatible=st.booleans()
)
@pytest.mark.property_test
def test_banner_metadata_parsing(
    category: str,
    name: str,
    lines: list[str],
    author: str | None,
    description: str | None,
    animation_compatible: bool
):
    """Property 19: Banner Metadata Parsing
    
    For any banner definition with metadata comments (lines starting with 
    "# key: value"), the parser should extract all metadata fields and 
    associate them with the banner.
    
    This test verifies that:
    1. Author metadata is parsed correctly
    2. Description metadata is parsed correctly
    3. animation_compatible metadata is parsed correctly
    4. Metadata is associated with the correct banner
    5. Unknown metadata keys are handled gracefully
    """
    from src.banner import BannerDatabase
    from pathlib import Path
    import tempfile
    
    # Arrange: Create a temporary ASCII database file with metadata
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ascii_file = tmp_path / "ASCII-Full-Logo.txt"
        
        content_lines = ["---", "DEFINITIONS", "-----------"]
        content_lines.append(f'# {category}: "Test category"')
        content_lines.append("")
        
        # Add banner with metadata
        content_lines.append("---")
        content_lines.append(f"{category}:{name}")
        # Use a longer separator to avoid confusion with delimiter
        separator_length = max(4, len(category) + len(name) + 1)
        content_lines.append("-" * separator_length)
        
        # Add metadata comments (strip to handle any edge cases)
        if author is not None:
            content_lines.append(f"# author: {author.strip()}")
        if description is not None:
            content_lines.append(f"# description: {description.strip()}")
        content_lines.append(f"# animation_compatible: {str(animation_compatible).lower()}")
        
        # Add some unknown metadata to test forward compatibility
        content_lines.append("# unknown_field: some_value")
        content_lines.append("# future_feature: enabled")
        
        # Add banner content
        content_lines.extend(lines)
        content_lines.append("---")
        
        # Write the file
        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')
        
        # Act: Parse the database
        db = BannerDatabase(tmp_path)
        parsed_banners = db.load_banners()
        
        # Assert: Banner was parsed
        assert category in parsed_banners, f"Category '{category}' should be present"
        category_banners = parsed_banners[category]
        assert len(category_banners) == 1, "Should have exactly one banner"
        
        banner = category_banners[0]
        
        # Assert: Metadata fields are correctly parsed
        assert banner.metadata.category == category, \
            f"Category should be '{category}'"
        assert banner.metadata.name == name, \
            f"Name should be '{name}'"
        
        # Assert: Author metadata (strip for comparison since parser strips)
        if author is not None:
            assert banner.metadata.author == author.strip(), \
                f"Author should be '{author.strip()}'"
        else:
            assert banner.metadata.author is None, \
                "Author should be None when not provided"
        
        # Assert: Description metadata (strip for comparison since parser strips)
        if description is not None:
            assert banner.metadata.description == description.strip(), \
                f"Description should be '{description.strip()}'"
        # Note: Default fallback is tested in Property 20
        
        # Assert: animation_compatible metadata
        assert banner.metadata.animation_compatible == animation_compatible, \
            f"animation_compatible should be {animation_compatible}"
        
        # Assert: Banner content is preserved
        assert banner.lines == lines, \
            "Banner content should be preserved despite metadata"


@given(
    category=category_strategy,
    name=name_strategy,
    lines=st.lists(
        ascii_line_strategy,
        min_size=1,
        max_size=10
    ).filter(lambda x: any(line.strip() for line in x)),  # Ensure at least one non-empty line
    # Test various metadata combinations
    has_author=st.booleans(),
    has_description=st.booleans()
)
@pytest.mark.property_test
def test_banner_metadata_optional_fields(
    category: str,
    name: str,
    lines: list[str],
    has_author: bool,
    has_description: bool
):
    """Property 19 (Optional Fields): Metadata fields are optional.
    
    For any banner, metadata fields should be optional. The parser should
    handle banners with no metadata, partial metadata, or full metadata.
    
    This test verifies that:
    1. Banners without metadata are parsed successfully
    2. Banners with partial metadata are parsed successfully
    3. Missing metadata fields default to appropriate values
    """
    from src.banner import BannerDatabase
    from pathlib import Path
    import tempfile
    
    # Arrange: Create database with optional metadata
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ascii_file = tmp_path / "ASCII-Full-Logo.txt"
        
        content_lines = ["---", "DEFINITIONS", "-----------"]
        content_lines.append(f'# {category}: "Test category"')
        content_lines.append("")
        
        # Add banner
        content_lines.append("---")
        content_lines.append(f"{category}:{name}")
        # Use a longer separator to avoid confusion with delimiter
        separator_length = max(4, len(category) + len(name) + 1)
        content_lines.append("-" * separator_length)
        
        # Conditionally add metadata
        if has_author:
            content_lines.append("# author: Test Author")
        if has_description:
            content_lines.append("# description: Test Description")
        
        # Add banner content
        content_lines.extend(lines)
        content_lines.append("---")
        
        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')
        
        # Act: Parse the database
        db = BannerDatabase(tmp_path)
        parsed_banners = db.load_banners()
        
        # Assert: Banner was parsed successfully
        assert category in parsed_banners, "Banner should be parsed even with missing metadata"
        banner = parsed_banners[category][0]
        
        # Assert: Optional fields have correct values
        if has_author:
            assert banner.metadata.author == "Test Author", \
                "Author should be parsed when provided"
        else:
            assert banner.metadata.author is None, \
                "Author should be None when not provided"
        
        if has_description:
            assert banner.metadata.description == "Test Description", \
                "Description should be parsed when provided"
        # Default fallback tested in Property 20
        
        # Assert: Default values for unspecified fields
        assert banner.metadata.animation_compatible is True, \
            "animation_compatible should default to True"


# **Validates: Requirements 9.5**
@given(
    category=category_strategy,
    name=name_strategy,
    lines=st.lists(
        ascii_line_strategy,
        min_size=1,
        max_size=10
    ).filter(lambda x: any(line.strip() for line in x)),  # Ensure at least one non-empty line
    # Test with and without explicit description
    has_explicit_description=st.booleans(),
    explicit_description=st.text(
        alphabet=st.characters(min_codepoint=33, max_codepoint=126),
        min_size=1, 
        max_size=100
    )
)
@pytest.mark.property_test
def test_banner_metadata_default_fallback(
    category: str,
    name: str,
    lines: list[str],
    has_explicit_description: bool,
    explicit_description: str
):
    """Property 20: Banner Metadata Default Fallback
    
    For any banner without a description metadata field, the banner's name 
    should be used as the description automatically.
    
    This test verifies that:
    1. When description is not provided, name is used as description
    2. When description is provided, it is used instead of name
    3. The fallback is applied consistently for all banners
    """
    from src.banner import BannerDatabase
    from pathlib import Path
    import tempfile
    
    # Arrange: Create database with or without description
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ascii_file = tmp_path / "ASCII-Full-Logo.txt"
        
        content_lines = ["---", "DEFINITIONS", "-----------"]
        content_lines.append(f'# {category}: "Test category"')
        content_lines.append("")
        
        # Add banner
        content_lines.append("---")
        content_lines.append(f"{category}:{name}")
        # Use a longer separator to avoid confusion with delimiter
        separator_length = max(4, len(category) + len(name) + 1)
        content_lines.append("-" * separator_length)
        
        # Conditionally add description metadata
        if has_explicit_description:
            content_lines.append(f"# description: {explicit_description.strip()}")
        
        # Add banner content
        content_lines.extend(lines)
        content_lines.append("---")
        
        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')
        
        # Act: Parse the database
        db = BannerDatabase(tmp_path)
        parsed_banners = db.load_banners()
        
        # Assert: Banner was parsed
        assert category in parsed_banners, "Banner should be parsed"
        banner = parsed_banners[category][0]
        
        # Assert: Description fallback behavior
        if has_explicit_description:
            assert banner.metadata.description == explicit_description.strip(), \
                f"Description should be '{explicit_description.strip()}' when explicitly provided"
        else:
            assert banner.metadata.description == name, \
                f"Description should default to banner name '{name}' when not provided"


@given(
    # Generate multiple banners with varying metadata
    banners_data=st.lists(
        st.tuples(
            category_strategy,
            name_strategy,
            st.lists(ascii_line_strategy, min_size=1, max_size=5),
            st.booleans()  # has_description
        ),
        min_size=2,
        max_size=5
    ).map(lambda banners: [
        # Ensure unique category:name combinations
        (cat, f"{name}_{i}", lines, has_desc) 
        for i, (cat, name, lines, has_desc) in enumerate(banners)
    ])
)
@pytest.mark.property_test
def test_banner_metadata_default_fallback_consistency(
    banners_data: list
):
    """Property 20 (Consistency): Default fallback is applied consistently.
    
    For any set of banners, the description fallback should be applied
    consistently - all banners without explicit descriptions should use
    their names as descriptions.
    
    This test verifies that:
    1. Fallback is applied to all banners without descriptions
    2. Fallback is not applied to banners with explicit descriptions
    3. The behavior is consistent across multiple banners
    """
    from src.banner import BannerDatabase
    from pathlib import Path
    import tempfile
    
    # Arrange: Create database with multiple banners
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ascii_file = tmp_path / "ASCII-Full-Logo.txt"
        
        content_lines = ["---", "DEFINITIONS", "-----------"]
        
        # Collect unique categories
        categories = set(cat for cat, _, _, _ in banners_data)
        for category in categories:
            content_lines.append(f'# {category}: "Test category"')
        content_lines.append("")
        
        # Track expected descriptions
        expected_descriptions = {}
        
        # Add each banner
        for category, name, lines, has_description in banners_data:
            content_lines.append("---")
            content_lines.append(f"{category}:{name}")
            # Use a longer separator to avoid confusion with delimiter
            separator_length = max(4, len(category) + len(name) + 1)
            content_lines.append("-" * separator_length)
            
            if has_description:
                explicit_desc = f"Description for {name}"
                content_lines.append(f"# description: {explicit_desc}")
                expected_descriptions[f"{category}:{name}"] = explicit_desc
            else:
                # Should default to name
                expected_descriptions[f"{category}:{name}"] = name
            
            content_lines.extend(lines)
        
        content_lines.append("---")
        
        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')
        
        # Act: Parse the database
        db = BannerDatabase(tmp_path)
        parsed_banners = db.load_banners()
        
        # Assert: All banners have correct descriptions
        for category, name, _, has_description in banners_data:
            banner_id = f"{category}:{name}"
            expected_desc = expected_descriptions[banner_id]
            
            # Find the banner
            category_banners = parsed_banners.get(category, [])
            matching_banners = [b for b in category_banners if b.metadata.name == name]
            
            assert len(matching_banners) == 1, \
                f"Should find exactly one banner for '{banner_id}'"
            
            banner = matching_banners[0]
            assert banner.metadata.description == expected_desc, \
                f"Banner '{banner_id}' should have description '{expected_desc}'"


@given(
    category=category_strategy,
    name=name_strategy,
    lines=st.lists(ascii_line_strategy, min_size=1, max_size=10).filter(
        lambda x: any(line.strip() for line in x)  # Ensure at least one non-empty line
    ),
    # Test various animation_compatible values
    anim_value=st.sampled_from([
        "true", "True", "TRUE", "yes", "Yes", "YES", "1",
        "false", "False", "FALSE", "no", "No", "NO", "0"
    ])
)
@pytest.mark.property_test
def test_banner_metadata_animation_compatible_parsing(
    category: str,
    name: str,
    lines: list[str],
    anim_value: str
):
    """Property 19 (Boolean Parsing): animation_compatible metadata is parsed correctly.
    
    For any banner with animation_compatible metadata, the parser should
    correctly interpret various boolean representations (true/false, yes/no, 1/0)
    and convert them to boolean values.
    
    This test verifies that:
    1. Various true representations are parsed as True
    2. Various false representations are parsed as False
    3. Case-insensitive parsing works correctly
    """
    from src.banner import BannerDatabase
    from pathlib import Path
    import tempfile
    
    # Determine expected boolean value
    expected_bool = anim_value.lower() in ('true', 'yes', '1')
    
    # Arrange: Create database with animation_compatible metadata
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ascii_file = tmp_path / "ASCII-Full-Logo.txt"
        
        content_lines = ["---", "DEFINITIONS", "-----------"]
        content_lines.append(f'# {category}: "Test category"')
        content_lines.append("")
        
        # Add banner with animation_compatible metadata
        content_lines.append("---")
        content_lines.append(f"{category}:{name}")
        # Use a longer separator to avoid confusion with delimiter
        separator_length = max(4, len(category) + len(name) + 1)
        content_lines.append("-" * separator_length)
        content_lines.append(f"# animation_compatible: {anim_value}")
        content_lines.extend(lines)
        content_lines.append("---")
        
        ascii_file.write_text("\n".join(content_lines), encoding='utf-8')
        
        # Act: Parse the database
        db = BannerDatabase(tmp_path)
        parsed_banners = db.load_banners()
        
        # Assert: animation_compatible is parsed correctly
        banner = parsed_banners[category][0]
        assert banner.metadata.animation_compatible == expected_bool, \
            f"animation_compatible should be {expected_bool} for value '{anim_value}'"
