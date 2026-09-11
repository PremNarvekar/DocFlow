import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Force Celery to run tasks synchronously during tests
import tasks
tasks.app.conf.task_always_eager = True
tasks.app.conf.task_eager_propagates = True

from main import app, store

client = TestClient(app)

@pytest.fixture(scope="module")
def auth_headers():
    """Register a user and return Auth headers."""
    import uuid
    email = f"test_{uuid.uuid4()}@example.com"
    password = "testpassword123"
    
    # Register
    reg_response = client.post("/auth/register", json={"email": email, "password": password})
    assert reg_response.status_code == 201
    
    # Login
    login_response = client.post("/auth/token", data={"username": email, "password": password})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}", "user_id": reg_response.json()["user_id"]}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch("main.process_document_task.delay")
def test_async_document_upload(mock_delay, auth_headers):
    """Test that POST /documents returns 202 and delegates to Celery."""
    mock_task = MagicMock()
    mock_task.id = "mock-task-123"
    mock_delay.return_value = mock_task

    file_content = b"%PDF-1.4 mock pdf content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    
    response = client.post("/documents", files=files, headers={"Authorization": auth_headers["Authorization"]})
    
    assert response.status_code == 202
    data = response.json()
    assert "document_id" in data
    assert data["task_id"] == "mock-task-123"
    assert data["status"] == "PENDING"
    mock_delay.assert_called_once()


def test_task_status(auth_headers):
    """Test task status retrieval using DB."""
    from db.session import SessionLocal
    from db.models import DocumentRecord, DocumentStatus
    import uuid
    
    test_id = str(uuid.uuid4())
    test_task_id = f"mock-task-{test_id}"
    
    with SessionLocal() as db:
        record = DocumentRecord(
            id=test_id,
            user_id=auth_headers["user_id"],
            filename="test.pdf",
            task_id=test_task_id,
            status=DocumentStatus.COMPLETED.value,
            extracted_data={"document_id": test_id, "status": "processed"}
        )
        db.add(record)
        db.commit()

    response = client.get(f"/tasks/{test_task_id}", headers={"Authorization": auth_headers["Authorization"]})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["result"]["document_id"] == test_id


@patch("main.get_router")
def test_rag_endpoint(mock_get_router, auth_headers):
    """Test the RAG ask endpoint."""
    from db.session import SessionLocal
    from db.models import DocumentRecord, DocumentStatus
    import uuid
    
    doc_id = str(uuid.uuid4())
    
    # Insert DB record
    with SessionLocal() as db:
        record = DocumentRecord(
            id=doc_id,
            user_id=auth_headers["user_id"],
            filename="test.pdf",
            status=DocumentStatus.COMPLETED.value
        )
        db.add(record)
        db.commit()

    # Insert a dummy document chunk
    store.add_document(doc_id, "Invoice total is $500", {"file_name": "test.pdf"})
    
    mock_router = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "The total is $500."
    mock_response.latency_ms = 150
    mock_response.model = "mock-model"
    mock_response.provider = "mock-provider"
    mock_router.generate.return_value = mock_response
    mock_get_router.return_value = mock_router

    response = client.post(
        f"/documents/{doc_id}/ask",
        json={"query": "What is the total?"},
        headers={"Authorization": auth_headers["Authorization"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == doc_id
    assert data["answer"] == "The total is $500."
    assert "metadata" in data
    assert data["metadata"]["chunks_used"] > 0
