"""Pytest configuration for peepBeefy tests.

Adds src directory to Python path so modules can be imported.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))
