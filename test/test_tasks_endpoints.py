from datetime import datetime, date
from typing import Any, Dict, Optional

from fastapi import status

from main import app
from dependencies import get_db_connection


class FakeConnTasks:
    """Minimal fake asyncpg connection for tasks endpoints in tests."""

    def __init__(self, scenario: str):
        self.scenario = scenario

    async def fetchrow(self, query: str, *args: Any) -> Optional[Dict[str, Any]]:
        # create_task uses INSERT ... RETURNING; get_task uses SELECT ... WHERE id=$1; update uses UPDATE ... RETURNING
        if self.scenario == "create_ok":
            # Map args according to tasks.create_task order
            title, description, status_id, creator_id, assignee_id, deadline_start, deadline_end = args
            return {
                "id": 101,
                "title": title,
                "description": description,
                "status_id": status_id,
                "creator_id": creator_id,
                "assignee_id": assignee_id,
                "deadline_start": deadline_start,
                "deadline_end": deadline_end,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        if self.scenario == "get_not_found":
            return None
        if self.scenario == "get_ok":
            return {
                "id": 101,
                "title": "Implement API",
                "description": "Create endpoints",
                "status_id": 1,
                "creator_id": 1,
                "assignee_id": 2,
                "deadline_start": date.today(),
                "deadline_end": date.today(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        if self.scenario == "update_not_found":
            return None
        if self.scenario == "update_ok":
            # Update returns the whole row after applying changes; emulate minimal
            return {
                "id": 101,
                "title": "Updated title",
                "description": "Updated description",
                "status_id": 2,
                "creator_id": 1,
                "assignee_id": 3,
                "deadline_start": date.today(),
                "deadline_end": date.today(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        raise AssertionError(f"Unknown scenario: {self.scenario}")

    async def fetchval(self, query: str, *args: Any) -> Optional[int]:
        # delete_task uses DELETE ... RETURNING id
        if self.scenario == "delete_ok":
            return args[0] if args else 101
        if self.scenario == "delete_not_found":
            return None
        raise AssertionError(f"Unknown scenario for fetchval: {self.scenario}")


def test_create_task_success(client):
    payload = {
        "title": "Implement API",
        "description": "Create endpoints",
        "status_id": 1,
        "creator_id": 1,
        "assignee_id": 2,
        "deadline_start": date.today().isoformat(),
        "deadline_end": date.today().isoformat(),
    }

    async def override_conn():
        yield FakeConnTasks("create_ok")

    app.dependency_overrides[get_db_connection] = override_conn

    resp = client.post("/tasks/", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    data = resp.json()

    assert data["id"] == 101
    assert data["title"] == payload["title"]
    assert data["status_id"] == payload["status_id"]
    assert data["creator_id"] == payload["creator_id"]
    assert data["assignee_id"] == payload["assignee_id"]
    assert "created_at" in data and data["created_at"]
    assert "updated_at" in data and data["updated_at"]


def test_get_task_not_found(client):
    async def override_conn():
        yield FakeConnTasks("get_not_found")

    app.dependency_overrides[get_db_connection] = override_conn

    resp = client.get("/tasks/424242")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in resp.json()["detail"].lower()


def test_get_task_success(client):
    async def override_conn():
        yield FakeConnTasks("get_ok")

    app.dependency_overrides[get_db_connection] = override_conn

    resp = client.get("/tasks/101")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["id"] == 101
    assert data["title"] == "Implement API"
    assert data["status_id"] == 1
    assert data["creator_id"] == 1
    assert data["assignee_id"] == 2
    assert "created_at" in data and data["created_at"]
    assert "updated_at" in data and data["updated_at"]


def test_update_task_not_found(client):
    async def override_conn():
        yield FakeConnTasks("update_not_found")

    app.dependency_overrides[get_db_connection] = override_conn

    # provide one field to trigger UPDATE path rather than validation error
    resp = client.put("/tasks/424242", json={"title": "X"})
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in resp.json()["detail"].lower()



def test_update_task_success(client):
    async def override_conn():
        yield FakeConnTasks("update_ok")

    app.dependency_overrides[get_db_connection] = override_conn

    payload = {
        "title": "Updated title",
        "description": "Updated description",
        "status_id": 2,
        "assignee_id": 3,
    }
    resp = client.put("/tasks/101", json=payload)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["id"] == 101
    assert data["title"] == "Updated title"
    assert data["status_id"] == 2
    assert data["assignee_id"] == 3
    assert "updated_at" in data and data["updated_at"]



def test_delete_task_not_found(client):
    async def override_conn():
        yield FakeConnTasks("delete_not_found")

    app.dependency_overrides[get_db_connection] = override_conn

    resp = client.delete("/tasks/424242")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in resp.json()["detail"].lower()



def test_delete_task_success(client):
    async def override_conn():
        yield FakeConnTasks("delete_ok")

    app.dependency_overrides[get_db_connection] = override_conn

    resp = client.delete("/tasks/101")
    assert resp.status_code == status.HTTP_204_NO_CONTENT
