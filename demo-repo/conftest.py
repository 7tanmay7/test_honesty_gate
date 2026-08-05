"""Pytest configuration for the demo repository.

Makes the ``src`` package importable from the test suite without requiring
an installation step.
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))