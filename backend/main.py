import shutil
import uuid
from pathlib import Path
from uuid import uuid4
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends, status, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from db.session import engine, Base, get_db
from db.models import DocumentRecord, DocumentStatus, User
from auth import get_current_user, get_password_hash, verify_password, create_access_token

from pipeline.store import DocumentStore
from ai import get_router, AITask
from tasks import process_document_task

from fastapi.middleware.cors import CORSMiddleware

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="DocFlow API",
    version="1.0.0",
    description="Document intelligence API with Async Celery Tasks, RAG, and JWT Auth",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for production Netlify deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

store = DocumentStore()
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class RAGQuery(BaseModel):
    query: str

class UserCreate(BaseModel):
    email: str
    password: str


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }


from config import PROVIDER_API_KEYS, PROVIDER_MODELS

@app.get("/providers/status")
def provider_status() -> list[dict]:
    """Returns the live status of AI providers based on loaded API keys."""
    status_list = []
    # Map backend keys to nice UI names
    ui_names = {
        "gemini": "Gemini",
        "xai": "Grok",
        "groq": "Groq",
        "cerebras": "Cerebras",
        "mistral": "Mistral",
        "openrouter": "OpenRouter",
        "huggingface": "Hugging Face"
    }
    
    for provider_id, name in ui_names.items():
        key = PROVIDER_API_KEYS.get(provider_id)
        model = PROVIDER_MODELS.get(provider_id) or "default"
        is_available = bool(key and key != "dummy")
        
        # Only include providers that are actually configured/available!
        if is_available:
            status_list.append({
                "name": name,
                "model": model,
                "status": "Available",
                "latency": "..."
            })
            
    return status_list


@app.post("/auth/register", status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    hashed_password = get_password_hash(user_in.password)
    user = User(
        id=str(uuid.uuid4()),
        email=user_in.email,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully", "user_id": user.id}


@app.post("/auth/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 compatible token login, get an access token for future requests."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/documents", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    provider: str = Form("auto"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF document. Returns immediately with a task_id while processing continues in the background.
    """
    if current_user.uploads_used >= current_user.upload_quota:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="You have exceeded your document upload quota."
        )

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported"
        )

    # Save file locally
    document_id = str(uuid.uuid4())
    task_id = f"task-{uuid.uuid4()}"
    file_path = UPLOAD_DIR / f"{document_id}.pdf"

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(exc)}"
        )

    # Update quota and persist state
    current_user.uploads_used += 1
    
    record = DocumentRecord(
        id=document_id,
        user_id=current_user.id,
        filename=file.filename,
        task_id=task_id,
        status=DocumentStatus.PENDING.value
    )
    db.add(record)
    db.commit()

    # Process in background
    background_tasks.add_task(process_document_task, document_id, str(file_path), file.filename, provider)

    return {
        "document_id": document_id,
        "task_id": task_id,
        "status": record.status
    }


from datetime import datetime

class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    task_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

@app.get("/documents", response_model=list[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all documents uploaded by the current user."""
    records = db.query(DocumentRecord).filter(DocumentRecord.user_id == current_user.id).order_by(DocumentRecord.created_at.desc()).all()
    return records

@app.get("/tasks/{task_id}")
def get_task_status(
    task_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Check the status of a document processing task via PostgreSQL, enforcing scoping."""
    record = db.query(DocumentRecord).filter(DocumentRecord.task_id == task_id).first()
    
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")
        
    response = {
        "task_id": task_id,
        "document_id": record.id,
        "status": record.status,
    }
    
    if record.status == DocumentStatus.COMPLETED.value:
        response["result"] = record.extracted_data
    elif record.status == DocumentStatus.FAILED.value:
        response["error"] = record.error_message
        
    return response


@app.post("/documents/{document_id}/ask")
@limiter.limit("5/minute")
def ask_document(
    request: Request,
    document_id: str, 
    payload: RAGQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """RAG-based Question Answering against a specific document, scoped to current user."""
    # Enforce multi-tenancy check
    record = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")

    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        search_results = store.search(query, limit=5, document_id=document_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(exc)}") from exc
        
    if not search_results or not search_results.get("documents") or not search_results["documents"][0]:
        raise HTTPException(status_code=404, detail="Document not found or no relevant content extracted.")
        
    chunks = search_results["documents"][0]
    context_text = "\n\n---\n\n".join(chunks)

    prompt = (
        f"Context from document:\n{context_text}\n\n"
        f"Question:\n{query}"
    )

    system_instruction = (
        "You are an expert document analysis assistant. Answer the user's question "
        "using ONLY the provided document context. If the context does not contain "
        "the answer, explicitly state that you cannot answer based on the document. "
        "Do not invent or assume outside information."
    )

    router = get_router()
    try:
        response = router.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            task=AITask.GENERAL_QUERY,
        )
        
        return {
            "document_id": document_id,
            "query": query,
            "answer": response.text,
            "metadata": {
                "chunks_used": len(chunks),
                "latency_ms": response.latency_ms,
                "model": response.model,
                "provider": response.provider,
            }
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(exc)}") from exc