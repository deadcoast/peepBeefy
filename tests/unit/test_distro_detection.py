"""Unit tests for distro-specific banner detection."""

import pytest
from pathlib import Path
from src.banner import BannerDatabase, Banner, BannerMetadata


class TestDistroDetection:
    """Test distro-specific ASCII art detection functionality."""
    
    @pytest.fixture
    def banner_db(self, tmp_path):
        """Create a BannerDatabase with test data."""
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        
        # Create a test ASCII database file
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
      _,met$$$$$gg.
   ,g$$$$$$$$$$$$$$$P.
 ,g$$P"     YYY$$.".
,$$P'              `$$$.
',$$P       ,ggs.     `$$b:
`d$$'     ,$P"'   .    $$$
 $$P      d$'     ,    $$P
 $$:      $$.   -    ,d$$'
 $$;      Y$b._   _,d$P'
 Y$$.    `.`"Y$$$$P"'
 `$$b      "-.__
  `Y$$
   `Y$$.
     `$$b.
       `Y$$b.
          `"Y$b._
              `YYY
---
---
LINUX:RedHat
# author: Test Author
# description: Red Hat Enterprise Linux
           .MMM..:MMMMMMM
          MMMMMMMMMMMMMMMMMM
          MMMMMMMMMMMMMMMMMMMM.
         MMMMMMMMMMMMMMMMMMMMMM
        ,MMMMMMMMMMMMMMMMMMMMMM:
        MMMMMMMMMMMMMMMMMMMMMMMM
  .MMMM'  MMMMMMMMMMMMMMMMMMMMMM
 MMMMMM    `MMMMMMMMMMMMMMMMMMMM.
MMMMMMMM      MMMMMMMMMMMMMMMMMM .
MMMMMMMMM.       `MMMMMMMMMMMMM' .M
MMMMMMMMMMM.                     .MM
MMMMMMMMMMMMM.                 .MMMM
 MMMMMMMMMMMMMMMM.             MMMMMM
  MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
   MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM:
    MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
     `MMMMMMMMMMMMMMMMMMMMMMMMMMMM:
        MMMMMMMMMMMMMMMMMMMMMMMM:
           `MMMMMMMMMMMMMMMMMM'
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
.cccccccccccccc.          .cccccc.
:cccccccccccccc            cccccc:
cccccccccccccc;            ;cccccc
ccccccccccccccc.          .ccccccc
ccccccccccccccc:          :ccccccc
ccccccccccccccccc.      .cccccccc.
'cccccccccccccccccc;..;ccccccccc'
 ;cccccccccccccccccccccccccccc;
  .cccccccccccccccccccccccccc.
    'ccccccccccccccccccccccc.
      .:ccccccccccccccccc:.
        .';:cccccccccc:;'.
            .........
---
"""
        ascii_file.write_text(test_content)
        
        db = BannerDatabase(assets_dir)
        return db
    
    def test_exact_case_insensitive_match(self, banner_db):
        """Test exact case-insensitive matching."""
        # Test lowercase
        banner = banner_db.get_banner_by_distro("ubuntu")
        assert banner.metadata.name == "Ubuntu"
        
        # Test uppercase
        banner = banner_db.get_banner_by_distro("UBUNTU")
        assert banner.metadata.name == "Ubuntu"
        
        # Test mixed case
        banner = banner_db.get_banner_by_distro("UbUnTu")
        assert banner.metadata.name == "Ubuntu"
    
    def test_alias_mapping(self, banner_db):
        """Test distro name alias support."""
        # Test CoreOS alias
        banner = banner_db.get_banner_by_distro("coreos")
        assert banner.metadata.name == "container_linux"
        
        # Test Red Hat alias
        banner = banner_db.get_banner_by_distro("rhel")
        assert banner.metadata.name == "RedHat"
        
        # Test with spaces
        banner = banner_db.get_banner_by_distro("red hat")
        assert banner.metadata.name == "RedHat"
    
    def test_partial_word_matching(self, banner_db):
        """Test partial word matching fallback."""
        # This should match "Debian" by partial word match
        banner = banner_db.get_banner_by_distro("deb")
        assert banner.metadata.name == "Debian"
    
    def test_unrecognized_distro_fallback(self, banner_db):
        """Test fallback banner for unrecognized distros."""
        banner = banner_db.get_banner_by_distro("nonexistent_distro")
        assert banner.metadata.category == "FALLBACK"
        assert banner.metadata.name == "DEFAULT"
    
    def test_empty_distro_name(self, banner_db):
        """Test handling of empty distro name."""
        banner = banner_db.get_banner_by_distro("")
        assert banner.metadata.category == "FALLBACK"
    
    def test_whitespace_handling(self, banner_db):
        """Test that whitespace is properly stripped."""
        banner = banner_db.get_banner_by_distro("  ubuntu  ")
        assert banner.metadata.name == "Ubuntu"
    
    def test_prefix_matching(self, banner_db):
        """Test case-insensitive prefix matching."""
        # "arch" should match "Arch"
        banner = banner_db.get_banner_by_distro("arch")
        assert banner.metadata.name == "Arch"
        
        # "deb" should match "Debian" via prefix
        banner = banner_db.get_banner_by_distro("deb")
        assert banner.metadata.name == "Debian"


class TestDistroAliases:
    """Test the DISTRO_ALIASES mapping."""
    
    def test_aliases_exist(self):
        """Test that common distro aliases are defined."""
        aliases = BannerDatabase.DISTRO_ALIASES
        
        # Test some common aliases
        assert 'coreos' in aliases
        assert aliases['coreos'] == 'container_linux'
        
        assert 'rhel' in aliases
        assert aliases['rhel'] == 'redhat'
        
        assert 'mint' in aliases
        assert aliases['mint'] == 'linuxmint'
        
        assert 'pop' in aliases
        assert aliases['pop'] == 'pop_os'
    
    def test_aliases_lowercase(self):
        """Test that all alias keys are lowercase."""
        aliases = BannerDatabase.DISTRO_ALIASES
        for key in aliases.keys():
            assert key == key.lower(), f"Alias key '{key}' should be lowercase"
