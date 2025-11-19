import sys
from pathlib import Path
import types
import asyncio
import pytest

# Ensure the 'src' folder is on the Python path so tests can import the app
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402


# --- Infra: prevent real DB connections during app lifespan ---
@pytest.fixture(autouse=True, scope="session")
def _patch_asyncpg_pool():
    """Patch asyncpg.create_pool to a fake in tests so TestClient startup doesn't hit real DB."""
    import asyncpg  # local import

    class _FakeAcquire:
        def __init__(self, conn):
            self._conn = conn

        async def __aenter__(self):
            return self._conn

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakePool:
        def __init__(self):
            # default connection used if someone acquires from the pool directly
            self._default_conn = object()

        def acquire(self):
            # Provide a minimal async context manager; the connection object is not used because
            # tests override the request-time dependency to inject their own fake connection.
            return _FakeAcquire(self._default_conn)

        async def close(self):
            return None

    async def fake_create_pool(*args, **kwargs):
        return FakePool()

    original = asyncpg.create_pool
    asyncpg.create_pool = fake_create_pool  # type: ignore
    try:
        yield
    finally:
        asyncpg.create_pool = original  # type: ignore


@pytest.fixture()
def client():
    """FastAPI test client with clean dependency overrides per test.

    Usage inside a test:
      - define a fake connection with methods your endpoint calls (e.g., fetchrow, execute)
      - set app.dependency_overrides[get_db_connection] = override_fn
      - perform requests via the returned client
    """
    # Make sure overrides are clean before each test
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        try:
            yield c
        finally:
            # Clean overrides after each test too
            app.dependency_overrides.clear()
