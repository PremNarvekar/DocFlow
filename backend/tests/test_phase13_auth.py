import os
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from main import app
from db.session import SessionLocal
from db.models import DocumentRecord, DocumentStatus

client = TestClient(app)

@pytest.fixture
def test_user_a():
    email = f"user_a_{uuid4()}@example.com"
    password = "password123"
    reg = client.post("/auth/register", json={"email": email, "password": password})
    res = client.post("/auth/token", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}", "user_id": reg.json()["user_id"]}

@pytest.fixture
def test_user_b():
    email = f"user_b_{uuid4()}@example.com"
    password = "password123"
    reg = client.post("/auth/register", json={"email": email, "password": password})
    res = client.post("/auth/token", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}", "user_id": reg.json()["user_id"]}


def test_document_scoping_isolation(test_user_a, test_user_b):
    """Test that User B cannot access User A's document task."""
    task_id = f"mock-task-{uuid4()}"
    doc_id = str(uuid4())
    
    # User A manually creates a document record
    with SessionLocal() as db:
        record = DocumentRecord(
            id=doc_id,
            user_id=test_user_a["user_id"],
            filename="test.pdf",
            task_id=task_id,
            status=DocumentStatus.COMPLETED.value
        )
        db.add(record)
        db.commit()

    # User A checks status - OK
    status_a = client.get(f"/tasks/{task_id}", headers={"Authorization": test_user_a["Authorization"]})
    assert status_a.status_code == 200

    # User B checks status - Not Found / Unauthorized
    status_b = client.get(f"/tasks/{task_id}", headers={"Authorization": test_user_b["Authorization"]})
    assert status_b.status_code == 404
