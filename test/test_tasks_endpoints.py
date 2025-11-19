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
        # create_task uses INSERT ... RETURNING; get_task uses SELECT ... WHERE id=$1
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
        raise AssertionError(f"Unknown scenario: {self.scenario}")


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
