"""
Document classifier — determines the type of a document.

CHANGED from original:
- Original: hardcoded google.genai client + GEMINI_API_KEY import
- Now: uses AI Router — provider is selected automatically
- PRESERVED: DocumentType enum, DocumentClassification model,
  classify_document() signature, empty-text → UNKNOWN behavior

The classifier sends a PREVIEW of the document (first 1000 chars)
to the AI for classification. This keeps API costs low and latency fast.

CHANGED from original: 500 chars → 1000 chars.
WHY: 500 chars was too aggressive. Documents with headers, logos, and
     whitespace often had classification-relevant content past position 500.
     1000 chars captures most first-page content while still being cheap.
"""

from enum import Enum

from pydantic import BaseModel

from ai import get_router, AITask


CLASSIFICATION_PREVIEW_CHARS = 1000


class DocumentType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    MEDICAL_REPORT = "medical_report"
    FINANCIAL_STATEMENT = "financial_statement"
    UNKNOWN = "unknown"


class DocumentClassification(BaseModel):
    document_type: DocumentType


CLASSIFICATION_SYSTEM_PROMPT = (
    "You are a document classification system. "
    "Classify the document into exactly one of these "
    "categories: invoice, contract, medical_report, "
    "financial_statement, or unknown. "
    "Return unknown if the document does not clearly "
    "belong to one of the supported categories."
)


def classify_document(text: str) -> DocumentClassification:

    if not text or not text.strip():
        return DocumentClassification(
            document_type=DocumentType.UNKNOWN
        )

    preview = text[:CLASSIFICATION_PREVIEW_CHARS]

    router = get_router()

    response = router.parse(
        prompt=preview,
        schema=DocumentClassification,
        system_instruction=CLASSIFICATION_SYSTEM_PROMPT,
        task=AITask.DOCUMENT_CLASSIFICATION,
    )

    return DocumentClassification.model_validate_json(
        response.text
    )