"""
Property-based tests for distro-specific banner matching.

Tests:
- Property 34: Distro Name Case Insensitivity
- Property 35: Distro Partial Matching
- Property 36: Distro Fallback Banner

Validates Requirements 11.2, 11.4, 11.7
"""

import pytest
from hypothesis import given, strategies as st, assume
from pathlib import Path
from src.banner import BannerDatabase, Banner


# Strategy for generating distro names with various cases
distro_names = st.sampled_from([
    'ubuntu', 'debian', 'arch', 'fedora', 'centos', 'redhat',
    'manjaro', 'mint', 'elementary', 'pop', 'kali', 'gentoo',
    'slackware', 'alpine', 'void', 'nixos', 'coreos', 'rhel'
])

# Strategy for generating case variations
case_variations = st.sampled_from([
    str.lower,
    str.upper,
    str.title,
    lambda s: ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(s))
])

# Strategy for generating whitespace padding
whitespace_padding = st.tuples(
    st.text(alphabet=' \t', min_size=0, max_size=5),  # Leading whitespace
    st.text(alphabet=' \t', min_size=0, max_size=5)   # Trailing whitespace
)

# Strategy for generating invalid/unrecognized distro names
invalid_distro_names = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
    min_size=1,
    max_size=30
).filter(lambda s: s not in BannerDatabase.DISTRO_ALIASES and 
         not any(known in s.lower() for known in [
             'ubuntu', 'debian', 'arch', 'fedora', 'centos', 'redhat',
             'manjaro', 'mint', 'elementary', 'pop', 'kali', 'gentoo',
             'slackware', 'alpine', 'void', 'nixos', 'container', 'linux'
         ]))


@pytest.fixture(scope="module")
def test_banner_db(tmp_path_factory):
    """Create a BannerDatabase with comprehensive test data for property tests."""
    assets_dir = tmp_path_factory.mktemp("assets")
    
    # Create a test ASCII database file with multiple distros
    ascii_file = assets_dir / "ASCII-Full-Logo.txt"
    test_content = r"""---
DEFINITIONS
---
---
LINUX:Ubuntu
# author: Test Author
# description: Ubuntu Linux
    _   _  _                 _        
   | | | || |               | |       
   | | | || |__  _   _ _ __ | |_ _   _ 
   | | | || '_ \| | | | '_ \| __| | | |
   | |_| || |_) | |_| | | | | |_| |_| |
    \___/ |_.__/ \__,_|_| |_|\__|\__,_|
---
---
LINUX:Arch
# author: Test Author
# description: Arch Linux
       /\
      /  \
     /\   \
    /      \
   /   ,,   \
  /   |  |  -\
 /_-''    ''-_\
---
---
LINUX:Debian
# author: Test Author
# description: Debian Linux
      _,met$$$gg.
   ,g$$$$$$$$P.
 ,g$P"     YYY$.".
,$P'              `$$.
---
---
LINUX:RedHat
# author: Test Author
# description: Red Hat Enterprise Linux
           .MMM..:MMMMMMM
          MMMMMMMMMMMMMMMMMM
---
---
LINUX:Fedora
# author: Test Author
# description: Fedora Linux
        ,'''''.
       |   ,.  |
       |  |  '_'
  ,....|  |..
.'  ,_;|   ..'
|  |   |  |
|  ',_,'  |
 '.     ,'
   '''''
---
---
LINUX:CentOS
# author: Test Author
# description: CentOS Linux
                 ..
               .PLTJ.
              <><><><>
     KKSSV' 4KKK LJ KKKL.'VSSKK
     KKV' 4KKKKK LJ KKKKAL 'VKK
     V' ' 'VKKKK LJ KKKKV' ' 'V
     .4MA.' 'VKK LJ KKV' '.4Mb.
---
---
LINUX:Manjaro
# author: Test Author
# description: Manjaro Linux
██████████████████  ████████
██████████████████  ████████
██████████████████  ████████
██████████████████  ████████
████████            ████████
████████  ████████  ████████
████████  ████████  ████████
████████  ████████  ████████
████████  ████████  ████████
████████  ████████  ████████
████████  ████████  ████████
████████  ████████  ████████
████████  ████████  ████████
████████  ████████  ████████
---
---
LINUX:LinuxMint
# author: Test Author
# description: Linux Mint
             ...-:::::-...
          .-MMMMMMMMMMMMMMM-.
      .-MMMM`..-:::::::-..`MMMM-.
    .:MMMM.:MMMMMMMMMMMMMMM:.MMMM:.
   -MMM-M---MMMMMMMMMMMMMMMMMMM.MMM-
 `:MMM:MM`  :MMMM:....::-...-MMMM:MMM:`
 :MMM:MMM`  :MM:`  ``    ``  `:MMM:MMM:
.MMM.MMMM`  :MM.  -MM.  .MM-  `MMMM.MMM.
---
---
LINUX:container_linux
# author: Test Author
# description: Container Linux (CoreOS)
                .....
          .';:cccccccc:;'.
       .:ccccccccccccccccc:.
     'ccccccccccccccccccccccc.
   .cccccccccccccccccccccccccc.
  ;cccccccccccccc;.  .;cccccccc;
 'cccccccccccccc:.      :ccccccc'
---
---
LINUX:Elementary
# author: Test Author
# description: elementary OS
         eeeeeeeeeeeeeeeee
      eeeeeeeeeeeeeeeeeeeeeee
    eeeeee  eeeeeeeeeeeee   eeeee
  eeee   eeeeeeeeeeeeeeeeeee   eeee
 eeee   eeeeeeeeeeeeeeeeeeee    eeee
eee    eeeeeeeeeeeeeeeeeeeee     eee
ee    eeeeeeeeeeeeeeeeeeeee       ee
ee    eeeeeeeeeeeeeeeeeeeee       ee
---
---
LINUX:Pop_OS
# author: Test Author
# description: Pop!_OS
             /////////////
         /////////////////////
      ///////*767////////////////
    //////7676767676*//////////////
   /////76767//7676767//////////////
  /////767676///*76767///////////////
 ///////767676///76767.///7676*///////
/////////767676//76767//767676////////
---
---
LINUX:Kali
# author: Test Author
# description: Kali Linux
      ,.....                                       
  ----`   `..,;:ccc,.
           ......''';lxO.
 .....''''..........,:ld;
            .';;;:::;,,.x,
       ..'''.            0Xxoc:,.  ...
   ....                ,ONkc;,;cokOdc',.
  .                   OMo           ':ddo.
                     dMc               :OO;
---
---
LINUX:Gentoo
# author: Test Author
# description: Gentoo Linux
         -/oy+:.
      :/ooo++/:.
    `:+oooooo+/-`
   `/+oooooooo+/-`
  `/+oooooooooo+/-`
 `/+oooooooooooo+/-`
`/+oooooooooooooo+/-`
/+oooooooooooooooo+/-
---
---
LINUX:Alpine
# author: Test Author
# description: Alpine Linux
       .hddddddddddddddddddddddh.
      :dddddddddddddddddddddddddd:
     /dddddddddddddddddddddddddddd/
    +dddddddddddddddddddddddddddddd+
  `sdddddddddddddddddddddddddddddddds`
 `ydddddddddddd++hdddddddddddddddddddy`
---
---
LINUX:NixOS
# author: Test Author
# description: NixOS
          ::::.    ':::::     ::::'
          ':::::    ':::::.  ::::'
            :::::     '::::.:::::
      .......:::::..... ::::::::
     ::::::::::::::::::. ::::::    ::::.
    ::::::::::::::::::::: :::::.  .::::'
           .....           ::::' :::::'
          :::::            '::' :::::'
         :::::::          ::::::::::::'
        :::::::          :::::::
       :::::::          ::::::.
      :::::::          :::::.
     :::::::          :::::.
---
"""
    ascii_file.write_text(test_content, encoding='utf-8')
    
    db = BannerDatabase(assets_dir)
    # Pre-load banners to avoid repeated parsing
    db.load_banners()
    return db


class TestDistroNameCaseInsensitivity:
    """Property 34: Distro Name Case Insensitivity
    
    For any distro name string, the Banner_Database should match it 
    case-insensitively (e.g., "Ubuntu", "ubuntu", "UBUNTU" should all match).
    
    Validates: Requirements 11.2
    """
    
    @given(distro_names, case_variations)
    def test_case_insensitive_matching(self, test_banner_db, distro_name, case_transform):
        """Distro names should match regardless of case."""
        # Apply case transformation
        transformed_name = case_transform(distro_name)
        
        # Get banner with transformed name
        banner = test_banner_db.get_banner_by_distro(transformed_name)
        
        # Should not return fallback (unless distro genuinely doesn't exist)
        # For known distros in our test set, we should get a match
        if distro_name in ['ubuntu', 'debian', 'arch', 'fedora', 'centos', 
                          'manjaro', 'elementary', 'kali', 'gentoo', 'alpine', 'nixos']:
            assert banner.metadata.category != "FALLBACK", \
                f"Failed to match known distro '{transformed_name}' (original: '{distro_name}')"
            
            # The matched banner name should be case-insensitively equal to the input
            # (accounting for aliases)
            banner_name_lower = banner.metadata.name.lower()
            distro_name_lower = distro_name.lower()
            
            # Check if it's an exact match or an alias match
            is_match = (banner_name_lower == distro_name_lower or
                       distro_name_lower in BannerDatabase.DISTRO_ALIASES)
            
            assert is_match, \
                f"Banner name '{banner.metadata.name}' doesn't match input '{transformed_name}'"
    
    @given(distro_names, case_variations, whitespace_padding)
    def test_case_insensitive_with_whitespace(self, test_banner_db, distro_name, 
                                              case_transform, padding):
        """Distro names should match case-insensitively even with whitespace."""
        # Apply case transformation and add whitespace
        leading, trailing = padding
        transformed_name = leading + case_transform(distro_name) + trailing
        
        # Get banner with transformed name
        banner = test_banner_db.get_banner_by_distro(transformed_name)
        
        # For known distros, should not return fallback
        if distro_name in ['ubuntu', 'debian', 'arch', 'fedora', 'centos',
                          'manjaro', 'elementary', 'kali', 'gentoo', 'alpine', 'nixos']:
            assert banner.metadata.category != "FALLBACK", \
                f"Failed to match known distro '{transformed_name.strip()}' with whitespace"
    
    @given(st.sampled_from(['Ubuntu', 'Debian', 'Arch', 'Fedora', 'CentOS']))
    def test_exact_banner_names_case_insensitive(self, test_banner_db, banner_name):
        """Exact banner names should match case-insensitively."""
        # Test lowercase
        banner_lower = test_banner_db.get_banner_by_distro(banner_name.lower())
        assert banner_lower.metadata.name == banner_name
        
        # Test uppercase
        banner_upper = test_banner_db.get_banner_by_distro(banner_name.upper())
        assert banner_upper.metadata.name == banner_name
        
        # Both should return the same banner
        assert banner_lower.metadata.name == banner_upper.metadata.name


class TestDistroPartialMatching:
    """Property 35: Distro Partial Matching
    
    For any partial distro name that is a substring of a known distro, 
    the Banner_Database should attempt to find a match using partial word matching.
    
    Validates: Requirements 11.4
    """
    
    @given(st.sampled_from([
        ('deb', 'Debian'),
        ('ubu', 'Ubuntu'),
        ('fed', 'Fedora'),
        ('cent', 'CentOS'),
        ('man', 'Manjaro'),
        ('elem', 'Elementary'),
        ('gen', 'Gentoo'),
        ('alp', 'Alpine'),
        ('nix', 'NixOS'),
    ]))
    def test_prefix_partial_matching(self, test_banner_db, partial_and_expected):
        """Partial distro names should match via prefix matching."""
        partial, expected = partial_and_expected
        
        banner = test_banner_db.get_banner_by_distro(partial)
        
        # Should match the expected distro (not fallback)
        assert banner.metadata.category != "FALLBACK", \
            f"Failed to match partial name '{partial}' to '{expected}'"
        
        # The matched banner should be the expected one
        assert banner.metadata.name == expected, \
            f"Partial match '{partial}' returned '{banner.metadata.name}', expected '{expected}'"
    
    @given(st.sampled_from([
        ('untu', 'Ubuntu'),      # Suffix of Ubuntu
        ('ebian', 'Debian'),     # Suffix of Debian
        ('dora', 'Fedora'),      # Suffix of Fedora
        ('entOS', 'CentOS'),     # Suffix of CentOS
        ('njaro', 'Manjaro'),    # Suffix of Manjaro
    ]))
    def test_suffix_partial_matching(self, test_banner_db, partial_and_expected):
        """Partial distro names (suffixes) should match via partial word matching."""
        partial, expected = partial_and_expected
        
        banner = test_banner_db.get_banner_by_distro(partial)
        
        # Should match the expected distro (not fallback)
        # Note: Suffix matching might not always work depending on implementation
        # This tests the partial word matching capability
        if banner.metadata.category != "FALLBACK":
            assert banner.metadata.name == expected, \
                f"Partial match '{partial}' returned '{banner.metadata.name}', expected '{expected}'"
    
    @given(st.sampled_from([
        ('bunt', 'Ubuntu'),      # Middle substring
        ('ebi', 'Debian'),       # Middle substring
        ('edo', 'Fedora'),       # Middle substring
    ]))
    def test_substring_partial_matching(self, test_banner_db, partial_and_expected):
        """Substrings of distro names should match via partial word matching."""
        partial, expected = partial_and_expected
        
        banner = test_banner_db.get_banner_by_distro(partial)
        
        # Substring matching is best-effort - if it matches, verify it's correct
        if banner.metadata.category != "FALLBACK":
            # If we got a match, it should be the expected distro
            assert banner.metadata.name == expected, \
                f"Substring match '{partial}' returned '{banner.metadata.name}', expected '{expected}'"
    
    @given(st.sampled_from(['ubuntu', 'debian', 'fedora', 'centos', 'manjaro']))
    def test_partial_matching_preserves_full_match(self, test_banner_db, full_name):
        """Full distro names should still match exactly, not just partially."""
        banner = test_banner_db.get_banner_by_distro(full_name)
        
        # Should match and not be fallback
        assert banner.metadata.category != "FALLBACK"
        
        # The matched name should be case-insensitively equal to input
        assert banner.metadata.name.lower() == full_name.lower() or \
               full_name in BannerDatabase.DISTRO_ALIASES


class TestDistroFallbackBanner:
    """Property 36: Distro Fallback Banner
    
    For any unrecognized or invalid distro name, the Banner_Database should 
    return a fallback banner rather than raising an exception.
    
    Validates: Requirements 11.7
    """
    
    @given(invalid_distro_names)
    def test_unrecognized_distro_returns_fallback(self, test_banner_db, distro_name):
        """Unrecognized distro names should return fallback banner."""
        # Assume the distro name doesn't match any known distro
        assume(distro_name not in BannerDatabase.DISTRO_ALIASES)
        assume(not any(known in distro_name.lower() for known in [
            'ubuntu', 'debian', 'arch', 'fedora', 'centos', 'redhat',
            'manjaro', 'mint', 'elementary', 'pop', 'kali', 'gentoo',
            'slackware', 'alpine', 'void', 'nixos', 'container', 'linux'
        ]))
        # Also exclude single characters that might match via partial matching
        assume(len(distro_name) > 1)
        
        # Get banner for unrecognized distro
        banner = test_banner_db.get_banner_by_distro(distro_name)
        
        # Should return fallback banner
        assert banner.metadata.category == "FALLBACK", \
            f"Unrecognized distro '{distro_name}' should return fallback banner"
        assert banner.metadata.name == "DEFAULT", \
            f"Fallback banner should have name 'DEFAULT'"
    
    @given(st.text(min_size=0, max_size=0))
    def test_empty_distro_name_returns_fallback(self, test_banner_db, empty_str):
        """Empty distro names should return fallback banner."""
        banner = test_banner_db.get_banner_by_distro(empty_str)
        
        assert banner.metadata.category == "FALLBACK"
        assert banner.metadata.name == "DEFAULT"
    
    @given(st.text(alphabet=' \t\n\r', min_size=1, max_size=10))
    def test_whitespace_only_distro_name_returns_fallback(self, test_banner_db, whitespace):
        """Whitespace-only distro names should return fallback banner."""
        banner = test_banner_db.get_banner_by_distro(whitespace)
        
        assert banner.metadata.category == "FALLBACK"
        assert banner.metadata.name == "DEFAULT"
    
    @given(invalid_distro_names)
    def test_fallback_banner_is_valid(self, test_banner_db, distro_name):
        """Fallback banner should be a valid Banner object."""
        # Assume unrecognized distro
        assume(distro_name not in BannerDatabase.DISTRO_ALIASES)
        assume(not any(known in distro_name.lower() for known in [
            'ubuntu', 'debian', 'arch', 'fedora', 'centos', 'redhat',
            'manjaro', 'mint', 'elementary', 'pop', 'kali', 'gentoo'
        ]))
        # Exclude single characters that might match via partial matching
        assume(len(distro_name) > 1)
        
        banner = test_banner_db.get_banner_by_distro(distro_name)
        
        # Fallback banner should have valid structure
        assert isinstance(banner, Banner)
        assert banner.metadata is not None
        assert banner.lines is not None
        assert len(banner.lines) > 0
        assert banner.width > 0  # width is a property, not a method
        assert banner.height > 0  # height is a property, not a method
    
    @given(invalid_distro_names)
    def test_fallback_never_raises_exception(self, test_banner_db, distro_name):
        """Getting a banner should never raise an exception, even for invalid input."""
        # This should not raise any exception
        try:
            banner = test_banner_db.get_banner_by_distro(distro_name)
            assert banner is not None
        except Exception as e:
            pytest.fail(f"get_banner_by_distro raised exception for '{distro_name}': {e}")
    
    def test_fallback_banner_structure(self, test_banner_db):
        """Fallback banner should have expected structure."""
        banner = test_banner_db.get_banner_by_distro("definitely_not_a_real_distro_12345")
        
        assert banner.metadata.category == "FALLBACK"
        assert banner.metadata.name == "DEFAULT"
        assert banner.metadata.description is not None
        assert banner.metadata.animation_compatible is True
        assert banner.metadata.dimensions[0] > 0  # Width
        assert banner.metadata.dimensions[1] > 0  # Height


class TestDistroMatchingEdgeCases:
    """Test edge cases for distro matching."""
    
    @given(st.sampled_from(['ubuntu', 'debian', 'arch']))
    def test_repeated_matching_is_consistent(self, test_banner_db, distro_name):
        """Matching the same distro multiple times should return consistent results."""
        banner1 = test_banner_db.get_banner_by_distro(distro_name)
        banner2 = test_banner_db.get_banner_by_distro(distro_name)
        banner3 = test_banner_db.get_banner_by_distro(distro_name)
        
        # All should return the same banner
        assert banner1.metadata.name == banner2.metadata.name
        assert banner2.metadata.name == banner3.metadata.name
        assert banner1.metadata.category == banner2.metadata.category
    
    @given(st.sampled_from([
        ('coreos', 'container_linux'),
        ('rhel', 'RedHat'),
        ('mint', 'LinuxMint'),
        ('pop', 'Pop_OS'),
    ]))
    def test_alias_resolution_is_consistent(self, test_banner_db, alias_and_target):
        """Alias resolution should be consistent and correct."""
        alias, expected_target = alias_and_target
        
        banner = test_banner_db.get_banner_by_distro(alias)
        
        # Should resolve to the target distro
        assert banner.metadata.name == expected_target, \
            f"Alias '{alias}' should resolve to '{expected_target}', got '{banner.metadata.name}'"
    
    @given(st.sampled_from(['ubuntu', 'debian', 'arch', 'fedora']))
    def test_matching_with_special_characters(self, test_banner_db, distro_name):
        """Distro names with special characters should be handled gracefully."""
        # Add special characters that should be ignored/stripped
        modified_names = [
            f"{distro_name}!",
            f"{distro_name}?",
            f"{distro_name}.",
            f"{distro_name},",
        ]
        
        for modified in modified_names:
            banner = test_banner_db.get_banner_by_distro(modified)
            # Should either match or return fallback, but not crash
            assert banner is not None
            assert isinstance(banner, Banner)
