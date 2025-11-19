from datetime import datetime
from typing import Any, Dict, Optional

import pytest
from fastapi import status

from main import app
from dependencies import get_db_connection


class FakeConnUsers:
    """Minimal fake asyncpg connection for users endpoints in tests."""

    def __init__(self, scenario: str):
        self.scenario = scenario

    async def fetchrow(self, query: str, *args: Any) -> Optional[Dict[str, Any]]:
        if self.scenario == "create_ok":
            # Emulate row returned by INSERT ... RETURNING in users.create_user
            return {
                "id": 1,
                "username": args[0],
                "email": args[1],
                "created_at": datetime.utcnow(),
                "last_login": None,
            }
        if self.scenario == "get_not_found":
            return None
        raise AssertionError(f"Unknown scenario: {self.scenario}")


@pytest.mark.parametrize(
    "payload",
    [
        {
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret",
        }
    ],
)
def test_create_user_success(client, payload):
    async def override_conn():
        yield FakeConnUsers("create_ok")

    # Override the DB connection dependency just for this test
    app.dependency_overrides[get_db_connection] = override_conn

    resp = client.post("/users/", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    data = resp.json()

    assert data["id"] == 1
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    # last_login can be null for new users
    assert "created_at" in data and data["created_at"]
    assert "last_login" in data


def test_get_user_not_found(client):
    async def override_conn():
        yield FakeConnUsers("get_not_found")

    app.dependency_overrides[get_db_connection] = override_conn

    resp = client.get("/users/9999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in resp.json()["detail"].lower()
