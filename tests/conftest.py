"""Main pytest configuration.

This conftest loads FastAPI dependencies only for endpoint tests.
Domain model tests use test/domain/conftest.py instead.
"""
import sys
from pathlib import Path

# Ensure the 'src' folder is on the Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Only import FastAPI dependencies if we're running endpoint tests
# Domain tests should use test/domain/conftest.py
# We check the test path to determine if we need FastAPI
import os

# Check if we're running domain tests by looking at the test path
test_path = os.environ.get('PYTEST_CURRENT_TEST', '')
if 'test/domain' not in test_path and 'domain/test' not in test_path:
    # Only load FastAPI dependencies for endpoint tests
    try:
        from conftest_endpoints import *  # noqa: F401, F403
    except ImportError:
        # If conftest_endpoints doesn't exist, continue without it
        # This allows domain tests to run without FastAPI dependencies
        pass

