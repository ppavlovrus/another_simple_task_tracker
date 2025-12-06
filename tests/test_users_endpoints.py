from datetime import datetime
from typing import Any, Dict, Optional

import asyncpg
import pytest
from fastapi import status

from main import app
from dependencies import get_db_connection


class FakeConnUsers:
    """Minimal fake asyncpg connection for users endpoints in tests.

    Scenarios:
      - create_ok: POST returns a valid row
      - get_not_found: GET returns None
      - duplicate_username / duplicate_email: raise UniqueViolationError
      - boom: raise generic unexpected error
      - get_ok: GET returns a valid row
    """

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
        if self.scenario == "get_ok":
            return {
                "id": 7,
                "username": "bob",
                "email": "b@example.com",
                "created_at": datetime.utcnow(),
                "last_login": None,
            }
        if self.scenario == "update_ok":
            return {
                "id": 1,
                "username": "newname",
                "email": "new@example.com",
                "created_at": datetime.utcnow(),
                "last_login": None,
            }
        if self.scenario == "get_not_found" or self.scenario == "update_not_found":
            return None
        if self.scenario == "duplicate_username":
            raise asyncpg.UniqueViolationError("username already exists")
        if self.scenario == "duplicate_email":
            raise asyncpg.UniqueViolationError("email already exists")
        if self.scenario == "boom":
            raise RuntimeError("boom")
        raise AssertionError(f"Unknown scenario: {self.scenario}")

    async def fetchval(self, query: str, *args: Any):
        # Used by DELETE endpoint tests; decide by scenario
        if self.scenario == "delete_ok":
            return 1
        if self.scenario == "delete_not_found":
            return None
        if self.scenario == "delete_fk_err":
            raise asyncpg.ForeignKeyViolationError("fk")
        if self.scenario == "boom":
            raise RuntimeError("boom")
        raise AssertionError(f"Unknown scenario for fetchval: {self.scenario}")


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

def test_create_user_duplicate_username(client):
    async def override_conn():
        yield FakeConnUsers("duplicate_username")

    app.dependency_overrides[get_db_connection] = override_conn

    resp = client.post(
        "/users/", json={"username": "alice", "email": "alice@example.com", "password": "x"}
    )
    assert resp.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in resp.json()["detail"].lower()


# --- Additional tests for users endpoints ---

def test_create_user_500_error(client):
    async def override_conn():
        yield FakeConnUsers("boom")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.post(
        "/users/", json={"username": "alice", "email": "a@e.com", "password": "x"}
    )
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_create_user_validation_422_missing_fields(client):
    # No override needed; validation happens before dependency is used
    resp = client.post("/users/", json={})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_user_validation_422_wrong_types(client):
    resp = client.post("/users/", json={"username": 123, "email": 456, "password": 789})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_user_response_no_password(client):
    async def override_conn():
        yield FakeConnUsers("create_ok")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.post(
        "/users/", json={"username": "alice", "email": "a@e.com", "password": "x"}
    )
    assert resp.status_code == status.HTTP_201_CREATED
    assert "password" not in resp.json()


def test_get_user_success(client):
    async def override_conn():
        yield FakeConnUsers("get_ok")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.get("/users/7")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert set(["id", "username", "email", "created_at", "last_login"]).issubset(data.keys())


def test_get_user_invalid_id_422(client):
    resp = client.get("/users/not-an-int")
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_user_500_error(client):
    async def override_conn():
        yield FakeConnUsers("boom")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.get("/users/1")
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_update_user_no_fields_400(client):
    async def override_conn():
        yield FakeConnUsers("update_ok")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.put("/users/1", json={})
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "at least one field" in resp.json()["detail"].lower()


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "newname"},
        {"email": "new@example.com"},
        {"password": "newpass"},
        {"username": "u", "email": "e@example.com"},
        {"email": "e@example.com", "password": "p"},
        {"username": "u", "password": "p"},
        {"username": "u", "email": "e@example.com", "password": "p"},
    ],
)
def test_update_user_success_variants(client, payload):
    async def override_conn():
        yield FakeConnUsers("update_ok")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.put("/users/1", json=payload)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert set(["id", "username", "email", "created_at", "last_login"]).issubset(data.keys())
    assert "password" not in data


def test_update_user_not_found_404(client):
    async def override_conn():
        yield FakeConnUsers("update_not_found")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.put("/users/9999", json={"email": "x@example.com"})
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_update_user_unique_conflict_409(client):
    async def override_conn():
        yield FakeConnUsers("duplicate_email")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.put("/users/1", json={"email": "dupe@example.com"})
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_update_user_invalid_id_422(client):
    resp = client.put("/users/not-an-int", json={"email": "x@example.com"})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_user_500_error(client):
    async def override_conn():
        yield FakeConnUsers("boom")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.put("/users/1", json={"email": "x@example.com"})
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_delete_user_success_204(client):
    async def override_conn():
        yield FakeConnUsers("delete_ok")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.delete("/users/1")
    assert resp.status_code == status.HTTP_204_NO_CONTENT
    assert resp.text == ""


def test_delete_user_not_found_404(client):
    async def override_conn():
        yield FakeConnUsers("delete_not_found")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.delete("/users/9999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_delete_user_fk_violation_400(client):
    async def override_conn():
        yield FakeConnUsers("delete_fk_err")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.delete("/users/1")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_user_invalid_id_422(client):
    resp = client.delete("/users/not-an-int")
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_delete_user_500_error(client):
    async def override_conn():
        yield FakeConnUsers("boom")
    app.dependency_overrides[get_db_connection] = override_conn
    resp = client.delete("/users/1")
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
