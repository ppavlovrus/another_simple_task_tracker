"""Main pytest configuration.

This conftest ensures the 'src' directory is in sys.path so that
domain models can be imported. FastAPI dependencies are loaded
only for endpoint tests via conditional imports in test files.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
SRC_PATH_STR = str(SRC_PATH)

if SRC_PATH_STR not in sys.path:
    sys.path.insert(0, SRC_PATH_STR)