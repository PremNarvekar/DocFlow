import os
from pathlib import Path
from typing import Any

from celery import Celery

from pipeline.anomaly import check_invoice
from pipeline.classifier import DocumentType, classify_document
from pipeline.extractor import extract_document
from pipeline.loader import load_and_extract
from pipeline.store import DocumentStore


# Initialize Celery app
# Defaults to localhost Redis unless overriden by env
REDIS_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

app = Celery(
    "docflow_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Global store instance for the worker
store = DocumentStore()


@app.task(name="process_document_task")
def process_document_task(
    document_id: str,
    file_path: str,
    file_name: str,
) -> dict[str, Any]:
    """Background task to process a document pipeline."""
    
    path_obj = Path(file_path)
    
    try:
        # 1. Load and extract text
        loaded_document = load_and_extract(str(path_obj))

        full_text = "\n".join(
            page.text
            for page in loaded_document.pages
            if page.text
        )

        if not full_text.strip():
            raise ValueError(
                "No text could be extracted from the PDF. "
                "OCR may be required."
            )

        # 2. Classify document
        classification = classify_document(full_text)

        if classification.document_type == DocumentType.UNKNOWN:
            return {
                "document_id": document_id,
                "file_name": file_name,
                "document_type": "unknown",
                "status": "unsupported_document",
            }

        # 3. Extract structured data
        extracted_data = extract_document(
            full_text,
            classification.document_type,
        )

        # 4. Anomaly Detection
        anomalies = []
        if classification.document_type == DocumentType.INVOICE:
            anomaly_report = check_invoice(extracted_data)
            anomalies = [
                {
                    "code": anomaly.code,
                    "message": anomaly.message,
                    "severity": anomaly.severity,
                    "field": anomaly.field,
                }
                for anomaly in anomaly_report.anomalies
            ]

        # 5. Semantic Chunking & Vector Storage
        store.add_document(
            document_id=document_id,
            text=full_text,
            metadata={
                "file_name": file_name,
                "document_type": classification.document_type.value,
                "page_count": loaded_document.page_count,
            },
        )

        result_payload = {
            "document_id": document_id,
            "file_name": file_name,
            "page_count": loaded_document.page_count,
            "document_type": classification.document_type.value,
            "extracted_data": extracted_data.model_dump(mode="json"),
            "anomalies": anomalies,
            "status": "processed",
        }
        
        # Persist success to PostgreSQL
        from db.session import SessionLocal
        from db.models import DocumentRecord, DocumentStatus
        
        with SessionLocal() as db:
            record = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
            if record:
                record.status = DocumentStatus.COMPLETED.value
                record.extracted_data = result_payload
                db.commit()

        return result_payload

    except Exception as exc:
        # Persist failure to PostgreSQL
        from db.session import SessionLocal
        from db.models import DocumentRecord, DocumentStatus
        
        with SessionLocal() as db:
            record = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
            if record:
                record.status = DocumentStatus.FAILED.value
                record.error_message = str(exc)
                db.commit()
                
        # Rethrow so Celery marks it as FAILURE and logs the traceback
        raise exc

    finally:
        # Cleanup temporary file
        if path_obj.exists():
            path_obj.unlink(missing_ok=True)
