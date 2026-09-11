import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from main import app
from db.session import SessionLocal
from db.models import User, DocumentRecord, DocumentStatus

client = TestClient(app)

@pytest.fixture
def auth_headers():
    email = f"quota_test_{uuid4()}@example.com"
    password = "password123"
    client.post("/auth/register", json={"email": email, "password": password})
    res = client.post("/auth/token", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

from unittest.mock import patch

def test_database_upload_quota(auth_headers: dict):
    """Test that a user cannot upload more documents than their upload_quota."""
    
    # Simulate reaching the quota
    with SessionLocal() as db_session:
        # Get the most recently created user (the one from auth_headers)
        user = db_session.query(User).order_by(User.created_at.desc()).first()
        assert user is not None
        user.upload_quota = 2
        user.uploads_used = 2
        db_session.commit()
    
    # Try to upload a new document (3rd, exceeding quota of 2)
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
    
    with patch("main.process_document_task") as mock_task:
        response = client.post(
            "/documents",
            headers=auth_headers,
            files={"file": ("test_quota.pdf", pdf_content, "application/pdf")}
        )
        
        assert response.status_code == 402
        assert "quota" in response.json()["detail"].lower()
        
        # Reset quota and verify upload succeeds
        with SessionLocal() as db_session:
            user = db_session.query(User).order_by(User.created_at.desc()).first()
            user.uploads_used = 1
            db_session.commit()
        
        response = client.post(
            "/documents",
            headers=auth_headers,
            files={"file": ("test_quota_success.pdf", pdf_content, "application/pdf")}
        )
        
        assert response.status_code == 202
        assert response.json()["status"] == "PENDING"
        
        with SessionLocal() as db_session:
            user = db_session.query(User).order_by(User.created_at.desc()).first()
            assert user.uploads_used == 2

def test_api_rate_limiter_rag_chat(auth_headers: dict):
    """Test that the slowapi rate limiter throttles /ask requests."""
    
    with SessionLocal() as db_session:
        user = db_session.query(User).order_by(User.created_at.desc()).first()
        
        # Create a dummy document so we don't get 404
        doc_id = str(uuid4())
        doc = DocumentRecord(
            id=doc_id,
            user_id=user.id,
            filename="rag_test.pdf",
            task_id="task-123",
            status=DocumentStatus.COMPLETED.value,
            extracted_data={"mock": "data"}
        )
        db_session.add(doc)
        db_session.commit()
    
    # The limit is 5/minute. We will spam 6 requests.
    payload = {"query": "Hello world"}
    
    for i in range(5):
        # We mock the return or we let it hit the real store and fail 404 (document not in ChromaDB)
        # It doesn't matter, rate limiter kicks in BEFORE endpoint execution
        res = client.post(f"/documents/{doc_id}/ask", headers=auth_headers, json=payload)
        # It might be 404 Document not found or 500 because Chroma is missing it, but it shouldn't be 429 yet
        assert res.status_code != 429
        
    # The 6th request should be rate-limited
    res_throttled = client.post(f"/documents/{doc_id}/ask", headers=auth_headers, json=payload)
    assert res_throttled.status_code == 429
    assert "Rate limit exceeded" in res_throttled.json()["error"]
